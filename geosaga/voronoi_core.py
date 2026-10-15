"""Núcleo testável do Voronoi Espacial (raster discretizado).

0.7.0: simples (menor distância euclidiana) e massa (maior M/d).
Os modelos de atrito e massa+atrito não são declarados equivalentes ao SAGA
até reconstrução/validação da integração do atrito ao longo da trajetória.
"""
from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class Generator:
    identifier: int
    x: float
    y: float
    mass: float = 1.0
    label: str = ''


def validate_generators(generators, *, weighted=False):
    if not generators:
        raise ValueError('Selecione pelo menos um ponto gerador.')
    ids = set()
    positions = set()
    for generator in generators:
        if not isinstance(generator.identifier, int) or generator.identifier <= 0:
            raise ValueError('Cada ponto precisa de um identificador inteiro positivo.')
        if generator.identifier in ids:
            raise ValueError('Identificadores de pontos repetidos.')
        ids.add(generator.identifier)
        if not all(math.isfinite(float(v)) for v in (generator.x, generator.y, generator.mass)):
            raise ValueError('Coordenadas e massas precisam ser números finitos.')
        if weighted and generator.mass <= 0:
            raise ValueError('As massas devem ser maiores que zero.')
        key = (float(generator.x), float(generator.y))
        if key in positions:
            raise ValueError('Pontos geradores coincidentes: separe ou consolide os pontos.')
        positions.add(key)


def assign_window(generators, geotransform, width, y_offset, height, *, mode='simple', mask=None):
    """Calcula IDs por centro de pixel; desempate pela ordem dos pontos.

    'mass': maximiza M / d, equivalente a minimizar d² / M². IDs 0
    representam áreas fora de máscara; a distância exata zero pertence
    ao respectivo centro gerador. A métrica exige CRS projetado.
    """
    if mode not in ('simple', 'mass'):
        raise ValueError('A modalidade de atrito ainda não foi implementada na versão 0.7.0.')
    validate_generators(generators, weighted=mode == 'mass')
    if len(geotransform) != 6 or width <= 0 or height <= 0 or y_offset < 0:
        raise ValueError('Parâmetros da grade inválidos.')
    if not all(math.isfinite(float(x)) for x in geotransform):
        raise ValueError('Transformação geográfica inválida.')
    t = geotransform
    if abs(t[1] * t[5] - t[2] * t[4]) < 1e-16:
        raise ValueError('Grade com área de pixel nula.')
    y, x = np.ogrid[y_offset:y_offset+height, :width]
    gx = t[0] + (x + .5) * t[1] + (y + .5) * t[2]
    gy = t[3] + (x + .5) * t[4] + (y + .5) * t[5]
    best = np.full((height, width), np.inf, dtype=np.float64)
    labels = np.zeros((height, width), dtype=np.int32)
    for generator in generators:
        dx = gx - generator.x
        dy = gy - generator.y
        dist_sq = dx * dx + dy * dy
        score = dist_sq / (generator.mass ** 2) if mode == 'mass' else dist_sq
        # '<' estável: empate conserva o primeiro ponto na ordem informada.
        better = score < best
        labels[better] = generator.identifier
        best[better] = score[better]
    if mask is not None:
        if mask.shape != labels.shape:
            raise ValueError('Dimensões da máscara não correspondem à janela.')
        labels[~mask.astype(bool)] = 0
    return labels



def build_nearest_index(generators):
    """Índice opcional SciPy; retorna None se indisponível no QGIS instalado.

    A implementação NumPy permanece como alternativa e produz o mesmo resultado.
    Não há dependência obrigatória adicional ao complemento.
    """
    if len(generators) < 2:
        return None
    try:
        from scipy.spatial import cKDTree
    except (ImportError, OSError):
        return None
    coordinates = np.asarray([(p.x, p.y) for p in generators], dtype=np.float64)
    return cKDTree(coordinates)


def assign_window_nearest(generators, geotransform, width, y_offset, height,
                          *, mask=None, index=None):
    """Voronoi simples exato, com índice espacial quando SciPy está disponível.

    A consulta ao índice devolve candidatos. Em pixels de empate numérico,
    o cálculo original é utilizado para preservar a regra de precedência.
    Sem SciPy, recorre ao cálculo NumPy existente, por blocos.
    """
    if index is None:
        return assign_window(generators, geotransform, width, y_offset, height,
                             mode='simple', mask=mask)
    validate_generators(generators)
    if len(geotransform) != 6 or width <= 0 or height <= 0 or y_offset < 0:
        raise ValueError('Parâmetros da grade inválidos.')
    t = geotransform
    if not all(math.isfinite(float(value)) for value in t):
        raise ValueError('Transformação geográfica inválida.')
    if abs(t[1]*t[5] - t[2]*t[4]) < 1e-16:
        raise ValueError('Grade com área de pixel nula.')
    rows, cols = np.ogrid[y_offset:y_offset+height, :width]
    xs = t[0] + (cols+.5)*t[1] + (rows+.5)*t[2]
    ys = t[3] + (cols+.5)*t[4] + (rows+.5)*t[5]
    xs, ys = np.broadcast_arrays(xs, ys)
    coords = np.column_stack((xs.ravel(), ys.ravel()))
    distances, indices = index.query(coords, k=2)
    ids = np.asarray([point.identifier for point in generators], dtype=np.int32)
    chosen = ids[indices[:, 0]].copy()
    # Um empate precisa respeitar a ordem original dos pontos, incluindo
    # situações com três ou mais centros igualmente próximos.
    ties = np.flatnonzero(np.isclose(distances[:, 0], distances[:, 1],
                                     rtol=1e-12, atol=1e-12))
    if ties.size:
        centers = np.asarray([(point.x, point.y) for point in generators],
                             dtype=np.float64)
        for offset in range(0, len(ties), 4096):
            subset = ties[offset:offset+4096]
            differences = coords[subset, None, :] - centers[None, :, :]
            dist_sq = np.sum(differences*differences, axis=2)
            chosen[subset] = ids[np.argmin(dist_sq, axis=1)]
    result = chosen.reshape((height, width))
    if mask is not None:
        if mask.shape != result.shape:
            raise ValueError('Dimensões da máscara não correspondem à janela.')
        result[~mask.astype(bool)] = 0
    return result

def pixel_area_m2(geotransform, units_to_meters=1.0):
    if not math.isfinite(units_to_meters) or units_to_meters <= 0:
        raise ValueError('Unidade linear desconhecida.')
    t = geotransform
    return abs(t[1] * t[5] - t[2] * t[4]) * units_to_meters ** 2


def counts_as_rows(generators, counts, geotransform, units_to_meters=1.0):
    area = pixel_area_m2(geotransform, units_to_meters)
    total = sum(int(counts.get(s.identifier, 0)) for s in generators)
    rows = []
    for point in generators:
        n = int(counts.get(point.identifier, 0))
        rows.append({'ID': point.identifier, 'CENTRO': point.label or f'Centro {point.identifier}',
                     'MASSA': float(point.mass), 'PIXELS': n,
                     'AREA_M2': n*area, 'AREA_HA': n*area/10000,
                     'PCT_AREA': 100*n/total if total else 0.0})
    return rows
