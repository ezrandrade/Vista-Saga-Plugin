"""Executar no Console Python do QGIS 4.x:

    from geosaga.tests.integration_tiff_vector_qgis import run
    run()

Testa em arquivos sintéticos temporários, sem alterar dados do usuário.
"""
from pathlib import Path
import tempfile
import numpy as np


def run():
    from osgeo import gdal, ogr, osr
    from qgis.core import QgsVectorLayer
    from geosaga.tiff_vector import convert_tif_to_vector

    with tempfile.TemporaryDirectory(prefix='vistasaga_tiff_vector_') as td:
        root = Path(td)
        tif = root / 'classes.tif'
        data = np.array([[0, 1, 1, 2], [0, 1, 2, 2], [1, 1, 0, 2]], dtype=np.uint8)
        driver = gdal.GetDriverByName('GTiff')
        ds = driver.Create(str(tif), 4, 3, 1, gdal.GDT_Byte)
        ds.SetGeoTransform((100, 10, 0, 230, 0, -10))
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(31985)
        ds.SetProjection(srs.ExportToWkt())
        band = ds.GetRasterBand(1)
        band.WriteArray(data)
        band.SetCategoryNames(['FUNDO', 'Floresta', 'Pastagem'])
        colors = gdal.ColorTable()
        for i, rgb in enumerate(((255,255,255), (5,128,200), (30,200,20))):
            colors.SetColorEntry(i, (*rgb, 255))
        band.SetRasterColorTable(colors)
        ds = None

        for ext in ('.gpkg', '.shp', '.geojson', '.fgb'):
            out = root / ('classe' + ext)
            convert_tif_to_vector(tif, out, ignore_background=True)
            ds = ogr.Open(str(out))
            if ds is None:
                raise RuntimeError(f'OGR não abriu {out.name}')
            layer = ds.GetLayer(0)
            records = sorted((f.GetField('CODIGO'), f.GetField('CLASSE'), f.GetField('COR_HEX')) for f in layer)
            if records != [(1, 'Floresta', '#0580C8'), (2, 'Pastagem', '#1EC814')]:
                raise RuntimeError(f'Classes erradas {ext}: {records}')
            if layer.GetSpatialRef() is None:
                raise RuntimeError(f'SRC ausente em {ext}')
            ds = None
            if not QgsVectorLayer(str(out), out.stem, 'ogr').isValid():
                raise RuntimeError(f'O QGIS não abriu {out.name}')
        # teste da seleção 'não excluir classe 0'
        bg = root/'fundo.gpkg'
        convert_tif_to_vector(tif, bg, ignore_background=False)
        ds = ogr.Open(str(bg))
        if ds.GetLayer(0).GetFeatureCount() != 4:
            raise RuntimeError('Classe 0 não foi vetorizada quando solicitada.')
        ds = None

        # RGB classificado, preservando a grade e mapeando cada cor HEX a um código.
        rgb = root/'rgb.tif'
        ds = driver.Create(str(rgb), 4, 3, 3, gdal.GDT_Byte)
        ds.SetGeoTransform((100, 10, 0, 230, 0, -10))
        ds.SetProjection(srs.ExportToWkt())
        palette = ((255,255,255), (5,128,200), (30,200,20))
        for c in range(3):
            plane = np.take([color[c] for color in palette], data)
            ds.GetRasterBand(c+1).WriteArray(plane.astype(np.uint8))
        ds = None
        rgb_out = root/'rgb.gpkg'
        convert_tif_to_vector(rgb, rgb_out)
        ds = ogr.Open(str(rgb_out))
        values = sorted((f.GetField('CLASSE'), f.GetField('COR_HEX')) for f in ds.GetLayer(0))
        if len(values) != 2 or set(color for _, color in values) != {'#0580C8', '#1EC814'}:
            raise RuntimeError(f'Cores RGB incorretas: {values}')
        ds = None
        print('Vista Saga 0.3.6: GeoTIFF categórico e RGB -> 4 vetores, SRC, FUNDO e HEX: OK')
    return True
