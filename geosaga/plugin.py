"""Integração do Vista Saga Plugin ao QGIS 4.x: menu único com sete módulos."""
import importlib
from pathlib import Path

from qgis.PyQt.QtGui import QAction, QIcon
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import QMessageBox, QMenu, QToolButton
from qgis.core import QgsApplication

from .errors import log_exception
from .provider import GeoSAGAProvider
from .i18n import tr

# (atributo, módulo, classe, título no menu, método público). A ordem define o menu.
MODULES = (
    ('signature_dialog', 'signature_dialog', 'SignatureDialog', 'Assinatura', 'open_signature'),
    ('monitoring_dialog', 'monitoring_dialog', 'MonitoringDialog', 'Monitoria', 'open_monitoring'),
    ('dialog', 'evaluation_dialog', 'EvaluationDialog', 'Avaliação', 'open_interactive'),
    ('voronoi_dialog', 'voronoi_dialog', 'VoronoiDialog', 'Análises Voronoi', 'open_voronoi'),
    ('combination_dialog', 'combination_dialog', 'CombinationDialog', 'Combinação de Mapas', 'open_combination'),
    ('rs2_dialog', 'rs2_dialog', 'RS2ConverterDialog', 'Conversão de Formatos', 'open_rs2_converter'),
    ('sequence_dialog', 'image_sequence_dialog', 'ImageSequenceDialog', 'Sequenciador de Mapas', 'open_sequence'),
)

# Ícone de cada módulo no menu suspenso (SVG em icons/modulos/), pelo método que o abre.
# Ficam fora de MODULES porque o código desempacota essa tabela pela posição.
MODULE_ICONS = {
    'open_signature': 'assinatura_espacial.svg',
    'open_monitoring': 'monitoria_espacial.svg',
    'open_interactive': 'avaliacao_espacial.svg',
    'open_voronoi': 'analises_voronoi.svg',
    'open_combination': 'combinacao_mapas.svg',
    'open_rs2_converter': 'conversor.svg',
    'open_sequence': 'sequenciador_mapas.svg',
}
MODULE_ICON_DIR = Path(__file__).resolve().parent / 'icons' / 'modulos'


def module_icon(method):
    """QIcon do módulo; ícone vazio (o item continua no menu) se o arquivo faltar."""
    name = MODULE_ICONS.get(method)
    path = MODULE_ICON_DIR / name if name else None
    return QIcon(str(path)) if path is not None and path.is_file() else QIcon()


class VistaSagaPlugin:
    MENU = 'Vista Saga Plugin'

    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.actions = []
        self.toolbar = None
        self.toolbar_button = None
        self.toolbar_widget_action = None
        self.modules_action = None
        self.toolbar_menu = None
        # Uma instância por módulo: preserva o estado entre aberturas.
        for attribute, *_rest in MODULES:
            setattr(self, attribute, None)

    # ------------------------------------------------------------ interface
    def initGui(self):
        self.provider = GeoSAGAProvider()
        if not QgsApplication.processingRegistry().addProvider(self.provider):
            self.provider = None
            raise RuntimeError(tr('Não foi possível registrar os algoritmos Vista Saga.'))

        icon_path = Path(__file__).resolve().parent / 'icon.png'
        plugin_icon = QIcon(str(icon_path))
        for size in (16, 19, 24, 32, 48, 50, 64, 128, 512):
            candidate = icon_path.parent / 'icons' / f'icon_{size}.png'
            if candidate.is_file():
                plugin_icon.addFile(str(candidate), QSize(size, size))
        # Ícone ausente não deve impedir o uso dos módulos: QAction aceita QIcon nulo.

        self.toolbar_menu = QMenu(self.iface.mainWindow())
        for *_spec, title, method in MODULES:
            action = QAction(module_icon(method), tr(title), self.iface.mainWindow())
            action.triggered.connect(getattr(self, method))
            self.toolbar_menu.addAction(action)
            self.actions.append(action)

        # Uma única ação nativa com ícone e submenu, reutilizada pela barra
        # clássica e pelos menus Raster/Complementos. QRibbonSkin constrói sua
        # guia a partir desses menus nativos; não há dependência do Ribbon.
        self.modules_action = QAction(plugin_icon, 'Vista Saga Plugin', self.iface.mainWindow())
        self.modules_action.setObjectName('vistaSagaModulesAction')
        self.modules_action.setToolTip(tr('Vista Saga Plugin — selecionar módulo'))
        self.modules_action.setMenu(self.toolbar_menu)
        self.toolbar_menu.setTitle('Vista Saga Plugin')
        self.toolbar_menu.setIcon(plugin_icon)
        self.toolbar_menu.setObjectName('vistaSagaModulesMenu')
        self.iface.addPluginToRasterMenu(self.MENU, self.modules_action)
        self.iface.addPluginToMenu(self.MENU, self.modules_action)

        self.toolbar = self.iface.addToolBar('Vista Saga Plugin')
        if self.toolbar is not None:
            self.toolbar.setObjectName('VistaSagaPluginToolbar')
            self.toolbar.setWindowTitle('Vista Saga Plugin')
            self.toolbar.setIconSize(QSize(24, 24))
            self.toolbar_widget_action = self.toolbar.addAction(self.modules_action)
            self.toolbar_button = self.toolbar.widgetForAction(self.modules_action)
            if isinstance(self.toolbar_button, QToolButton):
                self.toolbar_button.setObjectName('vistaSagaModulesButton')
                self.toolbar_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
                self.toolbar_button.setAutoRaise(True)
            self.toolbar.setVisible(True)

    def _open_dialog(self, attribute, module, class_name, title):
        """Abre (ou traz à frente) o diálogo do módulo, sem derrubar o QGIS."""
        try:
            dialog = getattr(self, attribute)
            if dialog is None:
                cls = getattr(importlib.import_module(f'{__package__}.{module}'), class_name)
                dialog = cls(self.iface, self.iface.mainWindow())
                setattr(self, attribute, dialog)
            if hasattr(dialog, 'refresh_available'):
                dialog.refresh_available()
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
        except Exception as exc:
            log_exception(f'Abrir módulo: {title}')
            QMessageBox.critical(
                self.iface.mainWindow(), tr(tr('Vista Saga Plugin — {module}').format(module=tr(title))),
                tr(tr('Não foi possível abrir o módulo. Detalhes técnicos foram registrados no '
                   'painel de mensagens do QGIS (aba Vista Saga Plugin).') + f'\n\n{tr(str(exc))}'))

    def _open_module(self, method):
        attribute, module, class_name, title, _method = next(m for m in MODULES if m[4] == method)
        self._open_dialog(attribute, module, class_name, title)

    # API pública preservada (scripts, painel antigo e testes de compatibilidade).
    def open_signature(self, checked=False):
        self._open_module('open_signature')

    def open_monitoring(self, checked=False):
        self._open_module('open_monitoring')

    def open_interactive(self, checked=False):
        self._open_module('open_interactive')

    def open_voronoi(self, checked=False):
        self._open_module('open_voronoi')

    def open_combination(self, checked=False):
        self._open_module('open_combination')

    def open_rs2_converter(self, checked=False):
        self._open_module('open_rs2_converter')

    def open_sequence(self, checked=False):
        self._open_module('open_sequence')

    def open_algorithm(self, algorithm):
        """Abre o diálogo Processing de um algoritmo geosaga:* (identificadores históricos)."""
        try:
            algorithm_id = 'geosaga:' + algorithm
            if QgsApplication.processingRegistry().algorithmById(algorithm_id) is None:
                raise RuntimeError(tr('O algoritmo {algorithm} não está registrado.').format(algorithm=algorithm_id))
            import processing
            processing.execAlgorithmDialog(algorithm_id, {})
        except Exception as exc:
            log_exception(f'Abrir algoritmo {algorithm}')
            QMessageBox.critical(self.iface.mainWindow(), tr('Vista Saga — Processing'),
                                 tr('Não foi possível abrir o módulo. Confira se o Processing do QGIS está ativado.')
                                 + f'\n\n{tr(str(exc))}')

    # --------------------------------------------------------------- descarga
    def _dispose_dialog(self, attribute):
        dialog = getattr(self, attribute, None)
        setattr(self, attribute, None)
        if dialog is None:
            return
        try:
            shutdown = getattr(dialog, 'shutdown', None)
            if callable(shutdown):
                shutdown()
            dialog.hide()
            dialog.deleteLater()
        except Exception:  # a descarga dos demais módulos deve prosseguir
            log_exception(f'Descarregar {attribute}')

    def unload(self):
        for attribute, *_rest in MODULES:
            self._dispose_dialog(attribute)
        try:
            if self.modules_action is not None:
                self.iface.removePluginMenu(self.MENU, self.modules_action)
                self.iface.removePluginRasterMenu(self.MENU, self.modules_action)
            if self.toolbar is not None:
                self.iface.mainWindow().removeToolBar(self.toolbar)
                self.toolbar.deleteLater()
        except Exception:
            log_exception('Remover menus e barra de ferramentas')
        self.toolbar = None
        self.toolbar_button = None
        self.toolbar_widget_action = None
        if self.modules_action is not None:
            self.modules_action.deleteLater()
            self.modules_action = None
        for action in self.actions:
            action.deleteLater()
        self.actions.clear()
        if self.toolbar_menu is not None:
            self.toolbar_menu.deleteLater()
            self.toolbar_menu = None
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None


# Alias interno para integrações que importavam a classe anterior.
GeoSAGAPlugin = VistaSagaPlugin
