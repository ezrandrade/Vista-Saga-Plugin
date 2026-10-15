"""Monitoria — interface nativa QGIS 4.x, sem formulários Processing."""
from pathlib import Path
import traceback
import re

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMessageBox, QProgressBar, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QTabWidget, QWidget, QToolButton, QScrollArea, QFrame,
)
from qgis.core import (Qgis, QgsApplication, QgsPalettedRasterRenderer,
                       QgsProject, QgsRasterLayer, QgsMessageLog)
from qgis.gui import QgsMapLayerComboBox
from .ui_shared import temporary_destination

from .raster_engine import file_source
from .monitoring_task import MonitoringTask


class MonitoringDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self._task = None
        self.setWindowTitle('Vista Saga Plugin — Monitoria')
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
        self.results_tab = QTabWidget()
        self.raster_results_page = QWidget()
        self.results_tab.addTab(self.raster_results_page, 'Raster')
        self.tabs.addTab(self.config_tab, 'Raster')
        # A aba Vetorial mostra diretamente os dois períodos e seus campos,
        # sem abrir uma janela secundária.
        self.vector_tab = QScrollArea()
        self.vector_tab.setWidgetResizable(True)
        self.vector_tab.setFrameShape(QFrame.Shape.NoFrame)
        self.tabs.addTab(self.vector_tab, 'Vetorial')
        self.tabs.addTab(self.results_tab, 'Resultados')
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

        output_group = QGroupBox('Saída da análise')
        layout = QFormLayout(output_group)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText('Ex.: Mudanças de uso da terra — 1985–2024')
        layout.addRow('Título do estudo:', self.title_edit)
        path_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText('Caminho de saída do GeoTIFF (.tif)')
        path_row.addWidget(self.output_edit, 1)
        browse = QPushButton('Procurar…')
        browse.clicked.connect(self._choose_output)
        path_row.addWidget(browse)
        layout.addRow('Mapa de transições:', path_row)
        hint = QLabel('Arquivos gerados automaticamente na mesma pasta: '
                      '_transicoes.csv, _matriz.csv e _resumo.txt.')
        hint.setWordWrap(True)
        layout.addRow('', hint)
        self.temporary_check = QCheckBox('Resultado temporário no QGIS (pode salvar depois)')
        self.temporary_check.setChecked(True)
        layout.addRow('', self.temporary_check)
        self.output_edit.setEnabled(False)
        self.temporary_check.toggled.connect(lambda active: self.output_edit.setEnabled(not active))
        self.load_check = QCheckBox('Adicionar mapa de transições ao projeto QGIS')
        self.load_check.setChecked(True)
        layout.addRow('', self.load_check)
        config.addWidget(output_group)

        self.advanced_toggle = QToolButton()
        self.advanced_toggle.setText('Opções avançadas: legenda e série temporal')
        self.advanced_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.advanced_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setChecked(False)
        config.addWidget(self.advanced_toggle)
        custom_group = QGroupBox('Legenda e tendência temporal')
        controls = QFormLayout(custom_group)
        self.legend_style = QComboBox()
        self.legend_style.addItems(['Descritiva: Permaneceu / Deixou de ser → Tornou-se',
                                    'Códigos: classe inicial → classe final'])
        controls.addRow('Legenda das transições:', self.legend_style)
        lookup_row = QHBoxLayout()
        self.legend_lookup = QLineEdit()
        self.legend_lookup.setPlaceholderText('Opcional: CSV com PERIODO;CODIGO;CLASSE')
        lookup_row.addWidget(self.legend_lookup, 1)
        lookup_btn = QPushButton('CSV…')
        lookup_btn.clicked.connect(self._choose_legend_lookup)
        lookup_row.addWidget(lookup_btn)
        controls.addRow('Nomes das classes:', lookup_row)
        self.series_check = QCheckBox('Adicionar mapas de outros anos para Mann–Kendall')
        controls.addRow('', self.series_check)
        self.series_table = QTableWidget(0, 2)
        self.series_table.setHorizontalHeaderLabels(['Ano (AAAA)', 'Arquivo raster adicional'])
        self.series_table.verticalHeader().setVisible(False)
        self.series_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.series_table.setMaximumHeight(110)
        controls.addRow('Série temporal:', self.series_table)
        buttons = QHBoxLayout()
        add = QPushButton('Adicionar rasters…')
        add.clicked.connect(self._add_temporal)
        remove = QPushButton('Remover selecionados')
        remove.clicked.connect(self._remove_temporal)
        buttons.addWidget(add)
        buttons.addWidget(remove)
        controls.addRow('', buttons)
        self.series_table.setVisible(False)
        add.setVisible(False)
        remove.setVisible(False)
        self.series_check.toggled.connect(self.series_table.setVisible)
        self.series_check.toggled.connect(add.setVisible)
        self.series_check.toggled.connect(remove.setVisible)
        note = QLabel('Mann–Kendall só será calculado com 5 ou mais datas válidas; '
                      '8–10 ou mais são recomendadas. Com duas datas, o relatório informa “não aplicável”.')
        note.setWordWrap(True)
        controls.addRow('', note)
        config.addWidget(custom_group)
        custom_group.setVisible(False)
        self.advanced_toggle.toggled.connect(custom_group.setVisible)
        self.advanced_toggle.toggled.connect(
            lambda visible: self.advanced_toggle.setArrowType(
                Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow))
        config.addStretch(1)

        results_group = QGroupBox('Resumo da monitoria')
        results = QVBoxLayout(results_group)
        self.summary = QLabel('Nenhuma monitoria executada nesta sessão.')
        self.summary.setWordWrap(True)
        results.addWidget(self.summary)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['ID', 'Inicial → Final', 'Situação', 'Pixels', '% válidos'])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        results.addWidget(self.table)
        results_layout = QVBoxLayout(self.raster_results_page)
        results_layout.addWidget(results_group, 1)

        bottom = QHBoxLayout()
        self.status = QLabel('Pronto para executar.')
        self.status.setWordWrap(True)
        bottom.addWidget(self.status, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        bottom.addWidget(self.progress)
        self.run_button = QPushButton('Executar monitoria')
        self.run_button.clicked.connect(self.run)
        bottom.addWidget(self.run_button)
        self.cancel_button = QPushButton('Cancelar')
        self.cancel_button.clicked.connect(self.cancel)
        self.cancel_button.setEnabled(False)
        bottom.addWidget(self.cancel_button)
        self.close_button = QPushButton('Fechar')
        self.close_button.clicked.connect(self.close)
        bottom.addWidget(self.close_button)
        outer.addLayout(bottom)
        self.tabs.currentChanged.connect(self._on_mode_changed)

    def _on_mode_changed(self, index):
        if index == 1:
            self._open_vector_monitoring()
        # A execução raster não deve ser oferecida enquanto uma configuração
        # vetorial estiver visível; cada modalidade mantém seu próprio comando.
        is_raster = index == 0
        for control in (self.status, self.progress, self.run_button, self.cancel_button):
            control.setVisible(is_raster)

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
                self.results_tab.addTab(results_page, 'Vetorial')
                dialog._embedded_results_host = (self.results_tab, self.tabs)
                for control in dialog.findChildren(QPushButton):
                    if control.text() == 'Fechar':
                        control.hide()
                self.vector_tab.setWidget(dialog)
                self._vector_dialog = dialog
            except Exception:
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
                return
        self._vector_dialog.show()

    def _make_input_group(self, outer, heading, period_caption, placeholder):
        group = QGroupBox(heading)
        form = QFormLayout(group)
        combo = QgsMapLayerComboBox()
        combo.setFilters(Qgis.LayerFilter.RasterLayer)
        combo.setAllowEmptyLayer(True)
        combo.setShowCrs(True)
        form.addRow('Camada carregada:', combo)
        file_edit = QLineEdit()
        file_edit.setPlaceholderText('Opcional: arquivo local .tif, .img, .vrt ou outro raster GDAL')
        file_row = QHBoxLayout()
        file_row.addWidget(file_edit, 1)
        browse = QPushButton('Arquivo…')
        browse.clicked.connect(lambda checked=False, field=file_edit: self._choose_input(field))
        file_row.addWidget(browse)
        form.addRow('Ou arquivo no disco:', file_row)
        file_edit.setToolTip('Quando preenchido, o caminho do arquivo tem prioridade sobre a camada selecionada.')
        period = QLineEdit(placeholder)
        form.addRow(period_caption + ':', period)
        outer.addWidget(group)
        return combo, file_edit, period

    def _choose_legend_lookup(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Tabela de nomes das classes', '',
                                              'CSV (*.csv);;Todos os arquivos (*)')
        if path:
            self.legend_lookup.setText(path)

    def _add_temporal(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Selecionar mapas adicionais da série temporal', '',
            'Mapas raster (*.tif *.tiff *.img *.vrt);;Todos os arquivos (*)')
        for path in paths:
            row = self.series_table.rowCount()
            self.series_table.insertRow(row)
            found = re.search(r'(?<!\d)(?:18|19|20|21)\d{2}(?!\d)', Path(path).stem)
            self.series_table.setItem(row, 0, QTableWidgetItem(found.group(0) if found else ''))
            self.series_table.setItem(row, 1, QTableWidgetItem(path))

    def _remove_temporal(self):
        rows = sorted({item.row() for item in self.series_table.selectedItems()}, reverse=True)
        for row in rows:
            self.series_table.removeRow(row)

    def _temporal_files(self):
        if not self.series_check.isChecked():
            return []
        results = []
        for row in range(self.series_table.rowCount()):
            year_item, path_item = self.series_table.item(row, 0), self.series_table.item(row, 1)
            year = year_item.text().strip() if year_item else ''
            path = path_item.text().strip() if path_item else ''
            if not year.isdigit() or len(year) != 4 or not path:
                raise ValueError(f'Série temporal: informe ano de 4 dígitos e caminho no item {row+1}.')
            results.append((int(year), file_source(path)))
        return results

    def _choose_input(self, target):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Selecionar raster categórico', '',
            'Mapas raster (*.tif *.tiff *.img *.vrt *.asc);;Todos os arquivos (*)')
        if path:
            target.setText(path)

    def _choose_output(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Salvar mapa de transições',
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
            output = (temporary_destination('monitoria_raster', '.tif')
                      if self.temporary_check.isChecked() else self.output_edit.text().strip())
            if not output:
                raise ValueError('Escolha o arquivo GeoTIFF de saída.')
            if not output.lower().endswith(('.tif', '.tiff')):
                raise ValueError('A saída deve ter extensão .tif ou .tiff.')
            basename = Path(output).with_suffix('')
            others = [output, str(basename) + '_transicoes.csv',
                      str(basename) + '_matriz.csv', str(basename) + '_resumo.txt',
                      str(basename) + '_tendencias_mk.csv']
            existing = [p for p in others if Path(p).exists()]
            if existing:
                choice = QMessageBox.question(
                    self, 'Sobrescrever resultados',
                    f'Já existem {len(existing)} arquivos de saída. Deseja substituí-los?\n'
                    'Os arquivos anteriores serão preservados se a análise falhar.',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)
                if choice != QMessageBox.StandardButton.Yes:
                    return
            self._task = MonitoringTask(before, after, output,
                                        self.before_label.text().strip() or 'Inicial',
                                        self.after_label.text().strip() or 'Final',
                                        self.title_edit.text().strip(), self._finished,
                                        descriptive_legend=(self.legend_style.currentIndex() == 0),
                                        temporal_files=self._temporal_files(),
                                        legend_lookup=self.legend_lookup.text().strip())
            self._task.progressChanged.connect(self._progress_changed)
            self.run_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.close_button.setEnabled(False)
            self.progress.setValue(0)
            self.status.setText('Monitoria em execução. Contando e classificando transições…')
            QgsApplication.taskManager().addTask(self._task)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, 'Vista Saga — Monitoria', str(exc))

    def _progress_changed(self, percent):
        self.progress.setValue(int(percent))

    def cancel(self):
        if self._task is not None:
            self._task.cancel()
            self.status.setText('Solicitação de cancelamento enviada…')

    def _finished(self, success, task):
        self._task = None
        self.run_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        if not success:
            self.status.setText('Monitoria cancelada.' if task.isCanceled() else 'Falha na monitoria.')
            if task.error:
                QMessageBox.warning(self, 'Monitoria não concluída', task.error)
            return
        summary = task.result
        self.progress.setValue(100)
        self.status.setText('Monitoria concluída. GeoTIFF, CSVs e TXT gravados.')
        self.results_tab.setCurrentIndex(0)
        self.tabs.setCurrentWidget(self.results_tab)
        self.summary.setText(
            f'Pixels válidos: {summary["validos"]:,} | '
            f'Permanências: {summary["permanencias"]:,} ({summary["pct_permanencia"]:.2f}%) | '
            f'Mudanças: {summary["mudancas"]:,} ({summary["pct_mudanca"]:.2f}%) | '
            f'Excluídos (NoData): {summary["invalidos"]:,}')
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
            self.status.setText('Concluído. Prévia limitada a 500 transições; CSV completo disponível.')
        if self.load_check.isChecked() or self.temporary_check.isChecked():
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
                QMessageBox.warning(self, 'Monitoria concluída',
                                    'Os arquivos foram gravados, mas não foi possível adicionar o mapa ao QGIS.')

    def closeEvent(self, event):
        if getattr(self._vector_dialog, '_busy', False):
            QMessageBox.information(self, 'Monitoria em andamento',
                                    'Aguarde a conclusão da monitoria vetorial antes de fechar.')
            event.ignore()
            return
        if self._task is not None:
            QMessageBox.information(self, 'Monitoria em andamento',
                                    'Cancele ou aguarde o término da tarefa antes de fechar.')
            event.ignore()
        else:
            super().closeEvent(event)
