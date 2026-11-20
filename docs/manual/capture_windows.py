"""Capturas das janelas e tabela de campos do manual do usuário (1.6.0), em QGIS real.

Uso, na raiz do repositório:
    QT_QPA_PLATFORM=offscreen python docs/manual/capture_windows.py <pasta_de_saida>

Para cada idioma (pt, en, es): cria dados sintéticos (nomes de camadas e classes no idioma), abre cada
módulo, preenche com um exemplo, salva as telas em <saida>/<idioma>/janelas/ e grava
<saida>/<idioma>/campos.json com rótulo e dica de cada botão, campo, caixa de marcar e lista.
Caixas de mensagem e de entrada são neutralizadas (respondem sozinhas) para a captura não travar.
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests', 'qgis'))

from qgis.core import QgsApplication  # noqa: E402

APP = QgsApplication([], True)
APP.initQgis()

import numpy as np  # noqa: E402
from osgeo import gdal, ogr, osr  # noqa: E402
from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer  # noqa: E402
from qgis.PyQt.QtCore import Qt  # noqa: E402
from qgis.PyQt.QtWidgets import (  # noqa: E402
    QAbstractButton, QFileDialog, QInputDialog, QMessageBox, QTabBar, QTabWidget,
)

# --- caixas de diálogo neutralizadas ---------------------------------------------------------
for name in ('warning', 'information', 'critical'):
    setattr(QMessageBox, name, staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok))
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
QInputDialog.getText = staticmethod(lambda *a, **k: ('', False))
QInputDialog.getItem = staticmethod(lambda *a, **k: ('', False))
QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ('', ''))
QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([], ''))
QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: ('', ''))

import tooltip_inventory as inv  # noqa: E402  (reaproveita o inventário de dicas)
from geosaga import i18n  # noqa: E402

NAMES = {
    'pt': {'uso': 'Uso do solo', 'solos': 'Solos', 'bairros': 'Bairros', 'pontos': 'Escolas',
           'atrito': 'Atrito', 'uso_v': 'Uso do solo (vetor)',
           'classes': ['FUNDO', 'Área edificada', 'Vegetação', 'Água', 'Agricultura'],
           'solos_c': ['FUNDO', 'Argissolo', 'Latossolo', 'Neossolo'],
           'bairros_c': ['Centro', 'Farol', 'Jaraguá', 'Pajuçara', 'Ponta Verde', 'Poço'], 'list': '(lista)',
           'footer': 'Rodapé e janelas auxiliares'},
    'en': {'uso': 'Land use', 'solos': 'Soils', 'bairros': 'Districts', 'pontos': 'Schools',
           'atrito': 'Friction', 'uso_v': 'Land use (vector)',
           'classes': ['BACKGROUND', 'Built-up area', 'Vegetation', 'Water', 'Agriculture'],
           'solos_c': ['BACKGROUND', 'Argisol', 'Latosol', 'Neosol'],
           'bairros_c': ['Centre', 'Lighthouse', 'Harbour', 'Seaside', 'Green Point', 'Well'], 'list': '(list)',
           'footer': 'Footer and auxiliary windows'},
    'es': {'uso': 'Uso del suelo', 'solos': 'Suelos', 'bairros': 'Barrios', 'pontos': 'Escuelas',
           'atrito': 'Fricción', 'uso_v': 'Uso del suelo (vector)',
           'classes': ['FONDO', 'Área edificada', 'Vegetación', 'Agua', 'Agricultura'],
           'solos_c': ['FONDO', 'Argisol', 'Latosol', 'Neosol'],
           'bairros_c': ['Centro', 'Faro', 'Puerto', 'Playa', 'Punta Verde', 'Pozo'], 'list': '(lista)',
           'footer': 'Pie y ventanas auxiliares'},
}
X0, Y1, CELL, W, H = 197500, 8941000, 10, 120, 90
COLORS = [(255, 255, 255), (235, 104, 52), (0, 131, 0), (42, 120, 214), (237, 161, 0)]


def _srs():
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(31985)
    return srs


def _raster(path, array, names):
    ds = gdal.GetDriverByName('GTiff').Create(path, W, H, 1, gdal.GDT_Byte)
    ds.SetGeoTransform((X0, CELL, 0, Y1, 0, -CELL))
    ds.SetProjection(_srs().ExportToWkt())
    band = ds.GetRasterBand(1)
    table = gdal.ColorTable()  # a paleta vai antes dos dados (exigência do GeoTIFF)
    for i in range(len(names)):
        table.SetColorEntry(i, COLORS[i % len(COLORS)] + (255,))
    band.SetRasterColorTable(table)
    band.SetCategoryNames(names)
    band.WriteArray(array.astype(np.uint8))
    ds = None


def _polygons(path, name, geoms, fields):
    ds = ogr.GetDriverByName('GPKG').CreateDataSource(path)
    layer = ds.CreateLayer(name, _srs(), ogr.wkbPolygon if 'POLYGON' in geoms[0][0] else ogr.wkbPoint)
    for field, kind in fields:
        layer.CreateField(ogr.FieldDefn(field, kind))
    for wkt, values in geoms:
        feature = ogr.Feature(layer.GetLayerDefn())
        for (field, _kind), value in zip(fields, values):
            feature.SetField(field, value)
        feature.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
        layer.CreateFeature(feature)
    ds = None


def _box(c0, r0, c1, r1):
    x0, x1 = X0 + c0 * CELL, X0 + c1 * CELL
    y0, y1 = Y1 - r1 * CELL, Y1 - r0 * CELL
    return f'POLYGON(({x0} {y0},{x1} {y0},{x1} {y1},{x0} {y1},{x0} {y0}))'


def make_data(folder, lang):
    n = NAMES[lang]
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:H, 0:W]
    base = ((xx // 30 + yy // 30) % 4 + 1)
    noise = rng.integers(0, 10, size=(H, W))
    uso1 = np.where(noise == 0, (base % 4) + 1, base)
    uso2 = np.where((xx > 60) & (yy < 45), 1, uso1)
    solos = (xx * 3 // W) + 1
    paths = {}
    for key, array, names in (('uso1', uso1, n['classes']), ('uso2', uso2, n['classes']),
                              ('solos', solos, n['solos_c'])):
        paths[key] = os.path.join(folder, f'{key}.tif')
        _raster(paths[key], array, names)
    bairros = []
    for i, label in enumerate(n['bairros_c']):
        c, r = (i % 3) * 40, (i // 3) * 45
        bairros.append((_box(c, r, c + 40, r + 45), [label, i + 1]))
    paths['bairros'] = os.path.join(folder, 'bairros.gpkg')
    _polygons(paths['bairros'], 'bairros', bairros, [('NOME', ogr.OFTString), ('CODIGO', ogr.OFTInteger)])
    uso_v = [(_box(0, 0, 60, 90), [n['classes'][1]]), (_box(60, 0, 120, 45), [n['classes'][2]]),
             (_box(60, 45, 120, 90), [n['classes'][4]])]
    paths['uso_v'] = os.path.join(folder, 'uso_v.gpkg')
    _polygons(paths['uso_v'], 'uso', uso_v, [('CLASSE', ogr.OFTString)])
    pts = [(f'POINT({X0 + c * CELL} {Y1 - r * CELL})', [name, m]) for (c, r, name, m) in
           ((20, 20, 'A', 3), (95, 25, 'B', 1), (30, 70, 'C', 2), (90, 75, 'D', 1))]
    paths['pontos'] = os.path.join(folder, 'pontos.gpkg')
    _polygons(paths['pontos'], 'pontos', pts, [('NOME', ogr.OFTString), ('MASSA', ogr.OFTReal)])
    project = QgsProject.instance()
    project.clear()
    project.setCrs(QgsRasterLayer(paths['uso1'], 'x').crs())
    layers = {
        'uso1': QgsRasterLayer(paths['uso1'], f"{n['uso']} 2000"),
        'uso2': QgsRasterLayer(paths['uso2'], f"{n['uso']} 2020"),
        'solos': QgsRasterLayer(paths['solos'], n['solos']),
        'bairros': QgsVectorLayer(paths['bairros'], n['bairros'], 'ogr'),
        'uso_v': QgsVectorLayer(paths['uso_v'], n['uso_v'], 'ogr'),
        'pontos': QgsVectorLayer(paths['pontos'], n['pontos'], 'ogr'),
    }
    for layer in layers.values():
        project.addMapLayer(layer)
    return paths, layers


def _process():
    for _ in range(3):
        APP.processEvents()


def _tabs(dialog):
    return dialog.findChildren(QTabWidget) + dialog.findChildren(QTabBar)


def _section(widget, dialog):
    """Título do grupo (QGroupBox) mais próximo; sem grupo, o texto da guia que contém o widget."""
    from qgis.PyQt.QtWidgets import QGroupBox
    parent = widget.parentWidget()
    while parent is not None and parent is not dialog:
        if isinstance(parent, QGroupBox) and parent.title():
            return parent.title()
        parent = parent.parentWidget()
    for tabs in dialog.findChildren(QTabWidget):
        for index in range(tabs.count()):
            page = tabs.widget(index)
            if page is not None and page.isAncestorOf(widget):
                return tabs.tabText(index)
    return ''


def fields_of(dialog, lang):
    """[{seção, tipo, rótulo, dica}] de todos os controles do módulo (visíveis ou não), sem repetições."""
    for bar in _tabs(dialog):
        for index in range(bar.count()):
            bar.setCurrentIndex(index)
            _process()
    from qgis.PyQt.QtWidgets import QWidget
    position = {id(w): i for i, w in enumerate(dialog.findChildren(QWidget))}  # ordem de criação = da janela
    rows, seen = [], set()
    for kind in inv.KINDS:
        for widget in dialog.findChildren(kind):
            if inv._internal(widget) or not widget.toolTip().strip():
                continue
            if isinstance(widget, QAbstractButton):
                label = widget.text()
            else:
                label = inv._label(widget) or getattr(widget, 'placeholderText', lambda: '')() or \
                    NAMES[lang]['list']
            label = label.replace('&', '').rstrip(':')
            key = (label, widget.toolTip())
            if key in seen:
                continue
            seen.add(key)
            rows.append({'pos': position.get(id(widget), 0), 'section': _section(widget, dialog).rstrip(':'),
                         'kind': type(widget).__name__.replace('Qgs', '').lstrip('Q'),
                         'label': label, 'tip': widget.toolTip()})
    import re
    result = re.compile(r'resultad|result|sa[íi]da|output', re.IGNORECASE)
    rows.sort(key=lambda r: r['pos'])
    sections = list(dict.fromkeys(r['section'] for r in rows))  # seções na ordem em que aparecem

    def rank(row):
        # Resultado perto do fim; rodapé e janelas auxiliares (sem grupo) por último.
        group = 2 if not row['section'] else 1 if result.search(row['section']) else 0
        return group, sections.index(row['section']), row['pos']
    rows.sort(key=rank)
    for row in rows:
        del row['pos']
        row['section'] = row['section'] or NAMES[lang]['footer']
    return rows


def grab(dialog, path, width=900, height=680):
    dialog.resize(width, height)
    _process()
    dialog.grab().save(path)


def capture(lang, out):
    i18n.qgis_language = lambda: lang
    i18n.translate_for_locale.cache_clear()
    folder = tempfile.mkdtemp(prefix=f'vsp_manual_{lang}_')
    paths, layers = make_data(folder, lang)
    shots = os.path.join(out, lang, 'janelas')
    os.makedirs(shots, exist_ok=True)
    fields = {}

    from geosaga.signature_dialog import SignatureDialog
    d = SignatureDialog(None)
    d.show()
    for key in ('uso1', 'uso2', 'solos'):
        d._append_raster(paths[key], 'EPSG:31985', layers[key].id())
    d._refresh_list(0)
    for i, key in enumerate(d._ref_classes):
        if key in (1, 2):
            d.class_list.item(i).setCheckState(Qt.CheckState.Checked)
    grab(d, f'{shots}/assinatura_raster.png', 900, 760)
    d.path.setText(os.path.join(folder, 'assinatura.csv'))
    d.run()
    grab(d, f'{shots}/assinatura_resultados.png', 900, 560)
    d.tabs.setCurrentIndex(0)
    d.type_tabs.setCurrentIndex(1)
    d._append_layer(1, layers['bairros'])
    d._append_layer(1, layers['uso_v'])
    d._refresh_list(1)
    layers['bairros'].selectByIds([f.id() for f in layers['bairros'].getFeatures()][:2])
    d.vector_list.setCurrentRow(1)
    _process()
    grab(d, f'{shots}/assinatura_vetorial.png', 900, 820)
    fields['assinatura'] = fields_of(d, lang)
    d.close()

    from geosaga.monitoring_dialog import MonitoringDialog
    d = MonitoringDialog(None)
    d.show()
    d.before_layer.setLayer(layers['uso1'])
    d.after_layer.setLayer(layers['uso2'])
    d.title_edit.setText(f"{NAMES[lang]['uso']} 2000 - 2020")
    grab(d, f'{shots}/monitoria_raster.png', 900, 700)
    d.tabs.setCurrentIndex(1)
    _process()
    grab(d, f'{shots}/monitoria_vetorial.png', 900, 760)
    fields['monitoria'] = fields_of(d, lang)
    d.close()

    from geosaga.evaluation_dialog import EvaluationDialog
    d = EvaluationDialog(None)
    d.show()
    d.refresh_available()
    for key in ('uso1', 'solos'):
        d.layer_combo.setCurrentIndex(d.layer_combo.findData(layers[key].id()))
        d.add_current_layer()
    if d.map_table.rowCount():
        d.map_table.selectRow(0)
    _process()
    grab(d, f'{shots}/avaliacao_raster.png', 1100, 900)
    tabs = d.findChildren(QTabWidget)[0]
    tabs.setCurrentIndex(1)
    _process()
    grab(d, f'{shots}/avaliacao_atributos.png', 1100, 900)
    tabs.setCurrentIndex(2)
    _process()
    grab(d, f'{shots}/avaliacao_sobreposicao.png', 1100, 900)
    tabs.setCurrentIndex(0)
    fields['avaliacao'] = fields_of(d, lang)
    d.close()

    from geosaga.voronoi_dialog import VoronoiDialog
    d = VoronoiDialog(None)
    d.show()
    d.point_layer.setLayer(layers['pontos'])
    d.mode.setCurrentIndex(1)
    _process()
    grab(d, f'{shots}/voronoi_raster.png', 900, 820)
    d.tabs.setCurrentIndex(1)
    _process()
    grab(d, f'{shots}/voronoi_vetorial.png', 900, 820)
    d.tabs.setCurrentIndex(0)
    fields['voronoi'] = fields_of(d, lang)
    d.close()

    from geosaga.combination_dialog import CombinationDialog
    d = CombinationDialog(None)
    d.show()
    for key in ('uso1', 'solos'):
        d.select_0.setLayer(layers[key])
        d._add_project(0)
    _process()
    grab(d, f'{shots}/combinacao_raster.png', 900, 640)
    d.tabs.setCurrentIndex(1)
    _process()
    grab(d, f'{shots}/combinacao_vetorial.png', 900, 760)
    d.tabs.setCurrentIndex(0)
    fields['combinacao'] = fields_of(d, lang)
    d.close()

    from geosaga.rs2_dialog import RS2ConverterDialog
    d = RS2ConverterDialog(None)
    d.show()
    d.mode.setCurrentIndex(4)
    _process()
    grab(d, f'{shots}/conversor.png', 820, 760)
    d.advanced_toggle.setChecked(True)
    _process()
    fields['conversor'] = fields_of(d, lang)
    d.mode.setCurrentIndex(0)
    d.advanced_toggle.setChecked(False)
    _process()
    grab(d, f'{shots}/conversor_rs2.png', 820, 720)
    d.close()

    from geosaga.image_sequence_dialog import ImageSequenceDialog
    d = ImageSequenceDialog(None)
    d.show()
    for key in ('uso1', 'uso2'):
        d.selected.setLayer(layers[key])
        d._add_selected()
    _process()
    grab(d, f'{shots}/sequenciador.png', 900, 860)
    fields['sequenciador'] = fields_of(d, lang)
    d.close()

    with open(os.path.join(out, lang, 'campos.json'), 'w', encoding='utf-8') as stream:
        json.dump(fields, stream, ensure_ascii=False, indent=1)
    print(lang, {k: len(v) for k, v in fields.items()})


if __name__ == '__main__':
    target = os.path.abspath(sys.argv[1])
    for language in (sys.argv[2:] or ['pt', 'en', 'es']):
        capture(language, target)
    APP.exitQgis()
