"""Executar no Console Python do QGIS 4.x:
from geosaga.tests.integration_evaluation_reports_qgis import run
run()
Testa o GDAL real + PyQGIS, sem modificar as camadas do projeto.
"""
import csv
import os
import tempfile
from pathlib import Path

import numpy as np
from osgeo import gdal, osr
from qgis.core import (QgsFeature, QgsField, QgsGeometry, QgsPointXY,
                       QgsVectorLayer)
from qgis.PyQt.QtCore import QVariant

from ..raster_engine import run_evaluation
from ..vector_evaluation_writer import evaluate_vector_layer


def _raster(path, data, wkt):
    driver = gdal.GetDriverByName('GTiff')
    ds = driver.Create(str(path), data.shape[1], data.shape[0], 1, gdal.GDT_Byte)
    if not ds:
        raise RuntimeError('GDAL não criou o raster de teste.')
    ds.SetGeoTransform((500000, 10, 0, 9000000, 0, -10))
    ds.SetProjection(wkt)
    ds.GetRasterBand(1).WriteArray(data)
    ds.GetRasterBand(1).SetNoDataValue(0)
    ds.FlushCache()
    ds = None


def run():
    with tempfile.TemporaryDirectory(prefix='vistasaga_relatorios_qgis_') as tmp:
        base = Path(tmp)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(31985)
        _raster(base/'uso.tif', np.array([[1, 1], [2, 2]], dtype=np.uint8), srs.ExportToWkt())
        _raster(base/'solo.tif', np.array([[3, 3], [3, 0]], dtype=np.uint8), srs.ExportToWkt())
        out = base/'carta.tif'
        result = run_evaluation([str(base/'uso.tif'), str(base/'solo.tif')],
            {'escala': 10, 'camadas': [
                {'peso': 50, 'notas': {'1': 2, '2': 6}},
                {'peso': 50, 'notas': {'3': 10}},
            ], 'nomes': ['Uso', 'Solo'],
            'legendas': [{'1': 'Vegetação', '2': 'Pastagem'}, {'3': 'Argissolo'}]},
            str(out), report=str(base/'carta_relatorio.csv'),
            report_txt=str(base/'carta_relatorio.txt'))
        assert result['pixels_validos'] == 3, result
        assert (base/'carta_relatorio.txt').is_file()
        assert (base/'carta_relatorio.csv').is_file()
        assert '0.03' in (base/'carta_relatorio.txt').read_text(encoding='utf-8-sig')

        layer = QgsVectorLayer('Polygon?crs=EPSG:31985', 'Teste vetorial', 'memory')
        assert layer.isValid(), 'Não foi possível criar a camada de memória.'
        p = layer.dataProvider()
        assert p.addAttributes([QgsField('USO', QVariant.String), QgsField('SOLO', QVariant.String)])
        layer.updateFields()
        for i, (xmax, uso) in enumerate(((10, '1'), (20, '2'))):
            feat = QgsFeature(layer.fields())
            x0 = 0 if i == 0 else 10
            ring = [QgsPointXY(x0, 0), QgsPointXY(xmax, 0),
                    QgsPointXY(xmax, 10), QgsPointXY(x0, 10), QgsPointXY(x0, 0)]
            feat.setGeometry(QgsGeometry.fromPolygonXY([ring]))
            feat.setAttributes([uso, '3'])
            assert p.addFeatures([feat])[0]
        layer.updateExtents()
        vector_output = base/'vetor.gpkg'
        result_vector = evaluate_vector_layer(layer, [
            {'field': 'USO', 'weight': 50, 'categories': {'1', '2'},
             'notes': {'1': 2, '2': 6}, 'excluded': set()},
            {'field': 'SOLO', 'weight': 50, 'categories': {'3'},
             'notes': {'3': 10}, 'excluded': set()},
        ], 10, str(vector_output))
        assert result_vector['total'] == 2, result_vector
        assert abs(result_vector['area_total_ha'] - .02) < 1e-9
        assert (base/'vetor_relatorio.txt').is_file()
        assert (base/'vetor_relatorio.csv').is_file()
        dst = QgsVectorLayer(str(vector_output), 'Teste de saída', 'ogr')
        assert dst.isValid(), 'GeoPackage criado não abriu no QGIS.'
        assert {'AVALIACAO','AREA_M2','AREA_HA','PCT_AREA'}.issubset(dst.fields().names())
        features = list(dst.getFeatures())
        assert len(features) == 2
        assert abs(sum(float(f['AREA_HA']) for f in features) - .02) < 1e-9
        assert abs(sum(float(f['PCT_AREA']) for f in features) - 100) < 1e-9
        dst = None
    print('Vista Saga 0.3.12: raster + TXT/CSV e vetor + áreas + TXT/CSV: testes QGIS concluídos.')
    return True
