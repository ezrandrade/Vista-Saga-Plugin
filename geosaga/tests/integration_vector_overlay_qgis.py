"""Execute no Console Python do QGIS 4.x:

from geosaga.tests.integration_vector_overlay_qgis import run
run()

Verifica 2 polígonos parcialmente sobrepostos e as notas ponderadas.
Não exige dados do usuário e remove as camadas de teste ao finalizar.
"""
import os
import tempfile


def _layer(name, wkt, value):
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsFeature, QgsField, QgsGeometry, QgsVectorLayer
    layer = QgsVectorLayer('Polygon?crs=EPSG:31985', name, 'memory')
    provider = layer.dataProvider()
    assert provider.addAttributes([QgsField('classe', QVariant.Int)])
    layer.updateFields()
    feature = QgsFeature(layer.fields())
    feature.setGeometry(QgsGeometry.fromWkt(wkt))
    feature.setAttributes([value])
    assert provider.addFeatures([feature])[0]
    layer.updateExtents()
    return layer


def run():
    from qgis.core import QgsProject, QgsVectorLayer
    from ..vector_overlay_engine import evaluate_overlay
    project = QgsProject.instance()
    a = _layer('VISTA_OVERLAY_A', 'POLYGON((0 0,10 0,10 10,0 10,0 0))', 1)
    b = _layer('VISTA_OVERLAY_B', 'POLYGON((5 0,15 0,15 10,5 10,5 0))', 2)
    project.addMapLayer(a, False)
    project.addMapLayer(b, False)
    try:
        rules = [
            {'layer_id': a.id(), 'source_field': 'classe', 'field': 'C01',
             'weight': 40, 'counts': {'1': 1}, 'notes': {'1': 2}, 'excluded': set()},
            {'layer_id': b.id(), 'source_field': 'classe', 'field': 'C02',
             'weight': 60, 'counts': {'2': 1}, 'notes': {'2': 8}, 'excluded': set()},
        ]
        with tempfile.TemporaryDirectory(prefix='vistasaga_overlay_test_') as folder:
            dest = os.path.join(folder, 'teste_sobreposicao.gpkg')
            report = evaluate_overlay(rules, 10, dest, project)
            output = QgsVectorLayer(dest, 'Teste Vista Saga', 'ogr')
            if not output.isValid():
                raise AssertionError('GeoPackage de saída não foi aberto.')
            assert report['total'] == 1, report
            feature = next(output.getFeatures())
            assert abs(feature.geometry().area() - 50) < 1e-7, feature.geometry().area()
            assert abs(feature['AVALIACAO'] - 5.6) < 1e-7, feature['AVALIACAO']
            assert feature['C01'] == '1' and feature['C02'] == '2'
            assert feature['VALIDO'] == 1
            output = None
    finally:
        project.removeMapLayer(a.id())
        project.removeMapLayer(b.id())
    return {'status': 'ok', 'teste': 'intersecao de duas camadas, notas e geometria'}
