"""Integração Vista Saga Plugin no QGIS 4.x, com módulos incrementais."""
from qgis.PyQt.QtGui import QAction
from qgis.PyQt.QtWidgets import QMessageBox, QStyle
from qgis.core import QgsApplication

from .provider import GeoSAGAProvider


class VistaSagaPlugin:
    MENU = 'Vista Saga Plugin'

    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.actions = []
        self.dialog = None  # preserva estado da Avaliação Espacial, projetos v0.2+
        self.home_dialog = None
        self.rs2_dialog = None
        self.monitoring_dialog = None
        self.signature_dialog = None
        self.combination_dialog = None
        self.voronoi_dialog = None
        self.sequence_dialog = None
        self.toolbar_action = None

    def initGui(self):
        self.provider = GeoSAGAProvider()
        if not QgsApplication.processingRegistry().addProvider(self.provider):
            self.provider = None
            raise RuntimeError('Não foi possível registrar os algoritmos Vista Saga.')

        self._add_menu_action('Painel de módulos', self.open_home, toolbar=True)
        self._add_menu_action('Avaliação Espacial', self.open_interactive)
        self._add_menu_action('Conversor RS2 / GeoTIFF / Vetor', self.open_rs2_converter)
        # A Avaliação Espacial utiliza exclusivamente a interface própria no menu.
        # O algoritmo geosaga:avaliacao permanece registrado por compatibilidade
        # com modelos/scripts e arquivos de projeto antigos.
        self._add_menu_action('Monitoria Espacial', self.open_monitoring)
        self._add_menu_action('Assinatura Espacial', self.open_signature)
        self._add_menu_action('Combinação de Mapas', self.open_combination)
        self._add_menu_action('Análises Voronoi', self.open_voronoi)
        self._add_menu_action('Sequenciador de Mapas', self.open_sequence)

    def _add_menu_action(self, title, callback, toolbar=False):
        action = QAction(title, self.iface.mainWindow())
        action.triggered.connect(callback)
        self.iface.addPluginToRasterMenu(self.MENU, action)
        if toolbar:
            action.setToolTip('Vista Saga Plugin — painel de módulos')
            action.setIcon(self.iface.mainWindow().style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogDetailedView))
            self.iface.addToolBarIcon(action)
            self.toolbar_action = action
        self.actions.append(action)

    def open_home(self, checked=False):
        try:
            from .home_dialog import HomeDialog
            if self.home_dialog is None:
                self.home_dialog = HomeDialog(self, self.iface.mainWindow())
            self.home_dialog.show()
            self.home_dialog.raise_()
            self.home_dialog.activateWindow()
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), 'Vista Saga — Interface',
                                 f'Não foi possível abrir o painel:\n{exc}')

    def open_rs2_converter(self, checked=False):
        try:
            from .rs2_dialog import RS2ConverterDialog
            if self.rs2_dialog is None:
                self.rs2_dialog = RS2ConverterDialog(self.iface, self.iface.mainWindow())
            self.rs2_dialog.show()
            self.rs2_dialog.raise_()
            self.rs2_dialog.activateWindow()
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), 'Vista Saga — RS2',
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
            QMessageBox.critical(self.iface.mainWindow(), 'Vista Saga — Monitoria Espacial',
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
            QMessageBox.critical(self.iface.mainWindow(), 'Vista Saga — Assinatura Espacial',
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
            QMessageBox.critical(self.iface.mainWindow(), 'Vista Saga — Combinação de Mapas',
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
            QMessageBox.critical(self.iface.mainWindow(), 'Vista Saga — Análises Voronoi',
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
            QMessageBox.critical(self.iface.mainWindow(), 'Vista Saga — Sequenciador de Mapas',
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
            QMessageBox.critical(self.iface.mainWindow(), 'Vista Saga — Avaliação Espacial',
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
            QMessageBox.critical(self.iface.mainWindow(), 'Vista Saga — Processing',
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
        if self.home_dialog is not None:
            self.home_dialog.hide()
            self.home_dialog.deleteLater()
            self.home_dialog = None
        if self.toolbar_action is not None:
            self.iface.removeToolBarIcon(self.toolbar_action)
            self.toolbar_action = None
        for action in self.actions:
            self.iface.removePluginRasterMenu(self.MENU, action)
            action.deleteLater()
        self.actions.clear()
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None


# Aliás interno para integrações que importavam a classe anterior.
GeoSAGAPlugin = VistaSagaPlugin
