"""Voronoi por atrito ao longo do segmento RETO centro-célula (experimental).

Modelo nesta fase: minimizar D * A, com A = soma de (1 + C_k) para
cada célula atravessada pelo segmento retilíneo entre o gerador e
centro da célula de destino. C_k >= 0; 1 é o custo basal explícito.
Não busca caminhos mínimos (Dijkstra) e não reivindica reprodução
numérica exata da implementação Vista SAGA/UFRJ.

Traçado DDA no espaço da matriz: cruza cantos sem contar células que
tocam apenas um vértice, soma uma vez cada célula atravessada.
"""
import math
import numpy as np
from .voronoi_core import validate_generators

MAX_FRICTION_CELLS = 8_000_000
MAX_FRICTION_CENTRES = 500
# Limite de trabalho conservador antes de alocar grandes buffers
MAX_ESTIMATED_CELL_VISITS = 700_000_000


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
    # Custo basal 1.0 permite que atrito=0 seja tratado como fricção mínima;
    # inf/nan assinalam barreiras explícitas.
    if np.any(np.isfinite(arr) & (arr < 0)):
        raise ValueError('O atrito não admite valores negativos; use valores >= 0 ou NoData.')
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


def _straight_cost_batch(raster, start_x, start_y, xs, ys, *, baseline=1.0,
                         max_costs=None, stats=None):
    """Custos em segmentos contínuos até centros de pixels, DDA vetorizado.

    start_x/start_y e xs/ys estão em coordenadas fracionárias de pixel.
    Uma trajetória que encontra NoData devolve infinito.

    max_costs: limite opcional por trajetória, em unidades de atrito acumulado.
    Se o custo parcial superar estritamente o limite, o restante da trajetória
    pode ser descartado sem alterar a escolha do gerador. Custos não negativos
    garantem que o escore não voltará a diminuir.
    
    """
    xs = np.asarray(xs, dtype=np.float64)
    ys = np.asarray(ys, dtype=np.float64)
    count = xs.size
    if max_costs is not None:
        limits = np.broadcast_to(np.asarray(max_costs, dtype=np.float64), (count,))
        if np.any(np.isnan(limits) | (limits < 0)):
            raise ValueError('Os limites máximos de custo devem ser não negativos.')
    else:
        limits = None
    width, height = raster.shape[1], raster.shape[0]
    x = np.full(count, int(math.floor(start_x)), dtype=np.int32)
    y = np.full(count, int(math.floor(start_y)), dtype=np.int32)
    dest_x = np.floor(xs).astype(np.int32)
    dest_y = np.floor(ys).astype(np.int32)
    dx = xs - start_x
    dy = ys - start_y
    step_x = np.sign(dx).astype(np.int32)
    step_y = np.sign(dy).astype(np.int32)
    with np.errstate(divide='ignore', invalid='ignore'):
        inc_x = np.where(step_x != 0, 1.0/np.abs(dx), np.inf)
        inc_y = np.where(step_y != 0, 1.0/np.abs(dy), np.inf)
        boundary_x = np.where(step_x > 0, x + 1, x)
        boundary_y = np.where(step_y > 0, y + 1, y)
        crossing_x = np.where(step_x != 0, (boundary_x-start_x)/dx, np.inf)
        crossing_y = np.where(step_y != 0, (boundary_y-start_y)/dy, np.inf)
    good = np.ones(count, dtype=bool)
    dropped = np.zeros(count, dtype=bool)
    cell_visits = count  # cada trajetória inclui a célula inicial
    result = np.zeros(count, dtype=np.float64)
    reached = (x == dest_x) & (y == dest_y)
    # Todas as trajetórias começam na mesma célula do centro gerador.
    c0 = raster[int(math.floor(start_y)), int(math.floor(start_x))]
    result[:] = float(c0) + baseline
    if limits is not None:
        dropped = result > limits
        good[dropped] = False
    for _ in range(width+height+2):
        move = (~reached) & good
        if not np.any(move):
            break
        tx = move & (crossing_x <= crossing_y)
        ty = move & (crossing_y <= crossing_x)
        x[tx] += step_x[tx]
        y[ty] += step_y[ty]
        crossing_x[tx] += inc_x[tx]
        crossing_y[ty] += inc_y[ty]
        # Valida limites antes de fazer indexação vetorizada.
        inside = move & (x >= 0) & (x < width) & (y >= 0) & (y < height)
        good[move & ~inside] = False
        if np.any(inside):
            ids = np.flatnonzero(inside)
            costs = raster[y[ids], x[ids]]
            valid = np.isfinite(costs)
            good[ids[~valid]] = False
            result[ids[valid]] += costs[valid] + baseline
            cell_visits += int(np.count_nonzero(valid))
            if limits is not None and np.any(valid):
                # Não desconsiderar empates: somente custo ESTRITAMENTE maior.
                checked = ids[valid]
                cannot_win = result[checked] > limits[checked]
                discarded = checked[cannot_win]
                good[discarded] = False
                dropped[discarded] = True
        reached = (x == dest_x) & (y == dest_y)
    else:
        raise RuntimeError('O traçado do atrito excedeu o limite de células da grade.')
    result[~good] = np.inf
    if stats is not None:
        stats['visited_cells'] = stats.get('visited_cells', 0) + cell_visits
        stats['early_stops'] = stats.get('early_stops', 0) + int(np.count_nonzero(dropped))
    return result


def assign_friction_window(generators, friction, geotransform, y_offset, height,
                           *, baseline=1.0, cancelled=None, batch_size=1536, mass_weighted=False, stats=None):
    """Retorna identificadores pelo menor D * soma(custo das células) / M opcional.

    A linha da matriz é dividida em lotes para limitar buffers, mantendo
    a precedência do primeiro gerador no caso de pontuações idênticas.
    """
    if not math.isfinite(baseline) or baseline <= 0:
        raise ValueError('O custo basal precisa ser positivo.')
    validate_generators(generators, weighted=mass_weighted)
    arr = np.asarray(friction)
    t = geotransform
    width = arr.shape[1]
    if height < 1 or y_offset < 0 or y_offset+height > arr.shape[0]:
        raise ValueError('Janela do raster de atrito inválida.')
    # Poda exata por limite inferior: para chegar à célula de destino, o
    # segmento precisa atravessar pelo menos a maior separação em linhas/colunas
    # (mais a célula inicial). Como C>=0, cada célula custa >= baseline.
    # Qualquer gerador cujo limite inferior já excede o melhor escore não
    # pode vencer a influência corrente. Nenhuma aproximação é introduzida.
    result = np.zeros((height, width), dtype=np.int32)
    npoints = len(generators)
    gcols = np.array([(p.x-t[0])/t[1] for p in generators], dtype=np.float64)
    grows = np.array([(p.y-t[3])/t[5] for p in generators], dtype=np.float64)
    source_cols = np.floor(gcols).astype(np.int32)
    source_rows = np.floor(grows).astype(np.int32)
    world_cx = np.array([p.x for p in generators], dtype=np.float64)
    world_cy = np.array([p.y for p in generators], dtype=np.float64)
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
            tx = cols.astype(np.float64) + .5
            ty = np.full(tx.size, row+.5, dtype=np.float64)
            world_x = t[0] + tx*t[1]
            world_y = t[3] + ty*t[5]
            # [centro, pixel] — memória limitada pelo batch_size.
            distances = np.hypot(world_x[None,:]-world_cx[:,None],
                                 world_y[None,:]-world_cy[:,None])
            min_cells = np.maximum(np.abs(cols[None,:]-source_cols[:,None]),
                                   abs(row-source_rows[:,None]))+1
            lower = distances * (baseline*min_cells) / mass[:,None]
            ordered = np.argsort(lower, axis=0, kind='stable')
            indexes = np.arange(tx.size)
            best = np.full(tx.size, np.inf)
            best_order = np.full(tx.size, npoints, dtype=np.int32)
            choices = np.zeros(tx.size, dtype=np.int32)
            for rank in range(npoints):
                if cancelled and cancelled():
                    raise InterruptedError('Voronoi com Atrito cancelado pelo usuário.')
                j_for_pixel = ordered[rank]
                can_win = lower[j_for_pixel,indexes] <= best
                if not np.any(can_win):
                    break
                for j in np.unique(j_for_pixel[can_win]):
                    sub = np.flatnonzero(can_win & (j_for_pixel == j))
                    if stats is not None:
                        stats['traced_paths'] = stats.get('traced_paths', 0) + int(sub.size)
                    # Escore = D * custo / massa. Se já existe um vencedor
                    # finito, nenhum percurso cujo custo parcial ultrapasse
                    # (melhor escore * massa / D) pode assumir essa célula.
                    # nextafter alarga o limiar para proteger empates em float64.
                    d = distances[j,sub]
                    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
                        cutoff = np.where((d > 0) & np.isfinite(best[sub]),
                                          best[sub] * mass[j] / d, np.inf)
                    cutoff = np.nextafter(np.nextafter(cutoff, np.inf), np.inf)
                    costs = _straight_cost_batch(
                        arr, gcols[j], grows[j], tx[sub], ty[sub],
                        baseline=baseline, max_costs=cutoff, stats=stats)
                    score = distances[j,sub] * costs / mass[j]
                    choose = np.isfinite(score) & ((score < best[sub]) |
                               ((score == best[sub]) & (j < best_order[sub])))
                    taken = sub[choose]
                    best[taken] = score[choose]
                    best_order[taken] = j
                    choices[taken] = identifiers[j]
            result[row-y_offset,cols] = choices
    return result
