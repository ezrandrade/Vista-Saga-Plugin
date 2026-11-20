"""Janela da Assinatura 1.5.0 em QGIS real (guias Raster e Vetorial), com dados sintéticos.

No Console Python do QGIS 4.x:

    from geosaga.tests.integration_signature_150_qgis import run
    run()

Ou sem interface, na raiz do repositório: ``QT_QPA_PLATFORM=offscreen python
geosaga/tests/integration_signature_150_qgis.py``.
"""
import csv
import os
import sys
import tempfile


def _tif(path, rows, names, epsg=31985):
    import numpy as np
    from osgeo import gdal, osr
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    array = np.array(rows, dtype='uint8')
    ds = gdal.GetDriverByName('GTiff').Create(path, array.shape[1], array.shape[0], 1, gdal.GDT_Byte)
    ds.SetProjection(srs.ExportToWkt())
    ds.SetGeoTransform((197510, 10, 0, 8940820, 0, -10))
    band = ds.GetRasterBand(1)
    band.WriteArray(array)
    band.SetCategoryNames(names)
    ds = None


def _layer(name, features):
    from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer
    layer = QgsVectorLayer('Polygon?crs=EPSG:31985&field=CLASSE:integer&field=NOME:string', name, 'memory')
    batch = []
    for code, label, wkt in features:
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromWkt(wkt))
        feature.setAttributes([code, label])
        batch.append(feature)
    layer.dataProvider().addFeatures(batch)
    layer.updateExtents()
    QgsProject.instance().addMapLayer(layer)
    return layer


def _square(x0, x1):
    return f'POLYGON(({x0} 0,{x1} 0,{x1} 100,{x0} 100,{x0} 0))'


def _rows(path):
    with open(path, encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream, delimiter=';'))


def run():
    from qgis.PyQt.QtCore import Qt
    from geosaga.signature_dialog import SignatureDialog
    with tempfile.TemporaryDirectory(prefix='vsp_assinatura_150_') as folder:
        ref, uso = os.path.join(folder, 'ref.tif'), os.path.join(folder, 'uso.tif')
        _tif(ref, [[0, 1, 1], [0, 2, 2]], ['FUNDO', 'A', 'B'])
        _tif(uso, [[5, 5, 6], [6, 6, 6]], ['', '', '', '', '', 'Edificada', 'Vegetação'])
        dialog = SignatureDialog(None)
        dialog._append_raster(ref)
        dialog._append_raster(uso)
        dialog._refresh_list(0)
        assert dialog._ref_classes == [0, 1, 2], dialog._ref_classes
        dialog.class_list.item(1).setCheckState(Qt.CheckState.Checked)  # classe A
        dialog.path.setText(os.path.join(folder, 'raster.csv'))
        dialog.run()
        rows = _rows(os.path.join(folder, 'raster.csv'))
        union_uso = {r['CODIGO']: r for r in rows if r['RECORTE'] == 'UNIAO' and r['MAPA'] == 'uso.tif'}
        assert union_uso['5']['PIXELS_ASN'] == '1' and union_uso['6']['PIXELS_ASN'] == '1', union_uso
        assert os.path.isfile(os.path.join(folder, 'raster.txt'))
        assert dialog.cut_choice.count() == 2  # união + classe A

        # Nomes do estilo da camada no QGIS (Paletado/Valores únicos) prevalecem sobre o arquivo.
        from qgis.core import QgsPalettedRasterRenderer, QgsProject, QgsRasterLayer
        from qgis.PyQt.QtGui import QColor
        layer = QgsRasterLayer(uso, 'uso', 'gdal')
        classes = [QgsPalettedRasterRenderer.Class(5, QColor('red'), 'Casas'),
                   QgsPalettedRasterRenderer.Class(6, QColor('green'), 'Mata')]
        layer.setRenderer(QgsPalettedRasterRenderer(layer.dataProvider(), 1, classes))
        QgsProject.instance().addMapLayer(layer)
        dialog._raster[1]['layer_id'] = layer.id()
        dialog.run()
        labels = {r['CODIGO']: r['CLASSE'] for r in _rows(os.path.join(folder, 'raster.csv'))
                  if r['MAPA'] == 'uso.tif'}
        assert labels == {'5': 'Casas', '6': 'Mata'}, labels
        QgsProject.instance().removeMapLayer(layer.id())

        bairros = _layer('Bairros', [(1, 'Centro', _square(0, 100)), (2, 'Farol', _square(100, 200))])
        usos = _layer('Usos', [(10, 'Edificada', _square(0, 150)), (20, 'Vegetação', _square(150, 200))])
        dialog.type_tabs.setCurrentIndex(1)
        dialog._append_layer(1, bairros)
        dialog._append_layer(1, usos)
        dialog._refresh_list(1)
        bairros.selectByIds([f.id() for f in bairros.getFeatures() if f['CLASSE'] == 2])
        assert dialog.selection_info.text().endswith(': 1.'), dialog.selection_info.text()
        dialog.path.setText(os.path.join(folder, 'vetor.csv'))
        dialog.run()
        rows = _rows(os.path.join(folder, 'vetor.csv'))
        union = {(r['MAPA'], r['CODIGO']): r for r in rows if r['RECORTE'] == 'UNIAO'}
        assert abs(float(union[('Usos', '10')]['PCT_AREA_ASN']) - 50.0) < 1e-6, union
        assert abs(float(union[('Usos', '20')]['PCT_CATEGORIA']) - 100.0) < 1e-6, union
        dialog.close()
    print('Assinatura 1.5.0: janela em QGIS real OK (Raster e Vetorial).')
    return True


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from qgis.core import QgsApplication
    app = QgsApplication([], True)
    app.initQgis()
    try:
        run()
    finally:
        app.exitQgis()
