"""Interface compacta da Monitoria vetorial direta para QGIS 4.x / Qt6.

Não altera a janela raster já homologada; aberta por um botão na aba Configuração.
"""
from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressDialog,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
    QHeaderView, QAbstractItemView,
)
from qgis.core import Qgis, QgsProject, QgsVectorLayer
from qgis.gui import QgsMapLayerComboBox
from .ui_shared import temporary_destination

from .vector_monitoring_engine import run_vector_monitoring, validate_vector_monitoring


class VectorMonitoringDialog(QWidget):
    """Reusable vector monitoring QWidget, embeddable in Monitoria tabs."""

    def __init__(self, iface, parent=None, embedded=False):
        super().__init__(parent)
        if not embedded:
            self.setWindowFlag(Qt.WindowType.Window, True)
        self.iface = iface
        self._busy = False
        self._file_layers = {}
        self.setWindowTitle('Vista Saga Plugin — Monitoria vetorial')
        self.resize(820, 490)
        self.setMinimumSize(690, 425)
        self._build_ui()

    def _build_ui(self):
        body = QVBoxLayout(self)
        body.setContentsMargins(9, 9, 9, 9)
        tabs = QTabWidget()
        self.tabs = tabs
        body.addWidget(tabs)
        settings = QWidget()
        results = QWidget()
        tabs.addTab(settings, 'Configuração')
        tabs.addTab(results, 'Resultados')
        root = QVBoxLayout(settings)
        rows = QHBoxLayout()
        self.before_select = self._make_layer_selection(rows, 'Mapa inicial', 'Inicial')
        self.after_select = self._make_layer_selection(rows, 'Mapa final', 'Final')
        root.addLayout(rows)

        out = QGroupBox('Saída')
        form = QFormLayout(out)
        self.title = QLineEdit()
        self.title.setPlaceholderText('Ex.: Mudanças de uso da terra entre 1986 e 2016')
        form.addRow('Título:', self.title)
        pathrow = QHBoxLayout()
        self.dest = QLineEdit()
        self.dest.setPlaceholderText('Arquivo .gpkg de transições')
        pathrow.addWidget(self.dest, 1)
        browse = QPushButton('Procurar…')
        browse.clicked.connect(self._output)
        pathrow.addWidget(browse)
        form.addRow('GeoPackage:', pathrow)
        note = QLabel('Serão gerados automaticamente os relatórios _transicoes.csv, '
                      '_matriz.csv (área em ha) e _resumo.txt na mesma pasta.')
        note.setWordWrap(True)
        form.addRow('', note)
        self.add_to_project = QCheckBox('Adicionar resultado ao projeto QGIS')
        self.add_to_project.setChecked(True)
        form.addRow('', self.add_to_project)
        root.addWidget(out)
        caution = QLabel('A monitoria compara somente a área comum às duas camadas. '
                         'Confira a equivalência temática entre os períodos e a topologia dos polígonos.')
        caution.setWordWrap(True)
        root.addWidget(caution)
        root.addStretch(1)

        result_layout = QVBoxLayout(results)
        self.summary_label = QLabel('Nenhuma monitoria vetorial executada nesta sessão.')
        self.summary_label.setWordWrap(True)
        result_layout.addWidget(self.summary_label)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['Transição', 'Situação', 'Área (ha)', '% da área'])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        result_layout.addWidget(self.table, 1)

        commands = QHBoxLayout()
        self.status = QLabel('Selecione os polígonos e campos de classificação.')
        self.status.setWordWrap(True)
        commands.addWidget(self.status, 1)
        self.temporary_check = QCheckBox('Resultado temporário no QGIS (pode salvar depois)')
        self.temporary_check.setChecked(True)
        self.dest.setEnabled(False)
        self.temporary_check.toggled.connect(lambda active: self.dest.setEnabled(not active))
        form.addRow('', self.temporary_check)
        self.run_button = QPushButton('Executar monitoria vetorial')
        self.run_button.clicked.connect(self.run)
        commands.addWidget(self.run_button)
        close = QPushButton('Fechar')
        close.clicked.connect(self.close)
        commands.addWidget(close)
        body.addLayout(commands)

    def _make_layer_selection(self, parent, heading, period):
        group = QGroupBox(heading)
        form = QFormLayout(group)
        selector = QgsMapLayerComboBox()
        selector.setFilters(Qgis.LayerFilter.VectorLayer)
        selector.setAllowEmptyLayer(True)
        selector.setShowCrs(True)
        form.addRow('Camada QGIS:', selector)
        file_path = QLineEdit()
        file_path.setPlaceholderText('Opcional: SHP, GPKG, GeoJSON, FlatGeobuf…')
        pathrow = QHBoxLayout()
        pathrow.addWidget(file_path, 1)
        pick = QPushButton('Arquivo…')
        pick.clicked.connect(lambda checked=False, field=file_path: self._input(field))
        pathrow.addWidget(pick)
        form.addRow('Ou arquivo:', pathrow)
        field = QComboBox()
        form.addRow('Campo de classe:', field)
        label = QComboBox()
        form.addRow('Campo de legenda:', label)
        period_text = QLineEdit(period)
        form.addRow('Período:', period_text)
        parent.addWidget(group)
        info = (selector, file_path, field, label, period_text)
        selector.layerChanged.connect(lambda layer, data=info: self._refresh_fields(data))
        file_path.editingFinished.connect(lambda data=info: self._refresh_fields(data))
        self._refresh_fields(info)
        return info

    def _input(self, edit):
        path, _ = QFileDialog.getOpenFileName(self, 'Selecionar mapa vetorial', '',
                                              'Vetores (*.gpkg *.shp *.geojson *.json *.fgb);;Todos (*)')
        if path:
            edit.setText(path)
            self._refresh_fields(self.before_select if edit is self.before_select[1]
                                 else self.after_select)

    def _output(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Salvar monitoria vetorial',
                                              self.dest.text().strip() or 'monitoria_vetorial.gpkg',
                                              'GeoPackage (*.gpkg)')
        if path:
            self.dest.setText(path if path.lower().endswith('.gpkg') else path + '.gpkg')

    def _chosen_layer(self, info):
        selector, file_path, _, _, _ = info
        path = file_path.text().strip()
        if not path:
            return selector.currentLayer()
        old = self._file_layers.get(path)
        if old is None:
            old = QgsVectorLayer(path, Path(path.split('|')[0]).stem, 'ogr')
            self._file_layers[path] = old
        return old

    def _refresh_fields(self, info):
        if self._busy:
            return
        _, _, field, label, _ = info
        chosen = field.currentText()
        legend = label.currentData()
        layer = self._chosen_layer(info)
        field.blockSignals(True)
        label.blockSignals(True)
        field.clear()
        label.clear()
        label.addItem('(usar o próprio campo, quando textual)', '')
        if layer is not None and layer.isValid():
            names = layer.fields().names()
            field.addItems(names)
            for name in names:
                label.addItem(name, name)
            if chosen in names:
                field.setCurrentText(chosen)
            else:
                for candidate in ('CODIGO', 'COD_INI', 'classe', 'CLASSE', 'TIPO_USO', 'USO'):
                    if candidate in names:
                        field.setCurrentText(candidate)
                        break
            if legend and legend in names:
                label.setCurrentIndex(label.findData(legend))
            else:
                for candidate in ('NOME', 'CLASSE', 'DESCRICAO', 'LEGENDA'):
                    if candidate in names and candidate != field.currentText():
                        label.setCurrentIndex(label.findData(candidate))
                        break
        label.blockSignals(False)
        field.blockSignals(False)

    def run(self):
        if self._busy:
            return
        a = self._chosen_layer(self.before_select)
        b = self._chosen_layer(self.after_select)
        fa = self.before_select[2].currentText()
        fb = self.after_select[2].currentText()
        na = self.before_select[3].currentData() or ''
        nb = self.after_select[3].currentData() or ''
        path = (temporary_destination('monitoria_vetorial', '.gpkg')
                if self.temporary_check.isChecked() else self.dest.text().strip())
        try:
            validate_vector_monitoring(a, b, fa, fb, path, na, nb)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, 'Monitoria vetorial — entrada', str(exc))
            return
        from pathlib import Path
        stem = str(Path(path).with_suffix(''))
        existing = [p for p in [path, stem+'_transicoes.csv', stem+'_matriz.csv', stem+'_resumo.txt']
                    if Path(p).exists()]
        if existing:
            answer = QMessageBox.question(self, 'Substituir saídas',
                f'{len(existing)} arquivos já existem. Deseja substituí-los?\n'
                'Os arquivos anteriores serão restaurados em caso de falha.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
        self._busy = True
        self.run_button.setEnabled(False)
        self.status.setText('Executando interseção e cálculo das áreas…')
        dialog = QProgressDialog('Monitoria vetorial em execução…', 'Cancelar', 0, 100, self)
        dialog.setWindowTitle('Vista Saga — Monitoria vetorial')
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.setMinimumDuration(0)
        dialog.setValue(0)
        dialog.show()
        def update(value):
            if value is not None:
                dialog.setValue(max(0, min(100, int(value))))
            QApplication.processEvents()
        try:
            result = run_vector_monitoring(
                a, b, fa, fb, path, name_before=na, name_after=nb,
                initial=self.before_select[4].text().strip() or 'Inicial',
                final=self.after_select[4].text().strip() or 'Final',
                title=self.title.text().strip(), progress=update,
                cancelled=dialog.wasCanceled)
            self.status.setText('Monitoria vetorial concluída. GeoPackage, CSVs e TXT disponíveis.')
            self._show_result(result)
            if self.add_to_project.isChecked() or self.temporary_check.isChecked():
                layer = QgsVectorLayer(path + '|layername=monitoria_vetorial',
                                       Path(path).stem, 'ogr')
                if layer.isValid():
                    self._style_layer(layer)
                    QgsProject.instance().addMapLayer(layer)
                else:
                    QMessageBox.warning(self, 'Resultado concluído',
                                        'Os arquivos foram gravados, mas a camada não pôde ser carregada.')
        except (ValueError, OSError, RuntimeError, InterruptedError) as exc:
            self.status.setText('Monitoria vetorial não concluída.')
            QMessageBox.warning(self, 'Monitoria vetorial', str(exc))
        except Exception as exc:
            self.status.setText('Erro inesperado na Monitoria vetorial.')
            QMessageBox.critical(self, 'Monitoria vetorial',
                                 f'{type(exc).__name__}: {exc}')
        finally:
            dialog.close()
            self._busy = False
            self.run_button.setEnabled(True)

    def _show_result(self, summary):
        host = getattr(self, '_embedded_results_host', None)
        if host is None:
            self.tabs.setCurrentIndex(1)
        else:
            result_tabs, main_tabs = host
            result_tabs.setCurrentIndex(1)
            main_tabs.setCurrentIndex(2)
        self.summary_label.setText(
            f"Área comum: {summary['area_total_ha']:.3f} ha | "
            f"Permanência: {summary['area_permanencia_ha']:.3f} ha "
            f"({summary['pct_permanencia']:.2f}%) | "
            f"Mudança: {summary['area_mudanca_ha']:.3f} ha "
            f"({summary['pct_mudanca']:.2f}%)")
        self.table.setRowCount(0)
        for row in summary['linhas'][:500]:
            line = self.table.rowCount()
            self.table.insertRow(line)
            for col, val in enumerate((row['legenda'], row['situacao'],
                                       f"{row['area_ha']:.3f}", f"{row['pct_area']:.3f}%")):
                self.table.setItem(line, col, QTableWidgetItem(str(val)))

    def _style_layer(self, layer):
        try:
            from qgis.core import QgsCategorizedSymbolRenderer, QgsFillSymbol, QgsRendererCategory
            entries = []
            for value, label, fill in [('Permanência', 'Permanência', '#B9C2C7'),
                                       ('Mudança', 'Mudança', '#D8854B')]:
                symbol = QgsFillSymbol.createSimple({'color': fill, 'outline_color': '#404040',
                                                     'outline_width': '0.15'})
                entries.append(QgsRendererCategory(value, symbol, label))
            layer.setRenderer(QgsCategorizedSymbolRenderer('SITUACAO', entries))
        except (RuntimeError, AttributeError, TypeError):
            pass

    def closeEvent(self, event):
        if self._busy:
            QMessageBox.information(self, 'Monitoria em execução',
                                    'Cancele ou aguarde o término da análise.')
            event.ignore()
        else:
            super().closeEvent(event)
