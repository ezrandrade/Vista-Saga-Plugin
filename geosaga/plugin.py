"""Integração Vista Saga Plugin no QGIS 4.x, com módulos incrementais."""
from pathlib import Path

from qgis.PyQt.QtGui import QAction, QIcon
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import QMessageBox, QMenu, QToolButton
from qgis.core import QgsApplication

from .provider import GeoSAGAProvider
from .i18n import tr


class VistaSagaPlugin:
    MENU = 'Vista Saga Plugin'

    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.actions = []
        self.dialog = None  # preserva estado da Avaliação, projetos v0.2+
        self.rs2_dialog = None
        self.monitoring_dialog = None
        self.signature_dialog = None
        self.combination_dialog = None
        self.voronoi_dialog = None
        self.sequence_dialog = None
        self.toolbar = None
        self.toolbar_button = None
        self.toolbar_widget_action = None
        self.modules_action = None
        self.toolbar_menu = None

    def initGui(self):
        self.provider = GeoSAGAProvider()
        if not QgsApplication.processingRegistry().addProvider(self.provider):
            self.provider = None
            raise RuntimeError(tr('Não foi possível registrar os algoritmos Vista Saga.'))

        # Uma única ação nativa com ícone e menu, reutilizada pela barra
        # clássica do QGIS e pelo menu de Complementos do próprio QGIS.
        # QRibbonSkin oculta as barras QGIS, mas importa os QMenus nativos
        # para sua guia Complementos. Não acessar classes internas do Ribbon.
        icon_path = Path(__file__).resolve().parent / 'icon.png'
        if not icon_path.is_file():
            raise RuntimeError('Vista Saga Plugin: icon.png não encontrado no pacote.')
        plugin_icon = QIcon(str(icon_path))
        for size in (16, 19, 24, 32, 48, 50, 64, 128, 512):
            candidate = icon_path.parent / 'icons' / f'icon_{size}.png'
            if candidate.is_file():
                plugin_icon.addFile(str(candidate), QSize(size, size))
        if plugin_icon.isNull() or plugin_icon.pixmap(QSize(24, 24)).isNull():
            raise RuntimeError('Vista Saga Plugin: falha ao decodificar o ícone PNG.')

        self.toolbar_menu = QMenu(self.iface.mainWindow())
        modules = (
            ('Assinatura', self.open_signature),
            ('Monitoria', self.open_monitoring),
            ('Avaliação', self.open_interactive),
            ('Análises Voronoi', self.open_voronoi),
            ('Combinação de Mapas', self.open_combination),
            ('Conversão de Formatos', self.open_rs2_converter),
            ('Sequenciador de Mapas', self.open_sequence),
        )
        for title, callback in modules:
            self._add_menu_action(title, callback)

        self.modules_action = QAction(plugin_icon, 'Vista Saga Plugin',
                                      self.iface.mainWindow())
        self.modules_action.setObjectName('vistaSagaModulesAction')
        self.modules_action.setToolTip(tr('Vista Saga Plugin — selecionar módulo'))
        self.modules_action.setMenu(self.toolbar_menu)
        # Set also on QMenu: QRibbonSkin can read the icon from the native
        # menuAction() when it builds its Ribbon groups from QGIS menus.
        self.toolbar_menu.setTitle('Vista Saga Plugin')
        self.toolbar_menu.setIcon(plugin_icon)
        self.toolbar_menu.setObjectName('vistaSagaModulesMenu')

        # Um único comando em Raster > Vista Saga Plugin, não sete ações
        # separadas. A Ribbon deve apresentar o ícone e um único menu de
        # sete módulos, sem subdividi-los em botões/overflow.
        self.iface.addPluginToRasterMenu(self.MENU, self.modules_action)

        # Registro nativo: aparece em Complementos > Vista Saga Plugin e é
        # aproveitado pelo QRibbonSkin quando ele constrói a guia Complementos.
        # O ícone não fica condicionado à visibilidade de barras QToolBar.
        self.iface.addPluginToMenu(self.MENU, self.modules_action)

        # QToolBar.addAction cria um botão nativo que herda o tamanho de ícones
        # do QGIS. Limitamos a 24 px para não ampliar a barra clássica.
        self.toolbar = self.iface.addToolBar('Vista Saga Plugin')
        if self.toolbar is None:
            raise RuntimeError('Vista Saga Plugin: não foi possível criar a barra de ferramentas.')
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

    def _add_menu_action(self, title, callback):
        action = QAction(tr(title), self.iface.mainWindow())
        action.triggered.connect(callback)
        self.toolbar_menu.addAction(action)
        self.actions.append(action)

    def open_rs2_converter(self, checked=False):
        try:
            from .rs2_dialog import RS2ConverterDialog
            if self.rs2_dialog is None:
                self.rs2_dialog = RS2ConverterDialog(self.iface, self.iface.mainWindow())
            self.rs2_dialog.show()
            self.rs2_dialog.raise_()
            self.rs2_dialog.activateWindow()
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), tr('Vista Saga — RS2'),
                                 f'Não foi possível abrir o conversor:\n{exc}')

    def open_monitoring(self, checked=False):
        try:
            from .monitoring_dialog import MonitoringDialog
            if self.monitoring_dialog is None:
                self.monitoring_dialog = MonitoringDialog(self.iface, self.iface.mainWindow())
            self.monitoring_dialog.show()
            self.monitoring_dialog.raise_()
            self.monitoring_dialog.activateWindow()
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), tr('Vista Saga — Monitoria'),
                                 f'Não foi possível abrir a monitoria:\n{exc}')

    def open_signature(self, checked=False):
        try:
            from .signature_dialog import SignatureDialog
            if self.signature_dialog is None:
                self.signature_dialog = SignatureDialog(self.iface, self.iface.mainWindow())
            self.signature_dialog.show()
            self.signature_dialog.raise_()
            self.signature_dialog.activateWindow()
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), tr('Vista Saga — Assinatura'),
                                 f'Não foi possível abrir a assinatura:\n{exc}')

    def open_combination(self, checked=False):
        try:
            from .combination_dialog import CombinationDialog
            if self.combination_dialog is None:
                self.combination_dialog = CombinationDialog(self.iface, self.iface.mainWindow())
            self.combination_dialog.show()
            self.combination_dialog.raise_()
            self.combination_dialog.activateWindow()
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), tr('Vista Saga — Combinação de Mapas'),
                                 f'Não foi possível abrir a combinação de mapas:\n{exc}')

    def open_voronoi(self, checked=False):
        try:
            from .voronoi_dialog import VoronoiDialog
            if self.voronoi_dialog is None:
                self.voronoi_dialog = VoronoiDialog(self.iface, self.iface.mainWindow())
            self.voronoi_dialog.show()
            self.voronoi_dialog.raise_()
            self.voronoi_dialog.activateWindow()
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), tr('Vista Saga — Análises Voronoi'),
                                 f'Não foi possível abrir o Voronoi:\n{exc}')

    def open_sequence(self, checked=False):
        try:
            from .image_sequence_dialog import ImageSequenceDialog
            if self.sequence_dialog is None:
                self.sequence_dialog = ImageSequenceDialog(self.iface, self.iface.mainWindow())
            self.sequence_dialog.show()
            self.sequence_dialog.raise_()
            self.sequence_dialog.activateWindow()
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), tr('Vista Saga — Sequenciador de Mapas'),
                                 f'Não foi possível abrir o Sequenciador:\n{exc}')

    def open_interactive(self, checked=False):
        try:
            from .evaluation_dialog import EvaluationDialog
            if self.dialog is None:
                self.dialog = EvaluationDialog(self.iface, self.iface.mainWindow())
            self.dialog.refresh_available()
            self.dialog.show()
            self.dialog.raise_()
            self.dialog.activateWindow()
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), tr('Vista Saga — Avaliação'),
                                 f'Não foi possível abrir a avaliação:\n{exc}')

    def open_algorithm(self, algorithm):
        try:
            # Identificadores geosaga:* mantidos para compatibilidade com projetos,
            # scripts e modelos da versão 0.2.0.
            algorithm_id = 'geosaga:' + algorithm
            if QgsApplication.processingRegistry().algorithmById(algorithm_id) is None:
                raise RuntimeError(f'O algoritmo {algorithm_id} não está registrado.')
            import processing
            processing.execAlgorithmDialog(algorithm_id, {})
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), tr('Vista Saga — Processing'),
                                 'Não foi possível abrir o módulo. Confira se o Processing '
                                 f'do QGIS está ativado.\n\n{exc}')

    def unload(self):
        if self.sequence_dialog is not None:
            self.sequence_dialog.hide()
            self.sequence_dialog.deleteLater()
            self.sequence_dialog = None
        if self.voronoi_dialog is not None:
            self.voronoi_dialog.shutdown()
            self.voronoi_dialog.hide()
            self.voronoi_dialog.deleteLater()
            self.voronoi_dialog = None
        if self.combination_dialog is not None:
            self.combination_dialog.hide()
            self.combination_dialog.deleteLater()
            self.combination_dialog = None
        if self.signature_dialog is not None:
            self.signature_dialog.hide()
            self.signature_dialog.deleteLater()
            self.signature_dialog = None
        if self.monitoring_dialog is not None:
            task = self.monitoring_dialog._task
            if task is not None:
                task.callback = None
                task.cancel()
            self.monitoring_dialog.hide()
            self.monitoring_dialog.deleteLater()
            self.monitoring_dialog = None
        if self.rs2_dialog is not None:
            self.rs2_dialog.hide()
            self.rs2_dialog.deleteLater()
            self.rs2_dialog = None
        if self.dialog is not None:
            task = self.dialog._task
            if task is not None:
                task.callback = None
                task.cancel()
            self.dialog.hide()
            self.dialog.deleteLater()
            self.dialog = None
        # Primeiro retirar a ação do menu de Complementos: evita pendências
        # visuais na Ribbon quando o Vista Saga for desativado ou atualizado.
        if self.modules_action is not None:
            self.iface.removePluginMenu(self.MENU, self.modules_action)
            self.iface.removePluginRasterMenu(self.MENU, self.modules_action)
        # O QToolBar e os botões nativos pertencem à janela do QGIS.
        if self.toolbar is not None:
            self.iface.mainWindow().removeToolBar(self.toolbar)
            self.toolbar.deleteLater()
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


# Aliás interno para integrações que importavam a classe anterior.
GeoSAGAPlugin = VistaSagaPlugin
