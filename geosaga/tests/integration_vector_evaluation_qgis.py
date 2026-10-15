"""Teste integrado da avaliação vetorial no QGIS 4.x (Console Python)."""
import os
import tempfile


def run():
    from qgis.core import QgsFeature, QgsGeometry, QgsVectorLayer
    from geosaga.vector_evaluation_writer import evaluate_vector_layer

    layer = QgsVectorLayer('Polygon?crs=EPSG:31985&field=USO:integer&field=SOLO:string',
                           'teste_avaliacao_vetorial', 'memory')
    if not layer.isValid():
        raise RuntimeError('Camada de teste inválida.')
    features = []
    for i, (uso, solo) in enumerate([(1, 'argiloso'), (2, 'arenoso'), (3, 'arenoso')]):
        feature = QgsFeature(layer.fields())
        feature.setAttributes([uso, solo])
        feature.setGeometry(QgsGeometry.fromWkt(
            f'POLYGON(({i*10} 0,{i*10+10} 0,{i*10+10} 10,{i*10} 10,{i*10} 0))'))
        features.append(feature)
    success, _ = layer.dataProvider().addFeatures(features)
    if not success:
        raise RuntimeError('Não foi possível preencher a camada sintética.')
    rules = [
        {'field': 'USO', 'weight': 60, 'categories': {'1','2','3'},
         'notes': {'1':8, '2':2}, 'excluded': {'3'}},
        {'field': 'SOLO', 'weight':40, 'categories': {'argiloso','arenoso'},
         'notes': {'argiloso':4,'arenoso':10}, 'excluded': set()},
    ]
    with tempfile.TemporaryDirectory(prefix='vista_saga_qgis4_') as folder:
        dest = os.path.join(folder, 'avaliacao.gpkg')
        report = evaluate_vector_layer(layer, rules, 10, dest)
        assert report == {'validos':2,'excluidos_ou_sem_dado':1,'total':3}, report
        result = QgsVectorLayer(dest, 'avaliacao', 'ogr')
        assert result.isValid(), 'GeoPackage inválido'
        assert result.featureCount() == 3, 'Número de polígonos alterado'
        assert result.crs().authid() == layer.crs().authid(), 'SRC não preservado'
        by_uso = {int(f['USO']): f for f in result.getFeatures()}
        assert abs(by_uso[1]['AVALIACAO'] - 6.4) < 1e-8
        assert abs(by_uso[2]['AVALIACAO'] - 5.2) < 1e-8
        assert by_uso[3]['VALIDO'] == 0
        assert 'Excluída' in by_uso[3]['MOTIVO']
        for orig in layer.getFeatures():
            assert by_uso[int(orig['USO'])].geometry().equals(orig.geometry()), 'Geometria alterada'
    print('Vista Saga — Avaliação Espacial vetorial: teste integrado aprovado.')
    return True
