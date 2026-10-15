"""Teste integrado para Console Python QGIS 4.x:

from geosaga.tests.integration_vector_monitoring_qgis import run
run()

Valida polígonos 1986/2016, geometria, áreas, CSV e descrição de transições.
"""
import csv
import tempfile
from pathlib import Path


def _source(name, values):
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsFeature, QgsField, QgsGeometry, QgsVectorLayer
    layer = QgsVectorLayer('Polygon?crs=EPSG:31985', name, 'memory')
    provider = layer.dataProvider()
    if not provider.addAttributes([QgsField('CODIGO', QVariant.Int),
                                   QgsField('NOME', QVariant.String)]):
        raise RuntimeError('Falha em atributos de teste.')
    layer.updateFields()
    data = []
    for coords, code, label in values:
        feat = QgsFeature(layer.fields())
        feat.setGeometry(QgsGeometry.fromWkt(coords))
        feat.setAttributes([code, label])
        data.append(feat)
    if not provider.addFeatures(data)[0]:
        raise RuntimeError('Falha ao criar polígonos de teste.')
    layer.updateExtents()
    return layer


def run():
    from qgis.core import QgsProject, QgsVectorLayer
    from ..vector_monitoring_engine import run_vector_monitoring
    before = _source('VISTA_MON_VET_1986', [
        ('POLYGON((0 0,10 0,10 10,0 10,0 0))', 1, 'Mata'),
        ('POLYGON((10 0,20 0,20 10,10 10,10 0))', 2, 'Pasto'),
    ])
    after = _source('VISTA_MON_VET_2016', [
        ('POLYGON((0 0,5 0,5 10,0 10,0 0))', 1, 'Mata'),
        ('POLYGON((5 0,20 0,20 10,5 10,5 0))', 3, 'Urbano'),
    ])
    project = QgsProject.instance()
    project.addMapLayer(before, False)
    project.addMapLayer(after, False)
    try:
        with tempfile.TemporaryDirectory(prefix='vistasaga_monitoria_vetor_') as directory:
            gpkg = str(Path(directory) / 'monitoria.gpkg')
            summary = run_vector_monitoring(before, after, 'CODIGO', 'CODIGO', gpkg,
                                            name_before='NOME', name_after='NOME',
                                            initial='1986', final='2016')
            if abs(summary['area_total_m2'] - 200) > 0.00001:
                raise AssertionError('Área total incorreta: ' + str(summary))
            if abs(summary['pct_permanencia'] - 25) > .00001:
                raise AssertionError('Permanência incorreta: ' + str(summary))
            if abs(summary['pct_mudanca'] - 75) > .00001:
                raise AssertionError('Mudança incorreta: ' + str(summary))
            output = QgsVectorLayer(gpkg + '|layername=monitoria_vetorial', 'Teste', 'ogr')
            if not output.isValid():
                raise AssertionError('GeoPackage não abriu.')
            names = set(output.fields().names())
            if not {'LEGENDA', 'AREA_M2', 'AREA_HA', 'PCT_AREA', 'SITUACAO'} <= names:
                raise AssertionError('Faltam campos: ' + str(names))
            feat_area = sum(float(f['AREA_M2']) for f in output.getFeatures())
            if abs(feat_area - 200) > .00001:
                raise AssertionError('Soma de áreas incorreta: ' + str(feat_area))
            output = None
            with open(summary['csv'], encoding='utf-8-sig', newline='') as csvfile:
                data = list(csv.DictReader(csvfile, delimiter=';'))
            if len(data) != 3:
                raise AssertionError('Transições incorretas: ' + str(data))
    finally:
        project.removeMapLayer(before.id())
        project.removeMapLayer(after.id())
    return {'status': 'ok', 'teste': 'monitoria vetorial com 3 transições, áreas e CSV'}
