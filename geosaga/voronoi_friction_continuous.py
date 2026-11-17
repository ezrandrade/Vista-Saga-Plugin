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
# Deslocamento ínfimo do polo nos testes de cruzamento (unidades do SRC, ~1 µm em metros): sem ele,
# um segmento que passa exatamente por um vértice (comum com polos no centro de células e polígonos
# em coordenadas redondas) conta o cruzamento errado. Efeito no custo: desprezível.
_NUDGE_X, _NUDGE_Y = 1.1e-6, 0.7e-6


class FrictionSurface:
    """Polígonos de atrito preparados para o cálculo vetorizado (arestas orientadas)."""

    def __init__(self, features, *, cancelled=None):
        """features: [(wkb, nota >= 0 ou None)] na ordem das feições; None = barreira."""
        from osgeo import ogr
        from .gdal_scope import gdal_exceptions
        with gdal_exceptions():
            geoms = []
            for wkb, rating in features:
                if rating is None:
                    continue
                rating = float(rating)
                if not math.isfinite(rating) or rating < 0:
                    raise ValueError('Nota de atrito inválida (use valor >= 0): {0}.'.format(rating))
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
            self.edge_rating = np.repeat(self.ratings, np.diff(np.append(self.starts, len(self.edges))))
            self.union_edges = np.array([e for ring, _ in _polygon_rings(covered)
                                         for e in _ring_edges(ring, ccw=True)], dtype=np.float64)
            self.min_rating = float(self.ratings.min())
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
        """
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        out = np.empty(x.size, dtype=np.float64)
        for sl in _slices(x.size, len(self.edges) + len(self.union_edges)):
            xs, ys = x[sl], y[sl]
            gxs, gys = np.full(xs.size, gx + _NUDGE_X), np.full(xs.size, gy + _NUDGE_Y)
            valid, tau, denom = _crossings(gxs, gys, xs, ys, self.edges)
            signed = np.where(denom < 0, -1.0, 1.0) * tau * tau * self.edge_rating[None, :]
            total = np.where(valid, signed, 0.0).sum(axis=1) / 2.0
            parity = (np.add.reduceat(valid, self.starts, axis=1) % 2) == 1
            inside = parity ^ g_inside[None, :]
            covered = inside.any(axis=1)
            end_rating = np.where(covered, self.ratings[inside.argmax(axis=1)], 0.0)
            leaves, _, _ = _crossings(gxs, gys, xs, ys, self.union_edges)
            d2 = (xs - gx) ** 2 + (ys - gy) ** 2
            value = d2 * (total + end_rating / 2.0)
            # Arredondamento: a soma ± pode dar um negativo ínfimo; o custo real é >= 0.
            value = np.maximum(value, 0.0)
            value[~covered | leaves.any(axis=1)] = np.inf
            value[d2 == 0] = 0.0
            out[sl] = value
        return out


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
        # Limite inferior exato: A >= nota mínima × D² / 2.
        lower = self.surface.min_rating * d2 / 2.0 / self.mass[:, None]
        order = np.argsort(lower, axis=0, kind='stable')
        best = np.full(count, np.inf)
        best_j = np.full(count, npoles, dtype=np.int64)
        index = np.arange(count)
        for rank in range(npoles):
            j_for = order[rank]
            can = lower[j_for, index] <= best
            if not can.any():
                break
            for j in np.unique(j_for[can]):
                sub = np.flatnonzero(can & (j_for == j))
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


def _bisect_edges(lattice, edges, cancelled):
    """Para cada lado (i0, j0, di, dj, tamanho) com rótulos diferentes nas pontas, acha o par de nós
    vizinhos da malha fina em que o rótulo muda. Devolve [(ponto, rótulo antes, rótulo depois)]."""
    lo = np.zeros(len(edges), dtype=np.int64)
    hi = np.array([e[4] for e in edges], dtype=np.int64)
    first = np.array(lattice.labels([(e[0], e[1]) for e in edges]), dtype=np.int64)
    while np.any(hi - lo > 1):
        if cancelled and cancelled():
            raise InterruptedError('Voronoi cancelado.')
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


def _refine(model, segments, tolerance, cancelled, max_depth=14):
    """Insere vértices até a corda ficar a menos de ``tolerance`` da fronteira verdadeira.

    segments: [(P, Q, a, b)], fronteira entre os rótulos a e b. Para cada corda, procura a fronteira
    na mediatriz (bisseção entre um ponto de rótulo a e um de rótulo b); se ela fica a mais de
    ``tolerance`` do meio da corda, divide a corda nesse ponto.
    """
    done = []
    work = [(np.array(p, float), np.array(q, float), a, b, 0) for p, q, a, b in segments]
    while work:
        if cancelled and cancelled():
            raise InterruptedError('Voronoi cancelado.')
        active = [w for w in work if w[4] < max_depth and np.hypot(*(w[1] - w[0])) > 2 * tolerance]
        done.extend(w for w in work if not (w[4] < max_depth and np.hypot(*(w[1] - w[0])) > 2 * tolerance))
        if not active:
            break
        P = np.array([w[0] for w in active]); Q = np.array([w[1] for w in active])
        A = np.array([w[2] for w in active]); B = np.array([w[3] for w in active])
        M = (P + Q) / 2
        d = Q - P
        length = np.hypot(d[:, 0], d[:, 1])
        n = np.column_stack((-d[:, 1], d[:, 0])) / length[:, None]
        found = np.zeros(len(active), dtype=bool)
        lo_pt = np.zeros_like(M); hi_pt = np.zeros_like(M)
        for reach in (0.5, 0.25):
            todo = ~found
            if not todo.any():
                break
            r = (reach * length)[:, None]
            plus, minus = M + r * n, M - r * n
            lp = model.labels(plus[todo, 0], plus[todo, 1])
            lm = model.labels(minus[todo, 0], minus[todo, 1])
            idx = np.flatnonzero(todo)
            for k, a_, b_, vp, vm in zip(idx, A[todo], B[todo], lp, lm):
                if vm == a_ and vp == b_:
                    found[k] = True; lo_pt[k] = minus[k]; hi_pt[k] = plus[k]
                elif vm == b_ and vp == a_:
                    found[k] = True; lo_pt[k] = plus[k]; hi_pt[k] = minus[k]
        # lo_pt tem o rótulo a; hi_pt, o rótulo b. Bisseção contínua até tolerance / 4.
        sel = np.flatnonzero(found)
        if sel.size:
            span = np.hypot(*(hi_pt[sel] - lo_pt[sel]).T).max()
            for _ in range(max(1, int(math.ceil(math.log2(max(span, tolerance) / (tolerance / 4)))))):
                mid = (lo_pt[sel] + hi_pt[sel]) / 2
                lab = model.labels(mid[:, 0], mid[:, 1])
                is_a = lab == A[sel]
                lo_pt[sel[is_a]] = mid[is_a]
                hi_pt[sel[~is_a]] = mid[~is_a]
        work = []
        for k, w in enumerate(active):
            if not found[k]:
                done.append(w)
                continue
            boundary = (lo_pt[k] + hi_pt[k]) / 2
            if np.hypot(*(boundary - M[k])) <= tolerance:
                done.append(w)
            else:
                work.append((w[0], boundary, w[2], w[3], w[4] + 1))
                work.append((boundary, w[1], w[2], w[3], w[4] + 1))
    return [((float(p[0]), float(p[1])), (float(q[0]), float(q[1]))) for p, q, *_ in done]


def friction_voronoi_polygons(generators, features, bounds, *, spacing, tolerance=0.01,
                              mass_weighted=False, cancelled=None, progress=None):
    """Regiões de influência com atrito em vetor direto (modelo contínuo).

    features: [(wkb, nota ou None)]; bounds: extensão (xmin, ymin, xmax, ymax) no SRC dos polígonos;
    spacing: espaçamento da malha de busca (regiões menores que ele podem não ser detectadas);
    tolerance: desvio máximo das fronteiras traçadas (unidades do SRC).
    Retorna ([(centro, multipolígono OGR)], estatísticas).
    """
    from osgeo import ogr
    from .gdal_scope import gdal_exceptions
    xmin, ymin, xmax, ymax = map(float, bounds)
    if not all(math.isfinite(v) for v in (xmin, ymin, xmax, ymax)) or xmin >= xmax or ymin >= ymax:
        raise ValueError('A extensão do Voronoi precisa ter área positiva.')
    if not (math.isfinite(spacing) and spacing > 0 and math.isfinite(tolerance) and 0 < tolerance < spacing):
        raise ValueError('Espaçamento da busca e tolerância inválidos (0 < tolerância < espaçamento).')
    if (xmax - xmin) * (ymax - ymin) / spacing ** 2 > 4_000_000:
        raise ValueError('Espaçamento da busca pequeno demais para a extensão (mais de 4 milhões de nós).')
    surface = FrictionSurface(features, cancelled=cancelled)
    model = ContinuousModel(generators, surface, mass_weighted=mass_weighted)
    lattice = _Lattice(model, (xmin, ymin, xmax, ymax), spacing, tolerance)
    step = lattice.step
    # 1. Rótulos nos nós base.
    nx, ny = lattice.nx, lattice.ny
    ii, jj = np.meshgrid(np.arange(nx), np.arange(ny))
    lattice.labels(list(zip((ii.ravel() * step).tolist(), (jj.ravel() * step).tolist())))
    base_nodes = nx * ny
    if progress:
        progress(20)
    # 2. Refinamento local: células base com 3+ rótulos nos cantos (junções) ou em sela são
    # divididas em R × R; se um lado de uma célula refinada troca de rótulo mais de uma vez, a
    # vizinha daquele lado também é refinada, até estabilizar. Assim, um lado compartilhado entre
    # célula grossa e célula refinada tem no máximo uma troca, e os pontos de fronteira coincidem.
    R = 2 ** _REFINE_LEVEL
    sub = step // R

    def corners(i0, j0, size):
        return lattice.labels([(i0, j0), (i0 + size, j0), (i0 + size, j0 + size), (i0, j0 + size)])

    refined, queue = set(), []
    for j in range(ny - 1):
        for i in range(nx - 1):
            c = corners(i * step, j * step, step)
            kinds = len(set(c))
            if kinds >= 3 or (kinds == 2 and c[0] == c[2] and c[1] == c[3] and c[0] != c[1]):
                queue.append((i, j))
    while queue:
        if cancelled and cancelled():
            raise InterruptedError('Voronoi cancelado.')
        batch = [cell for cell in dict.fromkeys(queue) if cell not in refined]
        queue = []
        if not batch:
            break
        keys = [(i * step + a * sub, j * step + b * sub) for i, j in batch for a in range(R + 1) for b in range(R + 1)]
        lattice.labels(keys)
        for i, j in batch:
            refined.add((i, j))
            i0, j0 = i * step, j * step
            sides = {(0, -1): [(i0 + a * sub, j0) for a in range(R + 1)],
                     (1, 0): [(i0 + step, j0 + b * sub) for b in range(R + 1)],
                     (0, 1): [(i0 + a * sub, j0 + step) for a in range(R + 1)],
                     (-1, 0): [(i0, j0 + b * sub) for b in range(R + 1)]}
            for (di, dj), nodes in sides.items():
                values = lattice.labels(nodes)
                changes = sum(1 for u, v in zip(values, values[1:]) if u != v)
                ni, nj = i + di, j + dj
                if changes > 1 and 0 <= ni < nx - 1 and 0 <= nj < ny - 1 and (ni, nj) not in refined:
                    queue.append((ni, nj))
    cells = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            if (i, j) in refined:
                cells.extend((i * step + a * sub, j * step + b * sub, sub) for a in range(R) for b in range(R))
            else:
                cells.append((i * step, j * step, step))
    if progress:
        progress(35)
    # 3. Pontos de fronteira nos lados das células (bisseção diádica na malha fina; lados iguais
    # dão pontos iguais).
    def side_keys(i0, j0, size):
        return [(i0, j0, 1, 0, size), (i0 + size, j0, 0, 1, size), (i0, j0 + size, 1, 0, size), (i0, j0, 0, 1, size)]

    edge_specs, edge_index = [], {}
    for i0, j0, size in cells:
        for key in side_keys(i0, j0, size):
            if key in edge_index:
                continue
            a = lattice.labels([(key[0], key[1])])[0]
            b = lattice.labels([(key[0] + key[2] * size, key[1] + key[3] * size)])[0]
            if a != b:
                edge_index[key] = len(edge_specs)
                edge_specs.append(key)
    points = _bisect_edges(lattice, edge_specs, cancelled) if edge_specs else []
    if progress:
        progress(50)
    # Segmentos em cada célula (2 pontos: corda; sela de 2 rótulos: pelo centro; 3+ rótulos: junção).
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
    if progress:
        progress(60)
    # 4. Refinamento até a tolerância.
    lines = _refine(model, segments, tolerance, cancelled)
    if progress:
        progress(80)
    # 5. Polígonos: linhas + contorno da malha → poligonização → rótulo de cada face → união por polo.
    with gdal_exceptions():
        x1, y1 = lattice.xy((lattice.nx - 1) * step, (lattice.ny - 1) * step)
        frame = [(lattice.x0, lattice.y0), (float(x1), lattice.y0), (float(x1), float(y1)),
                 (lattice.x0, float(y1)), (lattice.x0, lattice.y0)]
        net = ogr.Geometry(ogr.wkbMultiLineString)
        for (p, q) in lines + list(zip(frame, frame[1:])):
            line = ogr.Geometry(ogr.wkbLineString)
            line.AddPoint_2D(*p)
            line.AddPoint_2D(*q)
            net.AddGeometry(line)
        # Noding das linhas (GEOS): UnaryUnion na GDAL >= 3.7; antes, a união com uma das próprias
        # linhas produz o mesmo resultado.
        noded = net.UnaryUnion() if hasattr(net, 'UnaryUnion') else net.Union(net.GetGeometryRef(0).Clone())
        faces = noded.Polygonize()
        if faces is None:
            raise RuntimeError('Falha ao montar os polígonos do Voronoi com atrito.')
        extent = ogr.Geometry(ogr.wkbPolygon)
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for x, y in ((xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax), (xmin, ymin)):
            ring.AddPoint_2D(x, y)
        extent.AddGeometry(ring)
        # A fronteira com a área sem polígono (barreira) é conhecida exatamente: a borda da cobertura.
        domain = extent.Intersection(surface.union)
        # Cada face é recortada pelo domínio ANTES de receber o rótulo: uma face que cruza a borda
        # da cobertura (dentro da tolerância) seria rotulada por um ponto de fora e descartada.
        # O recorte pode partir uma face em vários pedaços: cada pedaço recebe o próprio rótulo.
        pieces = ogr.Geometry(ogr.wkbMultiPolygon)
        for k in range(faces.GetGeometryCount()):
            clipped = faces.GetGeometryRef(k).Intersection(domain)
            if clipped is not None and not clipped.IsEmpty():
                _collect(clipped, pieces)
        parts = [pieces.GetGeometryRef(k).Clone() for k in range(pieces.GetGeometryCount())]
        inner = [part.PointOnSurface() for part in parts]
        face_labels = model.labels(np.array([p.GetX() for p in inner]), np.array([p.GetY() for p in inner]))
        regions = {}
        for g in generators:
            group = ogr.Geometry(ogr.wkbMultiPolygon)
            for part, label in zip(parts, face_labels):
                if label == g.identifier:
                    _collect(part, group)
            if group.GetGeometryCount():
                region = group.UnionCascaded().Intersection(domain)
                if region is not None and not region.IsEmpty():
                    regions[g.identifier] = region
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
                perimeter = piece.Boundary().Length()
                if perimeter <= 0 or 2 * piece.GetArea() / perimeter >= 2 * tolerance:
                    continue
                edge = piece.Boundary()
                shared = {ident: (edge.Intersection(region).Length() if edge.Intersects(region) else 0.0)
                          for ident, region in regions.items()}
                ident = max(shared, key=shared.get)
                if shared[ident] > 0:
                    regions[ident] = regions[ident].Union(piece)
                    absorbed += 1
        results = []
        for g in generators:
            region = regions.get(g.identifier)
            if region is None:
                continue
            polygons = ogr.Geometry(ogr.wkbMultiPolygon)
            _collect(region, polygons)
            if polygons.GetGeometryCount():
                results.append((g, polygons))
    if progress:
        progress(90)
    stats = {'spacing': spacing, 'tolerance': tolerance, 'base_nodes': int(base_nodes),
             'refined_cells': len(refined),
             'evaluations': model.evaluations, 'boundary_vertices': len(lines),
             'polygons': len(surface.ratings), 'min_rating': surface.min_rating,
             'absorbed_residues': absorbed}
    return results, stats


def _collect(geometry, target):
    from osgeo import ogr
    kind = ogr.GT_Flatten(geometry.GetGeometryType())
    if kind == ogr.wkbPolygon:
        if geometry.GetArea() > 0:
            target.AddGeometry(geometry)
    elif kind in (ogr.wkbMultiPolygon, ogr.wkbGeometryCollection):
        for i in range(geometry.GetGeometryCount()):
            _collect(geometry.GetGeometryRef(i), target)
