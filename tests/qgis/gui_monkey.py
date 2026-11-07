"""Teste de estresse de interface: clica em todos os botões, caixas e abas de
cada diálogo, vazio e com camadas carregadas, e registra exceções Python não
tratadas (que no QGIS aparecem como janela de erro ou instabilidade).

Uso: qrun.sh tests/gui_monkey.py <pasta_que_contém_geosaga> <pasta_dados_smoke> [idioma]
"""
import os
import sys
import traceback

if os.environ.get('QGIS_PY'):  # instalação conda; no OSGeo4W/QGIS o qgis já é importável
    sys.path[:0] = [os.environ['QGIS_PY'], os.environ['QGIS_PY'] + '/plugins']
sys.path.insert(0, os.path.abspath(sys.argv[1]))
DATA = os.path.abspath(sys.argv[2])
LANG = sys.argv[3] if len(sys.argv) > 3 else 'pt_BR'

from qgis.core import QgsApplication, QgsProject, QgsRasterLayer, QgsVectorLayer, QgsSettings  # noqa: E402
from qgis.PyQt.QtCore import QCoreApplication, QTimer  # noqa: E402
from qgis.PyQt.QtWidgets import (  # noqa: E402
    QMainWindow, QToolBar, QMenu, QPushButton, QToolButton, QCheckBox, QRadioButton,
    QComboBox, QTabWidget, QMessageBox, QFileDialog, QInputDialog, QColorDialog, QApplication,
)

app = QgsApplication([], True)
QgsSettings().setValue('locale/overrideFlag', True)
QgsSettings().setValue('locale/userLocale', LANG)
app.initQgis()
from processing.core.Processing import Processing  # noqa: E402
Processing.initialize()

ERRORS = []


def hook(etype, value, tb):
    ERRORS.append((CURRENT[0], f'{etype.__name__}: {value}', ''.join(traceback.format_tb(tb))[-900:]))


sys.excepthook = hook
CURRENT = ['']
MESSAGES = []
for kind in ('information', 'warning', 'critical'):
    setattr(QMessageBox, kind, staticmethod(
        lambda *a, _k=kind, **k: MESSAGES.append((CURRENT[0], _k, str(a[1:3])[:200]))
        or QMessageBox.StandardButton.Ok))
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.No)
QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ('', ''))
QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([], ''))
QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: ('', ''))
QFileDialog.getExistingDirectory = staticmethod(lambda *a, **k: '')
QInputDialog.getText = staticmethod(lambda *a, **k: ('', False))
QInputDialog.getItem = staticmethod(lambda *a, **k: ('', False))
QInputDialog.getDouble = staticmethod(lambda *a, **k: (0.0, False))
QInputDialog.getInt = staticmethod(lambda *a, **k: (0, False))
QColorDialog.getColor = staticmethod(lambda *a, **k: __import__('qgis.PyQt.QtGui', fromlist=['QColor']).QColor())


class FakeIface:
    def __init__(self):
        self.window = QMainWindow()

    def mainWindow(self):
        return self.window

    def addToolBar(self, name):
        bar = QToolBar(name, self.window)
        self.window.addToolBar(bar)
        return bar

    def mapCanvas(self):
        from qgis.gui import QgsMapCanvas
        if not hasattr(self, '_canvas'):
            self._canvas = QgsMapCanvas(self.window)
        return self._canvas

    def messageBar(self):
        from qgis.gui import QgsMessageBar
        if not hasattr(self, '_bar'):
            self._bar = QgsMessageBar(self.window)
        return self._bar

    def __getattr__(self, name):
        return lambda *a, **k: None


def close_popups():
    for w in QApplication.topLevelWidgets():
        if w.isVisible() and w.isModal() and w.windowTitle() not in ('',):
            w.close()


def exercise(dialog, label):
    CURRENT[0] = label
    dialog.show()
    QCoreApplication.processEvents()
    tabs = dialog.findChildren(QTabWidget)
    tab_indices = [(t, i) for t in tabs for i in range(t.count())] or [(None, 0)]
    for tab, index in tab_indices:
        if tab is not None:
            tab.setCurrentIndex(index)
        for combo in dialog.findChildren(QComboBox):
            if combo.isVisible() and combo.isEnabled():
                for i in range(min(combo.count(), 6)):
                    combo.setCurrentIndex(i)
                    QCoreApplication.processEvents()
        for box in dialog.findChildren(QCheckBox) + dialog.findChildren(QRadioButton):
            if box.isVisible() and box.isEnabled():
                box.click()
                QCoreApplication.processEvents()
                box.click()
        for button in dialog.findChildren(QPushButton) + dialog.findChildren(QToolButton):
            text = button.text().lower()
            if any(w in text for w in ('fechar', 'close', 'cerrar')):
                continue
            if button.isVisible() and button.isEnabled():
                QTimer.singleShot(50, close_popups)
                button.click()
                for _ in range(5):
                    QCoreApplication.processEvents()
    dialog.hide()


import geosaga  # noqa: E402
import geosaga.i18n  # noqa: E402
geosaga.i18n.qgis_language = lambda: geosaga.i18n.normalize_language(LANG)
iface = FakeIface()
for phase in ('vazio', 'com camadas'):
    if phase == 'com camadas':
        for name in ('mapa_a.tif', 'mapa_b.tif', 'atrito.tif'):
            QgsProject.instance().addMapLayer(QgsRasterLayer(os.path.join(DATA, name), name))
        for name in ('aoi.gpkg', 'tema_a.gpkg', 'tema_c.gpkg', 'centros.gpkg'):
            QgsProject.instance().addMapLayer(QgsVectorLayer(os.path.join(DATA, name), name, 'ogr'))
    plugin = geosaga.classFactory(iface)
    plugin.initGui()
    for action in plugin.toolbar_menu.actions():
        CURRENT[0] = f'{phase}/abrir {action.text()}'
        action.trigger()
        QCoreApplication.processEvents()
    for attr in ('dialog', 'rs2_dialog', 'monitoring_dialog', 'signature_dialog',
                 'combination_dialog', 'voronoi_dialog', 'sequence_dialog'):
        dlg = getattr(plugin, attr)
        if dlg is not None:
            exercise(dlg, f'{phase}/{attr}')
    CURRENT[0] = f'{phase}/unload'
    plugin.unload()
    QCoreApplication.processEvents()

print(f'Idioma {LANG}: exceções não tratadas = {len(ERRORS)}; mensagens exibidas = {len(MESSAGES)}')
seen = set()
for where, err, tb in ERRORS:
    key = (where.split('/')[-1], err)
    if key in seen:
        continue
    seen.add(key)
    print(f'--- {where}: {err}\n{tb}')
with open(os.path.join(DATA, f'monkey_messages_{LANG}.txt'), 'w', encoding='utf-8') as fh:
    for m in MESSAGES:
        fh.write(' | '.join(m) + '\n')
sys.stdout.flush()
app.exitQgis()
os._exit(1 if ERRORS else 0)
