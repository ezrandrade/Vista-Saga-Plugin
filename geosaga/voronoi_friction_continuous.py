"""Voronoi com atrito em vetor direto (1.4.0): modelo contínuo, sem grade.

Modelo (versão contínua do atrito do Vista SAGA): para um polo G e um ponto x, o custo é

    A(G → x) = ∫₀^D s · f(G + s·u) ds,

ao longo do segmento reto G → x (D = |x − G|, u = direção), com f = nota de atrito do polígono
atravessado. Com nota uniforme, A = f·D²/2, e o Com Massa e Atrito (menor A / M) se reduz a M/d².
É o limite do modelo discreto da guia Raster quando a célula tende a zero; no caso de teste
validado, coincide com o Vista SAGA em 99,50% (sem massa) e 99,60% (com massa) das células.

Cálculo exato, sem amostragem: com τ = fração do segmento até cada cruzamento com a borda de um
polígono de nota f, A = D² × [Σ ± f·τ²/2 + f(x)/2] (− ao entrar, + ao sair; anéis orientados com o
interior à esquerda). Área sem polígono e feições sem nota são barreira: o ponto não recebe
resultado e nenhum segmento passa por elas. Em sobreposições, vale a última feição.

As fronteiras entre as regiões não têm fórmula fechada: são traçadas numericamente (ver
``friction_voronoi_polygons``) até uma tolerância declarada.
"""
import math

import numpy as np

# Limite de elementos por bloco (pontos × arestas) nas matrizes de cruzamento.
_BLOCK = 1_500_000
# Limite de pares (ponto, aresta candidata) por bloco no cálculo com índice angular.
_PAIRS = 2_000_000
# Deslocamento ínfimo do polo nos testes de cruzamento (unidades do SRC, ~1 µm em metros): sem ele,
# um segmento que passa exatamente por um vértice (comum com polos no centro de células e polígonos
# em coordenadas redondas) conta o cruzamento errado. Efeito no custo: desprezível.
_NUDGE_X, _NUDGE_Y = 1.1e-6, 0.7e-6


class FrictionSurface:
    """Polígonos de atrito preparados para o cálculo vetorizado (arestas orientadas)."""

    def __init__(self, features, *, cancelled=None, outside_rating=None):
        """features: [(wkb, nota > 0 ou None)] na ordem das feições.

        outside_rating: nota da área sem polígono (e das feições sem nota) para a PASSAGEM; ela nunca
        recebe resultado. None = barreira (sem passagem).
        """
        from osgeo import ogr
        from .gdal_scope import gdal_exceptions
        with gdal_exceptions():
            geoms = []
            for wkb, rating in features:
                if rating is None:
                    continue
                rating = float(rating)
                if not math.isfinite(rating) or rating <= 0:
                    raise ValueError('Nota de atrito inválida: {0}. Use valor maior que 0 (para quase sem '
                                     'atrito, um valor pequeno, como 0,1).'.format(rating))
                geometry = ogr.CreateGeometryFromWkb(bytes(wkb))
                if geometry is None or geometry.IsEmpty():
                    continue
                if not geometry.IsValid():
                    geometry = geometry.MakeValid()
                geoms.append((geometry, rating))
            if not geoms:
                raise ValueError('Nenhum polígono com nota de atrito.')
            # Sobreposições: vale a última feição (cada uma perde o que as seguintes cobrem).
            resolved, covered = [], None
            for geometry, rating in reversed(geoms):
                if cancelled and cancelled():
                    raise InterruptedError('Voronoi cancelado.')
                own = geometry if covered is None else geometry.Difference(covered)
                covered = geometry.Clone() if covered is None else covered.Union(geometry)
                if own is not None and not own.IsEmpty() and own.GetArea() > 0:
                    resolved.append((own, rating))
            resolved.reverse()
            self.union = covered
            edges, starts, ratings = [], [], []
            # Largura média (2 × área / perímetro) e envelope de cada polígono: base do espaçamento
            # automático da busca.
            self.widths = []
            for own, rating in resolved:
                perimeter = _length(own.Boundary())
                if perimeter > 0:
                    self.widths.append((2.0 * own.GetArea() / perimeter, own.GetEnvelope()))
            for own, rating in resolved:
                rings = _polygon_rings(own)
                if not rings:
                    continue
                starts.append(sum(len(e) for e in edges))
                ratings.append(rating)
                block = []
                for ring, exterior in rings:
                    block.extend(_ring_edges(ring, ccw=exterior))
                edges.append(block)
            self.edges = np.array([e for block in edges for e in block], dtype=np.float64)
            self.starts = np.array(starts, dtype=np.int64)
            self.ratings = np.array(ratings, dtype=np.float64)
            sizes = np.diff(np.append(self.starts, len(self.edges)))
            self.edge_rating = np.repeat(self.ratings, sizes)
            self.edge_poly = np.repeat(np.arange(len(self.ratings)), sizes)
            # Borda da cobertura com o interior (área coberta) à esquerda: exterior anti-horário,
            # buracos horários. Serve para detectar a saída da cobertura e, com outside_rating, para
            # somar o custo do trecho fora dela.
            self.union_edges = np.array([e for ring, exterior in _polygon_rings(covered)
                                         for e in _ring_edges(ring, ccw=exterior)], dtype=np.float64)
            if outside_rating is not None:
                outside_rating = float(outside_rating)
                if not math.isfinite(outside_rating) or outside_rating <= 0:
                    raise ValueError('Nota de atrito inválida: {0}. Use valor maior que 0 (para quase sem '
                                     'atrito, um valor pequeno, como 0,1).'.format(outside_rating))
            self.outside_rating = outside_rating
            self.min_rating = float(self.ratings.min() if outside_rating is None
                                    else min(self.ratings.min(), outside_rating))
            xs, ys = self.edges[:, [0, 2]], self.edges[:, [1, 3]]
            self.envelope = (float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max()))

    def locate(self, x, y):
        """Índice do polígono que contém cada ponto (−1 = sem polígono), por paridade de raio."""
        x = np.atleast_1d(np.asarray(x, dtype=np.float64))
        y = np.atleast_1d(np.asarray(y, dtype=np.float64))
        span = max(self.envelope[2] - self.envelope[0], self.envelope[3] - self.envelope[1], 1.0)
        # Raio até um ponto distante, em direção levemente inclinada (evita passar por vértices).
        far_x = self.envelope[2] + 3.1 * span
        far_y = y + 0.7071067811865 * span
        out = np.full(x.size, -1, dtype=np.int64)
        for sl in _slices(x.size, len(self.edges)):
            valid, _, _ = _crossings(x[sl], y[sl], np.full(x[sl].size, far_x), far_y[sl], self.edges)
            inside = (np.add.reduceat(valid, self.starts, axis=1) % 2) == 1
            out[sl] = np.where(inside.any(axis=1), inside.argmax(axis=1), -1)
        return out

    def costs(self, gx, gy, g_inside, x, y):
        """A(G → x) para um polo (gx, gy) e pontos x, y; infinito se inalcançável.

        g_inside: vetor booleano (por polígono) dos polígonos que contêm o polo deslocado
        (``locate`` no polo deslocado de _NUDGE).

        Exato e rápido (1.4.0-dev5): um segmento G → x só pode cruzar as arestas cuja faixa de
        direções, vista de G, contém a direção de x. As arestas são indexadas por setor angular
        (``_AngularIndex``, guardado por polo) e cada ponto é testado só contra as do seu setor.
        """
        x = np.asarray(x, dtype=np.float64).ravel()
        y = np.asarray(y, dtype=np.float64).ravel()
        ox, oy = gx + _NUDGE_X, gy + _NUDGE_Y
        key = (float(ox), float(oy))
        cache = self.__dict__.setdefault('_indexes', {})
        if key not in cache:
            cache[key] = (_AngularIndex(self.edges, ox, oy), _AngularIndex(self.union_edges, ox, oy))
        rated, union = cache[key]
        npoly = len(self.ratings)
        out = np.empty(x.size, dtype=np.float64)
        theta = np.mod(np.arctan2(y - oy, x - ox), 2 * np.pi)
        sector_r = rated.sector(theta)
        sector_u = union.sector(theta)
        start = 0
        while start < x.size:
            # Bloco de pontos limitado pelo número de pares (ponto, aresta candidata).
            counts = rated.counts(sector_r[start:]) + union.counts(sector_u[start:])
            cum = np.cumsum(counts)
            stop = start + max(1, int(np.searchsorted(cum, _PAIRS, side='right')))
            sl = slice(start, min(stop, x.size))
            xs, ys = x[sl], y[sl]
            n = xs.size
            k, e = rated.pairs(sector_r[sl])
            total = np.zeros(n)
            inside = np.zeros((n, npoly), dtype=bool)
            if k.size:
                valid, tau, denom = _pair_crossings(ox, oy, xs[k], ys[k], self.edges[e])
                kv, ev = k[valid], e[valid]
                signed = np.where(denom[valid] < 0, -1.0, 1.0) * tau[valid] ** 2 * self.edge_rating[ev]
                total = np.bincount(kv, weights=signed, minlength=n) / 2.0
                parity = np.bincount(kv * npoly + self.edge_poly[ev], minlength=n * npoly).reshape(n, npoly) % 2
                inside = parity.astype(bool)
            inside ^= g_inside[None, :]
            covered = inside.any(axis=1)
            end_rating = np.where(covered, self.ratings[inside.argmax(axis=1)], 0.0)
            k, e = union.pairs(sector_u[sl])
            leaves = np.zeros(n, dtype=bool)
            if k.size:
                valid, tau_u, denom_u = _pair_crossings(ox, oy, xs[k], ys[k], self.union_edges[e])
                if self.outside_rating is None:
                    leaves[np.unique(k[valid])] = True
                else:
                    # Trecho fora da cobertura: atravessável com a nota da área sem polígono. Sair da
                    # cobertura é entrar nesse trecho (sinal oposto ao de entrar na cobertura).
                    signed_u = -np.where(denom_u[valid] < 0, -1.0, 1.0) * tau_u[valid] ** 2 * self.outside_rating
                    total += np.bincount(k[valid], weights=signed_u, minlength=n) / 2.0
            d2 = (xs - gx) ** 2 + (ys - gy) ** 2
            value = d2 * (total + end_rating / 2.0)
            # Arredondamento: a soma ± pode dar um negativo ínfimo; o custo real é >= 0.
            value = np.maximum(value, 0.0)
            value[~covered | leaves] = np.inf
            value[d2 == 0] = 0.0
            out[sl] = value
            start = sl.stop
        return out


class _AngularIndex:
    """Arestas indexadas pelo setor angular que ocupam, vistas de um ponto (o polo).

    Uma aresta (segmento que não contém o polo) ocupa o arco menor entre as direções das suas
    pontas; ela é registrada em todos os setores desse arco, mais um de folga de cada lado.
    Arestas quase alinhadas com o polo ocupam todos os setores. O segmento polo → x cruza uma
    aresta só se a direção de x está no arco dela, logo testar o setor de x basta (exato).
    """

    def __init__(self, edges, ox, oy):
        count = len(edges)
        self.n = int(min(16384, max(256, 2 ** math.ceil(math.log2(max(count, 1) / 4)))))
        width = 2 * math.pi / self.n
        self.width = width
        if not count:
            self.ptr = np.zeros(self.n + 1, dtype=np.int64)
            self.index = np.zeros(0, dtype=np.int64)
            return
        a1 = np.arctan2(edges[:, 1] - oy, edges[:, 0] - ox)
        a2 = np.arctan2(edges[:, 3] - oy, edges[:, 2] - ox)
        d = np.mod(a2 - a1 + np.pi, 2 * np.pi) - np.pi          # arco menor, em (−π, π]
        begin = np.where(d >= 0, a1, a2)
        span = np.abs(d)
        first = np.floor(np.mod(begin, 2 * np.pi) / width).astype(np.int64) - 1
        many = (span / width).astype(np.int64) + 3
        many = np.where(span > np.pi - 1e-9, self.n, np.minimum(many, self.n))
        ids = np.repeat(np.arange(count), many)
        offset = np.arange(ids.size) - np.repeat(np.cumsum(many) - many, many)
        sectors = np.mod(np.repeat(first, many) + offset, self.n)
        order = np.argsort(sectors, kind='stable')
        self.index = ids[order]
        self.ptr = np.concatenate(([0], np.cumsum(np.bincount(sectors, minlength=self.n))))

    def sector(self, theta):
        return np.minimum((theta / self.width).astype(np.int64), self.n - 1)

    def counts(self, sectors):
        return self.ptr[sectors + 1] - self.ptr[sectors]

    def pairs(self, sectors):
        """(índice do ponto, índice da aresta) de todos os pares candidatos."""
        counts = self.counts(sectors)
        total = int(counts.sum())
        if not total:
            return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
        k = np.repeat(np.arange(sectors.size), counts)
        offset = np.arange(total) - np.repeat(np.cumsum(counts) - counts, counts)
        e = self.index[np.repeat(self.ptr[sectors], counts) + offset]
        return k, e


def _pair_crossings(ox, oy, x1, y1, edges):
    """Como ``_crossings``, mas para pares (ponto i, aresta i): vetores 1D."""
    dx = x1 - ox
    dy = y1 - oy
    ex = edges[:, 2] - edges[:, 0]
    ey = edges[:, 3] - edges[:, 1]
    wx = edges[:, 0] - ox
    wy = edges[:, 1] - oy
    denom = dx * ey - dy * ex
    with np.errstate(divide='ignore', invalid='ignore'):
        tau = (wx * ey - wy * ex) / denom
        t = (wx * dy - wy * dx) / denom
    valid = (denom != 0) & (tau > 0) & (tau < 1) & (t >= 0) & (t < 1)
    return valid, tau, denom


def _slices(count, width):
    step = max(1, _BLOCK // max(1, width))
    return [slice(i, min(count, i + step)) for i in range(0, count, step)]


def _crossings(x0, y0, x1, y1, edges):
    """Cruzamentos dos segmentos (x0,y0)→(x1,y1) com as arestas [ax, ay, bx, by].

    Devolve (válido, τ ao longo do segmento, d × e). Meio aberto na aresta (t ∈ [0, 1)) para
    contar cada vértice uma vez; τ estritamente em (0, 1).
    """
    dx = (x1 - x0)[:, None]
    dy = (y1 - y0)[:, None]
    ex = (edges[:, 2] - edges[:, 0])[None, :]
    ey = (edges[:, 3] - edges[:, 1])[None, :]
    wx = edges[:, 0][None, :] - x0[:, None]
    wy = edges[:, 1][None, :] - y0[:, None]
    denom = dx * ey - dy * ex
    with np.errstate(divide='ignore', invalid='ignore'):
        tau = (wx * ey - wy * ex) / denom
        t = (wx * dy - wy * dx) / denom
    valid = (denom != 0) & (tau > 0) & (tau < 1) & (t >= 0) & (t < 1)
    return valid, tau, denom


def _polygon_rings(geometry):
    """[(lista de (x, y), é_exterior)] de um Polygon/MultiPolygon/coleção (só partes poligonais)."""
    from osgeo import ogr
    out = []
    kind = ogr.GT_Flatten(geometry.GetGeometryType())
    if kind == ogr.wkbPolygon:
        for i in range(geometry.GetGeometryCount()):
            ring = geometry.GetGeometryRef(i)
            pts = [(ring.GetX(k), ring.GetY(k)) for k in range(ring.GetPointCount())]
            if len(pts) >= 4:
                out.append((pts, i == 0))
    elif kind in (ogr.wkbMultiPolygon, ogr.wkbGeometryCollection):
        for i in range(geometry.GetGeometryCount()):
            out.extend(_polygon_rings(geometry.GetGeometryRef(i)))
    return out


def _ring_edges(points, *, ccw):
    """Arestas do anel com o interior à esquerda: exterior anti-horário, buraco horário."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:]))
    if (area > 0) != ccw:
        points = points[::-1]
    return [(a[0], a[1], b[0], b[1]) for a, b in zip(points, points[1:]) if a != b]


class ContinuousModel:
    """Polos + superfície: rótulo (identificador do polo vencedor) de qualquer ponto do plano."""

    def __init__(self, generators, surface, *, mass_weighted):
        self.surface = surface
        self.generators = list(generators)
        self.gx = np.array([g.x for g in generators], dtype=np.float64)
        self.gy = np.array([g.y for g in generators], dtype=np.float64)
        self.mass = np.array([g.mass if mass_weighted else 1.0 for g in generators], dtype=np.float64)
        self.ids = np.array([g.identifier for g in generators], dtype=np.int64)
        where = surface.locate(self.gx + _NUDGE_X, self.gy + _NUDGE_Y)
        for g, poly in zip(generators, where):
            if poly < 0:
                raise ValueError(f'Centro {g.identifier} fora dos polígonos de atrito (ou sobre barreira).')
        self.g_inside = [np.arange(len(surface.ratings)) == poly for poly in where]
        self.evaluations = 0

    def labels(self, x, y):
        """Identificador do polo de menor A/M (0 = inalcançável); empate: primeiro polo."""
        x = np.asarray(x, dtype=np.float64).ravel()
        y = np.asarray(y, dtype=np.float64).ravel()
        count, npoles = x.size, len(self.generators)
        self.evaluations += count
        d2 = (x[None, :] - self.gx[:, None]) ** 2 + (y[None, :] - self.gy[:, None]) ** 2
        # Limite inferior exato: A >= nota mínima × D² / 2. Uma passada por polo, na ordem do menor
        # limite inferior médio; cada polo só calcula os pontos em que ainda pode vencer.
        lower = self.surface.min_rating * d2 / 2.0 / self.mass[:, None]
        best = np.full(count, np.inf)
        best_j = np.full(count, npoles, dtype=np.int64)
        nearest = np.argmin(lower, axis=0)
        order = sorted(range(npoles), key=lambda j: (-(nearest == j).sum(), float(lower[j].mean())))
        for j in order:
            sub = np.flatnonzero(lower[j] <= best)
            if not sub.size:
                continue
            score = self.surface.costs(self.gx[j], self.gy[j], self.g_inside[j], x[sub], y[sub]) / self.mass[j]
            take = np.isfinite(score) & ((score < best[sub]) | ((score == best[sub]) & (j < best_j[sub])))
            best[sub[take]] = score[take]
            best_j[sub[take]] = j
        out = np.zeros(count, dtype=np.int64)
        reached = best_j < npoles
        out[reached] = self.ids[best_j[reached]]
        return out


# ---------------------------------------------------------------------------
# Traçado das fronteiras
# ---------------------------------------------------------------------------
# Deslocamento da malha de busca (frações irracionais do espaçamento): evita que os nós caiam
# sobre vértices e bordas de polígonos alinhados a coordenadas redondas.
_SHIFT_X, _SHIFT_Y = 0.3183098861837907, 0.36787944117144233
# Refinamento local das células complexas: 2**_REFINE_LEVEL subdivisões por lado.
_REFINE_LEVEL = 3
# Máximo de células criadas pela correção da conferência final (protege a memória do QGIS).
_CELL_BUDGET = 400_000


class _Lattice:
    """Malha diádica: nós base a cada ``spacing``, subdivididos 2**level vezes para as bisseções.

    Os rótulos ficam em cache por índice inteiro, o que garante que duas células vizinhas encontrem
    exatamente o mesmo ponto de fronteira na aresta comum.
    """

    def __init__(self, model, bounds, spacing, tolerance):
        xmin, ymin, xmax, ymax = bounds
        self.model = model
        # Pelo menos 2**3 subdivisões: as células complexas são refinadas em 8 × 8.
        self.level = max(_REFINE_LEVEL, int(math.ceil(math.log2(spacing / tolerance))))
        self.unit = spacing / 2 ** self.level
        self.step = 2 ** self.level
        self.x0 = xmin - spacing * _SHIFT_X
        self.y0 = ymin - spacing * _SHIFT_Y
        self.nx = int(math.ceil((xmax - self.x0) / spacing)) + 1
        self.ny = int(math.ceil((ymax - self.y0) / spacing)) + 1
        self.cache = {}

    def xy(self, i, j):
        return self.x0 + np.asarray(i, dtype=np.float64) * self.unit, self.y0 + np.asarray(j, dtype=np.float64) * self.unit

    def labels(self, keys):
        """Rótulos dos nós (i, j) da malha fina, avaliando só os que faltam no cache."""
        missing = [k for k in dict.fromkeys(keys) if k not in self.cache]
        if missing:
            arr = np.array(missing, dtype=np.int64)
            x, y = self.xy(arr[:, 0], arr[:, 1])
            for key, value in zip(missing, self.model.labels(x, y)):
                self.cache[key] = int(value)
        return [self.cache[k] for k in keys]


def _bisect_edges(lattice, edges, cancelled, progress=None):
    """Para cada lado (i0, j0, di, dj, tamanho) com rótulos diferentes nas pontas, acha o par de nós
    vizinhos da malha fina em que o rótulo muda. Devolve [(ponto, rótulo antes, rótulo depois)]."""
    lo = np.zeros(len(edges), dtype=np.int64)
    hi = np.array([e[4] for e in edges], dtype=np.int64)
    first = np.array(lattice.labels([(e[0], e[1]) for e in edges]), dtype=np.int64)
    levels = max(1, int(math.ceil(math.log2(max(2, int(hi.max()) if hi.size else 2)))))
    done = 0
    while np.any(hi - lo > 1):
        if cancelled and cancelled():
            raise InterruptedError('Voronoi cancelado.')
        if progress:
            progress(min(1.0, done / levels))
        done += 1
        mid = np.where(hi - lo > 1, (lo + hi) // 2, lo)
        keys = [(e[0] + e[2] * m, e[1] + e[3] * m) for e, m in zip(edges, mid)]
        values = np.array(lattice.labels(keys), dtype=np.int64)
        same = values == first
        lo = np.where(same, mid, lo)
        hi = np.where(same, hi, mid)
    out = []
    for e, a, b in zip(edges, lo, hi):
        before = lattice.labels([(e[0] + e[2] * a, e[1] + e[3] * a)])[0]
        after = lattice.labels([(e[0] + e[2] * b, e[1] + e[3] * b)])[0]
        t = (a + b) / 2.0
        x, y = lattice.xy(e[0] + e[2] * t, e[1] + e[3] * t)
        out.append(((float(x), float(y)), before, after))
    return out


def _junction(lattice, i0, j0, size):
    """Ponto de encontro de três ou mais regiões dentro da célula (i0, j0, lado size), por
    subdivisão até a malha fina."""
    while size > 1:
        half = size // 2
        best, best_count = None, -1
        for di in (0, half):
            for dj in (0, half):
                corners = [(i0 + di, j0 + dj), (i0 + di + half, j0 + dj),
                           (i0 + di + half, j0 + dj + half), (i0 + di, j0 + dj + half)]
                count = len(set(lattice.labels(corners)))
                if count > best_count:
                    best, best_count = (i0 + di, j0 + dj), count
        i0, j0 = best
        size = half
    x, y = lattice.xy(i0 + size / 2.0, j0 + size / 2.0)
    return float(x), float(y)


def _refine(model, segments, tolerance, cancelled, max_depth=16, progress=None):
    """Insere vértices até a corda ficar a menos de ``tolerance`` da fronteira verdadeira.

    segments: [(P, Q, a, b)], fronteira entre os rótulos a e b. A corda é conferida em 1/4, 1/2 e
    3/4 do comprimento (só o meio deixaria passar cunhas finas, como as que nascem nos cantos dos
    polígonos de atrito): em cada ponto, procura a fronteira na perpendicular (bisseção entre um
    ponto de rótulo a e um de rótulo b, a partir da corda e com alcance crescente); se o maior desvio
    passa de ``tolerance``, a corda é dividida no ponto de fronteira do meio, e as metades são
    conferidas de novo.
    """
    fractions = np.array([0.25, 0.5, 0.75])
    nf = fractions.size
    done = []
    work = [(np.array(p, float), np.array(q, float), a, b, 0) for p, q, a, b in segments]
    level = 0
    while work:
        if cancelled and cancelled():
            raise InterruptedError('Voronoi cancelado.')
        if progress:
            progress(min(1.0, level / 10))
        level += 1
        keep = [w for w in work if w[4] < max_depth and np.hypot(*(w[1] - w[0])) > 2 * tolerance]
        done.extend(w for w in work if not (w[4] < max_depth and np.hypot(*(w[1] - w[0])) > 2 * tolerance))
        if not keep:
            break
        P = np.array([w[0] for w in keep]); Q = np.array([w[1] for w in keep])
        A = np.repeat([w[2] for w in keep], nf); B = np.repeat([w[3] for w in keep], nf)
        d = Q - P
        length = np.hypot(d[:, 0], d[:, 1])
        normal = np.column_stack((-d[:, 1], d[:, 0])) / length[:, None]
        # Pontos de conferência (segmento k, fração f) achatados em k * nf + f.
        M = (P[:, None, :] + fractions[None, :, None] * d[:, None, :]).reshape(-1, 2)
        n = np.repeat(normal, nf, axis=0)
        L = np.repeat(length, nf)
        found = np.zeros(M.shape[0], dtype=bool)
        lo_pt = np.zeros_like(M); hi_pt = np.zeros_like(M)
        # Busca da fronteira MAIS PRÓXIMA na perpendicular: a partir do ponto da corda, com alcance
        # crescente, para na primeira troca para o outro rótulo (um alcance grande logo de saída
        # pularia para a fronteira do outro lado de uma língua estreita).
        here = model.labels(M[:, 0], M[:, 1])
        on_a, on_b = here == A, here == B
        other = np.where(on_a, B, A)
        searchable = on_a | on_b
        for reach in (1 / 64, 1 / 32, 1 / 16, 1 / 8, 1 / 4, 1 / 2):
            todo = np.flatnonzero(~found & searchable)
            if not todo.size:
                break
            r = np.maximum(reach * L[todo], tolerance)[:, None]
            plus, minus = M[todo] + r * n[todo], M[todo] - r * n[todo]
            lp = model.labels(plus[:, 0], plus[:, 1])
            lm = model.labels(minus[:, 0], minus[:, 1])
            use_plus = lp == other[todo]
            use_minus = ~use_plus & (lm == other[todo])
            hit = use_plus | use_minus
            idx = todo[hit]
            far = np.where(use_plus[hit][:, None], plus[hit], minus[hit])
            found[idx] = True
            # lo_pt fica com o rótulo a; hi_pt, com o rótulo b.
            near_is_a = on_a[idx][:, None]
            lo_pt[idx] = np.where(near_is_a, M[idx], far)
            hi_pt[idx] = np.where(near_is_a, far, M[idx])
        sel = np.flatnonzero(found)
        if sel.size:
            span = np.hypot(*(hi_pt[sel] - lo_pt[sel]).T).max()
            for _ in range(max(1, int(math.ceil(math.log2(max(span, tolerance) / (tolerance / 4)))))):
                mid = (lo_pt[sel] + hi_pt[sel]) / 2
                is_a = model.labels(mid[:, 0], mid[:, 1]) == A[sel]
                lo_pt[sel[is_a]] = mid[is_a]
                hi_pt[sel[~is_a]] = mid[~is_a]
        boundary = (lo_pt + hi_pt) / 2
        deviation = np.where(found, np.hypot(*(boundary - M).T), -1.0).reshape(-1, nf)
        work = []
        middle = int(np.flatnonzero(fractions == 0.5)[0])
        for k, w in enumerate(keep):
            worst = int(np.argmax(deviation[k]))
            if deviation[k, worst] <= tolerance:
                done.append(w)
                continue
            # Divide no ponto de fronteira do MEIO da corda (mantém a ordem ao longo da curva quando
            # ela se dobra, como numa língua); só sem fronteira no meio usa o ponto de maior desvio.
            pick = middle if deviation[k, middle] >= 0 else worst
            point = boundary[k * nf + pick]
            work.append((w[0], point, w[2], w[3], w[4] + 1))
            work.append((point, w[1], w[2], w[3], w[4] + 1))
    return [((float(p[0]), float(p[1])), (float(q[0]), float(q[1]))) for p, q, *_ in done]


# Padrões da 1.4.0 (decisões do autor, 18/11/2026): tolerância de 0,5 m, coerente com mapas temáticos
# 1:10.000 (erro-padrão de 3 m no PEC Classe A), limitada a 1/2000 do maior lado em extensões pequenas;
# espaçamento automático da busca.
DEFAULT_TOLERANCE_M = 0.5
_AUTO_FRACTION = 100          # espaçamento ≈ maior lado da extensão / 100 (1/200: mesmo resultado, 3,5× mais lento)
_AUTO_WIDTH_DIVISOR = 4       # ... e nunca maior que 1/4 da largura do polígono mais estreito
_AUTO_MAX_NODES = 100_000     # ... nem tão pequeno que a malha base passe deste número de nós


def default_tolerance(bounds, units_to_meters=1.0):
    """Tolerância padrão em unidades do SRC: 0,5 m, ou 1/2000 do maior lado se for menor."""
    xmin, ymin, xmax, ymax = map(float, bounds)
    return min(DEFAULT_TOLERANCE_M / units_to_meters, max(xmax - xmin, ymax - ymin) / 2000.0)


def automatic_spacing(surface, bounds, tolerance):
    """Espaçamento da malha de busca escolhido pelos dados (unidades do SRC).

    Maior lado da extensão / 100, reduzido a 1/4 da largura média (2 × área / perímetro) do polígono
    de atrito mais estreito que toca a extensão, e aumentado se a malha base passasse de 100 mil nós.
    Nunca menor que 8 × a tolerância. A conferência automática corrige o que escapar a essa escolha.
    """
    xmin, ymin, xmax, ymax = map(float, bounds)
    side = max(xmax - xmin, ymax - ymin)
    spacing = side / _AUTO_FRACTION
    widths = [w for w, (ex0, ex1, ey0, ey1) in surface.widths
              if w > 0 and ex1 >= xmin and ex0 <= xmax and ey1 >= ymin and ey0 <= ymax]
    if widths:
        spacing = min(spacing, min(widths) / _AUTO_WIDTH_DIVISOR)
    spacing = max(spacing, math.sqrt((xmax - xmin) * (ymax - ymin) / _AUTO_MAX_NODES), 8 * tolerance)
    return spacing


def friction_voronoi_polygons(generators, features, bounds, *, spacing=None, tolerance=None,
                              mass_weighted=False, cancelled=None, progress=None, units_to_meters=1.0,
                              outside_rating=None):
    """Regiões de influência com atrito em vetor direto (modelo contínuo).

    features: [(wkb, nota ou None)]; bounds: extensão (xmin, ymin, xmax, ymax) no SRC dos polígonos;
    spacing: espaçamento da malha de busca (regiões menores que ele podem não ser detectadas); None =
    automático (``automatic_spacing``). tolerance: tolerância das fronteiras traçadas (unidades do
    SRC); None = padrão (``default_tolerance``: 0,5 m).
    units_to_meters: metros por unidade do SRC (para a tolerância padrão).
    outside_rating: nota de passagem da área sem polígono (sem resultado); None = barreira.
    Retorna ([(centro, multipolígono OGR)], estatísticas).
    """
    from osgeo import ogr
    from .gdal_scope import gdal_exceptions
    xmin, ymin, xmax, ymax = map(float, bounds)
    if not all(math.isfinite(v) for v in (xmin, ymin, xmax, ymax)) or xmin >= xmax or ymin >= ymax:
        raise ValueError('A extensão do Voronoi precisa ter área positiva.')
    surface = FrictionSurface(features, cancelled=cancelled, outside_rating=outside_rating)
    automatic = spacing is None
    if tolerance is None:
        tolerance = default_tolerance((xmin, ymin, xmax, ymax), units_to_meters)
    if automatic:
        spacing = automatic_spacing(surface, (xmin, ymin, xmax, ymax), tolerance)
    if not (math.isfinite(spacing) and spacing > 0 and math.isfinite(tolerance) and 0 < tolerance < spacing):
        raise ValueError('Espaçamento da busca e tolerância inválidos (0 < tolerância < espaçamento).')
    if (xmax - xmin) * (ymax - ymin) / spacing ** 2 > 4_000_000:
        raise ValueError('Espaçamento da busca pequeno demais para a extensão (mais de 4 milhões de nós).')
    model = ContinuousModel(generators, surface, mass_weighted=mass_weighted)
    lattice = _Lattice(model, (xmin, ymin, xmax, ymax), spacing, tolerance)
    step = lattice.step
    # 1. Rótulos nos nós base.
    nx, ny = lattice.nx, lattice.ny
    ii, jj = np.meshgrid(np.arange(nx), np.arange(ny))
    # Progresso em porcentagem (1.4.0-dev5): etapas com faixas fixas; dentro das etapas longas, avanço
    # por blocos ou por rodadas (o número de rodadas não é conhecido de antemão).
    def report(value):
        if progress:
            progress(int(max(0, min(99, value))))
        if cancelled and cancelled():
            raise InterruptedError('Voronoi cancelado.')

    report(5)
    keys = list(zip((ii.ravel() * step).tolist(), (jj.ravel() * step).tolist()))
    chunk = 20_000
    for start in range(0, len(keys), chunk):
        lattice.labels(keys[start:start + chunk])
        report(5 + 15 * min(1.0, (start + chunk) / len(keys)))
    base_nodes = nx * ny
    R = 2 ** _REFINE_LEVEL
    sub = step // R

    def corners(i0, j0, size):
        return lattice.labels([(i0, j0), (i0 + size, j0), (i0 + size, j0 + size), (i0, j0 + size)])

    def side_keys(i0, j0, size):
        return [(i0, j0, 1, 0, size), (i0 + size, j0, 0, 1, size), (i0, j0 + size, 1, 0, size), (i0, j0, 0, 1, size)]

    # Células iniciais: as células base com 3+ rótulos nos cantos (junções) ou em sela, e as forçadas
    # pela conferência final, já entram divididas em R × R.
    initial = set()
    for j in range(ny - 1):
        for i in range(nx - 1):
            c = corners(i * step, j * step, step)
            kinds = len(set(c))
            if kinds >= 3 or (kinds == 2 and c[0] == c[2] and c[1] == c[3] and c[0] != c[1]):
                initial.add((i, j))
    report(22)

    def trace(forced, lo, hi):
        """Malha adaptativa → pontos de fronteira → segmentos → linhas → regiões, com as células
        base de ``forced`` ({(i, j): profundidade}) pré-divididas em (2**3)**profundidade partes por
        lado. Devolve (regiões {id: geometria}, informações)."""
        cells = set()
        for j in range(ny - 1):
            for i in range(nx - 1):
                depth = max(forced.get((i, j), 0), 1 if (i, j) in initial else 0)
                size = max(1, step >> (_REFINE_LEVEL * depth))
                n = step // size
                cells.update((i * step + a * size, j * step + b * size, size) for a in range(n) for b in range(n))
        sizes = sorted({step >> k for k in range(lattice.level + 1)}, reverse=True)

        def owner(i, j):
            """Célula que contém o nó (i, j) da malha fina (convenção semiaberta)."""
            for size in sizes:
                key = (i - i % size, j - j % size, size)
                if key in cells:
                    return key
            return None

        def across(cell, side):
            """Células do outro lado de um lado da célula (podem ser maiores, iguais ou menores)."""
            i0, j0, size = cell
            out, t = [], 0
            while t < size:
                if side == 0:
                    probe = (i0 + t, j0 - 1)
                elif side == 1:
                    probe = (i0 + size, j0 + t)
                elif side == 2:
                    probe = (i0 + t, j0 + size)
                else:
                    probe = (i0 - 1, j0 + t)
                other = owner(*probe)
                if other is None:
                    break
                out.append(other)
                o_i, o_j, o_size = other
                t = (o_i + o_size - i0) if side in (0, 2) else (o_j + o_size - j0)
            return out

        found = {}
        cache = lattice.cache

        def plan(cell):
            """Nós que a conferência da célula usa: [(lado, chave, posições ao longo do lado)], interior."""
            i0, j0, size = cell
            sides = []
            for side, key in enumerate(side_keys(i0, j0, size)):
                offsets = {size // 2} | ({size // 4, 3 * size // 4} if size >= 4 else set())
                for other in across(cell, side):
                    if other[2] < size:
                        edge_pos = (other[0] - i0) if side in (0, 2) else (other[1] - j0)
                        for t in (edge_pos, edge_pos + other[2]):
                            if 0 < t < size:
                                offsets.add(t)
                sides.append((key, [0] + sorted(offsets) + [size]))
            inner = [(i0 + size // 2, j0 + size // 2)]
            if size >= 4:
                q = size // 4
                inner += [(i0 + q, j0 + q), (i0 + 3 * q, j0 + q), (i0 + 3 * q, j0 + 3 * q), (i0 + q, j0 + 3 * q)]
            return sides, inner

        span = hi - lo
        dirty = set(cells)
        rounds = 0
        # Até estabilizar: cada rodada divide células, e o tamanho mínimo (1 nó da malha fina) garante
        # o fim. Um limite fixo pequeno deixava lados incoerentes entre células grossas e finas (pontas
        # soltas na rede de fronteiras e regiões fundidas), como no teste com dados reais.
        def tick(part):
            # Avanço assintótico por rodada (o total de rodadas não é conhecido), com marcos dentro dela.
            # A 1ª rodada (todas as células) é a mais pesada: leva metade da faixa das rodadas.
            r = rounds - 1 + part
            report(lo + span * 0.45 * (1 - 0.5 ** r))

        while True:
            rounds += 1
            tick(0.0)
            # Pontos de fronteira (bisseção diádica) nos lados novos com pontas diferentes.
            new_sides = [key for i0, j0, size in cells for key in side_keys(i0, j0, size) if key not in found]
            new_sides = list(dict.fromkeys(new_sides))
            lattice.labels([(k[0], k[1]) for k in new_sides] +
                           [(k[0] + k[2] * k[4], k[1] + k[3] * k[4]) for k in new_sides])
            pending = []
            for key in new_sides:
                a = cache[(key[0], key[1])]
                b = cache[(key[0] + key[2] * key[4], key[1] + key[3] * key[4])]
                if a == b:
                    found[key] = None
                else:
                    pending.append((key, a, b))
            tick(0.2)
            if pending:
                bisected = _bisect_edges(lattice, [k for k, _, _ in pending], cancelled,
                                         progress=lambda f: tick(0.2 + 0.4 * f))
                for (key, a, b), point in zip(pending, bisected):
                    found[key] = (point, point[1] != a or point[2] != b)
            tick(0.6)
            # Conferência das células novas e das vizinhas das divididas: (1) lado com duas trocas
            # achado na bisseção; (2) nos lados, pontos intermediários (1/4, 1/2, 3/4 e os cantos das
            # vizinhas menores) com mais trocas do que o lado representa; (3) no interior (centro e
            # quartos), rótulo que não está nos cantos. Todos os nós são avaliados de uma vez.
            plans = {cell: plan(cell) for cell in dirty if cell in cells and cell[2] >= 2}
            need = []
            for cell, (sides, inner) in plans.items():
                for key, ts in sides:
                    need.extend((key[0] + key[2] * t, key[1] + key[3] * t) for t in ts)
                need.extend(inner)
                i0, j0, size = cell
                need.extend([(i0, j0), (i0 + size, j0), (i0 + size, j0 + size), (i0, j0 + size)])
            for start in range(0, len(need), 50_000):
                lattice.labels(need[start:start + 50_000])
                tick(0.6 + 0.35 * min(1.0, (start + 50_000) / max(1, len(need))))
            split = set()
            for cell, (sides, inner) in plans.items():
                i0, j0, size = cell
                c = {cache[(i0, j0)], cache[(i0 + size, j0)], cache[(i0 + size, j0 + size)], cache[(i0, j0 + size)]}
                bad = False
                for key, ts in sides:
                    value = found.get(key)
                    if value is not None and value[1]:
                        bad = True
                        break
                    seq = [cache[(key[0] + key[2] * t, key[1] + key[3] * t)] for t in ts]
                    changes = sum(1 for u, v in zip(seq, seq[1:]) if u != v)
                    if changes > (0 if seq[0] == seq[-1] else 1):
                        bad = True
                        break
                if not bad and any(cache[node] not in c for node in inner):
                    bad = True
                if bad:
                    split.add(cell)
            if not split:
                break
            dirty = set()
            for cell in split:
                for side in range(4):
                    dirty.update(across(cell, side))
            for i0, j0, size in split:
                cells.discard((i0, j0, size))
                half = size // 2
                children = [(i0 + a * half, j0 + b * half, half) for a in (0, 1) for b in (0, 1)]
                cells.update(children)
                dirty.update(children)
            dirty = {cell for cell in dirty if cell in cells}
        edge_index, points = {}, []
        for i0, j0, size in cells:
            for key in side_keys(i0, j0, size):
                value = found.get(key)
                if value is not None and key not in edge_index:
                    edge_index[key] = len(points)
                    points.append(value[0])
        # Segmentos em cada célula (2 pontos: corda; sela de 2 rótulos: pelo centro; 3+: junção).
        segments = []
        for i0, j0, size in cells:
            c = corners(i0, j0, size)
            sides = [edge_index.get(key) for key in side_keys(i0, j0, size)]
            present = [s_ for s_ in sides if s_ is not None]
            if not present:
                continue
            if len(present) == 2:
                (p, a, b), (q, _, _) = points[present[0]], points[present[1]]
                segments.append((p, q, a, b))
            elif len(present) == 4 and len(set(c)) == 2:
                center = lattice.labels([(i0 + size // 2, j0 + size // 2)])[0] if size > 1 else c[0]
                pairs = ((0, 1), (2, 3)) if center == c[0] else ((3, 0), (1, 2))
                for s_, t_ in pairs:
                    (p, a, b), (q, _, _) = points[sides[s_]], points[sides[t_]]
                    segments.append((p, q, a, b))
            else:
                hub = _junction(lattice, i0, j0, size)
                for s_ in present:
                    p, a, b = points[s_]
                    segments.append((p, hub, a, b))
        report(lo + span * 0.5)
        lines = _refine(model, segments, tolerance, cancelled,
                        progress=lambda f: report(lo + span * (0.5 + 0.3 * f)))
        report(lo + span * 0.8)
        regions, absorbed = _assemble(model, surface, lines, lattice, (xmin, ymin, xmax, ymax), tolerance,
                                      progress=lambda f: report(lo + span * (0.8 + 0.15 * f)))
        report(lo + span * 0.95)
        return regions, {'cells': len(cells), 'boundary_vertices': len(lines), 'absorbed_residues': absorbed,
                         'rounds': rounds}

    # Conferência final, independente do traçado: o modelo em um ponto de cada célula base (posição
    # fixa, fora dos nós) contra os polígonos traçados. Divergência longe da fronteira (> 5 ×
    # tolerância) aprofunda a pré-divisão daquela célula base e das vizinhas, e o traçado é refeito
    # (até 3 passadas). O que restar é informado no relatório.
    forced = {}
    sample_i, sample_j = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1))
    sample_x = lattice.x0 + (sample_i.ravel() + 0.6180339887) * spacing
    sample_y = lattice.y0 + (sample_j.ravel() + 0.4142135624) * spacing
    inside = (sample_x > xmin) & (sample_x < xmax) & (sample_y > ymin) & (sample_y < ymax)
    sample_i, sample_j = sample_i.ravel()[inside], sample_j.ravel()[inside]
    sample_x, sample_y = sample_x[inside], sample_y[inside]
    expected = model.labels(sample_x, sample_y)
    passes, divergent, budget_hit = 0, [], False
    while True:
        passes += 1
        # 1ª passada: 22-70%; correções (o traçado é refeito por inteiro): 70-88% e 88-95%.
        lo, hi = {1: (22, 70), 2: (70, 88)}.get(passes, (88, 95))
        regions, info = trace(forced, lo, hi)
        report(hi)
        divergent = _divergent_samples(regions, sample_x, sample_y, expected, 5 * tolerance,
                                       grid=(lattice, spacing, sample_i, sample_j))
        if not divergent or passes >= 3:
            break
        # A célula base da amostra divergente desce um nível; as vizinhas, pelo menos ao primeiro.
        # Orçamento de células: acima dele a correção para (e o relatório informa o que restou).
        proposal = dict(forced)
        max_depth = max(1, lattice.level // _REFINE_LEVEL)
        for k in divergent:
            ci, cj = int(sample_i[k]), int(sample_j[k])
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    i, j = ci + di, cj + dj
                    if not (0 <= i < nx - 1 and 0 <= j < ny - 1):
                        continue
                    current = proposal.get((i, j), 1 if (i, j) in initial else 0)
                    target = min(current + 1, max_depth) if (di, dj) == (0, 0) else max(current, 1)
                    if target > proposal.get((i, j), 0):
                        proposal[(i, j)] = target
        budget = sum(4 ** (_REFINE_LEVEL * d) for d in proposal.values())
        if proposal == forced or budget > _CELL_BUDGET:
            budget_hit = budget > _CELL_BUDGET
            break
        forced = proposal
    results = []
    from osgeo import ogr as _ogr
    for g in generators:
        region = regions.get(g.identifier)
        if region is None:
            continue
        polygons = _ogr.Geometry(_ogr.wkbMultiPolygon)
        _collect(region, polygons)
        if polygons.GetGeometryCount():
            results.append((g, polygons))
    refined = initial
    cells = range(info['cells'])
    lines = range(info['boundary_vertices'])
    absorbed = info['absorbed_residues']
    check = {'samples': int(sample_x.size), 'divergent': len(divergent), 'passes': passes,
             'forced_cells': len(forced), 'budget_hit': budget_hit}
    if progress:
        progress(90)
    stats = {'spacing': spacing, 'spacing_automatic': automatic, 'tolerance': tolerance,
             'base_nodes': int(base_nodes),
             'refined_cells': len(refined), 'cells': len(cells),
             'evaluations': model.evaluations, 'boundary_vertices': len(lines),
             'polygons': len(surface.ratings), 'min_rating': surface.min_rating,
             'absorbed_residues': absorbed, 'check': check}
    return results, stats


def _assemble(model, surface, lines, lattice, bounds, tolerance, progress=None):
    """Linhas + contorno da malha → poligonização → rótulo de cada face → união por polo.

    Devolve ({identificador: geometria}, resíduos absorvidos).
    """
    from osgeo import ogr
    from .gdal_scope import gdal_exceptions
    xmin, ymin, xmax, ymax = bounds
    step = lattice.step
    with gdal_exceptions():
        x1, y1 = lattice.xy((lattice.nx - 1) * step, (lattice.ny - 1) * step)
        frame = [(lattice.x0, lattice.y0), (float(x1), lattice.y0), (float(x1), float(y1)),
                 (lattice.x0, float(y1)), (lattice.x0, lattice.y0)]
        net = ogr.Geometry(ogr.wkbMultiLineString)
        for (p, q) in list(lines) + list(zip(frame, frame[1:])):
            line = ogr.Geometry(ogr.wkbLineString)
            line.AddPoint_2D(*p)
            line.AddPoint_2D(*q)
            net.AddGeometry(line)
        # Noding das linhas (GEOS): UnaryUnion na GDAL >= 3.7; antes, a união com uma das próprias
        # linhas produz o mesmo resultado.
        noded = net.UnaryUnion() if hasattr(net, 'UnaryUnion') else net.Union(net.GetGeometryRef(0).Clone())
        if progress:
            progress(0.15)
        faces = noded.Polygonize()
        if progress:
            progress(0.3)
        if faces is None:
            raise RuntimeError('Falha ao montar os polígonos do Voronoi com atrito.')
        extent = ogr.Geometry(ogr.wkbPolygon)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for x, y in ((xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax), (xmin, ymin)):
            ring.AddPoint_2D(x, y)
        extent.AddGeometry(ring)
        # A fronteira com a área sem polígono (barreira) é conhecida exatamente: a borda da cobertura.
        domain = extent.Intersection(surface.union)
        # Cada face é recortada pelo domínio ANTES de receber o rótulo; o recorte pode partir uma face
        # em vários pedaços, e cada pedaço recebe o próprio rótulo.
        pieces = ogr.Geometry(ogr.wkbMultiPolygon)
        total_faces = max(1, faces.GetGeometryCount())
        for k in range(faces.GetGeometryCount()):
            if progress and k % 200 == 0:
                progress(0.3 + 0.3 * k / total_faces)
            clipped = faces.GetGeometryRef(k).Intersection(domain)
            if clipped is not None and not clipped.IsEmpty():
                _collect(clipped, pieces)
        parts = [pieces.GetGeometryRef(k).Clone() for k in range(pieces.GetGeometryCount())]
        inner = [part.PointOnSurface() for part in parts]
        face_labels = model.labels(np.array([p.GetX() for p in inner]), np.array([p.GetY() for p in inner]))
        face_labels = _absorb_slivers(parts, face_labels, tolerance)
        if progress:
            progress(0.7)
        regions = {}
        idents = sorted({int(v) for v in face_labels if v})
        for n_ident, ident in enumerate(idents):
            if progress:
                progress(0.7 + 0.25 * n_ident / max(1, len(idents)))
            group = ogr.Geometry(ogr.wkbMultiPolygon)
            for part, label in zip(parts, face_labels):
                if label == ident:
                    _collect(part, group)
            if group.GetGeometryCount():
                region = group.UnionCascaded().Intersection(domain)
                if region is not None and not region.IsEmpty():
                    regions[ident] = region
        # Resíduos finos (largura média < 2 × tolerância) entre o traçado e a borda exata ficam com o
        # vizinho de maior fronteira comum, como na Combinação vetorial (1.2.0).
        absorbed = 0
        if regions:
            covered = None
            for region in regions.values():
                covered = region.Clone() if covered is None else covered.Union(region)
            rest = domain.Difference(covered)
            leftovers = ogr.Geometry(ogr.wkbMultiPolygon)
            if rest is not None and not rest.IsEmpty():
                _collect(rest, leftovers)
            for k in range(leftovers.GetGeometryCount()):
                piece = leftovers.GetGeometryRef(k).Clone()
                perimeter = _length(piece.Boundary())
                if perimeter <= 0 or 2 * piece.GetArea() / perimeter >= 2 * tolerance:
                    continue
                edge = piece.Boundary()
                shared = {ident: (_length(edge.Intersection(region)) if edge.Intersects(region) else 0.0)
                          for ident, region in regions.items()}
                ident = max(shared, key=shared.get)
                if shared[ident] > 0:
                    regions[ident] = regions[ident].Union(piece)
                    absorbed += 1
    return regions, absorbed


def _divergent_samples(regions, xs, ys, expected, margin, grid=None):
    """Índices das amostras cujo rótulo do modelo não é o da região traçada que as contém, a mais de
    ``margin`` da fronteira traçada (perto dela, a diferença está dentro da tolerância).

    grid = (malha, espaçamento, i, j): as amostras formam uma grade regular (uma por célula base, na
    posição fixa 0,618/0,414); as regiões são então "carimbadas" de uma vez nessa grade (GDAL, regra do
    centro do pixel), sem um teste de ponto em polígono por amostra.
    """
    from osgeo import gdal, ogr
    from .gdal_scope import gdal_exceptions
    got = np.zeros(xs.size, dtype=np.int64)
    if grid is not None and regions:
        lattice, spacing, si, sj = grid
        cols, rows = lattice.nx - 1, lattice.ny - 1
        with gdal_exceptions():
            target = gdal.GetDriverByName('MEM').Create('', int(cols), int(rows), 1, gdal.GDT_Int32)
            target.SetGeoTransform((lattice.x0 + (0.6180339887 - 0.5) * spacing, spacing, 0.0,
                                    lattice.y0 + (rows + 0.4142135624 - 0.5) * spacing, 0.0, -spacing))
            source = None
            for name in ('Memory', 'MEM'):
                driver = ogr.GetDriverByName(name)
                if driver is not None and driver.GetMetadataItem('DCAP_VECTOR') == 'YES':
                    source = driver.CreateDataSource('regioes')
                    break
            layer = source.CreateLayer('regioes', None, ogr.wkbMultiPolygon)
            layer.CreateField(ogr.FieldDefn('ID', ogr.OFTInteger))
            for ident, region in regions.items():
                feature = ogr.Feature(layer.GetLayerDefn())
                feature.SetField('ID', int(ident))
                feature.SetGeometry(region)
                layer.CreateFeature(feature)
            gdal.PushErrorHandler('CPLQuietErrorHandler')   # camada e grade sem SRC: mesmo SRC por construção
            try:
                gdal.RasterizeLayer(target, [1], layer, options=['ATTRIBUTE=ID'])
            finally:
                gdal.PopErrorHandler()
            stamp = target.GetRasterBand(1).ReadAsArray()
            target = source = None
        got = stamp[rows - 1 - np.asarray(sj), np.asarray(si)].astype(np.int64)
    else:
        for ident, region in regions.items():
            env = region.GetEnvelope()
            cand = np.flatnonzero((got == 0) & (xs >= env[0]) & (xs <= env[1]) & (ys >= env[2]) & (ys <= env[3]))
            for k in cand:
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint_2D(float(xs[k]), float(ys[k]))
                if region.Contains(point):
                    got[k] = ident
    out = []
    boundaries = None
    for k in np.flatnonzero(got != expected):
        if boundaries is None:
            boundaries = ogr.Geometry(ogr.wkbMultiLineString)
            for region in regions.values():
                b = region.Boundary()
                if ogr.GT_Flatten(b.GetGeometryType()) == ogr.wkbLineString:
                    boundaries.AddGeometry(b)
                else:
                    for n in range(b.GetGeometryCount()):
                        boundaries.AddGeometry(b.GetGeometryRef(n))
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint_2D(float(xs[k]), float(ys[k]))
        if boundaries.Distance(point) > margin:
            out.append(int(k))
    return out


def _absorb_slivers(parts, labels, tolerance):
    """Faces-fio (largura média < 2 × tolerância) ficam com o vizinho de maior fronteira comum.

    Perto de junções, duas linhas do traçado podem correr quase juntas e deixar entre elas uma face
    de largura milimétrica; o rótulo do ponto interior dela não é confiável (o ponto fica praticamente
    sobre a fronteira) e a região vizinha sairia partida. A regra é a dos resíduos da Combinação
    vetorial (1.2.0).
    """
    labels = np.array(labels, dtype=np.int64)
    widths = []
    for part in parts:
        perimeter = _length(part.Boundary())
        widths.append(2 * part.GetArea() / perimeter if perimeter > 0 else 0.0)
    thin = [k for k, w in enumerate(widths) if w < 2 * tolerance]
    if not thin:
        return labels
    thin_set = set(thin)
    envelopes = [part.GetEnvelope() for part in parts]
    for k in sorted(thin, key=lambda k: parts[k].GetArea()):
        x0, x1, y0, y1 = envelopes[k]
        edge = parts[k].Boundary()
        shared = {}
        for n, (a0, a1, b0, b1) in enumerate(envelopes):
            if n == k or n in thin_set or a1 < x0 or a0 > x1 or b1 < y0 or b0 > y1:
                continue
            length = _length(edge.Intersection(parts[n].Boundary()))
            if length > 0:
                shared[labels[n]] = shared.get(labels[n], 0.0) + length
        if shared:
            labels[k] = max(shared, key=shared.get)
    return labels


def absorb_clip_slivers(regions, tolerance):
    """Lascas criadas pelo recorte final (área de estudo) ficam com a região vizinha (1.4.0-dev6).

    O recorte pela área de estudo vem depois da eliminação das faces-fio do traçado; onde uma
    fronteira encontra a borda da área quase tangente, sobra uma parte de largura milimétrica (no
    teste da dev5 com dados reais: 0,017 m e 0,077 m). Mesma regra de ``_absorb_slivers``: parte com
    largura média 2A/P < 2 × tolerância vai para a região de maior fronteira comum; sem vizinha,
    fica onde está. regions: [(centro, multipolígono OGR)]. Devolve (regiões, partes movidas).
    """
    from osgeo import ogr
    parts, owners = [], []
    for index, (_, geometry) in enumerate(regions):
        for k in range(geometry.GetGeometryCount()):
            parts.append(geometry.GetGeometryRef(k).Clone())
            owners.append(index + 1)
    if not parts:
        return regions, 0
    labels = _absorb_slivers(parts, owners, tolerance)
    moved = int(sum(1 for a, b in zip(owners, labels) if a != b))
    if not moved:
        return regions, 0
    result = []
    for index, (generator, _) in enumerate(regions):
        group = ogr.Geometry(ogr.wkbMultiPolygon)
        for part, label in zip(parts, labels):
            if label == index + 1:
                group.AddGeometry(part)
        merged = ogr.Geometry(ogr.wkbMultiPolygon)
        if group.GetGeometryCount():
            _collect(group.UnionCascaded(), merged)
        result.append((generator, merged))
    return result, moved


def small_parts(regions, units_to_meters, threshold_m2):
    """Partes com área < threshold_m2 (m²), por região: [(centro, quantidade, área total em m²)]."""
    found = []
    for generator, geometry in regions:
        areas = [geometry.GetGeometryRef(k).GetArea() * units_to_meters ** 2
                 for k in range(geometry.GetGeometryCount())]
        small = [a for a in areas if a < threshold_m2]
        if small:
            found.append((generator, len(small), float(sum(small))))
    return found


def _length(geometry):
    """Comprimento só das partes lineares (uma interseção de bordas pode vir como ponto ou coleção;
    pedir Length() a um ponto gera aviso do GDAL no log do QGIS)."""
    from osgeo import ogr
    if geometry is None or geometry.IsEmpty():
        return 0.0
    kind = ogr.GT_Flatten(geometry.GetGeometryType())
    if kind in (ogr.wkbLineString, ogr.wkbLinearRing, ogr.wkbMultiLineString):
        return geometry.Length()
    if kind == ogr.wkbGeometryCollection:
        return sum(_length(geometry.GetGeometryRef(i)) for i in range(geometry.GetGeometryCount()))
    return 0.0


def _collect(geometry, target):
    from osgeo import ogr
    kind = ogr.GT_Flatten(geometry.GetGeometryType())
    if kind == ogr.wkbPolygon:
        if geometry.GetArea() > 0:
            target.AddGeometry(geometry)
    elif kind in (ogr.wkbMultiPolygon, ogr.wkbGeometryCollection):
        for i in range(geometry.GetGeometryCount()):
            _collect(geometry.GetGeometryRef(i), target)
