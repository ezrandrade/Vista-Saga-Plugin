"""Avaliação Espacial — modalidade vetorial por atributos, QGIS 4 / Qt6.

Esta janela não altera o formulário raster nem oferece fluxo Processing.
"""
import os
from collections import Counter

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QApplication, QAbstractItemView, QCheckBox, QComboBox, QDialog,
    QDoubleSpinBox, QFileDialog, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QProgressDialog, QPushButton,
    QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from qgis.core import QgsProject, Qgis, QgsVectorLayer
from qgis.gui import QgsMapLayerComboBox
from .ui_shared import temporary_destination

from .vector_evaluation_core import category_key, category_sort, validate_criteria
from .vector_evaluation_writer import evaluate_vector_layer


def button(text, callback):
    widget = QPushButton(text)
    widget.clicked.connect(callback)
    return widget


def locked(text):
    item = QTableWidgetItem(str(text))
    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    return item


class VectorEvaluationDialog(QWidget):
    """Reusable evaluation form (QWidget inside tabs or standalone window)."""

    def __init__(self, iface, parent=None, embedded=False):
        super().__init__(parent)
        if not embedded:
            self.setWindowFlag(Qt.WindowType.Window, True)
        self._embedding_host = parent if embedded else None
        self.iface = iface
        self.criteria = []
        self.active = -1
        self._rendering = False
        self.running = False
        self.setWindowTitle('Vista Saga Plugin — Avaliação Espacial vetorial')
        self.setMinimumSize(850, 600)
        self.resize(1070, 740)
        self._build()
        self._populate_fields()

    def _build(self):
        root = QVBoxLayout(self)
        heading = QLabel('<b>AVALIAÇÃO ESPACIAL — VETOR POR ATRIBUTOS</b>')
        root.addWidget(heading)
        intro = QLabel(
            'Selecione uma camada de polígonos. Cada campo temático constitui um critério: '
            'atribua pesos e notas às categorias. A geometria das feições será preservada. '
            'Não há sobreposição entre camadas nesta modalidade.')
        intro.setWordWrap(True)
        root.addWidget(intro)
        root.addWidget(button('Empilhar camadas vetoriais independentes…', self.open_overlay_dialog))
        input_group = QGroupBox('1. Base territorial')
        in_layout = QHBoxLayout(input_group)
        in_layout.addWidget(QLabel('Camada de polígonos:'))
        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(Qgis.LayerFilter.PolygonLayer)
        self.layer_combo.setAllowEmptyLayer(True, "— selecione um polígono —")
        self.layer_combo.layerChanged.connect(self._layer_changed)
        in_layout.addWidget(self.layer_combo, stretch=1)
        in_layout.addWidget(button('Atualizar', self._populate_fields))
        in_layout.addWidget(QLabel('Notas:'))
        self.scale_combo = QComboBox()
        self.scale_combo.addItem('0–10', 10)
        self.scale_combo.addItem('0–100', 100)
        in_layout.addWidget(self.scale_combo)
        root.addWidget(input_group)
        split = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(split, stretch=1)
        left = QGroupBox('2. Campos de avaliação e pesos')
        ll = QVBoxLayout(left)
        addrow = QHBoxLayout()
        self.field_combo = QComboBox()
        addrow.addWidget(self.field_combo, 1)
        addrow.addWidget(button('Adicionar campo', self.add_field))
        ll.addLayout(addrow)
        ll.addWidget(button('Remover campo selecionado', self.remove_field))
        self.criteria_table = QTableWidget(0, 3)
        self.criteria_table.setHorizontalHeaderLabels(['Campo', 'Peso (%)', 'Categorias'])
        self.criteria_table.verticalHeader().setVisible(False)
        self.criteria_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.criteria_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.criteria_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.criteria_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.criteria_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.criteria_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.criteria_table.itemSelectionChanged.connect(self._criterion_selected)
        ll.addWidget(self.criteria_table, stretch=1)
        ll.addWidget(button('Distribuir pesos igualmente', self.distribute_weights))
        self.weights_label = QLabel('Nenhum critério selecionado.')
        self.weights_label.setWordWrap(True)
        ll.addWidget(self.weights_label)
        split.addWidget(left)
        right = QGroupBox('3. Notas e classes excluídas')
        rl = QVBoxLayout(right)
        self.class_label = QLabel('Selecione um campo à esquerda.')
        self.class_label.setWordWrap(True)
        rl.addWidget(self.class_label)
        self.classes_table = QTableWidget(0, 4)
        self.classes_table.setHorizontalHeaderLabels(['Categoria', 'Feições', 'Nota', 'Excluir'])
        self.classes_table.verticalHeader().setVisible(False)
        self.classes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.classes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.classes_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.classes_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        rl.addWidget(self.classes_table, stretch=1)
        batch = QHBoxLayout()
        batch.addWidget(QLabel('Nota:'))
        self.batch_note = QDoubleSpinBox()
        self.batch_note.setRange(0, 100)
        self.batch_note.setDecimals(2)
        batch.addWidget(self.batch_note)
        batch.addWidget(button('Aplicar às selecionadas', self.apply_note))
        rl.addLayout(batch)
        tip = QLabel('Nota em branco = não configurada. Excluir invalida a feição, '
                     'mas ela permanece no GeoPackage com AVALIACAO nulo. '
                     'Valores nulos também invalidam a feição.')
        tip.setWordWrap(True)
        rl.addWidget(tip)
        split.addWidget(right)
        split.setSizes([435, 635])
        output_group = QGroupBox('4. Resultado')
        ol = QVBoxLayout(output_group)
        row = QHBoxLayout()
        row.addWidget(QLabel('GeoPackage:'))
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText('Escolha onde salvar o resultado (.gpkg)')
        row.addWidget(self.output_edit, stretch=1)
        row.addWidget(button('Procurar…', self.select_output))
        ol.addLayout(row)
        self.temporary_check = QCheckBox('Resultado temporário no QGIS (pode salvar depois)')
        self.temporary_check.setChecked(True)
        ol.addWidget(self.temporary_check)
        self.output_edit.setEnabled(False)
        self.temporary_check.toggled.connect(lambda active: self.output_edit.setEnabled(not active))
        self.load_check = QCheckBox('Adicionar resultado ao QGIS')
        self.load_check.setChecked(True)
        ol.addWidget(self.load_check)
        report_row = QHBoxLayout()
        self.csv_check = QCheckBox('Relatório CSV: combinações, pesos e áreas')
        self.csv_check.setChecked(True)
        self.txt_check = QCheckBox('Relatório TXT: padrão Vista SAGA')
        self.txt_check.setChecked(True)
        report_row.addWidget(self.csv_check)
        report_row.addWidget(self.txt_check)
        ol.addLayout(report_row)
        root.addWidget(output_group)
        foot = QHBoxLayout()
        self.status = QLabel('Selecione um campo temático para iniciar.')
        self.status.setWordWrap(True)
        foot.addWidget(self.status, stretch=1)
        foot.addWidget(button('Validar', self.validate_configuration))
        self.run_button = button('Executar avaliação', self.execute)
        foot.addWidget(self.run_button)
        self.close_button = button('Fechar', self._close_form)
        foot.addWidget(self.close_button)
        root.addLayout(foot)

    def _close_form(self):
        """In a tab, close the whole module; as a window, close only this form."""
        host = self._embedding_host
        if host is not None:
            host.close()
        else:
            self.close()

    def open_overlay_dialog(self):
        host = getattr(self, '_embedding_host', None)
        if host is not None:
            host.open_vector_overlay()
            return
        from .vector_overlay_dialog import VectorOverlayEvaluationDialog
        dialog = getattr(self, '_overlay_dialog', None)
        if dialog is None:
            dialog = VectorOverlayEvaluationDialog(self.iface, self)
            self._overlay_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _layer(self):
        layer = self.layer_combo.currentLayer()
        return layer if isinstance(layer, QgsVectorLayer) and layer.isValid() else None

    def _layer_changed(self, _layer=None):
        if self.running:
            return
        self.criteria.clear()
        self.active = -1
        self.classes_table.setRowCount(0)
        self.criteria_table.setRowCount(0)
        self._populate_fields()
        self._update_weight_status()

    def _populate_fields(self):
        selected = self.field_combo.currentText()
        self.field_combo.clear()
        layer = self._layer()
        if layer:
            self.field_combo.addItems([f.name() for f in layer.fields()])
        index = self.field_combo.findText(selected)
        if index >= 0:
            self.field_combo.setCurrentIndex(index)

    def add_field(self):
        layer = self._layer()
        field = self.field_combo.currentText()
        if not layer or not field:
            QMessageBox.warning(self, 'Avaliação vetorial', 'Selecione uma camada e um campo.')
            return
        if any(x['field'] == field for x in self.criteria):
            QMessageBox.warning(self, 'Avaliação vetorial', 'Este campo já está incluído.')
            return
        counts = Counter()
        missing = 0
        for feature in layer.getFeatures():
            key = category_key(feature[field])
            if key is None:
                missing += 1
            else:
                counts[key] += 1
                if len(counts) > 256:
                    QMessageBox.warning(self, 'Campo com muitas categorias',
                        f'O campo {field} apresenta mais de 256 valores distintos. '
                        'Reclassifique-o por intervalos antes da avaliação; '
                        'esta modalidade aplica notas a categorias discretas.')
                    return
        if not counts:
            QMessageBox.warning(self, 'Avaliação vetorial',
                                'O campo selecionado não contém categorias válidas.')
            return
        self._save_classes()
        self.criteria.append({'field': field, 'counts': dict(counts), 'missing': missing,
                              'weight': 0., 'notes': {}, 'excluded': set()})
        self._distribute()
        self._render_criteria(select=len(self.criteria)-1)
        self.status.setText(f'Campo {field}: {len(counts)} categorias; {missing} feições sem dados.')

    def remove_field(self):
        indices = sorted({item.row() for item in self.criteria_table.selectedItems()}, reverse=True)
        if not indices:
            return
        self._save_classes()
        for index in indices:
            if 0 <= index < len(self.criteria):
                self.criteria.pop(index)
        self.active = -1
        self._distribute()
        self._render_criteria(select=min(indices[-1], len(self.criteria)-1))

    def _distribute(self):
        n = len(self.criteria)
        if n:
            weights = [round(100. / n, 2)] * (n-1)
            weights.append(round(100 - sum(weights), 2))
            for criterion, weight in zip(self.criteria, weights):
                criterion['weight'] = weight

    def distribute_weights(self):
        self._save_classes()
        self._distribute()
        self._render_criteria(select=self.criteria_table.currentRow())

    def _render_criteria(self, select=None):
        self._rendering = True
        self.criteria_table.setRowCount(len(self.criteria))
        for row, criterion in enumerate(self.criteria):
            self.criteria_table.setItem(row, 0, locked(criterion['field']))
            spin = QDoubleSpinBox()
            spin.setRange(0, 100)
            spin.setDecimals(2)
            spin.setValue(criterion['weight'])
            spin.valueChanged.connect(lambda value, i=row: self._weight_changed(i, value))
            self.criteria_table.setCellWidget(row, 1, spin)
            self.criteria_table.setItem(row, 2, locked(len(criterion['counts'])))
        self._rendering = False
        self.active = -1
        if select is not None and 0 <= select < len(self.criteria):
            self.criteria_table.selectRow(select)
            self._criterion_selected()
        else:
            self.classes_table.setRowCount(0)
        self._update_weight_status()

    def _weight_changed(self, index, value):
        if not self._rendering and 0 <= index < len(self.criteria):
            self.criteria[index]['weight'] = value
            self._update_weight_status()

    def _update_weight_status(self):
        total = sum(c['weight'] for c in self.criteria)
        self.weights_label.setText(f'Pesos: {total:.2f}% (necessário: 100%).')

    def _save_classes(self):
        if self._rendering or not 0 <= self.active < len(self.criteria):
            return
        criterion = self.criteria[self.active]
        notes = {}
        excluded = set()
        for row in range(self.classes_table.rowCount()):
            key = self.classes_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            check = self.classes_table.cellWidget(row, 3)
            if check and check.isChecked():
                excluded.add(key)
            else:
                note_item = self.classes_table.item(row, 2)
                if note_item and note_item.text().strip():
                    notes[key] = note_item.text().strip()
        criterion['notes'] = notes
        criterion['excluded'] = excluded

    def _criterion_selected(self):
        if self._rendering:
            return
        next_index = self.criteria_table.currentRow()
        if next_index == self.active:
            return
        self._save_classes()
        self.active = next_index
        if not 0 <= next_index < len(self.criteria):
            self.classes_table.setRowCount(0)
            return
        criterion = self.criteria[next_index]
        categories = sorted(criterion['counts'], key=category_sort)
        self._rendering = True
        self.classes_table.setRowCount(len(categories))
        for row, key in enumerate(categories):
            item = locked(key)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.classes_table.setItem(row, 0, item)
            self.classes_table.setItem(row, 1, locked(criterion['counts'][key]))
            note = QTableWidgetItem(str(criterion['notes'].get(key, '')))
            self.classes_table.setItem(row, 2, note)
            check = QCheckBox()
            check.setChecked(key in criterion['excluded'])
            self.classes_table.setCellWidget(row, 3, check)
        self._rendering = False
        self.class_label.setText(f'{criterion["field"]}: {len(categories)} categorias válidas.')

    def apply_note(self):
        if self.active < 0:
            return
        scale = int(self.scale_combo.currentData())
        if self.batch_note.value() > scale:
            QMessageBox.warning(self, 'Nota fora da escala', f'O limite é {scale}.')
            return
        selected = {item.row() for item in self.classes_table.selectedItems()}
        for row in selected:
            self.classes_table.item(row, 2).setText(str(self.batch_note.value()))
            self.classes_table.cellWidget(row, 3).setChecked(False)
        self._save_classes()

    def _rules(self):
        self._save_classes()
        return validate_criteria([
            {'field': c['field'], 'weight': c['weight'], 'categories': set(c['counts']),
             'notes': dict(c['notes']), 'excluded': set(c['excluded'])}
            for c in self.criteria], scale=int(self.scale_combo.currentData()))

    def validate_configuration(self):
        try:
            rules = self._rules()
            layer = self._layer()
            if not layer:
                raise ValueError('Selecione uma camada de polígonos válida.')
            if layer.isEditable():
                raise ValueError('Salve as alterações da camada antes de avaliar.')
            QMessageBox.information(self, 'Avaliação vetorial',
                f'Configuração válida: {len(rules)} critérios; {layer.featureCount()} feições. '
                'As feições excluídas ou sem dado terão avaliação nula.')
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, 'Regras incompletas', str(exc))

    def select_output(self):
        suggestion = self.output_edit.text() or os.path.join(os.path.expanduser('~'), 'avaliacao_vetorial.gpkg')
        dest, _ = QFileDialog.getSaveFileName(self, 'Salvar avaliação vetorial', suggestion,
                                              'GeoPackage (*.gpkg)')
        if dest:
            self.output_edit.setText(dest if dest.lower().endswith('.gpkg') else dest + '.gpkg')

    def execute(self):
        if self.running:
            return
        try:
            rules = self._rules()
            layer = self._layer()
            if not layer:
                raise ValueError('Selecione uma camada poligonal válida.')
            dest = (temporary_destination('avaliacao_atributos', '.gpkg')
                    if self.temporary_check.isChecked() else self.output_edit.text().strip())
            if not dest:
                raise ValueError('Informe o GeoPackage de saída.')
            dest = os.path.abspath(dest)
            if os.path.exists(dest):
                if QMessageBox.question(self, 'Substituir resultado?',
                    'O GeoPackage já existe. Deseja substituí-lo?\n'
                    'Se estiver aberto no QGIS, remova a camada de saída antes de continuar.') != QMessageBox.StandardButton.Yes:
                    return
            self.running = True
            self.run_button.setEnabled(False)
            self.close_button.setEnabled(False)
            progress = QProgressDialog('Calculando notas das feições…', 'Cancelar', 0, 100, self)
            progress.setMinimumDuration(0)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            def update(pct):
                progress.setValue(pct)
                QApplication.processEvents()
            try:
                result = evaluate_vector_layer(
                    layer, [
                        {'field': c['field'], 'weight': c['weight'], 'categories': set(c['counts']),
                         'notes': dict(c['notes']), 'excluded': set(c['excluded'])}
                        for c in self.criteria],
                    int(self.scale_combo.currentData()), dest,
                    progress=update, cancelled=progress.wasCanceled,
                    report_csv=self.csv_check.isChecked(), report_txt=self.txt_check.isChecked())
            finally:
                progress.close()
            if self.load_check.isChecked() or self.temporary_check.isChecked():
                added = self.iface.addVectorLayer(dest, 'Vista Saga — Avaliação Espacial vetorial', 'ogr')
                if not added or not added.isValid():
                    self.status.setText('Arquivo criado, mas não foi possível adicioná-lo ao QGIS.')
            self.status.setText('Avaliação vetorial concluída: ' + dest)
            QMessageBox.information(self, 'Avaliação concluída',
                f'Feições: {result["total"]}\nAvaliadas: {result["validos"]}\n'
                f'Sem avaliação: {result["excluidos_ou_sem_dado"]}\n'
                f'Área total: {result["area_total_ha"]:.4f} ha\n'
                f'Área avaliada: {result["area_avaliada_ha"]:.4f} ha\n\nSaída: {dest}'
                + (f'\nCSV: {result["relatorio_csv"]}' if result.get('relatorio_csv') else '')
                + (f'\nTXT: {result["relatorio_txt"]}' if result.get('relatorio_txt') else ''))
        except (OSError, ValueError, InterruptedError, RuntimeError) as exc:
            QMessageBox.warning(self, 'Avaliação vetorial não concluída', str(exc))
        finally:
            self.running = False
            self.run_button.setEnabled(True)
            self.close_button.setEnabled(True)

    def closeEvent(self, event):
        if self.running:
            event.ignore()
        else:
            event.accept()
