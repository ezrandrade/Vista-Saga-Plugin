"""Composição rastreável de múltiplas superfícies de atrito para o Voronoi.

Cada superfície precisa estar no MESMO SRC, grade e resolução. Os valores
representam resistências >= 0. Opcionalmente os códigos categóricos podem ser
convertidos para notas de resistência informadas pelo usuário.

Não normaliza automaticamente mapas heterogêneos: valores e notas devem estar
em escala comparável antes da ponderação. NoData em qualquer critério vira
barreira (NaN) para preservar a cobertura comum entre os critérios.
"""
import math
import numpy as np

MAX_FRICTION_LAYERS = 12


def parse_class_notes(text):
    """Lê '1=2; 2=7' como {código: nota}; string vazia usa valores originais."""
    if not str(text or '').strip():
        return {}
    mapping = {}
    for raw in str(text).split(';'):
        raw = raw.strip()
        if not raw:
            continue
        if '=' not in raw:
            raise ValueError('Notas inválidas. Use código=nota; código=nota (ex.: 1=2;2=8).')
        source, score = raw.split('=', 1)
        try:
            code = float(source.strip())
            value = float(score.strip())
        except ValueError:
            raise ValueError('Códigos e notas devem ser valores numéricos.') from None
        if not (math.isfinite(code) and math.isfinite(value) and value >= 0):
            raise ValueError('Notas/códigos precisam ser finitos, com resistência >= 0.')
        if code in mapping:
            raise ValueError(f'Código repetido no mapa de notas: {code:g}.')
        mapping[code] = value
    if not mapping:
        raise ValueError('Informe pelo menos uma nota por classe ou deixe o campo vazio.')
    if len(mapping) > 4096:
        raise ValueError('O máximo é 4096 códigos por superfície.')
    return mapping


def apply_class_notes(array, notes):
    """Traduz códigos originais para resistências, preservando NaN/barreiras."""
    raster = np.asarray(array, dtype=np.float64)
    if not notes:
        return raster
    out = np.full(raster.shape, np.nan, dtype=np.float64)
    valid = np.isfinite(raster)
    remaining = valid.copy()
    for code, value in notes.items():
        chosen = valid & (raster == float(code))
        out[chosen] = float(value)
        remaining[chosen] = False
    if remaining.any():
        unknown = float(raster[remaining][0])
        raise ValueError(f'Classe {unknown:g} sem nota na reclassificação do atrito.')
    return out


def combine_friction_arrays(arrays, weights, note_specs=None):
    """Média ponderada sobre cobertura comum; NoData invalida a célula.

    Saída float64 com NaN em barreiras. Não aplica custo basal aqui: o motor
    do Voronoi continua usando (1 + C) por célula na trajetória.
    """
    if not arrays or len(arrays) > MAX_FRICTION_LAYERS or len(weights) != len(arrays):
        raise ValueError('Selecione entre 1 e 12 superfícies com um peso por camada.')
    if note_specs is None:
        note_specs = [''] * len(arrays)
    if len(note_specs) != len(arrays):
        raise ValueError('As notas precisam corresponder às superfícies.')
    normalized_weights = [float(weight) for weight in weights]
    if any(not math.isfinite(weight) or weight <= 0 for weight in normalized_weights):
        raise ValueError('Cada superfície deve possuir peso positivo e finito.')
    shape = np.asarray(arrays[0]).shape
    if len(shape) != 2:
        raise ValueError('O atrito deve ser um raster monobanda.')
    total = np.zeros(shape, dtype=np.float64)
    covered = np.ones(shape, dtype=bool)
    for raster, weight, spec in zip(arrays, normalized_weights, note_specs):
        arr = np.asarray(raster, dtype=np.float64)
        if arr.shape != shape:
            raise ValueError('Todas as superfícies precisam ter as mesmas dimensões.')
        if np.any(np.isfinite(arr) & (arr < 0)):
            raise ValueError('Uma superfície contém valores negativos de atrito.')
        if np.isinf(arr).any():
            raise ValueError('Atrito infinito não é suportado; use NoData.')
        notes = parse_class_notes(spec) if isinstance(spec, str) else spec
        ratings = apply_class_notes(arr, notes)
        valid = np.isfinite(ratings)
        covered &= valid
        total += np.where(valid, ratings, 0) * weight
    total /= sum(normalized_weights)
    total[~covered] = np.nan
    return total


def read_friction_stack(components, gdal, target_wkt, transform, width, height, osr):
    """Lê arquivos GDAL somente na thread de processamento; alinha sem reamostrar."""
    import os
    if not components or len(components) > MAX_FRICTION_LAYERS:
        raise ValueError('Adicione de 1 a 12 superfícies de atrito.')
    target = osr.SpatialReference()
    if target.ImportFromWkt(target_wkt) != 0:
        raise ValueError('SRC de referência inválido para composição do atrito.')
    # Acumulação em streaming: não mantém até 12 matrizes completas em RAM.
    # Em grades de 8 milhões de pixels isso evita centenas de MB adicionais.
    weighted_sum = np.zeros((height,width), dtype=np.float64)
    covered = np.ones((height,width), dtype=bool)
    weight_sum = 0.
    for comp in components:
        path = os.path.abspath(str(comp['path']))
        if not os.path.isfile(path):
            raise ValueError('Raster de atrito não encontrado: ' + path)
        ds = gdal.Open(path, gdal.GA_ReadOnly)
        if ds is None or ds.RasterCount != 1:
            raise ValueError('O atrito precisa ser monobanda e acessível: ' + path)
        if (ds.RasterXSize, ds.RasterYSize) != (width, height):
            raise ValueError('Dimensões diferentes entre superfícies de atrito: ' + path)
        gt = ds.GetGeoTransform()
        # Tolerância numérica subpixel; não altera pixels nem realiza reprojeção.
        if any(abs(float(a)-float(b)) > max(1.e-7, abs(transform[1]) * 1.e-6)
               for a,b in zip(gt, transform)):
            raise ValueError('Grades espacialmente desalinhadas: ' + path)
        srs = osr.SpatialReference()
        if srs.ImportFromWkt(ds.GetProjectionRef()) != 0 or not srs.IsSame(target):
            raise ValueError('SRC distinto na superfície de atrito: ' + path)
        band = ds.GetRasterBand(1)
        raster = band.ReadAsArray().astype(np.float64)
        nodata = band.GetNoDataValue()
        if nodata is not None:
            raster[np.isnan(raster) if np.isnan(nodata) else raster == nodata] = np.nan
        raster[band.GetMaskBand().ReadAsArray() == 0] = np.nan
        weight = float(comp['weight'])
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError('Todos os pesos das superfícies devem ser positivos e finitos.')
        if np.any(np.isfinite(raster) & (raster < 0)) or np.isinf(raster).any():
            raise ValueError('Atrito inválido: use resistência não negativa e NoData como barreira.')
        notes = parse_class_notes(comp.get('notes',''))
        ratings = apply_class_notes(raster, notes)
        good = np.isfinite(ratings)
        covered &= good
        weighted_sum += np.where(good, ratings, 0.) * weight
        weight_sum += weight
        del raster, ratings
        band = None
        ds = None
    weighted_sum /= weight_sum
    weighted_sum[~covered] = np.nan
    return weighted_sum
