"""Capturas do tutorial (janelas preenchidas com os dados de Vila Serena) e GIF do Sequenciador.

Uso, na raiz do repositório, depois de executar_tutorial.py na mesma pasta de trabalho:
    QT_SCALE_FACTOR=2 QT_QPA_PLATFORM=offscreen python3.12 docs/tutorial/capturar_tutorial.py <trabalho> [pt|en|es]

Salva <trabalho>/janelas_<idioma>/tNN_*.png e, em pt, <trabalho>/resultados/vila_serena_2000_2020.gif.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'docs', 'manual'))

import capture_windows as cw  # noqa: E402  (QgsApplication, caixas neutralizadas, grab)

from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsRasterLayer, QgsVectorLayer  # noqa: E402
from qgis.PyQt.QtCore import Qt  # noqa: E402
from qgis.PyQt.QtWidgets import QFileDialog, QTabWidget  # noqa: E402

from geosaga import i18n  # noqa: E402

BAIRROS = {'pt': ['Beira-Rio', 'Centro', 'Alto da Serra', 'Porto', 'Jardim Novo', 'Vila Verde']}
LAYER_NAMES = {
    'pt': {'uso': 'Uso do solo', 'solos': 'Solos', 'decl': 'Declividade', 'atrito': 'Atrito',
           'bairros': 'Bairros', 'escolas': 'Escolas', 'bairros_r': 'Bairros (raster)', 'title': 'Uso do solo'},
    'en': {'uso': 'Land use', 'solos': 'Soils', 'decl': 'Slope', 'atrito': 'Friction',
           'bairros': 'Districts', 'escolas': 'Schools', 'bairros_r': 'Districts (raster)', 'title': 'Land use'},
    'es': {'uso': 'Uso del suelo', 'solos': 'Suelos', 'decl': 'Pendiente', 'atrito': 'Fricción',
           'bairros': 'Barrios', 'escolas': 'Escuelas', 'bairros_r': 'Barrios (ráster)', 'title': 'Uso del suelo'},
}


def _layers(work, lang):
    data, res = os.path.join(work, 'dados'), os.path.join(work, 'resultados')
    n = LAYER_NAMES[lang]
    project = QgsProject.instance()
    project.clear()
    crs = QgsCoordinateReferenceSystem('EPSG:31985')
    project.setCrs(crs)
    layers = {f'uso{y}': QgsRasterLayer(os.path.join(data, f'uso_solo_{y}.tif'), f"{n['uso']} {y}")
              for y in (2000, 2010, 2020)}
    layers['solos'] = QgsRasterLayer(os.path.join(data, 'solos.tif'), n['solos'])
    layers['decl'] = QgsRasterLayer(os.path.join(data, 'declividade.tif'), n['decl'])
    layers['atrito'] = QgsRasterLayer(os.path.join(data, 'atrito.tif'), n['atrito'])
    layers['bairros'] = QgsVectorLayer(os.path.join(data, 'bairros.gpkg'), n['bairros'], 'ogr')
    layers['escolas'] = QgsVectorLayer(os.path.join(data, 'escolas.gpkg'), n['escolas'], 'ogr')
    layers['bairros_r'] = QgsRasterLayer(os.path.join(res, 'bairros.tif'), n['bairros_r'])
    # Passo do tutorial: renomear as classes do raster dos bairros na Simbologia (Classe 1 -> Beira-Rio...).
    renderer = layers['bairros_r'].renderer()
    if hasattr(renderer, 'setLabel'):
        for code, name in enumerate(BAIRROS['pt'], 1):
            renderer.setLabel(code, name)
    for layer in layers.values():
        layer.setCrs(crs)
        project.addMapLayer(layer)
    return data, res, layers


def capture(work, lang):
    i18n.qgis_language = lambda: lang
    i18n.translate_for_locale.cache_clear()
    data, res, layers = _layers(work, lang)
    shots = os.path.join(work, f'janelas_{lang}')
    os.makedirs(shots, exist_ok=True)
    from qgis.PyQt.QtCore import QCoreApplication, QEvent

    def process():
        cw._process()
        QCoreApplication.sendPostedEvents(None, int(QEvent.Type.DeferredDelete))  # apaga widgets antigos
        cw._process()

    def grab(dialog, path, width, height):
        dialog.resize(width, height)
        process()
        dialog.grab().save(path)

    # 1. Conversor: Vetor -> GeoTIFF (bairros) e GeoTIFF -> RS2 (uso 2020).
    from geosaga.rs2_dialog import RS2ConverterDialog
    d = RS2ConverterDialog(None)
    d.show()
    d.mode.setCurrentIndex(4)
    process()
    d.loaded_layers.setLayer(layers['bairros'])
    d._use_layer()
    d.vector_field.setCurrentText('CODIGO')
    d.pixel_size.setValue(10.0)
    d.destination.setText(os.path.join(res, 'bairros.tif'))
    process()
    grab(d, f'{shots}/t01_conversor_vetor_geotiff.png', 820, 760)
    d.mode.setCurrentIndex(1)
    process()
    d._set_source(os.path.join(data, 'uso_solo_2020.tif'))
    d.destination.setText(os.path.join(res, 'uso_solo_2020.rs2'))
    process()
    grab(d, f'{shots}/t02_conversor_geotiff_rs2.png', 820, 720)
    d.close()

    # 2. Assinatura (guia Raster): Bairros (raster) como referência; Centro e Beira-Rio.
    from geosaga.signature_dialog import SignatureDialog
    d = SignatureDialog(None)
    d.show()
    for key in ('bairros_r', 'uso2020', 'solos', 'decl'):
        d._append_raster(layers[key].source(), 'EPSG:31985', layers[key].id())
    d._refresh_list(0)
    for i, key in enumerate(d._ref_classes):
        if key in (1, 2):
            d.class_list.item(i).setCheckState(Qt.CheckState.Checked)
    d.title.setText('Centro e Beira-Rio')
    d.path.setText(os.path.join(res, 'assinatura.csv'))
    process()
    grab(d, f'{shots}/t03_assinatura_configuracao.png', 900, 800)
    d.run()
    process()
    grab(d, f'{shots}/t04_assinatura_resultados.png', 1000, 620)
    d.close()

    # 3. Monitoria 2000 -> 2020.
    from geosaga.monitoring_dialog import MonitoringDialog
    d = MonitoringDialog(None)
    d.show()
    d.before_layer.setLayer(layers['uso2000'])
    d.after_layer.setLayer(layers['uso2020'])
    d.before_label.setText('2000')
    d.after_label.setText('2020')
    d.title_edit.setText(f"{LAYER_NAMES[lang]['title']} 2000 - 2020")
    d.output_edit.setText(os.path.join(res, 'transicoes_2000_2020.tif'))
    process()
    grab(d, f'{shots}/t05_monitoria.png', 900, 640)
    d.close()

    # 4. Combinação: uso 2020 x solos.
    from geosaga.combination_dialog import CombinationDialog
    d = CombinationDialog(None)
    d.show()
    for key in ('uso2020', 'solos'):
        d.select_0.setLayer(layers[key])
        d._add_project(0)
    d.output_0.setText(os.path.join(res, 'uso2020_x_solos.tif'))
    process()
    grab(d, f'{shots}/t06_combinacao.png', 900, 640)
    d.close()

    # 5. Avaliação: projeto pronto (Abrir projeto...).
    from geosaga.evaluation_dialog import EvaluationDialog
    project = os.path.join(data, 'aptidao_expansao.geosaga.json')
    QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: (project, ''))
    d = EvaluationDialog(None)
    d.show()
    d.open_project()
    process()
    if d.map_table.rowCount():
        d.map_table.selectRow(2)
    d.output_edit.setText(os.path.join(res, 'aptidao_expansao.tif'))
    process()
    grab(d, f'{shots}/t07_avaliacao.png', 1100, 900)
    d.close()
    QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ('', ''))

    # 6. Voronoi Com Atrito, grade do raster de atrito.
    from geosaga.voronoi_dialog import VoronoiDialog
    d = VoronoiDialog(None)
    d.show()
    d.point_layer.setLayer(layers['escolas'])
    process()
    index = d.label_field.findText('NOME')
    if index >= 0:
        d.label_field.setCurrentIndex(index)
    d.mode.setCurrentIndex(2)
    process()
    d.friction_kind.setCurrentIndex(0)
    d.friction_layer.setLayer(layers['atrito'])
    d.extent_mode.setCurrentIndex(d.extent_mode.findData('reference'))
    process()
    d.grid_layer.setLayer(layers['atrito'])
    d.output_edits[0].setText(os.path.join(res, 'voronoi_com_atrito.tif'))
    process()
    grab(d, f'{shots}/t08_voronoi_atrito.png', 900, 860)
    d.mode.setCurrentIndex(1)
    process()
    index = d.mass_field.findText('MATRICULAS')
    if index >= 0:
        d.mass_field.setCurrentIndex(index)
    d.output_edits[0].setText(os.path.join(res, 'voronoi_com_massa.tif'))
    process()
    grab(d, f'{shots}/t09_voronoi_massa.png', 900, 820)
    d.close()

    # 7. Sequenciador: 2000, 2010, 2020 -> GIF.
    from geosaga.image_sequence_dialog import ImageSequenceDialog
    d = ImageSequenceDialog(None)
    d.show()
    for year in (2000, 2010, 2020):
        d.selected.setLayer(layers[f'uso{year}'])
        d._add_selected()
    d.width_spin.setValue(600)
    d.height_spin.setValue(600)
    gif = os.path.join(res, 'vila_serena_2000_2020.gif')
    d.output.setText(gif)
    if lang == 'pt':
        d.export_png.setChecked(True)
        d._run()
    process()
    grab(d, f'{shots}/t10_sequenciador.png', 900, 900)
    d.close()
    print(lang, sorted(os.listdir(shots)))


if __name__ == '__main__':
    work = os.path.abspath(sys.argv[1])
    for language in (sys.argv[2:] or ['pt']):
        capture(work, language)
    cw.APP.exitQgis()
