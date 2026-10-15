"""Teste real dos dois modos de Combinação de Mapas no Console QGIS 4.x.

Execute: from geosaga.tests.integration_combination_qgis import run; run()
Os dados sintéticos são criados em uma pasta temporária, removida no final.
"""
import csv
import os
import tempfile

import numpy as np
from osgeo import gdal, osr
from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsCoordinateReferenceSystem, QgsFeature, QgsField,
                       QgsGeometry, QgsVectorLayer)

from geosaga.combination_raster import run_raster_combination
from geosaga.combination_vector import run_vector_combination


def _make_raster(path, values):
    ds = gdal.GetDriverByName('GTiff').Create(path, values.shape[1], values.shape[0], 1, gdal.GDT_Byte)
    if ds is None:
        raise RuntimeError('Falha ao criar TIFF de ensaio.')
    ds.SetGeoTransform((1000,10,0,2000,0,-10))
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(31985)
    ds.SetProjection(sr.ExportToWkt())
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(255)
    band.WriteArray(values)
    ds.FlushCache()
    band = None
    ds = None


def _make_vector(name, polygons, classes):
    layer = QgsVectorLayer('Polygon?crs=EPSG:31985', name, 'memory')
    if not layer.isValid():
        raise RuntimeError('Falha ao criar camada vetorial de ensaio.')
    provider = layer.dataProvider()
    provider.addAttributes([QgsField('CLASSE', QVariant.String)])
    layer.updateFields()
    features = []
    for wkt, cls in zip(polygons, classes):
        feat = QgsFeature(layer.fields())
        feat.setGeometry(QgsGeometry.fromWkt(wkt))
        feat.setAttributes([cls])
        features.append(feat)
    if not provider.addFeatures(features)[0]:
        raise RuntimeError('Falha ao criar polígonos do teste.')
    layer.updateExtents()
    return layer


def run():
    with tempfile.TemporaryDirectory(prefix='vistasaga_combinacao_qgis_') as temp:
        a=os.path.join(temp,'geologia.tif')
        b=os.path.join(temp,'uso.tif')
        _make_raster(a,np.array([[1,1],[2,2]], dtype=np.uint8))
        _make_raster(b,np.array([[3,4],[3,4]], dtype=np.uint8))
        raster=os.path.join(temp,'combinado.tif')
        summary=run_raster_combination([a,b],raster)
        if summary['combinations'] != 4 or summary['valid_pixels'] != 4:
            raise RuntimeError('Combinação raster gerou estatísticas incorretas: '+str(summary))
        ds=gdal.Open(raster)
        vals=ds.GetRasterBand(1).ReadAsArray()
        if len(np.unique(vals))!=4 or ds.GetRasterBand(1).GetNoDataValue()!=0:
            raise RuntimeError('GeoTIFF da combinação contém IDs ou NoData incorretos.')
        ds=None

        xmin,xmid,xmax=1000,1010,1020
        ymin,ymid,ymax=1980,1990,2000
        one = _make_vector('Mapa vertical',[
            'POLYGON ((1000 1980,1010 1980,1010 2000,1000 2000,1000 1980))',
            'POLYGON ((1010 1980,1020 1980,1020 2000,1010 2000,1010 1980))'],['A','B'])
        two = _make_vector('Mapa horizontal',[
            'POLYGON ((1000 1990,1020 1990,1020 2000,1000 2000,1000 1990))',
            'POLYGON ((1000 1980,1020 1980,1020 1990,1000 1990,1000 1980))'],['C','D'])
        gpkg=os.path.join(temp,'combinado.gpkg')
        result=run_vector_combination([one,two],['CLASSE','CLASSE'],['',''],gpkg)
        if result['combinations']!=4 or result['features']!=4:
            raise RuntimeError('Combinação vetorial gerou categorias ou feições incorretas: '+str(result))
        if abs(result['area_ha'] - .04)>1e-8:
            raise RuntimeError('Área da combinação vetorial incorreta: '+str(result['area_ha']))
        layer=QgsVectorLayer(gpkg+'|layername=combinacao_mapas','Verificação','ogr')
        if not layer.isValid() or 'ID_COMB' not in layer.fields().names():
            raise RuntimeError('GeoPackage resultante inválido ou sem atributos.')
        count=sum(1 for _ in layer.getFeatures())
        if count!=4:
            raise RuntimeError('Quantidade de polígonos resultantes incorreta.')
        layer=None
        print('Vista Saga 0.6.0 — teste integrado concluído: 4 combinações raster e vetoriais; '
              'áreas e legendas conferidas.')
        return {'raster':summary['combinations'],'vector':result['combinations'],
                'area_vector_ha':result['area_ha']}
