"""Discretização controlada de GeoTIFFs contínuos para vetorização poligonal.

O raster de avaliação original NÃO é modificado. Sem QGIS no import: executa os
cálculos usando NumPy e usa GDAL somente nos procedimentos de E/S.
"""
import math

import numpy as np

from .rs2_format import RS2Error


def valid_values(values, nodata):
    """Mascara NaN, +/-infinito e NoData sem excluir valores 0 legítimos."""
    valid = np.isfinite(values)
    if nodata is not None:
        if np.isfinite(nodata):
            valid &= values != nodata
        # NaN/-inf/+inf já são inválidos por isfinite.
    return valid


def class_edges(minimum, maximum, requested_classes):
    """Limites equidistantes: início inclusivo, término exclusivo (última inclusiva)."""
    if not (math.isfinite(minimum) and math.isfinite(maximum)) or minimum > maximum:
        raise RS2Error('Intervalo de valores contínuos inválido.')
    if not isinstance(requested_classes, int) or not (2 <= requested_classes <= 20):
        raise RS2Error('A quantidade de classes deve estar entre 2 e 20.')
    if maximum == minimum:
        return np.asarray([minimum, maximum], dtype=np.float64)
    # np.linspace preserva melhor bordas exatas em intervalos regulares.
    edges = np.linspace(minimum, maximum, requested_classes + 1, dtype=np.float64)
    edges[0], edges[-1] = minimum, maximum
    if not np.all(np.diff(edges) > 0):
        raise RS2Error('Intervalos indistinguíveis na precisão numérica dos valores.')
    return edges


def classify_array(values, edges, nodata=None):
    """Retorna códigos 1..n e 0 para células inválidas/NoData."""
    array = np.asarray(values)
    valid = valid_values(array, nodata)
    codes = np.zeros(array.shape, dtype=np.uint8)
    if np.any(valid):
        # Índice da próxima borda interna; valores exatamente no limite
        # são incluídos na classe seguinte, exceto o máximo na última.
        indices = np.searchsorted(edges[1:-1], array[valid], side='right') + 1
        codes[valid] = np.clip(indices, 1, len(edges) - 1).astype(np.uint8)
    return codes


def class_intervals(edges):
    """Dicionário código -> (legenda textual, valor mínimo, valor máximo)."""
    result = {}
    for i in range(len(edges) - 1):
        lo, hi = float(edges[i]), float(edges[i+1])
        if len(edges) == 2 and lo == hi:
            label = f'Valor {lo:.9g}'
        else:
            closer = ']' if i == len(edges) - 2 else ')'
            label = f'[{lo:.9g}; {hi:.9g}{closer}'
        result[i+1] = (label, lo, hi)
    return result


def _scan_range(band, width, height, notify):
    minimum = math.inf
    maximum = -math.inf
    nodata = band.GetNoDataValue()
    for y in range(0, height, 128):
        n = min(128, height-y)
        arr = band.ReadAsArray(0, y, width, n)
        if arr is None:
            raise RS2Error('Falha ao ler valores contínuos do GeoTIFF.')
        valid = valid_values(arr, nodata)
        if np.any(valid):
            minimum = min(minimum, float(np.min(arr[valid])))
            maximum = max(maximum, float(np.max(arr[valid])))
        notify(.03 + .14 * (y+n)/height)
    if minimum == math.inf:
        raise RS2Error('O GeoTIFF não contém pixels válidos para vetorizar.')
    return minimum, maximum


def discretize_tiff(gdal, ds, tmp_path, pixel_count, notify, geotransform=None):
    """Cria GTiff temporário de categorias 1..n. Não altera dados de entrada.

    É seguro para grandes rasters: percorre o original em blocos de 128 linhas.
    """
    band = ds.GetRasterBand(1)
    width, height = ds.RasterXSize, ds.RasterYSize
    minimum, maximum = _scan_range(band, width, height, notify)
    edges = class_edges(minimum, maximum, pixel_count)
    driver = gdal.GetDriverByName('GTiff')
    out = driver.Create(str(tmp_path), width, height, 1, gdal.GDT_Byte,
                        options=['TILED=YES', 'COMPRESS=DEFLATE', 'BIGTIFF=IF_SAFER'])
    if out is None:
        raise RS2Error('Falha ao criar raster temporário de classes.')
    try:
        gt = geotransform if geotransform is not None else ds.GetGeoTransform(can_return_null=True)
        if gt is not None:
            out.SetGeoTransform(gt)
        projection = ds.GetProjectionRef()
        if projection:
            out.SetProjection(projection)
        target = out.GetRasterBand(1)
        target.SetNoDataValue(0)
        nodata = band.GetNoDataValue()
        for y in range(0, height, 128):
            n = min(128, height-y)
            data = band.ReadAsArray(0, y, width, n)
            if data is None:
                raise RS2Error('Falha ao classificar valores contínuos do TIFF.')
            target.WriteArray(classify_array(data, edges, nodata), 0, y)
            notify(.17 + .16 * (y+n)/height)
        target.FlushCache()
        out.FlushCache()
    finally:
        target = None
        out = None
    return class_intervals(edges)
