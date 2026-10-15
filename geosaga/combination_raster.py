"""Combina dois ou mais GeoTIFFs categóricos por sobreposição de códigos.

Usa GDAL do QGIS 4; dois passes por janelas, sem criar combinações inexistentes.
Os arquivos de origem nunca são modificados.
"""
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from collections import Counter

import numpy as np

from .combination_core import (MAX_COMBINATIONS, normalized_code,
                               combination_index, composition_rows, write_combination_reports)


def _cancelled(cancelled):
    if cancelled and cancelled():
        raise InterruptedError('Combinação de mapas cancelada.')


def _same_grid(reference, dataset, osr):
    if reference.RasterXSize != dataset.RasterXSize or reference.RasterYSize != dataset.RasterYSize:
        raise ValueError('Dimensões diferentes entre mapas. Alinhe os rasters previamente no QGIS.')
    a, b = reference.GetGeoTransform(), dataset.GetGeoTransform()
    scale = max(abs(a[1]), abs(a[2]), abs(a[4]), abs(a[5]), 1e-15)
    if any(abs(x-y) > scale * 1e-5 for x,y in zip(a,b)):
        raise ValueError('Grades ou resoluções diferentes. Alinhe os rasters previamente no QGIS.')
    first, second = osr.SpatialReference(), osr.SpatialReference()
    if not reference.GetProjection() or not dataset.GetProjection():
        raise ValueError('Todos os GeoTIFFs precisam possuir SRC definido.')
    if first.ImportFromWkt(reference.GetProjection()) != 0 or second.ImportFromWkt(dataset.GetProjection()) != 0 or not first.IsSame(second):
        raise ValueError('SRCs diferentes; reprojete os mapas para um SRC comum no QGIS.')


def _valid_integer_pixels(values, nodata):
    valid = np.isfinite(values)
    if nodata is not None and math.isfinite(float(nodata)):
        valid &= (values != nodata)
    if np.any(valid & (values != np.trunc(values))):
        raise ValueError('Raster com valores decimais contínuos. Reclassifique em códigos de classes inteiras.')
    if valid.any() and (np.max(np.abs(values[valid])) > 2**53):
        raise ValueError('Classes com códigos superiores a 2^53 não são suportadas.')
    return valid


def _get_names(path, band, codes):
    """Prioriza sidecar RS2 e CategoryNames; código sem legenda recebe rótulo neutro."""
    names = band.GetCategoryNames() or []
    mapped = {str(i): str(name) for i, name in enumerate(names) if name}
    sidecar = Path(str(path) + '.rs2.json')
    if sidecar.is_file():
        try:
            with sidecar.open(encoding='utf-8') as fp:
                info = json.load(fp)
            if info.get('format') == 'Vista SAGA RS2':
                mapped.update({str(i): str(label) for i,label in enumerate(info.get('labels', [])) if label})
        except (OSError, ValueError, TypeError):
            pass
    return {str(code): mapped.get(str(code), f'Classe {code}') for code in codes}


def _pixel_area(ds, osr):
    spatial = osr.SpatialReference()
    spatial.ImportFromWkt(ds.GetProjection())
    if not spatial.IsProjected():
        return None, 'Área indisponível em SRC geográfico; reprojete para sistema métrico.'
    factor = spatial.GetLinearUnits()
    if not factor or factor <= 0:
        return None, 'Unidades lineares do SRC indefinidas.'
    t = ds.GetGeoTransform()
    return abs(t[1]*t[5] - t[2]*t[4]) * factor ** 2, 'Determinante da grade × conversão da unidade linear para m².'


def run_raster_combination(sources, destination, *, progress=None, cancelled=None):
    """Retorna resumo, com arquivos .tif, _combinacoes.csv, _resumo.txt.

    Uma classe saída por combinação observada; valor 0 é NoData de SAÍDA.
    O código 0 em entradas continua válido quando não for explicitamente NoData.
    """
    from osgeo import gdal, osr
    sources = [os.path.abspath(str(p)) for p in sources]
    if len(sources) < 2 or len(set(map(os.path.normcase, sources))) != len(sources):
        raise ValueError('Selecione dois ou mais GeoTIFFs distintos.')
    if any(not os.path.isfile(p) for p in sources):
        raise ValueError('Um dos mapas não existe como arquivo local.')
    dest = os.path.abspath(str(destination))
    if not dest.lower().endswith(('.tif', '.tiff')):
        raise ValueError('A saída deve ser um GeoTIFF (.tif ou .tiff).')
    root = os.path.splitext(dest)[0]
    final_files = [dest, root+'_combinacoes.csv', root+'_resumo.txt']
    if os.path.normcase(os.path.realpath(dest)) in {os.path.normcase(os.path.realpath(p)) for p in sources}:
        raise ValueError('A saída não pode substituir um raster de entrada.')
    if not os.path.isdir(os.path.dirname(dest)):
        raise ValueError('A pasta de saída não existe.')
    datasets = []
    staging = tempfile.mkdtemp(prefix='.vistasaga_comb_raster_', dir=os.path.dirname(dest))
    try:
        for path in sources:
            ds = gdal.Open(path, gdal.GA_ReadOnly)
            if ds is None or ds.RasterCount != 1:
                raise ValueError(f'Raster inválido ou com mais de uma banda: {path}')
            if not ds.GetProjection():
                raise ValueError(f'Raster sem SRC: {path}')
            if datasets:
                _same_grid(datasets[0], ds, osr)
            datasets.append(ds)
        first = datasets[0]
        bands = [ds.GetRasterBand(1) for ds in datasets]
        nodata = [b.GetNoDataValue() for b in bands]
        counts = Counter()
        source_codes = [set() for _ in sources]
        width, height = first.RasterXSize, first.RasterYSize
        total_valid = 0
        stripe = 128
        # Contagem por tuplas, usando poucos MB de memória de cada vez.
        for y in range(0, height, stripe):
            _cancelled(cancelled)
            h = min(stripe, height-y)
            arrays = [b.ReadAsArray(0,y,width,h) for b in bands]
            if any(a is None for a in arrays):
                raise OSError('Falha na leitura de uma banda categórica.')
            valid = np.ones((h,width), bool)
            for a, nd in zip(arrays, nodata):
                valid &= _valid_integer_pixels(a, nd)
            n = int(valid.sum())
            total_valid += n
            if n:
                unique, frequencies = np.unique(np.stack([a[valid].astype(np.int64)
                                                  for a in arrays], axis=1), axis=0, return_counts=True)
                for key, amount in zip(unique, frequencies):
                    keys = tuple(str(int(k)) for k in key)
                    counts[keys] += int(amount)
                    for ix, code in enumerate(keys):
                        source_codes[ix].add(code)
                if len(counts) > MAX_COMBINATIONS:
                    raise ValueError('Mais de 100 mil combinações: reclassifique alguns critérios.')
            if progress:progress(int(45*(y+h)/height))
        ids = combination_index(counts)
        area_per_pixel, area_method = _pixel_area(first, osr)
        names = [_get_names(path, band, observed) for path, band, observed in
                 zip(sources, bands, source_codes)]
        rows = composition_rows(counts, names, pixel_area_m2=area_per_pixel)
        stage_tif = os.path.join(staging, os.path.basename(dest))
        driver = gdal.GetDriverByName('GTiff')
        target = driver.Create(stage_tif, width, height, 1, gdal.GDT_Int32,
                               options=['TILED=YES','COMPRESS=LZW','BIGTIFF=IF_SAFER'])
        if target is None:
            raise OSError('GDAL não conseguiu criar o GeoTIFF de saída.')
        target.SetGeoTransform(first.GetGeoTransform())
        target.SetProjection(first.GetProjection())
        target.SetMetadataItem('VISTA_SAGA_MODULE', 'COMBINACAO_MAPAS')
        target.SetMetadataItem('VISTA_SAGA_CSV', os.path.basename(final_files[1]))
        outband = target.GetRasterBand(1)
        outband.SetNoDataValue(0)
        for y in range(0,height,stripe):
            _cancelled(cancelled)
            h = min(stripe,height-y)
            arrays = [b.ReadAsArray(0,y,width,h) for b in bands]
            valid = np.ones((h,width), bool)
            for a,nd in zip(arrays,nodata):
                valid &= _valid_integer_pixels(a,nd)
            result = np.zeros((h,width), dtype=np.int32)
            if valid.any():
                values = np.stack([a[valid].astype(np.int64) for a in arrays], axis=1)
                groups, inverses = np.unique(values,axis=0,return_inverse=True)
                lookup = np.array([ids[tuple(str(int(c)) for c in key)] for key in groups],dtype=np.int32)
                result[valid] = lookup[inverses]
            if outband.WriteArray(result,0,y) != 0:
                raise OSError('GDAL não gravou o bloco da combinação.')
            if progress:progress(45+int(45*(y+h)/height))
        outband.FlushCache()
        target.FlushCache()
        target = None
        outband = None
        staged_csv = os.path.join(staging, os.path.basename(final_files[1]))
        staged_txt = os.path.join(staging, os.path.basename(final_files[2]))
        write_combination_reports(staged_csv, staged_txt, rows, sources, mode='Raster',
                                  crs=first.GetProjection(), area_method=area_method)
        # As saídas são substituídas apenas quando todos os arquivos passaram pela validação.
        from .vector_evaluation_writer import _publish_set
        _cancelled(cancelled)
        _publish_set([(stage_tif, final_files[0]), (staged_csv, final_files[1]),
                      (staged_txt, final_files[2])], os.path.dirname(dest))
        if progress:progress(100)
        return {'output':dest,'csv':final_files[1],'txt':final_files[2],
                'combinations':len(rows),'valid_pixels':total_valid,
                'area_ha':None if area_per_pixel is None else area_per_pixel*total_valid/10000,
                'rows':rows}
    finally:
        datasets.clear()
        shutil.rmtree(staging,ignore_errors=True)
