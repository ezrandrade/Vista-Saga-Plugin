"""Operações GDAL puras (sem Qt/QGIS), usadas pela interface do GeoSAGA.

A versão visual oferece avaliação por classes discretas. Entradas são caminhos
locais para arquivos raster, não objetos QgsRasterLayer (segurança de threads).
"""
import csv
import math
import os
from collections import Counter

import numpy as np
from osgeo import gdal, osr

from .core import NODATA_OUT, evaluate_block, parse_config, valid_mask, pixel_area_ha
from .evaluation_reports import add_raster_combinations, create_reports

TILE = 512
MAX_CLASSES = 300


def file_source(source):
    """Suporta arquivos locais simples; subdatasets devem ser exportados antes."""
    path = source.split('|', 1)[0]
    if not os.path.isfile(path):
        raise ValueError('Esta versão requer um raster armazenado em arquivo local. '
                         'Exporte a camada para GeoTIFF e tente novamente.')
    return os.path.abspath(path)


def open_raster(path):
    ds = gdal.Open(path, gdal.GA_ReadOnly)
    if ds is None or ds.RasterCount < 1:
        raise ValueError(f'Não foi possível abrir o raster: {path}')
    if ds.GetRasterBand(1).DataType in (gdal.GDT_CFloat32, gdal.GDT_CFloat64):
        raise ValueError('Rasters complexos não são suportados.')
    return ds


def iter_windows(ds):
    for y in range(0, ds.RasterYSize, TILE):
        h = min(TILE, ds.RasterYSize - y)
        for x in range(0, ds.RasterXSize, TILE):
            yield x, y, min(TILE, ds.RasterXSize - x), h


def same_grid(datasets):
    if not datasets:
        raise ValueError('É necessário selecionar pelo menos um raster.')
    ref = datasets[0]
    if not ref.GetProjection():
        raise ValueError('Raster sem sistema de referência. Defina o SRC antes da avaliação.')
    transform = ref.GetGeoTransform()
    for ds in datasets[1:]:
        if (ref.RasterXSize, ref.RasterYSize) != (ds.RasterXSize, ds.RasterYSize):
            raise ValueError('Os mapas apresentam dimensões diferentes. Alinhe as grades antes da avaliação.')
        if not np.allclose(transform, ds.GetGeoTransform(), rtol=0, atol=1e-8):
            raise ValueError('Resolução, extensão ou alinhamento diferentes. Alinhe os mapas antes da avaliação.')
        if ref.GetProjection() != ds.GetProjection():
            a, b = osr.SpatialReference(), osr.SpatialReference()
            if (a.ImportFromWkt(ref.GetProjection()) != 0 or
                b.ImportFromWkt(ds.GetProjection()) != 0 or not a.IsSame(b)):
                raise ValueError('Os rasters apresentam SRC diferentes. Reprojete antes da avaliação.')
    return True


def class_code(n):
    number = float(n)
    if not math.isfinite(number):
        raise ValueError('Classe não finita.')
    return str(int(number)) if number.is_integer() else format(number, '.15g')


def scan_classes(path, progress=None, cancelled=None, max_classes=MAX_CLASSES):
    """Identifica classes em todos os pixels válidos; interrompe rasters contínuos."""
    ds = open_raster(path)
    band = ds.GetRasterBand(1)
    nd = band.GetNoDataValue()
    counts = Counter()
    for x, y, w, h in iter_windows(ds):
        if cancelled and cancelled():
            raise InterruptedError('Leitura das classes cancelada.')
        arr = band.ReadAsArray(x, y, w, h)
        if arr is None:
            raise ValueError('Falha na leitura do raster.')
        vals, n = np.unique(arr[valid_mask(arr, nd)], return_counts=True)
        for v, nn in zip(vals, n):
            counts[class_code(v)] += int(nn)
        if len(counts) > max_classes:
            raise ValueError(f'O raster possui mais de {max_classes} valores distintos. '
                             'Reclassifique-o em categorias temáticas antes de utilizá-lo.')
        if progress:
            progress(min(100, int(100*(y+h)/ds.RasterYSize)))
    if not counts:
        raise ValueError('O raster não contém pixels válidos.')
    return sorted(counts.items(), key=lambda p: float(p[0]))


def run_evaluation(paths, config, output, report='', title='', author='',
                   progress=None, cancelled=None, report_txt=''):
    """Processa avaliação e opcionalmente emite relatório CSV de rastreabilidade.

    Todos os parâmetros são tipos Python simples; seguro invocar em QgsTask.run.
    """
    if not output.lower().endswith(('.tif', '.tiff')):
        raise ValueError('O resultado deve ser salvo em arquivo GeoTIFF (.tif).')
    if not paths:
        raise ValueError('Adicione mapas para a avaliação.')
    for path in paths:
        if os.path.realpath(output) == os.path.realpath(path):
            raise ValueError('O arquivo de saída não pode substituir nenhum mapa de entrada.')
    if (report and os.path.realpath(report) == os.path.realpath(output)) or (report_txt and os.path.realpath(report_txt) == os.path.realpath(output)):
        raise ValueError('O relatório não pode substituir o raster de saída.')
    rules = parse_config(config, len(paths))
    datasets = [open_raster(p) for p in paths]
    same_grid(datasets)
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    driver = gdal.GetDriverByName('GTiff')
    if driver is None:
        raise ValueError('Driver GDAL GeoTIFF indisponível.')
    ref = datasets[0]
    ref_transform = ref.GetGeoTransform()
    ref_projection = ref.GetProjection()
    dst = driver.Create(output, ref.RasterXSize, ref.RasterYSize, 1, gdal.GDT_Float32,
                        options=['TILED=YES', 'COMPRESS=DEFLATE', 'PREDICTOR=3', 'BIGTIFF=IF_SAFER'])
    if dst is None:
        raise ValueError('Não foi possível criar o GeoTIFF de saída.')
    completed = False
    total_valid, total_pixels, score_sum = 0, 0, 0.0
    minimum, maximum = None, None
    combinations = Counter()
    collect_report = bool(report or report_txt)
    try:
        dst.SetGeoTransform(ref.GetGeoTransform())
        dst.SetProjection(ref.GetProjection())
        band = dst.GetRasterBand(1)
        band.SetNoDataValue(NODATA_OUT)
        if title:
            dst.SetMetadataItem('TITLE', title)
        if author:
            dst.SetMetadataItem('AUTHOR', author)
        dst.SetMetadataItem('VISTASAGA_PLUGIN_VERSION', '0.3.4')
        dst.SetMetadataItem('GEOSAGA_VERSION', '0.3.0')
        nodatas = [ds.GetRasterBand(1).GetNoDataValue() for ds in datasets]
        for x, y, w, h in iter_windows(ref):
            if cancelled and cancelled():
                raise InterruptedError('Avaliação cancelada.')
            arrays = [ds.GetRasterBand(1).ReadAsArray(x, y, w, h) for ds in datasets]
            if any(a is None for a in arrays):
                raise ValueError('Falha na leitura de um dos mapas de entrada.')
            out = evaluate_block(arrays, nodatas, rules)
            band.WriteArray(out, x, y)
            valid = np.isfinite(out) & (out != NODATA_OUT)
            n_valid = int(np.count_nonzero(valid))
            if n_valid:
                vals = out[valid]
                local_min, local_max = float(vals.min()), float(vals.max())
                minimum = local_min if minimum is None else min(minimum, local_min)
                maximum = local_max if maximum is None else max(maximum, local_max)
                score_sum += float(vals.sum(dtype=np.float64))
            if collect_report and n_valid:
                add_raster_combinations(combinations, arrays, valid)
            total_valid += n_valid
            total_pixels += w*h
            if progress:
                progress(min(100., 100. * (y + h) / ref.RasterYSize))
        band.FlushCache()
        dst.FlushCache()
        completed = True
    finally:
        dst = None
        datasets.clear()
        if not completed and os.path.isfile(output):
            os.remove(output)
    summary = {'pixels_validos': total_valid, 'pixels_sem_avaliacao': total_pixels-total_valid,
               'minimo': minimum, 'maximo': maximum,
               'media': (score_sum / total_valid) if total_valid else None}
    if collect_report:
        ref_crs = osr.SpatialReference()
        ref_crs.ImportFromWkt(ref_projection)
        # Área medida na unidade linear real do SRC, nunca em graus².
        area_ha = pixel_area_ha(ref_transform, bool(ref_crs.IsProjected()),
                                ref_crs.GetLinearUnits() if ref_crs.IsProjected() else 1.0)
        criteria = []
        for i, (rule, meta) in enumerate(zip(config['camadas'], config.get('nomes', paths))):
            criteria.append({'name': meta, 'source': paths[i], 'weight': float(rule['peso']),
                             'notes': {str(k): float(v) for k,v in rule['notas'].items()},
                             'excluded': set(str(x) for x in rule.get('bloqueadas', [])),
                             'labels': (config.get('legendas', [{}]*len(paths))[i] or {})})
        create_reports(report_txt, report, combinations={key: (count, None) for key, count in combinations.items()},
                       criteria=criteria, total_units=total_pixels, valid_units=total_valid,
                       area_per_unit_ha=area_ha, title=title, author=author,
                       crs=ref_projection, unit_label='Pixels',
                       invalid_area_ha=(total_pixels-total_valid)*area_ha if area_ha is not None else None)
    return summary
