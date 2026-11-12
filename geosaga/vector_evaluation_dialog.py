"""Avaliação — modalidade vetorial por atributos, QGIS 4 / Qt6.

Esta janela não altera o formulário raster nem oferece fluxo Processing.
O leiaute segue o da guia Raster: projeto, escala das notas, (1) critérios e
pesos, (2) classes do critério selecionado, (3) resultado.
"""
from .i18n import tr
import json
import os
from collections import Counter

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QApplication, QAbstractItemView, QComboBox, QFileDialog, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QMessageBox, QProgressDialog, QPushButton,
    QSplitter, QTableWidget, QVBoxLayout, QWidget, QDoubleSpinBox,
)
from qgis.core import Qgis, QgsProject, QgsVectorLayer
from qgis.gui import QgsMapLayerComboBox
from .ui_shared import (
    HeaderSort, OutputSection, class_sort_key, install_column_tab_navigation, VECTOR_OUTPUT_HINT, cell_check, centered_check, materialize_in_memory,
    open_polygon_files, load_vector_source, score_spin, table_item, temporary_destination,
    vector_start_directory, weight_spin,
)

from .evaluation_config import (
    SUFFIX, apply_saved, build_config, config_path_for, read_config, write_config,
)
from .vector_evaluation_core import category_key, validate_criteria
from .vector_evaluation_writer import evaluate_vector_layer

MAX_CATEGORIES = 256
COL_CLASS, COL_COUNT, COL_SCORE, COL_SKIP = range(4)


def button(text, callback, tooltip=''):
    widget = QPushButton(tr(text))
    widget.clicked.connect(callback)
    if tooltip:
        widget.setToolTip(tr(tooltip))
    return widget


def locked(text):
    return table_item(text)


def scan_categories(layer, field):
    """Conta as feições por classe; recusa campos contínuos (> 256 classes)."""
    counts = Counter()
    missing = 0
    for feature in layer.getFeatures():
        key = category_key(feature[field])
        if key is None:
            missing += 1
            continue
        counts[key] += 1
        if len(counts) > MAX_CATEGORIES:
            raise ValueError(f'{layer.name()} / {field}: há mais de 256 classes. '
                             'Reclassifique o campo por intervalos antes da avaliação; '
                             'esta modalidade aplica notas a classes discretas.')
    if not counts:
        raise ValueError(f'{layer.name()} / {field}: o campo não contém classes válidas.')
    return dict(counts), missing


class VectorEvaluationDialog(QWidget):
    """Reusable evaluation form (QWidget inside tabs or standalone window)."""

    MODALITY = 'atributos'
    WINDOW_TITLE = 'Vista Saga Plugin — Avaliação vetorial'
    HEADING = '<b>AVALIAÇÃO ESPACIAL — VETOR POR ATRIBUTOS</b>'
    INTRO = ('Selecione uma camada de polígonos. Cada campo temático constitui um critério: '
             'atribua pesos e notas às classes. A geometria das feições será preservada. '
             'Não há sobreposição entre camadas nesta modalidade.')
    SOURCES_TITLE = '1. Campos temáticos e pesos'
    CLASSES_TITLE = '2. Classes do campo selecionado'
    CRITERION_HEADER = 'Campo'
    EMPTY_CLASSES = 'Selecione um campo à esquerda.'
    START_STATUS = 'Selecione um campo temático para iniciar.'
    RESULT_PREFIX = 'avaliacao_atributos'
    RESULT_NAME = 'Vista Saga — Avaliação vetorial'
    RUN_TEXT = 'Executar avaliação'

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
        self.project_path = ''
        self._last_scale = 10
        self.setWindowTitle(tr(self.WINDOW_TITLE))
        self.setMinimumSize(850, 600)
        self.resize(1070, 740)
        self._build()
        self._populate_fields()

    # ------------------------------------------------------------------ leiaute
    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(9)
        root.addWidget(QLabel(tr(self.HEADING)))
        intro = QLabel(tr(self.INTRO))
        intro.setWordWrap(True)
        root.addWidget(intro)

        top = QHBoxLayout()
        top.addWidget(button('Novo projeto', self.new_project))
        top.addWidget(button('Abrir projeto…', self.open_project,
                             'Reabre pesos, notas e classes não avaliadas de uma avaliação anterior.'))
        top.addWidget(button('Salvar projeto…', self.save_project,
                             'Salva pesos, notas e classes não avaliadas para reaproveitá-los.'))
        top.addStretch(1)
        root.addLayout(top)

        meta = QHBoxLayout()
        meta.addWidget(QLabel(tr('Escala das notas:')))
        self.scale_combo = QComboBox()
        self.scale_combo.addItem(tr('0 a 10'), 10)
        self.scale_combo.addItem(tr('0 a 100'), 100)
        self.scale_combo.currentIndexChanged.connect(self._update_score_limits)
        meta.addWidget(self.scale_combo)
        meta.addStretch(1)
        root.addLayout(meta)

        split = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(split, stretch=1)
        left = QGroupBox(tr(self.SOURCES_TITLE))
        ll = QVBoxLayout(left)
        self._build_source_controls(ll)
        self.criteria_table = QTableWidget(0, 3)
        self.criteria_table.setHorizontalHeaderLabels(
            [tr(self.CRITERION_HEADER), tr('Peso (%)'), tr('Classes')])
        self.criteria_table.verticalHeader().setVisible(False)
        self.criteria_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.criteria_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.criteria_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        head = self.criteria_table.horizontalHeader()
        head.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        head.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        head.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.criteria_table.itemSelectionChanged.connect(self._criterion_selected)
        self._weight_tab = install_column_tab_navigation(self.criteria_table, 1)
        ll.addWidget(self.criteria_table, stretch=1)
        ll.addWidget(button('Distribuir pesos igualmente', self.distribute_weights,
                            'Volta a dividir 100% igualmente entre os critérios, '
                            'desfazendo pesos digitados.'))
        self.weights_label = QLabel(tr('Nenhum critério selecionado.'))
        self.weights_label.setWordWrap(True)
        ll.addWidget(self.weights_label)
        split.addWidget(left)

        right = QGroupBox(tr(self.CLASSES_TITLE))
        rl = QVBoxLayout(right)
        self.class_label = QLabel(tr(self.EMPTY_CLASSES))
        self.class_label.setWordWrap(True)
        rl.addWidget(self.class_label)
        self.classes_table = QTableWidget(0, 4)
        self.classes_table.setHorizontalHeaderLabels(
            [tr('Classe'), tr('Feições'), tr('Nota'), tr('Não avaliar')])
        self.classes_table.verticalHeader().setVisible(False)
        self.classes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.classes_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.classes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        head = self.classes_table.horizontalHeader()
        head.setSectionResizeMode(COL_CLASS, QHeaderView.ResizeMode.Stretch)
        for column in (COL_COUNT, COL_SCORE, COL_SKIP):
            head.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self._score_tab = install_column_tab_navigation(self.classes_table, COL_SCORE)
        self.class_sort = HeaderSort(self.classes_table, (COL_CLASS, COL_COUNT, COL_SCORE, COL_SKIP),
                                     self._resort_classes)
        rl.addWidget(self.classes_table, stretch=1)
        batch = QHBoxLayout()
        batch.addWidget(QLabel(tr('Nota selecionada:')))
        self.batch_note = QDoubleSpinBox()
        self.batch_note.setRange(0, 10)
        self.batch_note.setDecimals(2)
        self.batch_note.setSingleStep(1)
        batch.addWidget(self.batch_note)
        batch.addWidget(button('Aplicar às classes marcadas', self.apply_note))
        batch.addStretch(1)
        rl.addLayout(batch)
        tip = QLabel(tr('Clique nas notas para editá-las. A nota “—” significa não definida: '
                        'a avaliação só é executada quando todas as classes têm nota ou estão '
                        'marcadas em “Não avaliar”. Marcar “Não avaliar” deixa a feição sem nota '
                        '(AVALIACAO nula), mas ela permanece no GeoPackage. '
                        'Valores nulos no campo também deixam a feição sem nota.'))
        tip.setWordWrap(True)
        rl.addWidget(tip)
        split.addWidget(right)
        split.setSizes([435, 635])

        self.output = OutputSection(self.select_output, '[Camada temporária em memória]',
                                    VECTOR_OUTPUT_HINT)
        self.output_edit = self.output.edit
        self.csv_check = self.output.csv_check
        self.txt_check = self.output.txt_check
        root.addWidget(self.output.group)

        foot = QHBoxLayout()
        self.status = QLabel(tr(self.START_STATUS))
        self.status.setWordWrap(True)
        foot.addWidget(self.status, stretch=1)
        foot.addWidget(button('Validar', self.validate_configuration))
        self.run_button = button(self.RUN_TEXT, self.execute)
        foot.addWidget(self.run_button)
        self.close_button = button('Fechar', self._close_form)
        foot.addWidget(self.close_button)
        root.addLayout(foot)

    def _build_source_controls(self, layout):
        """Atributos: uma camada e vários campos dela."""
        layer_row = QHBoxLayout()
        layer_row.addWidget(QLabel(tr('Camada:')))
        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(Qgis.LayerFilter.PolygonLayer)
        self.layer_combo.setAllowEmptyLayer(True, tr('— selecione um polígono —'))
        self.layer_combo.layerChanged.connect(self._layer_changed)
        layer_row.addWidget(self.layer_combo, 1)
        layer_row.addWidget(button('Atualizar', self._populate_fields,
                                   'Atualiza a lista de campos da camada selecionada.'))
        layer_row.addWidget(button('Arquivo…', self.add_file,
                                   'Abre uma camada de polígonos em arquivo, adiciona-a ao '
                                   'projeto QGIS e a seleciona.'))
        layout.addLayout(layer_row)
        field_row = QHBoxLayout()
        field_row.addWidget(QLabel(tr('Campo:')))
        self.field_combo = QComboBox()
        field_row.addWidget(self.field_combo, 1)
        field_row.addWidget(button('Adicionar campo', self.add_field))
        field_row.addWidget(button('Remover', self.remove_field))
        layout.addLayout(field_row)

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

    # ------------------------------------------------------------ camada e campos
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

    def add_file(self):
        layers, warnings = open_polygon_files(
            self, 'Abrir camada de polígonos',
            vector_start_directory([self._layer().source()] if self._layer() else []),
            multiple=False)
        if layers:
            self.layer_combo.setLayer(layers[0])
        if warnings:
            QMessageBox.warning(self, tr('Avaliação vetorial'), '\n'.join(warnings))

    def _new_criterion(self, layer, field):
        """Cria o critério de um campo; ValueError com mensagem ao usuário."""
        if any(x['field'] == field for x in self.criteria):
            raise ValueError('Este campo já está incluído.')
        counts, missing = scan_categories(layer, field)
        return {'field': field, 'counts': counts, 'missing': missing,
                'weight': 0., 'notes': {}, 'excluded': set()}

    def _criterion_source(self, criterion):
        layer = self._layer()
        return (layer.name(), layer.source()) if layer else ('', '')

    def _criterion_field(self, criterion):
        return criterion['field']

    def add_field(self):
        layer = self._layer()
        field = self.field_combo.currentText()
        if not layer or not field:
            QMessageBox.warning(self, tr('Avaliação vetorial'), tr('Selecione uma camada e um campo.'))
            return
        try:
            criterion = self._new_criterion(layer, field)
        except ValueError as exc:
            QMessageBox.warning(self, tr('Avaliação vetorial'), tr(str(exc)))
            return
        self._append(criterion)
        self.status.setText(tr('Campo {field}: {count} classes; {missing} feições sem dados.').format(
            field=field, count=len(criterion['counts']), missing=criterion['missing']))

    def _append(self, criterion, distribute=True):
        self._save_classes()
        self.criteria.append(criterion)
        if distribute:
            self._distribute()
        self._render_criteria(select=len(self.criteria) - 1)

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
        self._render_criteria(select=min(indices[-1], len(self.criteria) - 1))

    # --------------------------------------------------------------------- pesos
    def _distribute(self):
        n = len(self.criteria)
        if n:
            weights = [round(100. / n, 2)] * (n - 1)
            weights.append(round(100 - sum(weights), 2))
            for criterion, weight in zip(self.criteria, weights):
                criterion['weight'] = weight

    def distribute_weights(self):
        self._save_classes()
        self._distribute()
        self._render_criteria(select=self.criteria_table.currentRow())

    def _criterion_label(self, criterion):
        return criterion['field']

    def _render_criteria(self, select=None):
        self._rendering = True
        self.criteria_table.setRowCount(len(self.criteria))
        for row, criterion in enumerate(self.criteria):
            self.criteria_table.setItem(row, 0, table_item(self._criterion_label(criterion), numeric=False))
            spin = weight_spin(criterion['weight'], lambda value, i=row: self._weight_changed(i, value))
            spin.installEventFilter(self._weight_tab)
            self.criteria_table.setCellWidget(row, 1, spin)
            self.criteria_table.setItem(row, 2, table_item(len(criterion['counts']), numeric=True))
        self._rendering = False
        self.active = -1
        if select is not None and 0 <= select < len(self.criteria):
            self.criteria_table.selectRow(select)
            self._criterion_selected()
        else:
            self.classes_table.setRowCount(0)
            self.class_label.setText(tr(self.EMPTY_CLASSES))
        self._update_weight_status()

    def _weight_changed(self, index, value):
        if not self._rendering and 0 <= index < len(self.criteria):
            self.criteria[index]['weight'] = value
            self._update_weight_status()

    def _update_weight_status(self):
        total = sum(c['weight'] for c in self.criteria)
        if not self.criteria:
            self.weights_label.setText(tr('Nenhum critério selecionado.'))
        elif abs(total - 100) <= .011 and all(c['weight'] > 0 for c in self.criteria):
            self.weights_label.setText(tr('Pesos: 100,00% — distribuição válida.'))
        else:
            self.weights_label.setText(
                tr('Pesos: {total:.2f}% | Falta para 100%: {remaining:+.2f} ponto(s). '
                   'Todos os critérios precisam ter peso maior que zero.').format(
                    total=total, remaining=round(100 - total, 3)))

    # -------------------------------------------------------------------- classes
    def _save_classes(self):
        if self._rendering or not 0 <= self.active < len(self.criteria):
            return
        criterion = self.criteria[self.active]
        notes = {}
        excluded = set()
        for row in range(self.classes_table.rowCount()):
            key = self.classes_table.item(row, COL_CLASS).data(Qt.ItemDataRole.UserRole)
            check = cell_check(self.classes_table, row, COL_SKIP)
            spin = self.classes_table.cellWidget(row, COL_SCORE)
            if check is not None and check.isChecked():
                excluded.add(key)
            elif spin is not None and spin.value() >= 0:
                notes[key] = spin.value()
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
            self.class_label.setText(tr(self.EMPTY_CLASSES))
            return
        criterion = self.criteria[next_index]
        categories = self._ordered_classes(criterion)
        scale = self._scale()
        self._rendering = True
        self.classes_table.setRowCount(len(categories))
        for row, key in enumerate(categories):
            item = table_item(key)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.classes_table.setItem(row, COL_CLASS, item)
            self.classes_table.setItem(row, COL_COUNT, table_item(criterion['counts'][key], numeric=True))
            note = criterion['notes'].get(key)
            spin = score_spin(scale, None if note is None else min(float(note), scale))
            spin.installEventFilter(self._score_tab)
            self.classes_table.setCellWidget(row, COL_SCORE, spin)
            holder, check = centered_check(key in criterion['excluded'],
                                           'Deixa sem nota as feições desta classe.')
            spin.setEnabled(not check.isChecked())
            check.toggled.connect(lambda checked, target=spin: target.setEnabled(not checked))
            self.classes_table.setCellWidget(row, COL_SKIP, holder)
        self._rendering = False
        self.class_label.setText(tr('{field}: {count} classes válidas.').format(
            field=self._criterion_label(criterion), count=len(categories)))

    def _ordered_classes(self, criterion):
        counts, notes, excluded = criterion['counts'], criterion['notes'], criterion['excluded']
        return self.class_sort.order(counts, {
            COL_CLASS: class_sort_key,
            COL_COUNT: lambda k: (counts[k], class_sort_key(k)),
            COL_SCORE: lambda k: (-2.0 if k in excluded else float(notes.get(k, -1)), class_sort_key(k)),
            COL_SKIP: lambda k: (k in excluded, class_sort_key(k)),
        })

    def _resort_classes(self):
        """Reconstrói a tabela de classes na ordem do cabeçalho, sem perder notas."""
        self._save_classes()
        self.active = -1
        self._criterion_selected()

    def apply_note(self):
        if self.active < 0:
            return
        rows = {index.row() for index in self.classes_table.selectedIndexes()}
        if not rows:
            QMessageBox.information(self, tr('Vista Saga'),
                                    tr('Selecione uma ou mais classes na tabela de notas.'))
            return
        for row in rows:
            spin = self.classes_table.cellWidget(row, COL_SCORE)
            check = cell_check(self.classes_table, row, COL_SKIP)
            if spin is not None and check is not None and not check.isChecked():
                spin.setValue(self.batch_note.value())
        self._save_classes()

    def _scale(self):
        return int(self.scale_combo.currentData())

    def _update_score_limits(self):
        if not hasattr(self, 'batch_note'):
            return
        self._save_classes()
        scale = self._scale()
        if scale < self._last_scale and any(
                float(v) > scale for c in self.criteria for v in c['notes'].values()):
            QMessageBox.warning(self, tr('Notas fora da nova escala'),
                                tr('Há notas acima do limite solicitado. Corrija-as antes de alterar a escala.'))
            self.scale_combo.blockSignals(True)
            self.scale_combo.setCurrentIndex(self.scale_combo.findData(self._last_scale))
            self.scale_combo.blockSignals(False)
            return
        self._last_scale = scale
        self.batch_note.setMaximum(scale)
        for row in range(self.classes_table.rowCount()):
            spin = self.classes_table.cellWidget(row, COL_SCORE)
            if spin is not None:
                spin.setMaximum(scale)
        self.status.setText(tr('Escala de notas: 0 a {scale}. Revise as notas ao mudar a escala.').format(scale=scale))

    # ------------------------------------------------------------------- regras
    def _engine_criteria(self):
        return [{'field': c['field'], 'weight': c['weight'], 'categories': set(c['counts']),
                 'notes': dict(c['notes']), 'excluded': set(c['excluded'])}
                for c in self.criteria]

    def _rules(self):
        self._save_classes()
        return validate_criteria(self._engine_criteria(), scale=self._scale())

    def validate_configuration(self):
        try:
            rules = self._rules()
            layer = self._layer()
            if not layer:
                raise ValueError('Selecione uma camada de polígonos válida.')
            if layer.isEditable():
                raise ValueError('Salve as alterações da camada antes de avaliar.')
            QMessageBox.information(self, tr('Avaliação vetorial'),
                tr(f'Configuração válida: {len(rules)} critérios; {layer.featureCount()} feições. '
                'As feições excluídas ou sem dado terão avaliação nula.'))
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, tr('Regras incompletas'), tr(str(exc)))

    # ---------------------------------------------------------- pesos e notas
    def _config_records(self):
        self._save_classes()
        records = []
        for c in self.criteria:
            name, source = self._criterion_source(c)
            records.append({'camada': name, 'fonte': source, 'campo': self._criterion_field(c),
                            'peso': c['weight'], 'notas': c['notes'], 'nao_avaliar': c['excluded']})
        return records

    def _write_config(self, path):
        return write_config(path, build_config(self.MODALITY, self._scale(), self._config_records(),
                                               os.path.dirname(os.path.abspath(path))))

    def save_project(self):
        if not self.criteria:
            QMessageBox.information(self, tr('Vista Saga'), tr('Não há critérios para salvar.'))
            return
        suggestion = self.project_path or os.path.join(
            vector_start_directory([self._criterion_source(c)[1] for c in self.criteria]),
            self.RESULT_PREFIX + SUFFIX)
        filename, _ = QFileDialog.getSaveFileName(self, tr('Salvar projeto Vista Saga'), suggestion,
                                                  tr('Projetos Vista Saga (*.geosaga.json)'))
        if not filename:
            return
        if not filename.lower().endswith(SUFFIX):
            filename += SUFFIX
        try:
            self.project_path = self._write_config(filename)
            self.status.setText(tr('Projeto salvo: ') + filename)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, tr('Vista Saga'), tr(f'Falha ao salvar projeto:\n{exc}'))

    def new_project(self):
        if self.running:
            return
        if self.criteria and QMessageBox.question(self, tr('Novo projeto'),
                tr('Descartar a configuração atual (se não estiver salva)?')) != QMessageBox.StandardButton.Yes:
            return
        self._clear_criteria()
        self.project_path = ''
        self.output_edit.clear()
        self.scale_combo.setCurrentIndex(0)
        self.status.setText(tr('Novo projeto criado.'))

    def _clear_criteria(self):
        self.criteria.clear()
        self.active = -1
        self._render_criteria()

    def open_project(self):
        if self.running:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, tr('Abrir projeto Vista Saga'), os.path.dirname(self.project_path) or vector_start_directory(),
            tr('Projetos Vista Saga (*.geosaga.json *.json)'))
        if not path:
            return
        try:
            saved = read_config(path, self.MODALITY)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, tr('Vista Saga — Projeto inválido'), tr(str(exc)))
            return
        if self.criteria and QMessageBox.question(self, tr('Carregar projeto'),
                tr('Substituir a configuração atual pelo projeto salvo?')) != QMessageBox.StandardButton.Yes:
            return
        self.scale_combo.blockSignals(True)
        self.scale_combo.setCurrentIndex(self.scale_combo.findData(saved['escala']))
        self.scale_combo.blockSignals(False)
        self._last_scale = saved['escala']
        self.batch_note.setMaximum(saved['escala'])
        problems = self._restore(saved['criterios'])
        self.project_path = path
        restored = len(self.criteria)
        self.status.setText(tr('Projeto carregado: {count} critério(s).').format(count=restored))
        if problems:
            QMessageBox.warning(self, tr('Projeto carregado com pendências'), '\n'.join(problems))

    def _restore(self, records):
        """Atributos: a camada da primeira linha; todos os campos dela."""
        problems = []
        first = records[0]
        layer = load_vector_source(first['fonte'], first['camada']) if first['fonte'] else None
        if layer is None:
            layer = self._layer()
            if layer is None:
                return [tr('Camada não encontrada: {source}. Selecione-a e abra o projeto novamente.').format(
                    source=first['fonte'] or first['camada'])]
            problems.append(tr('Camada original não encontrada; os campos foram aplicados a {layer}.').format(
                layer=layer.name()))
        self.layer_combo.setLayer(layer)  # limpa a pilha atual
        self._clear_criteria()
        for rec in records:
            if rec['campo'] not in layer.fields().names():
                problems.append(tr('{layer}: o campo {field} não existe.').format(
                    layer=layer.name(), field=rec['campo']))
                continue
            try:
                criterion = self._new_criterion(layer, rec['campo'])
            except ValueError as exc:
                problems.append(tr(str(exc)))
                continue
            problems.extend(self._apply_record(criterion, rec))
        return problems

    def _apply_record(self, criterion, rec):
        obsolete, pending = apply_saved(criterion, rec)
        self._append(criterion, distribute=False)
        notes = []
        label = self._criterion_label(criterion)
        if obsolete:
            notes.append(tr('{label}: {count} classe(s) do projeto não existem mais na camada.').format(
                label=label, count=len(obsolete)))
        if pending:
            notes.append(tr('{label}: {count} classe(s) novas sem nota.').format(
                label=label, count=len(pending)))
        return notes

    # ------------------------------------------------------------------ resultado
    def select_output(self):
        suggestion = self.output_edit.text() or os.path.join(
            vector_start_directory([self._criterion_source(c)[1] for c in self.criteria]),
            self.RESULT_PREFIX + '.gpkg')
        dest, _ = QFileDialog.getSaveFileName(self, tr('Salvar avaliação vetorial'), suggestion,
                                              'GeoPackage (*.gpkg)')
        if dest:
            self.output_edit.setText(dest if dest.lower().endswith('.gpkg') else dest + '.gpkg')

    def _destination(self):
        """(caminho, temporário?). Pergunta antes de substituir um arquivo do usuário."""
        if self.output.is_temporary():
            return os.path.abspath(temporary_destination(self.RESULT_PREFIX, '.gpkg')), True
        dest = self.output.path()
        if not dest.lower().endswith('.gpkg'):
            dest += '.gpkg'
        dest = os.path.abspath(dest)
        if os.path.exists(dest) and QMessageBox.question(
                self, tr('Substituir resultado?'),
                tr('O GeoPackage já existe. Deseja substituí-lo?\n'
                   'Se estiver aberto no QGIS, remova a camada de saída antes de continuar.')
        ) != QMessageBox.StandardButton.Yes:
            return None, False
        return dest, False

    def _check_inputs(self):
        self._rules()  # valida as regras antes de abrir a camada
        if not self._layer():
            raise ValueError('Selecione uma camada poligonal válida.')

    def _run_engine(self, dest, update, cancelled):
        return evaluate_vector_layer(
            self._layer(), self._engine_criteria(), self._scale(), dest,
            progress=update, cancelled=cancelled,
            report_csv=self.csv_check.isChecked(), report_txt=self.txt_check.isChecked())

    def _summary_text(self, result, dest):
        return tr(f'Feições: {result["total"]}\nAvaliadas: {result["validos"]}\n'
                  f'Sem avaliação: {result["excluidos_ou_sem_dado"]}\n'
                  f'Área total: {result["area_total_ha"]:.4f} ha\n'
                  f'Área avaliada: {result["area_avaliada_ha"]:.4f} ha\n\nSaída: {dest}')

    def _load_result(self, dest, temporary):
        """Temporário: camada em memória; senão, o GeoPackage salvo."""
        if temporary:
            layer = materialize_in_memory(dest, self.RESULT_NAME)
            if layer is not None:
                QgsProject.instance().addMapLayer(layer)
            return layer
        layer = self.iface.addVectorLayer(dest, self.RESULT_NAME, 'ogr')
        return layer if layer and layer.isValid() else None

    def execute(self):
        if self.running:
            return
        try:
            self._check_inputs()
            dest, temporary = self._destination()
            if not dest:
                return
            self.running = True
            self.run_button.setEnabled(False)
            self.close_button.setEnabled(False)
            progress = QProgressDialog(tr('Calculando notas das feições…'), tr('Cancelar'), 0, 100, self)
            progress.setMinimumDuration(0)
            progress.setWindowModality(Qt.WindowModality.WindowModal)

            def update(pct):
                if pct is not None:
                    progress.setValue(max(0, min(100, int(pct))))
                QApplication.processEvents()
            try:
                result = self._run_engine(dest, update, progress.wasCanceled)
            finally:
                progress.close()
            message = self._summary_text(result, dest if not temporary else tr('camada temporária em memória'))
            if result.get('relatorio_csv'):
                message += '\n' + tr('Relatório CSV: ') + result['relatorio_csv']
            if result.get('relatorio_txt'):
                message += '\n' + tr('Relatório TXT: ') + result['relatorio_txt']
            try:
                message += '\n' + tr('Pesos e notas: ') + self._write_config(config_path_for(dest))
            except (OSError, ValueError) as exc:
                message += '\n' + tr('Atenção: não foi possível gravar os pesos e as notas: ') + str(exc)
            if self._load_result(dest, temporary) is None:
                message += '\n\n' + tr('Atenção: não foi possível carregar o resultado no QGIS.')
            self.status.setText(tr('Avaliação concluída.'))
            QMessageBox.information(self, tr('Avaliação concluída'), message)
        except (OSError, ValueError, TypeError, InterruptedError, RuntimeError) as exc:
            QMessageBox.warning(self, tr('Avaliação vetorial não concluída'), tr(str(exc)))
        finally:
            self.running = False
            self.run_button.setEnabled(True)
            self.close_button.setEnabled(True)

    def closeEvent(self, event):
        if self.running:
            event.ignore()
        else:
            event.accept()
