"""Console Python do QGIS 4.x:
from geosaga.tests.integration_signature_overlap_qgis import run
run()
"""
import csv
import tempfile
from pathlib import Path


def run():
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsVectorLayer
    from geosaga.signature_engine import run_signature

    def polygon(left, right):
        return QgsGeometry.fromPolygonXY([[QgsPointXY(left, 10), QgsPointXY(right, 10),
            QgsPointXY(right, 0), QgsPointXY(left, 0), QgsPointXY(left, 10)]])

    theme = QgsVectorLayer('Polygon?crs=EPSG:31985', 'Temas sobrepostos', 'memory')
    prov = theme.dataProvider()
    prov.addAttributes([QgsField('CODIGO', QVariant.String)])
    theme.updateFields()
    for code, x1, x2 in [('A', 0, 10), ('A', 5, 15), ('B', 10, 20)]:
        f = QgsFeature(theme.fields())
        f.setGeometry(polygon(x1, x2))
        f.setAttributes([code])
        prov.addFeatures([f])
    theme.updateExtents()
    aoi = QgsVectorLayer('Polygon?crs=EPSG:31985', 'Área', 'memory')
    f = QgsFeature(aoi.fields())
    f.setGeometry(polygon(0, 20))
    aoi.dataProvider().addFeatures([f])
    aoi.updateExtents()
    with tempfile.TemporaryDirectory(prefix='sig_overlaps_') as d:
        result = run_signature(theme, aoi, 'vector', 'CODIGO', str(Path(d) / 'assinatura.csv'))
        with open(result['csv'], encoding='utf-8-sig', newline='') as r:
            rows = list(csv.DictReader(r, delimiter=';'))
        counts = {r['CODIGO']:float(r['AREA_HA']) for r in rows}
        if abs(counts['A'] - .01) > 1e-5 or abs(counts['B'] - .005) > 1e-5:
            raise RuntimeError(f'Áreas incorretas: {counts}')
        if abs(float(rows[0]['AREA_CONFLITO_HA']) - .005) > 1e-5:
            raise RuntimeError('O conflito entre A e B não foi registrado.')
        from qgis.core import QgsVectorLayer
        output = QgsVectorLayer(result['gpkg']+'|layername=assinatura_areas', 'resultado', 'ogr')
        if not output.isValid() or output.featureCount() != 1:
            raise RuntimeError('GeoPackage inválido')
        row = next(output.getFeatures())
        if abs(row['AREA_CONF_HA'] - .005) > 1e-5:
            raise RuntimeError('Área de conflito ausente no GeoPackage')
    print('Assinatura 0.5.1: dissolução, conflito por classe e relatórios OK')
    return True
