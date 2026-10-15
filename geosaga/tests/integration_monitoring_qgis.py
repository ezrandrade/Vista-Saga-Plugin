"""Teste integrado: executar dentro do Console Python do QGIS 4.x.

from geosaga.tests.integration_monitoring_qgis import run
run()
"""
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from osgeo import gdal, osr

from ..monitoring_engine import run_monitoring


def _raster(path, data):
    driver = gdal.GetDriverByName('GTiff')
    ds = driver.Create(str(path), data.shape[1], data.shape[0], 1, gdal.GDT_Int16)
    if ds is None:
        raise RuntimeError('Não foi possível criar o teste GeoTIFF.')
    ds.SetGeoTransform((500000, 10, 0, 9000000, 0, -10))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(31985)
    ds.SetProjection(srs.ExportToWkt())
    ds.GetRasterBand(1).SetNoDataValue(-9999)
    ds.GetRasterBand(1).WriteArray(data)
    ds.FlushCache()
    ds = None


def run():
    with TemporaryDirectory(prefix='vistasaga_monitoria_test_') as d:
        d = Path(d)
        before = np.array([[1, 1, 2], [-9999, 0, 3]], dtype=np.int16)
        after = np.array([[2, 1, 2], [1, 0, 2]], dtype=np.int16)
        p, q, output = d / 'a.tif', d / 'b.tif', d / 'monitoria.tif'
        _raster(p, before)
        _raster(q, after)
        report = run_monitoring(str(p), str(q), str(output),
                                before_label='1985', after_label='2024')
        if not (report['validos'] == 5 and report['mudancas'] == 2):
            raise RuntimeError(f'Contagem de mudanças incorreta: {report}')
        if not abs(report['area_valida_ha'] - .05) < 1e-8:
            raise RuntimeError(f'Área incorreta: {report}')
        ds = gdal.Open(str(output))
        pixels = ds.GetRasterBand(1).ReadAsArray()
        ids = report['ids']
        expected = [[ids[(1., 2.)], ids[(1., 1.)], ids[(2., 2.)]],
                    [-9999, ids[(0., 0.)], ids[(3., 2.)]]]
        if not np.array_equal(pixels, expected):
            raise RuntimeError(f'IDs de transição incorretos: {pixels}')
        ds = None
        with open(report['matriz'], encoding='utf-8-sig', newline='') as f:
            matrix = list(csv.reader(f, delimiter=';'))
        if int(matrix[-1][-1]) != 5:
            raise RuntimeError(f'Total da matriz incorreto: {matrix}')
        if not all(Path(report[key]).is_file()
                   for key in ('mapa', 'transicoes', 'matriz', 'resumo')):
            raise RuntimeError('Arquivos esperados não encontrados.')
        print('OK — Monitoria Ambiental 0.4.0: GeoTIFF e matriz conferidos; '
              '5 pixels válidos, 2 mudanças, 3 permanências; áreas corretas.')
        return True
