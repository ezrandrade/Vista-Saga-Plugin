"""Teste de GeoTIFF Float32 de avaliação -> vetor no Console do QGIS 4.x.

    from geosaga.tests.integration_continuous_vector_qgis import run
    run()

Usa somente arquivos temporários sintéticos; não modifica o projeto do usuário.
"""
from pathlib import Path
import tempfile
import numpy as np


def run():
    from osgeo import gdal, ogr, osr
    from qgis.core import QgsVectorLayer
    from geosaga.tiff_vector import convert_tif_to_vector

    data = np.array([[-9999., 0., 1., 1.],
                     [0.2, 1.7, 2.1, 4.5],
                     [np.nan, 3.2, 4.9, 5.]], dtype=np.float32)
    with tempfile.TemporaryDirectory(prefix='vistasaga_continuo_') as folder:
        root = Path(folder)
        tif = root/'avaliacao_float32.tif'
        ds = gdal.GetDriverByName('GTiff').Create(str(tif), 4, 3, 1, gdal.GDT_Float32)
        ds.SetGeoTransform((100., 10., 0., 300., 0., -10.))
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(31985)
        ds.SetProjection(srs.ExportToWkt())
        band = ds.GetRasterBand(1)
        band.WriteArray(data)
        band.SetNoDataValue(-9999.)
        ds = None
        for ext in ('.gpkg', '.shp', '.geojson', '.fgb'):
            target = root/('avaliacao_classes' + ext)
            convert_tif_to_vector(tif, target, continuous_classes=5,
                                  ignore_background=False)
            layer = QgsVectorLayer(str(target), target.stem, 'ogr')
            if not layer.isValid():
                raise RuntimeError(f'Não abriu o vetor {ext} no QGIS')
            ds = ogr.Open(str(target))
            if ds is None:
                raise RuntimeError(f'OGR não abriu o vetor {ext}')
            geom_layer = ds.GetLayer(0)
            names = {f.name for f in layer.fields()}
            required = {'CODIGO', 'CLASSE', 'COR_HEX', 'VALOR_MIN', 'VALOR_MAX'}
            if not required.issubset(names):
                raise RuntimeError(f'Campos ausentes {ext}: {required - names}')
            if geom_layer.GetSpatialRef() is None:
                raise RuntimeError(f'SRC perdido em {ext}')
            codes = set()
            area = 0.
            for feature in geom_layer:
                code = feature.GetField('CODIGO')
                if not (1 <= code <= 5):
                    raise RuntimeError(f'Classe inválida {code} no {ext}')
                if not (feature.GetField('VALOR_MIN') <= feature.GetField('VALOR_MAX')):
                    raise RuntimeError('Intervalo inválido')
                codes.add(code)
                area += feature.GetGeometryRef().GetArea()
            ds = None
            # 12 células, das quais NoData (-9999) e NaN são excluídas.
            if abs(area - 1000.) > 0.01:
                raise RuntimeError(f'Área divergente no {ext}: {area}')
            if codes != {1, 2, 3, 4, 5}:
                raise RuntimeError(f'Nem todas as cinco classes foram recuperadas: {codes}')
        print('Vista Saga 0.3.9: raster Float32 de avaliação -> quatro vetores: OK')
    return True
