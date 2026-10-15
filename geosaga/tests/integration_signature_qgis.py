"""Teste integrado para Console Python no QGIS 4.x:
from geosaga.tests.integration_signature_qgis import run
run()
"""
import csv
import tempfile
from pathlib import Path


def run():
    import numpy as np
    from osgeo import gdal, osr
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsVectorLayer, QgsFeature, QgsField
    from qgis.core import QgsGeometry, QgsPointXY
    from geosaga.signature_engine import run_signature

    with tempfile.TemporaryDirectory(prefix='vistasaga_assinatura_qgis_') as d:
        d = Path(d)
        sr = osr.SpatialReference()
        sr.ImportFromEPSG(31985)
        tif = str(d/'classes.tif')
        ds = gdal.GetDriverByName('GTiff').Create(tif, 4, 2, 1, gdal.GDT_Byte)
        ds.SetProjection(sr.ExportToWkt())
        ds.SetGeoTransform((300000, 10, 0, 9000000, 0, -10))
        band = ds.GetRasterBand(1)
        band.WriteArray(np.array([[1, 1, 2, 2], [1, 2, 2, 0]], dtype='uint8'))
        band.SetNoDataValue(0)
        ds = None
        from qgis.core import QgsRasterLayer
        raster = QgsRasterLayer(tif, 'Classes')
        areas = QgsVectorLayer('Polygon?crs=EPSG:31985', 'Áreas de teste', 'memory')
        p = areas.dataProvider()
        p.addAttributes([QgsField('NOME', QVariant.String)])
        areas.updateFields()
        ft = QgsFeature(areas.fields())
        ft.setGeometry(QgsGeometry.fromPolygonXY([[QgsPointXY(300000, 9000000),
            QgsPointXY(300040, 9000000), QgsPointXY(300040, 8999980),
            QgsPointXY(300000, 8999980), QgsPointXY(300000, 9000000)]]))
        ft.setAttributes(['Unidade 1'])
        p.addFeatures([ft]); areas.updateExtents()
        out = run_signature(raster, areas, 'raster', '', str(d/'sig.csv'),
                            area_name_field='NOME')
        with open(out['csv'], encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f, delimiter=';'))
        if {r['CODIGO']: int(r['PIXELS']) for r in rows} != {'1': 3, '2': 4}:
            raise RuntimeError('Distribuição de pixels incorreta: ' + repr(rows))
        if abs(sum(float(r['AREA_HA']) for r in rows) - .07) >= 1e-6:
            raise RuntimeError('Área raster incorreta.')
        gpkg = QgsVectorLayer(out['gpkg']+'|layername=assinatura_areas', 'R', 'ogr')
        if not gpkg.isValid() or gpkg.featureCount() != 1:
            raise RuntimeError('GeoPackage raster inválido.')
        row = next(gpkg.getFeatures())
        if abs(row['AREA_ANAL_HA'] - .07) >= 1e-6:
            raise RuntimeError('Campo de área analisada incorreto.')
        if row['PREDOMINA'] != '2':
            raise RuntimeError('Classe dominante incorreta.')

        thematic = QgsVectorLayer('Polygon?crs=EPSG:31985', 'Classes vetoriais', 'memory')
        tprov = thematic.dataProvider()
        tprov.addAttributes([QgsField('CODIGO', QVariant.Int)])
        thematic.updateFields()
        for code, left, right in ((1, 300000, 300020), (2, 300020, 300040)):
            feat = QgsFeature(thematic.fields())
            feat.setGeometry(QgsGeometry.fromPolygonXY([[QgsPointXY(left,9000000),
                QgsPointXY(right,9000000), QgsPointXY(right,8999980),
                QgsPointXY(left,8999980), QgsPointXY(left,9000000)]]))
            feat.setAttributes([code])
            tprov.addFeatures([feat])
        thematic.updateExtents()
        second = run_signature(thematic, areas, 'vector', 'CODIGO', str(d/'vetor.csv'))
        with open(second['csv'], encoding='utf-8-sig', newline='') as f:
            vector_rows = list(csv.DictReader(f, delimiter=';'))
        if len(vector_rows) != 2:
            raise RuntimeError('Número de classes vetoriais incorreto.')
        if abs(sum(float(r['AREA_HA']) for r in vector_rows) - .08) >= 1e-6:
            raise RuntimeError('Área vetorial incorreta.')
    print('Assinatura Ambiental: raster e vetor, CSV/TXT e GeoPackage — OK')
    return True
