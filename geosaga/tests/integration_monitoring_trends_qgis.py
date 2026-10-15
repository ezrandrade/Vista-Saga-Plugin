"""Console QGIS 4.x: from geosaga.tests.integration_monitoring_trends_qgis import run; run()"""
from pathlib import Path
import csv
import tempfile

import numpy as np
from osgeo import gdal, osr

from geosaga.monitoring_engine import run_monitoring


def run():
    """Testa tendência da proporção da classe 1 em 5 datas sintéticas."""
    with tempfile.TemporaryDirectory(prefix='vistasaga_mk_') as temp:
        base = Path(temp)
        years = [1986, 1991, 1996, 2001, 2016]
        src = osr.SpatialReference()
        src.ImportFromEPSG(31985)
        paths = []
        for index, year in enumerate(years, 1):
            path = base / f'mapa_{year}.tif'
            ds = gdal.GetDriverByName('GTiff').Create(str(path), 10, 10, 1, gdal.GDT_Byte)
            if ds is None:
                raise RuntimeError('GDAL não conseguiu criar raster sintético.')
            ds.SetGeoTransform((500000, 10, 0, 9000000, 0, -10))
            ds.SetProjection(src.ExportToWkt())
            data = np.full((10, 10), 2, dtype=np.uint8)
            data.flat[:index * 10] = 1
            ds.GetRasterBand(1).WriteArray(data)
            ds.GetRasterBand(1).SetNoDataValue(0)
            ds.FlushCache()
            ds = None
            paths.append(path)
        summary = run_monitoring(
            paths[0], paths[-1], base / 'saida.tif',
            before_label='1986', after_label='2016',
            temporal_files=list(zip(years[1:-1], paths[1:-1])))
        if summary['temporal']['status'] != 'calculado':
            raise RuntimeError(f"MK não calculado: {summary['temporal']}")
        with open(summary['tendencias'], encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream, delimiter=';'))
        if len(rows) != 2 or not all(float(r['MK_P_BILATERAL']) < .05 for r in rows):
            raise RuntimeError('O resultado do teste de tendências sintéticas divergiu.')
        print('Vista Saga 0.4.1 — teste QGIS/GDAL da Monitoria e Mann–Kendall: OK')
        return True
