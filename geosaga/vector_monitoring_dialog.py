"""Interface compacta da Monitoria vetorial direta para QGIS 4.x / Qt6.

Não altera a janela raster já homologada; aberta por um botão na aba Configuração.
"""
from .i18n import tr
from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressDialog,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
    QHeaderView, QAbstractItemView,
)
from qgis.core import Qgis, QgsProject, QgsVectorLayer
from qgis.gui import QgsMapLayerComboBox
from .ui_shared import enable_table_copy, layer_name, materialize_in_memory, result_name, temporary_destination
from .ui_shared import RUN_TEXT, FooterStatus, report_outcome


VECTOR_MONITORING_HINT = (
    'Em branco, o resultado é carregado no QGIS como camada temporária em memória (salve-a '
    'antes de fechar o QGIS). Com um arquivo indicado, ele é salvo em disco e carregado no '
    'QGIS. Na mesma pasta são gerados _transicoes.csv, _matriz.csv (área em ha) e '
    '_resumo.txt; sem arquivo indicado, eles ficam na pasta temporária do QGIS.')

from .vector_monitoring_engine import run_vector_monitoring, validate_vector_monitoring
from .errors import log_exception


class VectorMonitoringDialog(QWidget):
    """Reusable vector monitoring QWidget, embeddable in Monitoria tabs."""

    def __init__(self, iface, parent=None, embedded=False):
        super().__init__(parent)
        if not embedded:
            self.setWindowFlag(Qt.WindowType.Window, True)
        self.iface = iface
        self._busy = False
        self._file_layers = {}
        self.setWindowTitle(tr('Vista Saga Plugin - Monitoria vetorial'))
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
        tabs.addTab(settings, tr('Configuração'))
        tabs.addTab(results, tr('Resultados'))
        root = QVBoxLayout(settings)
        rows = QHBoxLayout()
        self.before_select = self._make_layer_selection(rows, 'Mapa inicial', 'Inicial')
        self.after_select = self._make_layer_selection(rows, 'Mapa final', 'Final')
        root.addLayout(rows)

        out = QGroupBox(tr('Resultado'))
        form = QFormLayout(out)
        self.title = QLineEdit()
        self.title.setPlaceholderText(tr('Ex.: Mudanças de uso da terra entre 1986 e 2016'))
        form.addRow(tr('Título do estudo:'), self.title)
        pathrow = QHBoxLayout()
        self.dest = QLineEdit()
        # Em branco: camada temporária em memória; preenchido: GeoPackage salvo.
        # Nos dois casos o resultado é carregado no QGIS.
        self.dest.setPlaceholderText(tr('[Camada temporária em memória]'))
        self.dest.setClearButtonEnabled(True)
        pathrow.addWidget(self.dest, 1)
        browse = QPushButton(tr('Procurar…'))
        browse.clicked.connect(self._output)
        pathrow.addWidget(browse)
        form.addRow(tr('Salvar em:'), pathrow)
        note = QLabel(tr(VECTOR_MONITORING_HINT))
        note.setWordWrap(True)
        form.addRow('', note)
        root.addWidget(out)
        caution = QLabel(tr('A monitoria compara somente a área comum às duas camadas. '
                         'Confira a equivalência temática entre os períodos e a topologia dos polígonos.'))
        caution.setWordWrap(True)
        root.addWidget(caution)
        root.addStretch(1)

        result_layout = QVBoxLayout(results)
        self.summary_label = QLabel(tr('Nenhuma monitoria vetorial executada nesta sessão.'))
        self.summary_label.setWordWrap(True)
        result_layout.addWidget(self.summary_label)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([tr('Transição'), tr('Situação'), tr('Área (ha)'), tr('% da área')])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        enable_table_copy(self.table)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        result_layout.addWidget(self.table, 1)

        commands = QHBoxLayout()
        self.status = FooterStatus(tr('Selecione os polígonos e campos de classificação.'))
        self.status.setWordWrap(True)
        commands.addStretch(1)
        self.run_button = QPushButton(tr(RUN_TEXT))
        self.run_button.clicked.connect(self.run)
        commands.addWidget(self.run_button)
        self.close_button = QPushButton(tr('Fechar'))
        self.close_button.clicked.connect(self.close)
        commands.addWidget(self.close_button)
        body.addLayout(commands)

    def _make_layer_selection(self, parent, heading, period):
        group = QGroupBox(tr(heading))
        form = QFormLayout(group)
        selector = QgsMapLayerComboBox()
        selector.setFilters(Qgis.LayerFilter.VectorLayer)
        selector.setAllowEmptyLayer(True)
        selector.setShowCrs(True)
        form.addRow(tr('Camada no QGIS:'), selector)
        file_path = QLineEdit()
        file_path.setPlaceholderText(tr('Opcional: SHP, GPKG, GeoJSON, FlatGeobuf…'))
        pathrow = QHBoxLayout()
        pathrow.addWidget(file_path, 1)
        pick = QPushButton(tr('Arquivo…'))
        pick.clicked.connect(lambda checked=False, field=file_path: self._input(field))
        pathrow.addWidget(pick)
        form.addRow(tr('Ou arquivo:'), pathrow)
        field = QComboBox()
        form.addRow(tr('Campo de classe:'), field)
        label = QComboBox()
        form.addRow(tr('Campo de legenda:'), label)
        period_text = QLineEdit(tr(period))
        form.addRow(tr('Período:'), period_text)
        parent.addWidget(group)
        info = (selector, file_path, field, label, period_text)
        selector.layerChanged.connect(lambda layer, data=info: self._refresh_fields(data))
        file_path.editingFinished.connect(lambda data=info: self._refresh_fields(data))
        self._refresh_fields(info)
        return info

    def _input(self, edit):
        path, _ = QFileDialog.getOpenFileName(self, tr('Selecionar mapa vetorial'), '',
                                              tr('Vetores (*.gpkg *.shp *.geojson *.json *.fgb);;Todos (*)'))
        if path:
            edit.setText(path)
            self._refresh_fields(self.before_select if edit is self.before_select[1]
                                 else self.after_select)

    def _output(self):
        path, _ = QFileDialog.getSaveFileName(self, tr('Salvar monitoria vetorial'),
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
        label.addItem(tr('(usar o próprio campo, quando textual)'), '')
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
        chosen = self.dest.text().strip()
        temporary = not chosen
        path = chosen or temporary_destination(result_name('Monitoria', 'Vetorial'), '.gpkg')
        try:
            validate_vector_monitoring(a, b, fa, fb, path, na, nb)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, tr('Monitoria vetorial - entrada'), tr(str(exc)))
            return
        from pathlib import Path
        stem = str(Path(path).with_suffix(''))
        existing = [p for p in [path, stem+'_transicoes.csv', stem+'_matriz.csv', stem+'_resumo.txt']
                    if Path(p).exists()]
        if existing:
            answer = QMessageBox.question(self, tr('Substituir saídas'),
                tr(f'{len(existing)} arquivos já existem. Deseja substituí-los?\n'
                'Os arquivos anteriores serão restaurados em caso de falha.'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
        self._busy = True
        self.run_button.setEnabled(False)
        self.status.setText(tr('Executando interseção e cálculo das áreas…'))
        dialog = QProgressDialog(tr('Monitoria vetorial em execução…'), tr('Cancelar'), 0, 100, self)
        dialog.setWindowTitle(self.window().windowTitle())  # título da janela do módulo (1.4.1)
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
            report_outcome(self.status, 'Monitoria vetorial',
                           tr('Monitoria vetorial concluída. GeoPackage, CSVs e TXT disponíveis.'), 'success')
            self._show_result(result)
            # O resultado é sempre carregado no QGIS: em memória, se não houver arquivo.
            uri = path + '|layername=monitoria_vetorial'
            name = layer_name(path)
            layer = (materialize_in_memory(uri, name) if temporary
                     else QgsVectorLayer(uri, name, 'ogr'))
            if layer is not None and layer.isValid():
                self._style_layer(layer)
                QgsProject.instance().addMapLayer(layer)
            else:
                QMessageBox.warning(self, tr('Resultado concluído'),
                                    tr('Os arquivos foram gravados, mas a camada não pôde ser carregada.'))
            self._warn_omitted(result, fa, fb)
        except (ValueError, OSError, RuntimeError, InterruptedError) as exc:
            self.status.setText(tr('Monitoria vetorial não concluída.'))
            QMessageBox.warning(self, tr('Monitoria vetorial'), tr(str(exc)))
        except Exception as exc:
            log_exception()
            self.status.setText(tr('Erro inesperado na Monitoria vetorial.'))
            QMessageBox.critical(self, tr('Monitoria vetorial'),
                                 tr(f'{type(exc).__name__}: {exc}'))
        finally:
            dialog.close()
            self._busy = False
            self.run_button.setEnabled(True)

    def _warn_omitted(self, result, field_before, field_after):
        """Avisa quando feições ficaram fora por não terem classe (ou geometria).

        Essas áreas não entram na monitoria e aparecem como vazios no mapa
        resultante; antes, isso só constava do _resumo.txt.
        """
        lines = []
        for count, field, caption in ((result.get('omitidas_inicial', 0), field_before, tr('mapa inicial')),
                                      (result.get('omitidas_final', 0), field_after, tr('mapa final'))):
            if count:
                lines.append(tr('{0}: {1} feição(ões) sem valor no campo de classe “{2}” '
                                '(ou sem geometria).').format(caption, count, field))
        if lines:
            QMessageBox.warning(
                self, tr('Feições sem classe ignoradas'),
                '\n'.join(lines) + '\n\n' + tr(
                    'Essas áreas ficaram fora da monitoria e aparecem como vazios no mapa '
                    'resultante. Preencha o campo de classe ou escolha outro campo (por exemplo, '
                    'o campo com os nomes das classes) e execute de novo.'))

    def _show_result(self, summary):
        host = getattr(self, '_embedded_results_host', None)
        if host is None:
            self.tabs.setCurrentIndex(1)
        else:
            result_tabs, main_tabs = host
            result_tabs.setCurrentIndex(1)
            main_tabs.setCurrentIndex(2)
        self.summary_label.setText(
            tr(f"Área comum: {summary['area_total_ha']:.3f} ha | "
            f"Permanência: {summary['area_permanencia_ha']:.3f} ha "
            f"({summary['pct_permanencia']:.2f}%) | "
            f"Mudança: {summary['area_mudanca_ha']:.3f} ha "
            f"({summary['pct_mudanca']:.2f}%)"))
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
            QMessageBox.information(self, tr('Monitoria em execução'),
                                    tr('Cancele ou aguarde o término da análise.'))
            event.ignore()
        else:
            super().closeEvent(event)
