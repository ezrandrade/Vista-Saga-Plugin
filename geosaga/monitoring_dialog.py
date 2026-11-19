"""Monitoria — interface nativa QGIS 4.x, sem formulários Processing."""
from .i18n import tr
from pathlib import Path
import traceback

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QDialog, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMessageBox, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QTabWidget, QWidget, QToolButton, QScrollArea, QFrame,
)
from qgis.core import (Qgis, QgsApplication, QgsPalettedRasterRenderer,
                       QgsProject, QgsRasterLayer, QgsMessageLog)
from qgis.gui import QgsMapLayerComboBox
from .ui_shared import use_tab_background, temporary_destination, enable_table_copy
from .ui_shared import RUN_TEXT, FooterStatus, TaskProgressWindow, report_outcome


RASTER_MONITORING_HINT = (
    'Em branco, o mapa de transições é gravado num arquivo temporário e carregado no QGIS '
    '(o QGIS não mantém rasters em memória; salve-o antes de fechar o QGIS). Com um arquivo '
    'indicado, ele é salvo em disco e carregado no QGIS. Na mesma pasta são gerados '
    '_transicoes.csv, _matriz.csv e _resumo.txt; sem arquivo indicado, eles ficam na pasta '
    'temporária do QGIS.')

from .raster_engine import file_source
from .monitoring_task import MonitoringTask
from .errors import log_exception


class MonitoringDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self._task = None
        self.setWindowTitle(tr('Vista Saga Plugin - Monitoria'))
        self.setMinimumSize(700, 445)
        self.resize(840, 565)
        self.setModal(False)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(9, 9, 9, 9)
        outer.setSpacing(7)
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, 1)
        self.config_tab = QScrollArea()
        self.config_tab.setWidgetResizable(True)
        self.config_tab.setFrameShape(QFrame.Shape.NoFrame)
        holder = QWidget()
        self.config_tab.setWidget(holder)
        use_tab_background(self.config_tab)
        self.results_tab = QTabWidget()
        self.raster_results_page = QWidget()
        self.results_tab.addTab(self.raster_results_page, tr('Raster'))
        self.tabs.addTab(self.config_tab, tr('Raster'))
        # A aba Vetorial mostra diretamente os dois períodos e seus campos,
        # sem abrir uma janela secundária.
        self.vector_tab = QScrollArea()
        self.vector_tab.setWidgetResizable(True)
        self.vector_tab.setFrameShape(QFrame.Shape.NoFrame)
        self.tabs.addTab(self.vector_tab, tr('Vetorial'))
        self.tabs.addTab(self.results_tab, tr('Resultados'))
        config = QVBoxLayout(holder)
        config.setContentsMargins(9, 9, 9, 9)
        config.setSpacing(8)
        maps = QHBoxLayout()
        maps.setSpacing(8)
        self.before_layer, self.before_file, self.before_label = self._make_input_group(
            maps, 'Mapa inicial', 'Período', 'Inicial')
        self.after_layer, self.after_file, self.after_label = self._make_input_group(
            maps, 'Mapa final', 'Período', 'Final')
        config.addLayout(maps)
        self._vector_dialog = None

        output_group = QGroupBox(tr('Resultado'))
        layout = QFormLayout(output_group)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(tr('Ex.: Mudanças de uso da terra - 1985–2024'))
        layout.addRow(tr('Título do estudo:'), self.title_edit)
        path_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        # Em branco: arquivo temporário; preenchido: salvo nesse arquivo.
        # Nos dois casos o mapa de transições é carregado no QGIS.
        self.output_edit.setPlaceholderText(tr('[Arquivo temporário]'))
        self.output_edit.setClearButtonEnabled(True)
        path_row.addWidget(self.output_edit, 1)
        browse = QPushButton(tr('Procurar…'))
        browse.clicked.connect(self._choose_output)
        path_row.addWidget(browse)
        layout.addRow(tr('Salvar em:'), path_row)
        hint = QLabel(tr(RASTER_MONITORING_HINT))
        hint.setWordWrap(True)
        layout.addRow('', hint)
        config.addWidget(output_group)

        self.advanced_toggle = QToolButton()
        self.advanced_toggle.setText(tr('Opções avançadas: legenda'))
        self.advanced_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.advanced_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setChecked(False)
        config.addWidget(self.advanced_toggle)
        custom_group = QGroupBox(tr('Legenda das transições'))
        controls = QFormLayout(custom_group)
        self.legend_style = QComboBox()
        self.legend_style.addItems([tr('Descritiva: Permaneceu / Deixou de ser → Tornou-se'),
                                    tr('Códigos: classe inicial → classe final')])
        controls.addRow(tr('Legenda das transições:'), self.legend_style)
        lookup_row = QHBoxLayout()
        self.legend_lookup = QLineEdit()
        self.legend_lookup.setPlaceholderText(tr('Opcional: CSV com PERIODO;CODIGO;CLASSE'))
        lookup_row.addWidget(self.legend_lookup, 1)
        lookup_btn = QPushButton(tr('CSV…'))
        lookup_btn.clicked.connect(self._choose_legend_lookup)
        lookup_row.addWidget(lookup_btn)
        controls.addRow(tr('Nomes das classes:'), lookup_row)
        config.addWidget(custom_group)
        custom_group.setVisible(False)
        self.advanced_toggle.toggled.connect(custom_group.setVisible)
        self.advanced_toggle.toggled.connect(
            lambda visible: self.advanced_toggle.setArrowType(
                Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow))
        config.addStretch(1)

        results_group = QGroupBox(tr('Resumo da monitoria'))
        results = QVBoxLayout(results_group)
        self.summary = QLabel(tr('Nenhuma monitoria executada nesta sessão.'))
        self.summary.setWordWrap(True)
        results.addWidget(self.summary)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([tr('ID'), tr('Inicial → Final'), tr('Situação'), tr('Pixels'), tr('% válidos')])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        enable_table_copy(self.table)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        results.addWidget(self.table)
        results_layout = QVBoxLayout(self.raster_results_page)
        results_layout.addWidget(results_group, 1)

        # Rodapé padrão (1.4.1): [Executar] [Fechar]. O "Executar" da guia Vetorial é o botão do
        # formulário vetorial, trazido para cá quando a guia é aberta; o progresso e o Cancelar ficam
        # numa janela que aparece só durante a execução.
        bottom = QHBoxLayout()
        self.status = FooterStatus(tr('Pronto para executar.'))
        self._progress_window = None
        bottom.addStretch(1)
        self.run_button = QPushButton(tr(RUN_TEXT))
        self.run_button.clicked.connect(self.run)
        bottom.addWidget(self.run_button)
        self.close_button = QPushButton(tr('Fechar'))
        self.close_button.clicked.connect(self.close)
        bottom.addWidget(self.close_button)
        outer.addLayout(bottom)
        self._footer = bottom
        self.tabs.currentChanged.connect(self._on_mode_changed)

    def _on_mode_changed(self, index):
        if index == 1:
            self._open_vector_monitoring()
        # A execução raster não deve ser oferecida enquanto uma configuração
        # vetorial estiver visível; cada modalidade mantém seu próprio comando.
        is_raster = index == 0
        self.run_button.setVisible(is_raster)
        if self._vector_dialog is not None:
            self._vector_dialog.run_button.setVisible(not is_raster)

    def _open_vector_monitoring(self):
        if self._vector_dialog is None:
            try:
                from .vector_monitoring_dialog import VectorMonitoringDialog
                dialog = VectorMonitoringDialog(self.iface, parent=self, embedded=True)
                dialog.setMinimumSize(0, 0)
                # Share the results area without opening a secondary window.
                results_page = dialog.tabs.widget(1)
                dialog.tabs.removeTab(1)
                dialog.tabs.tabBar().hide()
                self.results_tab.addTab(results_page, tr('Vetorial'))
                dialog._embedded_results_host = (self.results_tab, self.tabs)
                dialog.close_button.hide()
                # O "Executar" vetorial vai para o rodapé comum, ao lado do "Fechar".
                self._footer.insertWidget(self._footer.indexOf(self.close_button), dialog.run_button)
                self.vector_tab.setWidget(dialog)
                use_tab_background(self.vector_tab)
                self._vector_dialog = dialog
            except Exception:
                log_exception()
                details = traceback.format_exc()
                QgsMessageLog.logMessage(details, 'Vista Saga Plugin', Qgis.MessageLevel.Critical)
                if self.vector_tab.widget() is not None:
                    old = self.vector_tab.takeWidget()
                    old.deleteLater()
                error = QLabel('Erro ao iniciar Monitoria vetorial. Consulte as mensagens '
                               'de log do QGIS, na seção Vista Saga Plugin.\n\n'
                               + details.splitlines()[-1])
                error.setWordWrap(True)
                self.vector_tab.setWidget(error)
                use_tab_background(self.vector_tab)
                return
        self._vector_dialog.show()

    def _make_input_group(self, outer, heading, period_caption, placeholder):
        group = QGroupBox(tr(heading))
        form = QFormLayout(group)
        combo = QgsMapLayerComboBox()
        combo.setFilters(Qgis.LayerFilter.RasterLayer)
        combo.setAllowEmptyLayer(True)
        combo.setShowCrs(True)
        form.addRow(tr('Camada no QGIS:'), combo)
        file_edit = QLineEdit()
        file_edit.setPlaceholderText(tr('Opcional: arquivo local .tif, .img, .vrt ou outro raster GDAL'))
        file_row = QHBoxLayout()
        file_row.addWidget(file_edit, 1)
        browse = QPushButton(tr('Arquivo…'))
        browse.clicked.connect(lambda checked=False, field=file_edit: self._choose_input(field))
        file_row.addWidget(browse)
        form.addRow(tr('Ou arquivo:'), file_row)
        file_edit.setToolTip(tr('Quando preenchido, o caminho do arquivo tem prioridade sobre a camada selecionada.'))
        period = QLineEdit(tr(placeholder))
        form.addRow(tr(period_caption + ':'), period)
        outer.addWidget(group)
        return combo, file_edit, period

    def _choose_legend_lookup(self):
        path, _ = QFileDialog.getOpenFileName(self, tr('Tabela de nomes das classes'), '',
                                              tr('CSV (*.csv);;Todos os arquivos (*)'))
        if path:
            self.legend_lookup.setText(path)

    def _choose_input(self, target):
        path, _ = QFileDialog.getOpenFileName(
            self, tr('Selecionar raster categórico'), '',
            tr('Mapas raster (*.tif *.tiff *.img *.vrt *.asc);;Todos os arquivos (*)'))
        if path:
            target.setText(path)

    def _choose_output(self):
        path, _ = QFileDialog.getSaveFileName(self, tr('Salvar mapa de transições'),
                                              self.output_edit.text().strip() or 'monitoria.tif',
                                              'GeoTIFF (*.tif)')
        if path:
            if not path.lower().endswith(('.tif', '.tiff')):
                path += '.tif'
            self.output_edit.setText(path)

    def _selected_file(self, layer_selector, file_edit):
        typed = file_edit.text().strip()
        if typed:
            return file_source(typed)
        layer = layer_selector.currentLayer()
        if layer is None:
            raise ValueError('Selecione uma camada carregada ou indique um arquivo no disco em cada período.')
        return file_source(layer.source())

    def run(self):
        if self._task is not None:
            return
        try:
            before = self._selected_file(self.before_layer, self.before_file)
            after = self._selected_file(self.after_layer, self.after_file)
            chosen = self.output_edit.text().strip()
            output = chosen or temporary_destination('monitoria_raster', '.tif')
            if not output.lower().endswith(('.tif', '.tiff')):
                raise ValueError('A saída deve ter extensão .tif ou .tiff.')
            basename = Path(output).with_suffix('')
            others = [output, str(basename) + '_transicoes.csv',
                      str(basename) + '_matriz.csv', str(basename) + '_resumo.txt']
            existing = [p for p in others if Path(p).exists()]
            if existing:
                choice = QMessageBox.question(
                    self, tr('Sobrescrever resultados'),
                    tr(f'Já existem {len(existing)} arquivos de saída. Deseja substituí-los?\n'
                    'Os arquivos anteriores serão preservados se a análise falhar.'),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)
                if choice != QMessageBox.StandardButton.Yes:
                    return
            self._task = MonitoringTask(before, after, output,
                                        self.before_label.text().strip() or 'Inicial',
                                        self.after_label.text().strip() or 'Final',
                                        self.title_edit.text().strip(), self._finished,
                                        descriptive_legend=(self.legend_style.currentIndex() == 0),
                                        legend_lookup=self.legend_lookup.text().strip())
            self.run_button.setEnabled(False)
            self.close_button.setEnabled(False)
            self.status.setText(tr('Monitoria em execução. Contando e classificando transições…'))
            self._progress_window = TaskProgressWindow(
                self, 'Monitoria em execução. Contando e classificando transições…', self._task)
            QgsApplication.taskManager().addTask(self._task)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, tr('Vista Saga - Monitoria'), tr(str(exc)))

    def cancel(self):
        if self._task is not None:
            self._task.cancel()
            self.status.setText(tr('Solicitação de cancelamento enviada…'))

    def _finished(self, success, task):
        self._task = None
        if self._progress_window is not None:
            self._progress_window.close()
            self._progress_window = None
        self.run_button.setEnabled(True)
        self.close_button.setEnabled(True)
        if not success:
            text = tr('Monitoria cancelada.' if task.isCanceled() else 'Falha na monitoria.')
            if task.error:
                self.status.setText(text)
                QMessageBox.warning(self, tr('Monitoria não concluída'), tr(task.error))
            else:
                report_outcome(self.status, 'Monitoria', text, 'warning')
            return
        summary = task.result
        report_outcome(self.status, 'Monitoria', tr('Monitoria concluída. GeoTIFF, CSVs e TXT gravados.'), 'success')
        self.results_tab.setCurrentIndex(0)
        self.tabs.setCurrentWidget(self.results_tab)
        self.summary.setText(
            tr(f'Pixels válidos: {summary["validos"]:,} | '
            f'Permanências: {summary["permanencias"]:,} ({summary["pct_permanencia"]:.2f}%) | '
            f'Mudanças: {summary["mudancas"]:,} ({summary["pct_mudanca"]:.2f}%) | '
            f'Excluídos (NoData): {summary["invalidos"]:,}'))
        self.table.setRowCount(0)
        for row in summary['linhas'][:500]:
            line = self.table.rowCount()
            self.table.insertRow(line)
            for column, value in enumerate((row['id'],
                                             f"{row['inicial']:g} → {row['final']:g}",
                                             row['situacao'], row['pixels'],
                                             f"{row['percentual']:.3f}%")):
                cell = QTableWidgetItem(str(value))
                cell.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(line, column, cell)
        if len(summary['linhas']) > 500:
            report_outcome(self.status, 'Monitoria',
                           tr('Concluído. Prévia limitada a 500 transições; CSV completo disponível.'), 'info')
        # O mapa de transições é sempre carregado no QGIS.
        layer = QgsRasterLayer(summary['mapa'], Path(summary['mapa']).stem)
        if layer.isValid():
            # Paleta pequena para leitura direta no painel de camadas:
            # permanências cinza; alterações com matizes distintos.
            if len(summary['linhas']) <= 128:
                try:
                    classes = []
                    for item in summary['linhas']:
                        hue = (int(item['id']) * 53) % 360
                        color = (QColor('#b9c2c7') if item['situacao'] == 'Permanência'
                                 else QColor.fromHsv(hue, 160, 205))
                        caption = (item['legenda'] if self.legend_style.currentIndex() == 0
                                   else f"{item['inicial']:g} → {item['final']:g}")
                        classes.append(QgsPalettedRasterRenderer.Class(item['id'], color, caption))
                    layer.setRenderer(QgsPalettedRasterRenderer(layer.dataProvider(), 1, classes))
                except (TypeError, RuntimeError, AttributeError):
                    pass  # a rasterização e os relatórios não dependem da paleta Qt
            QgsProject.instance().addMapLayer(layer)
        else:
            QMessageBox.warning(self, tr('Monitoria concluída'),
                                tr('Os arquivos foram gravados, mas não foi possível adicionar o mapa ao QGIS.'))

    def shutdown(self):
        """Descarga do plugin: cancela a tarefa e impede callbacks em janela destruída."""
        task, self._task = self._task, None
        if self._progress_window is not None:
            self._progress_window.close()
            self._progress_window = None
        if task is not None:
            task.callback = None
            try:
                task.progressChanged.disconnect()
            except (TypeError, RuntimeError):
                pass  # sem conexões ou objeto C++ já liberado
            task.cancel()

    def closeEvent(self, event):
        if getattr(self._vector_dialog, '_busy', False):
            QMessageBox.information(self, tr('Monitoria em andamento'),
                                    tr('Aguarde a conclusão da monitoria vetorial antes de fechar.'))
            event.ignore()
            return
        if self._task is not None:
            QMessageBox.information(self, tr('Monitoria em andamento'),
                                    tr('Cancele ou aguarde o término da tarefa antes de fechar.'))
            event.ignore()
        else:
            super().closeEvent(event)
