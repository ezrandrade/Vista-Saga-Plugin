"""Voronoi com atrito no modelo do Vista SAGA/UFRJ (validado na 1.4.0).

Para cada célula x e cada polo G, o custo acumulado é

    A(G → x) = Σ_k  d(G, c_k) × nota(c_k) × passo_k

sobre as células c_k da reta de Bresenham entre a célula do polo e x (sem a célula do polo, cuja
distância é zero): d é a distância do centro da célula do polo ao centro de c_k; passo_k é o
comprimento do passo (largura da célula, altura da célula ou a diagonal, √2 em células quadradas).
Sem massa, vence o menor A; com massa, o menor A / M. Como A cresce com d², a massa vale como
M/d², a mesma lei da modalidade Com Massa. Empates: vence o polo que vem primeiro na lista; a célula
do próprio polo é sempre dele.

A nota de cada célula entra direto como custo (nota 1 = custo basal). NoData é barreira: a célula
não recebe resultado e nenhuma reta passa por ela.

Validação caixa-preta contra o Vista SAGA original (caso sintético de 80 × 60 células, 17/11/2026):
99,67% das células sem massa e 99,69% com massa; as diferenças ficam todas na fronteira entre
regiões (detalhe do traçado). Ver docs/CONTEXTO_SESSOES.md e scripts/comparar_caso_atrito.py.
"""
import math
import numpy as np
from .voronoi_core import validate_generators

MAX_FRICTION_CELLS = 8_000_000
MAX_FRICTION_CENTRES = 500
# Limite de trabalho conservador antes de alocar grandes buffers
MAX_ESTIMATED_CELL_VISITS = 700_000_000

FRICTION_MODEL = 'SUM(d(G,c_k) * nota_k * passo_k), Bresenham; Vista SAGA'
MASS_FRICTION_MODEL = 'SUM(d(G,c_k) * nota_k * passo_k) / M, Bresenham; Vista SAGA'


def validate_friction(raster, geotransform, generators):
    arr = np.asarray(raster)
    if arr.ndim != 2 or arr.size == 0 or arr.size > MAX_FRICTION_CELLS:
        raise ValueError('O atrito deve conter entre 1 e 8 milhões de células; reduza a extensão/resolução.')
    if len(generators) > MAX_FRICTION_CENTRES:
        raise ValueError('O Voronoi com Atrito aceita até 500 centros nesta etapa.')
    validate_generators(generators)
    if len(geotransform) != 6 or not all(math.isfinite(float(v)) for v in geotransform):
        raise ValueError('Transformação geográfica inválida.')
    t = geotransform
    if t[1] <= 0 or t[5] >= 0 or t[2] != 0 or t[4] != 0:
        raise ValueError('A superfície de atrito precisa ser norte-acima, sem rotação ou cisalhamento.')
    # A nota entra direto como custo; NaN assinala barreira. Nota 0 é recusada desde a 1.4.0 (custo
    # zero cria empates resolvidos pela ordem dos pontos; comportamento do Vista SAGA não testado).
    if np.any(np.isfinite(arr) & (arr <= 0)):
        raise ValueError('O atrito precisa ser maior que 0 em todas as células (NoData = barreira); para '
                         'quase sem atrito, use um valor pequeno, como 0,1.')
    if np.any(np.isposinf(arr) | np.isneginf(arr)):
        raise ValueError('Use NoData para células inacessíveis; valores infinitos não são suportados.')
    width = arr.shape[1]
    height = arr.shape[0]
    for point in generators:
        col = (point.x-t[0])/t[1]
        row = (point.y-t[3])/t[5]
        if not 0 <= col < width or not 0 <= row < height:
            raise ValueError(f'Centro {point.identifier} fora da extensão do raster de atrito.')
        if not np.isfinite(arr[int(row),int(col)]):
            raise ValueError(f'Centro {point.identifier} está sobre NoData; reposicione-o ou corrija o mapa.')


def estimated_visits(height, width, centers):
    # estimativa de ordem de grandeza, não uma previsão de tempo
    return height * width * centers * (height + width) // 4


def _vista_saga_cost_batch(raster, start_col, start_row, cols, rows, *, pixel_x=1.0, pixel_y=1.0,
                           max_costs=None, stats=None):
    """Custos A(G → x) do polo na célula (start_col, start_row) até as células (cols, rows).

    Reta de Bresenham inteira (a mesma da validação), vetorizada: todas as trajetórias andam um
    passo por iteração. Uma trajetória que encontra NoData devolve infinito.

    max_costs: limite opcional por trajetória. Se o custo parcial superar estritamente o limite,
    o restante pode ser descartado sem alterar a escolha do polo, porque cada parcela é >= 0.
    """
    cols = np.asarray(cols, dtype=np.int64)
    rows = np.asarray(rows, dtype=np.int64)
    count = cols.size
    if max_costs is not None:
        limits = np.broadcast_to(np.asarray(max_costs, dtype=np.float64), (count,))
        if np.any(np.isnan(limits) | (limits < 0)):
            raise ValueError('Os limites máximos de custo devem ser não negativos.')
    else:
        limits = None
    height, width = raster.shape
    x0, y0 = int(start_col), int(start_row)
    if not (0 <= x0 < width and 0 <= y0 < height):
        raise ValueError('A célula do polo está fora da grade de atrito.')
    if count and (cols.min() < 0 or rows.min() < 0 or cols.max() >= width or rows.max() >= height):
        raise ValueError('Célula de destino fora da grade de atrito.')
    px, py = float(pixel_x), float(pixel_y)
    diagonal = math.hypot(px, py)
    x = np.full(count, x0, dtype=np.int64)
    y = np.full(count, y0, dtype=np.int64)
    dx = np.abs(cols - x0)
    dy = -np.abs(rows - y0)
    sx = np.where(x0 < cols, 1, -1)
    sy = np.where(y0 < rows, 1, -1)
    err = dx + dy
    result = np.zeros(count, dtype=np.float64)
    good = np.ones(count, dtype=bool)
    dropped = np.zeros(count, dtype=bool)
    reached = (x == cols) & (y == rows)
    visits = 0
    for _ in range(width + height + 2):
        move = good & ~reached
        if not np.any(move):
            break
        e2 = 2 * err
        mx = move & (e2 >= dy)
        my = move & (e2 <= dx)
        err[mx] += dy[mx]
        x[mx] += sx[mx]
        err[my] += dx[my]
        y[my] += sy[my]
        ids = np.flatnonzero(move)
        ratings = raster[y[ids], x[ids]]
        valid = np.isfinite(ratings)
        good[ids[~valid]] = False
        ids, ratings = ids[valid], ratings[valid]
        step = np.where(mx[ids] & my[ids], diagonal, np.where(mx[ids], px, py))
        dist = np.hypot((x[ids] - x0) * px, (y[ids] - y0) * py)
        result[ids] += dist * ratings * step
        visits += ids.size
        if limits is not None and ids.size:
            # Não desconsiderar empates: somente custo ESTRITAMENTE maior.
            discarded = ids[result[ids] > limits[ids]]
            good[discarded] = False
            dropped[discarded] = True
        reached = (x == cols) & (y == rows)
    else:
        raise RuntimeError('O traçado do atrito excedeu o limite de células da grade.')
    result[~good] = np.inf
    if stats is not None:
        stats['visited_cells'] = stats.get('visited_cells', 0) + visits
        stats['early_stops'] = stats.get('early_stops', 0) + int(np.count_nonzero(dropped))
    return result


def assign_friction_window(generators, friction, geotransform, y_offset, height,
                           *, cancelled=None, batch_size=1536, mass_weighted=False, stats=None,
                           min_rating=None):
    """Retorna identificadores pelo menor A(G → x), ou A / M com massa (ver o módulo).

    A linha da matriz é dividida em lotes para limitar buffers, mantendo a precedência do
    primeiro polo no caso de pontuações idênticas. min_rating: menor nota finita da grade
    (calculada se omitida); serve só à poda.
    """
    validate_generators(generators, weighted=mass_weighted)
    arr = np.asarray(friction, dtype=np.float64)
    t = geotransform
    width = arr.shape[1]
    if height < 1 or y_offset < 0 or y_offset+height > arr.shape[0]:
        raise ValueError('Janela do raster de atrito inválida.')
    px, py = abs(float(t[1])), abs(float(t[5]))
    if min_rating is None:
        finite = arr[np.isfinite(arr)]
        min_rating = float(finite.min()) if finite.size else 0.0
    # Poda exata por limite inferior: na reta de Bresenham, o k-ésimo passo chega a uma célula
    # a k células (Chebyshev) do polo; logo d >= k × menor lado, passo >= menor lado e
    # A >= nota mínima × menor lado² × n(n+1)/2, com n = maior separação em linhas/colunas.
    # Nenhuma aproximação é introduzida.
    lower_factor = max(float(min_rating), 0.0) * min(px, py) ** 2 / 2.0
    result = np.zeros((height, width), dtype=np.int32)
    npoints = len(generators)
    source_cols = np.array([math.floor((p.x-t[0])/t[1]) for p in generators], dtype=np.int64)
    source_rows = np.array([math.floor((p.y-t[3])/t[5]) for p in generators], dtype=np.int64)
    mass = np.array([p.mass if mass_weighted else 1.0 for p in generators], dtype=np.float64)
    identifiers = np.array([p.identifier for p in generators], dtype=np.int32)
    for row in range(y_offset, y_offset+height):
        if cancelled and cancelled():
            raise InterruptedError('Voronoi com Atrito cancelado pelo usuário.')
        candidates = np.flatnonzero(np.isfinite(arr[row]))
        for off in range(0, candidates.size, batch_size):
            if cancelled and cancelled():
                raise InterruptedError('Voronoi com Atrito cancelado pelo usuário.')
            cols = candidates[off:off+batch_size]
            if stats is not None:
                stats['candidate_pairs'] = stats.get('candidate_pairs', 0) + int(npoints * cols.size)
            steps = np.maximum(np.abs(cols[None, :] - source_cols[:, None]),
                               np.abs(row - source_rows)[:, None]).astype(np.float64)
            lower = lower_factor * steps * (steps + 1) / mass[:, None]
            ordered = np.argsort(lower, axis=0, kind='stable')
            indexes = np.arange(cols.size)
            best = np.full(cols.size, np.inf)
            best_order = np.full(cols.size, npoints, dtype=np.int32)
            choices = np.zeros(cols.size, dtype=np.int32)
            for rank in range(npoints):
                if cancelled and cancelled():
                    raise InterruptedError('Voronoi com Atrito cancelado pelo usuário.')
                j_for_pixel = ordered[rank]
                can_win = lower[j_for_pixel, indexes] <= best
                if not np.any(can_win):
                    break
                for j in np.unique(j_for_pixel[can_win]):
                    sub = np.flatnonzero(can_win & (j_for_pixel == j))
                    if stats is not None:
                        stats['traced_paths'] = stats.get('traced_paths', 0) + int(sub.size)
                    # Escore = A / M: nenhum percurso cujo custo parcial ultrapasse
                    # (melhor escore × M) pode assumir a célula. nextafter protege empates.
                    with np.errstate(invalid='ignore', over='ignore'):
                        cutoff = np.where(np.isfinite(best[sub]), best[sub] * mass[j], np.inf)
                    cutoff = np.nextafter(np.nextafter(cutoff, np.inf), np.inf)
                    costs = _vista_saga_cost_batch(
                        arr, source_cols[j], source_rows[j], cols[sub], np.full(sub.size, row),
                        pixel_x=px, pixel_y=py, max_costs=cutoff, stats=stats)
                    score = costs / mass[j]
                    choose = np.isfinite(score) & ((score < best[sub]) |
                               ((score == best[sub]) & (j < best_order[sub])))
                    taken = sub[choose]
                    best[taken] = score[choose]
                    best_order[taken] = j
                    choices[taken] = identifiers[j]
            result[row-y_offset, cols] = choices
    # A célula do polo pertence ao próprio polo (no Vista SAGA ela é marcada como "Ponto"); com
    # vários polos na mesma célula, vence o primeiro da lista. Evita que um empate de custo zero
    # (notas 0) entregue a célula do polo a outro centro.
    for j in range(npoints - 1, -1, -1):
        r, c = int(source_rows[j]), int(source_cols[j])
        if y_offset <= r < y_offset + height and np.isfinite(arr[r, c]):
            result[r - y_offset, c] = identifiers[j]
    return result
