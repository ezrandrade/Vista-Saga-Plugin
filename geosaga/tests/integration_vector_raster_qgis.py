"""Teste real de rasterização e leitura GDAL, executar no console QGIS 4.x:

    from geosaga.tests.integration_vector_raster_qgis import run
    run()
"""
from pathlib import Path
import tempfile
import numpy as np


def run():
    from osgeo import ogr, osr, gdal
    from geosaga.vector_raster import convert_vector_to_tif

    with tempfile.TemporaryDirectory(prefix='vistasaga_vetor_tif_') as td:
        root = Path(td)
        gpkg = root / 'classes.gpkg'
        ds = ogr.GetDriverByName('GPKG').CreateDataSource(str(gpkg))
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(31985)
        layer = ds.CreateLayer('temas', srs=srs, geom_type=ogr.wkbPolygon)
        layer.CreateField(ogr.FieldDefn('CODIGO', ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn('CLASSE', ogr.OFTString))
        layer.CreateField(ogr.FieldDefn('COR_HEX', ogr.OFTString))
        for code, name, color, ring_points in (
            (1, 'Caatinga', '#008000', ((100, 200), (120, 200), (120, 220), (100, 220))),
            (2, 'Pastagem', '#FFFF00', ((120, 200), (140, 200), (140, 220), (120, 220))),
        ):
            ring = ogr.Geometry(ogr.wkbLinearRing)
            for x, y in (*ring_points, ring_points[0]):
                ring.AddPoint_2D(x, y)
            polygon = ogr.Geometry(ogr.wkbPolygon)
            polygon.AddGeometry(ring)
            feat = ogr.Feature(layer.GetLayerDefn())
            feat.SetField('CODIGO', code)
            feat.SetField('CLASSE', name)
            feat.SetField('COR_HEX', color)
            feat.SetGeometry(polygon)
            if layer.CreateFeature(feat) != 0:
                raise RuntimeError('Erro ao construir vetor de teste.')
        layer.SyncToDisk()
        ds = None
        for field, codes, names in (
            ('CODIGO', {1, 2}, {'Caatinga', 'Pastagem'}),
            ('CLASSE', {1, 2}, {'Caatinga', 'Pastagem'}),
        ):
            tiff = root / (field + '.tif')
            convert_vector_to_tif(str(gpkg) + '|layername=temas', tiff, field, 10)
            raster = gdal.Open(str(tiff), gdal.GA_ReadOnly)
            if raster is None or raster.RasterXSize != 4 or raster.RasterYSize != 2:
                raise RuntimeError('Grade incorreta.')
            actual = raster.GetRasterBand(1).ReadAsArray()
            if set(np.unique(actual)) != codes:
                raise RuntimeError(f'Valores incorretos em {field}: {actual}')
            labels = set(raster.GetRasterBand(1).GetCategoryNames() or [])
            if not names.issubset(labels):
                raise RuntimeError(f'Legenda perdida em {field}: {labels}')
            if not raster.GetProjectionRef():
                raise RuntimeError('SRC não foi preservado.')
            raster = None
        print('Vista Saga 0.3.8: vetores inteiro/texto -> GeoTIFF, códigos, cores e SRC: OK')
    return True
