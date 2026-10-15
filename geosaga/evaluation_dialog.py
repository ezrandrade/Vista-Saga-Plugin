"""Interface visual de Avaliação para QGIS 4.x / Qt6.

A classe evita editar JSON: usa tabelas, botões e camadas do projeto QGIS.
"""
import json
import os
import math
import traceback
from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QApplication, QAbstractItemView, QCheckBox, QComboBox, QDialog,
    QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMessageBox, QProgressDialog,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QTabWidget, QScrollArea, QFrame,
)
from qgis.core import QgsApplication, QgsProject, QgsRasterLayer, QgsPalettedRasterRenderer, QgsMessageLog, Qgis

from .evaluation_task import EvaluationTask
from .ui_shared import choose_project_layers, temporary_destination
from .raster_engine import file_source, open_raster, same_grid, scan_classes


def button(text, callback, tooltip=''):
    b = QPushButton(text)
    b.clicked.connect(callback)
    if tooltip:
        b.setToolTip(tooltip)
    return b


def view_item(value, editable=False):
    item = QTableWidgetItem(str(value))
    flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    if editable:
        flags |= Qt.ItemFlag.ItemIsEditable
    item.setFlags(flags)
    return item


class EvaluationDialog(QDialog):
    PROJECT_VERSION = 1

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.entries = []
        self._rendering = False
        self.current_index = -1
        self._task = None
        self.project_path = ''
        self._last_scale = 10
        self.setWindowTitle('Vista Saga Plugin — Avaliação')
        self.setMinimumSize(900, 610)
        self.resize(1110, 770)
        self.setModal(False)
        self._setup_ui()
        self.refresh_available()
        self._render_maps()
        self._refresh_weight_status()
        self.analysis_tabs.currentChanged.connect(self._on_analysis_tab_changed)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        self.analysis_tabs = QTabWidget()
        root.addWidget(self.analysis_tabs)
        raster_page = QWidget()
        outer = QVBoxLayout(raster_page)
        outer.setSpacing(9)
        self.analysis_tabs.addTab(raster_page, 'Raster')
        # As modalidades vetoriais são formulários completos, não botões para
        # abrir uma segunda janela. Instanciação sob demanda preserva o arranque.
        self.attributes_scroll = QScrollArea()
        self.attributes_scroll.setWidgetResizable(True)
        self.attributes_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.analysis_tabs.addTab(self.attributes_scroll, 'Vetorial — atributos')
        self.overlay_scroll = QScrollArea()
        self.overlay_scroll.setWidgetResizable(True)
        self.overlay_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.analysis_tabs.addTab(self.overlay_scroll, 'Vetorial — sobreposição')
        heading = QLabel('<b>AVALIAÇÃO ESPACIAL — PESOS E NOTAS</b>')
        outer.addWidget(heading)
        info = QLabel('Selecione mapas categóricos, informe o peso de cada tema e atribua notas às suas classes. '
                      'Classes bloqueadas não serão avaliadas.')
        info.setWordWrap(True)
        outer.addWidget(info)


        top = QHBoxLayout()
        top.addWidget(button('Novo projeto', self.new_project))
        top.addWidget(button('Abrir projeto…', self.open_project))
        top.addWidget(button('Salvar projeto…', self.save_project))
        top.addStretch(1)
        outer.addLayout(top)

        meta = QHBoxLayout()
        meta.addWidget(QLabel('Título:'))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText('Título da carta de avaliação')
        meta.addWidget(self.title_edit, 3)
        meta.addWidget(QLabel('Autor:'))
        self.author_edit = QLineEdit()
        meta.addWidget(self.author_edit, 2)
        meta.addWidget(QLabel('Escala:'))
        self.scale_combo = QComboBox()
        self.scale_combo.addItem('0 a 10', 10)
        self.scale_combo.addItem('0 a 100', 100)
        self.scale_combo.currentIndexChanged.connect(self._update_score_limits)
        meta.addWidget(self.scale_combo)
        outer.addLayout(meta)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(splitter, stretch=1)

        left = QGroupBox('1. Mapas temáticos e pesos')
        left_layout = QVBoxLayout(left)
        layer_row = QHBoxLayout()
        self.layer_combo = QComboBox()
        self.layer_combo.setMinimumWidth(210)
        layer_row.addWidget(self.layer_combo, 1)
        layer_row.addWidget(button('Adicionar', self.add_current_layer))
        layer_row.addWidget(button('Adicionar várias…', self.add_project_many))
        left_layout.addLayout(layer_row)
        actions = QHBoxLayout()
        actions.addWidget(button('Atualizar', self.refresh_available,
                                 'Atualiza a lista de camadas raster carregadas no QGIS.'))
        actions.addWidget(button('Arquivo(s)…', self.add_file,
                                 'Carregar um raster em arquivo para o projeto QGIS e adicioná-lo à avaliação.'))
        actions.addWidget(button('Remover', self.remove_map))
        actions.addStretch()
        left_layout.addLayout(actions)

        self.map_table = QTableWidget(0, 3)
        self.map_table.setHorizontalHeaderLabels(['Mapa', 'Peso (%)', 'Classes'])
        self.map_table.verticalHeader().setVisible(False)
        self.map_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.map_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.map_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.map_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.map_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.map_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.map_table.itemSelectionChanged.connect(self._map_selected)
        left_layout.addWidget(self.map_table, stretch=1)
        left_layout.addWidget(button('Distribuir pesos igualmente', self.distribute_weights))
        self.weight_label = QLabel()
        self.weight_label.setWordWrap(True)
        left_layout.addWidget(self.weight_label)
        splitter.addWidget(left)

        right = QGroupBox('2. Categorias do mapa selecionado')
        right_layout = QVBoxLayout(right)
        self.class_info = QLabel('Selecione um mapa à esquerda.')
        self.class_info.setWordWrap(True)
        right_layout.addWidget(self.class_info)
        self.class_table = QTableWidget(0, 4)
        self.class_table.setHorizontalHeaderLabels(['Classe', 'Descrição', 'Nota', 'Não avaliar'])
        self.class_table.verticalHeader().setVisible(False)
        self.class_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.class_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.class_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        head = self.class_table.horizontalHeader()
        head.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        head.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        head.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        head.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        right_layout.addWidget(self.class_table, stretch=1)
        assign = QHBoxLayout()
        assign.addWidget(QLabel('Nota selecionada:'))
        self.batch_score = QDoubleSpinBox()
        self.batch_score.setDecimals(2)
        self.batch_score.setRange(0, 10)
        self.batch_score.setSingleStep(1)
        assign.addWidget(self.batch_score)
        assign.addWidget(button('Aplicar às classes marcadas', self.apply_score))
        assign.addStretch()
        right_layout.addLayout(assign)
        hint = QLabel('Clique nas notas para editá-las. A nota “—” significa não definida. '
                      'Marcar “Não avaliar” transforma os pixels da classe em NoData.')
        hint.setWordWrap(True)
        right_layout.addWidget(hint)
        splitter.addWidget(right)
        splitter.setSizes([410, 660])

        output_group = QGroupBox('3. Resultado')
        output_layout = QVBoxLayout(output_group)
        output_row = QHBoxLayout()
        output_row.addWidget(QLabel('Carta GeoTIFF:'))
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText('Selecione onde salvar a carta de avaliação espacial (.tif)')
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(button('Procurar…', self.select_output))
        output_layout.addLayout(output_row)
        self.temporary_check = QCheckBox('Resultado temporário no QGIS (pode ser salvo posteriormente)')
        self.temporary_check.setChecked(True)
        output_layout.addWidget(self.temporary_check)
        self.output_edit.setEnabled(False)
        self.temporary_check.toggled.connect(lambda active: self.output_edit.setEnabled(not active))
        opts = QHBoxLayout()
        self.csv_check = QCheckBox('Gerar relatório CSV (combinações, notas e áreas)')
        self.csv_check.setChecked(True)
        opts.addWidget(self.csv_check)
        self.txt_check = QCheckBox('Gerar relatório TXT (modelo Vista SAGA)')
        self.txt_check.setChecked(True)
        opts.addWidget(self.txt_check)
        self.load_check = QCheckBox('Adicionar resultado ao QGIS')
        self.load_check.setChecked(True)
        opts.addWidget(self.load_check)
        opts.addStretch()
        output_layout.addLayout(opts)
        outer.addWidget(output_group)
        footer = QHBoxLayout()
        self.status = QLabel('')
        self.status.setWordWrap(True)
        footer.addWidget(self.status, 1)
        self.validate_button = button('Validar', self.preview_validation)
        footer.addWidget(self.validate_button)
        self.execute_button = button('Executar avaliação', self.execute)
        self.execute_button.setDefault(True)
        footer.addWidget(self.execute_button)
        self.cancel_button = button('Cancelar execução', self.cancel_task)
        self.cancel_button.setEnabled(False)
        footer.addWidget(self.cancel_button)
        self.close_button = button('Fechar', self.close)
        footer.addWidget(self.close_button)
        outer.addLayout(footer)

    def _on_analysis_tab_changed(self, index):
        if index in (1, 2):
            self._show_embedded_evaluation(index)

    def _show_embedded_evaluation(self, index):
        """Embed a native QWidget instead of reparenting a running QDialog.

        The dedicated vector forms keep their established controls and engines.
        A failure is reported inside the tab and to the QGIS Python log rather
        than leaving a blank page with an uncaught exception.
        """
        scroll = self.attributes_scroll if index == 1 else self.overlay_scroll
        attribute = '_vector_dialog' if index == 1 else '_overlay_dialog'
        dialog = getattr(self, attribute, None)
        if dialog is None:
            try:
                if index == 1:
                    from .vector_evaluation_dialog import VectorEvaluationDialog
                    dialog_type = VectorEvaluationDialog
                else:
                    from .vector_overlay_dialog import VectorOverlayEvaluationDialog
                    dialog_type = VectorOverlayEvaluationDialog
                dialog = dialog_type(self.iface, parent=self, embedded=True)
                dialog.setMinimumSize(0, 0)
                scroll.setWidget(dialog)
                setattr(self, attribute, dialog)
            except Exception:
                details = traceback.format_exc()
                QgsMessageLog.logMessage(details, 'Vista Saga Plugin', Qgis.MessageLevel.Critical)
                if scroll.widget() is not None:
                    old = scroll.takeWidget()
                    old.deleteLater()
                error = QLabel(
                    'Não foi possível montar o formulário vetorial. '
                    'Consulte Exibir → Painéis → Mensagens de Log no QGIS, '
                    'na seção Vista Saga Plugin, para obter o erro detalhado.\n\n'
                    + details.splitlines()[-1]
                )
                error.setWordWrap(True)
                error.setAlignment(Qt.AlignmentFlag.AlignTop)
                scroll.setWidget(error)
                return
        dialog.show()

    def open_vector_evaluation(self):
        self.analysis_tabs.setCurrentIndex(1)
        self._show_embedded_evaluation(1)

    def open_vector_overlay(self):
        self.analysis_tabs.setCurrentIndex(2)
        self._show_embedded_evaluation(2)

    def _current_scale(self):
        return int(self.scale_combo.currentData())

    def _update_score_limits(self):
        if not hasattr(self, 'batch_score'):
            return
        scale = self._current_scale()
        if scale < self._last_scale:
            pending = any(float(value) > scale for e in self.entries for value in e['notes'].values())
            pending |= any(self.class_table.cellWidget(i, 2).value() > scale for i in range(self.class_table.rowCount()))
            if pending:
                QMessageBox.warning(self, 'Notas fora da nova escala',
                    'Há notas acima do limite solicitado. Corrija-as antes de alterar a escala.')
                self.scale_combo.blockSignals(True)
                self.scale_combo.setCurrentIndex(self.scale_combo.findData(self._last_scale))
                self.scale_combo.blockSignals(False)
                return
        self._last_scale = scale
        self.batch_score.setMaximum(scale)
        for row in range(self.class_table.rowCount()):
            spin = self.class_table.cellWidget(row, 2)
            if spin:
                spin.setMaximum(scale)
        self.status.setText(f'Escala de notas: 0 a {scale}. Revise as notas ao mudar a escala.')

    def refresh_available(self):
        selected = self.layer_combo.currentData()
        self.layer_combo.clear()
        available = [v for v in QgsProject.instance().mapLayers().values()
                     if isinstance(v, QgsRasterLayer) and v.isValid()]
        for layer in sorted(available, key=lambda k: k.name().casefold()):
            self.layer_combo.addItem(layer.name(), layer.id())
        found = self.layer_combo.findData(selected)
        if found >= 0:
            self.layer_combo.setCurrentIndex(found)

    def add_current_layer(self):
        layer_id = self.layer_combo.currentData()
        layer = QgsProject.instance().mapLayer(layer_id) if layer_id else None
        if layer is None:
            QMessageBox.warning(self, 'GeoSAGA', 'Selecione um raster do projeto QGIS.')
            return
        self._add_layer(layer)

    def add_project_many(self):
        for layer in choose_project_layers(self, 'raster', 'Adicionar vários mapas à avaliação'):
            self._add_layer(layer)

    def add_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'Selecionar mapas raster', '',
                                              'Rasters (*.tif *.tiff *.img *.asc *.vrt);;Todos os arquivos (*)')
        for path in paths:
            layer = self.iface.addRasterLayer(path, Path(path).stem)
            if not layer or not layer.isValid():
                QMessageBox.warning(self, 'GeoSAGA', f'Não foi possível carregar o raster: {path}')
                continue
            self.refresh_available()
            self._add_layer(layer)

    def _scan_with_progress(self, path):
        dlg = QProgressDialog('Identificando classes temáticas…', 'Cancelar', 0, 100, self)
        dlg.setWindowModality(Qt.WindowModality.WindowModal)
        dlg.setMinimumDuration(250)
        last_progress = [-1]
        def progress(percent):
            if percent != last_progress[0]:
                last_progress[0] = percent
                dlg.setValue(percent)
                QApplication.processEvents()
        try:
            return scan_classes(path, progress, dlg.wasCanceled)
        finally:
            dlg.setValue(100)

    def _add_layer(self, layer, restored=None, select=True):
        try:
            path = file_source(layer.source())
            if any(item['path'] == path for item in self.entries):
                raise ValueError('Este raster já foi adicionado à avaliação.')
            self.status.setText(f'Lendo as classes de {layer.name()}…')
            categories = self._scan_with_progress(path)
        except (ValueError, OSError, InterruptedError) as exc:
            QMessageBox.warning(self, 'Não foi possível adicionar o raster', str(exc))
            return False
        category_names = {}
        renderer = layer.renderer()
        if isinstance(renderer, QgsPalettedRasterRenderer):
            try:
                category_names = {str(int(c.value)) if float(c.value).is_integer() else format(float(c.value), '.15g'):
                                  c.label for c in renderer.classes() if c.label}
            except (AttributeError, TypeError, ValueError):
                category_names = {}
        entry = {
            'labels': category_names,
            'layer_id': layer.id(), 'name': layer.name(), 'path': path,
            'weight': float(restored.get('peso', 0)) if restored else 0.,
            'classes': categories,
            'notes': dict(restored.get('notas', {})) if restored else {},
            'blocked': list(restored.get('bloqueadas', [])) if restored else [],
        }
        self._save_current_notes()
        self.entries.append(entry)
        if restored is None:
            self._assign_equal_weights()
        self._render_maps(select=len(self.entries)-1 if select else None)
        self.status.setText(f'{len(categories)} categorias carregadas de {layer.name()}.')
        return True

    def remove_map(self):
        selected = sorted({item.row() for item in self.map_table.selectedItems()}, reverse=True)
        if not selected:
            return
        self._save_current_notes()
        for i in selected:
            if 0 <= i < len(self.entries):
                self.entries.pop(i)
        self._assign_equal_weights()
        self.current_index = -1
        self._render_maps(select=min(selected[-1], len(self.entries)-1))
        self._refresh_weight_status()

    def _assign_equal_weights(self):
        if not self.entries:
            return
        n = len(self.entries)
        vals = [round(100/n, 2)] * (n-1)
        vals.append(round(100-sum(vals), 2))
        for e, v in zip(self.entries, vals):
            e['weight'] = v

    def distribute_weights(self):
        if self._task:
            return
        self._assign_equal_weights()
        self._render_maps(select=self.map_table.currentRow())
        self._refresh_weight_status()

    def _weight_changed(self, index, weight):
        if 0 <= index < len(self.entries):
            self.entries[index]['weight'] = weight
            self._refresh_weight_status()

    def _refresh_weight_status(self):
        total = sum(e['weight'] for e in self.entries)
        remaining = round(100-total, 3)
        if not self.entries:
            self.weight_label.setText('Nenhum mapa selecionado.')
        elif abs(remaining) <= .011 and all(e['weight'] > 0 for e in self.entries):
            self.weight_label.setText('Pesos: 100,00% — distribuição válida.')
        else:
            self.weight_label.setText(
                f'Pesos: {total:.2f}% | Falta para 100%: {remaining:+.2f} ponto(s). '
                'Todos os mapas precisam ter peso maior que zero.')

    def _render_maps(self, select=None):
        self._rendering = True
        try:
            self.map_table.setRowCount(len(self.entries))
            for i, e in enumerate(self.entries):
                name_item = view_item(e['name'])
                name_item.setToolTip(e['path'])
                self.map_table.setItem(i, 0, name_item)
                spin = QDoubleSpinBox()
                spin.setRange(0, 100)
                spin.setDecimals(2)
                spin.setSuffix(' %')
                spin.setValue(e['weight'])
                spin.valueChanged.connect(lambda value, idx=i: self._weight_changed(idx, value))
                self.map_table.setCellWidget(i, 1, spin)
                self.map_table.setItem(i, 2, view_item(str(len(e['classes']))))
            if select is not None and 0 <= select < len(self.entries):
                self.map_table.selectRow(select)
                self.current_index = select
            elif not self.entries:
                self.current_index = -1
        finally:
            self._rendering = False
        self._render_classes()
        self._refresh_weight_status()

    def _map_selected(self):
        if self._rendering:
            return
        new_index = self.map_table.currentRow()
        if new_index == self.current_index:
            return
        self._save_current_notes()
        self.current_index = new_index
        self._render_classes()

    def _save_current_notes(self):
        index = self.current_index
        if not 0 <= index < len(self.entries):
            return
        entry = self.entries[index]
        scores, blocked = {}, []
        for r in range(self.class_table.rowCount()):
            code_item = self.class_table.item(r, 0)
            if code_item is None:
                continue
            code = code_item.text()
            check = self._get_skip(r)
            spin = self.class_table.cellWidget(r, 2)
            if check is not None and check.isChecked():
                blocked.append(code)
            elif spin is not None and spin.value() >= 0:
                scores[code] = spin.value()
        entry['notes'], entry['blocked'] = scores, blocked

    def _render_classes(self):
        self._rendering = True
        try:
            self.class_table.setRowCount(0)
            idx = self.current_index
            if not 0 <= idx < len(self.entries):
                self.class_info.setText('Selecione um mapa à esquerda.')
                return
            e = self.entries[idx]
            self.class_info.setText(f'<b>{e["name"]}</b> — {len(e["classes"])} classes identificadas '
                                    'na banda 1, excluindo NoData.')
            self.class_table.setRowCount(len(e['classes']))
            for r, (code, count) in enumerate(e['classes']):
                self.class_table.setItem(r, 0, view_item(code))
                class_name = e['labels'].get(code, '')
                count_text = f'{count:,}'.replace(',', '.')
                label = view_item(f'{class_name}  ({count_text} px)' if class_name else f'{count_text} pixels')
                label.setToolTip('Nome da classe quando disponível na legenda do QGIS; quantidade de pixels válidos.')
                self.class_table.setItem(r, 1, label)
                score = QDoubleSpinBox()
                score.setRange(-1, self._current_scale())
                score.setDecimals(2)
                score.setSingleStep(1)
                score.setSpecialValueText('—')
                score.setValue(float(e['notes'].get(code, -1)))
                self.class_table.setCellWidget(r, 2, score)
                skip = QCheckBox()
                skip.setToolTip('Exclui da avaliação os pixels desta classe.')
                skip.setChecked(code in e['blocked'])
                score.setEnabled(not skip.isChecked())
                skip.toggled.connect(lambda checked, target=score: target.setEnabled(not checked))
                center = QWidget()
                row_layout = QHBoxLayout(center)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.addStretch(1)
                row_layout.addWidget(skip)
                row_layout.addStretch(1)
                # cellWidget parent now container; _get_skip reads layout widget below.
                self.class_table.setCellWidget(r, 3, center)
        finally:
            self._rendering = False

    def _get_skip(self, row):
        wrapper = self.class_table.cellWidget(row, 3)
        return wrapper.findChild(QCheckBox) if wrapper else None

    def apply_score(self):
        rows = {i.row() for i in self.class_table.selectedIndexes()}
        if not rows:
            QMessageBox.information(self, 'GeoSAGA', 'Selecione uma ou mais classes na tabela de notas.')
            return
        for r in rows:
            spin = self.class_table.cellWidget(r, 2)
            skip = self._get_skip(r)
            if spin and skip and not skip.isChecked():
                spin.setValue(self.batch_score.value())
        self._save_current_notes()

    def _collect_configuration(self):
        self._save_current_notes()
        if not self.entries:
            raise ValueError('Adicione pelo menos um mapa temático.')
        total = sum(e['weight'] for e in self.entries)
        if abs(total - 100) > 0.011 or any(e['weight'] <= 0 for e in self.entries):
            raise ValueError(f'Os pesos precisam somar 100%, com pesos positivos. Soma atual: {total:.2f}%.')
        layers = []
        for e in self.entries:
            codes = {code for code, _ in e['classes']}
            notes = {str(k): v for k, v in e['notes'].items() if k in codes}
            blocked = {str(k) for k in e['blocked'] if k in codes}
            missing = codes - set(notes) - blocked
            if missing:
                excerpt = ', '.join(sorted(missing, key=float)[:8])
                raise ValueError(f'Mapa {e["name"]}: atribua notas ou bloqueie todas as classes. '
                                 f'Classes pendentes: {excerpt}.')
            scale = self._current_scale()
            for code, value in notes.items():
                if not math.isfinite(float(value)) or not 0 <= float(value) <= scale:
                    raise ValueError(f'Mapa {e["name"]}: nota {value} fora da escala 0–{scale} (classe {code}).')
            layers.append({'peso': e['weight'], 'notas': notes,
                           'bloqueadas': sorted(blocked, key=float)})
        datasets = [open_raster(e['path']) for e in self.entries]
        same_grid(datasets)
        return {'escala': self._current_scale(), 'camadas': layers,
                'nomes': [e['name'] for e in self.entries],
                'legendas': [e['labels'] for e in self.entries]}

    def preview_validation(self):
        try:
            config = self._collect_configuration()
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, 'Validação — GeoSAGA', str(exc))
            return
        QMessageBox.information(self, 'Validação — GeoSAGA',
            f'Configuração válida.\nMapas: {len(config["camadas"])}\n'
            f'Escala: 0–{config["escala"]}\nPesos: 100%\n'
            'Grades verificadas: dimensões, resolução, alinhamento e SRC.')

    def select_output(self):
        suggested = self.output_edit.text() or os.path.join(os.path.expanduser('~'), 'avaliacao_geosaga.tif')
        path, _ = QFileDialog.getSaveFileName(self, 'Salvar carta de avaliação', suggested,
                                              'GeoTIFF (*.tif)')
        if path:
            self.output_edit.setText(path if path.lower().endswith(('.tif', '.tiff')) else path + '.tif')

    def execute(self):
        if self._task:
            return
        try:
            config = self._collect_configuration()
            dest = (temporary_destination('avaliacao_raster', '.tif')
                    if self.temporary_check.isChecked() else self.output_edit.text().strip())
            if not dest:
                raise ValueError('Informe o caminho do raster de saída (.tif).')
            if not dest.lower().endswith(('.tif', '.tiff')):
                raise ValueError('A carta de avaliação deve ser salva em GeoTIFF (.tif).')
            dest = os.path.abspath(dest)
            if any(os.path.realpath(dest) == os.path.realpath(e['path']) for e in self.entries):
                raise ValueError('A saída não pode sobrescrever um mapa de entrada.')
            if os.path.exists(dest):
                if QMessageBox.question(self, 'Substituir resultado?',
                    f'O arquivo já existe:\n{dest}\n\nDeseja substituí-lo?') != QMessageBox.StandardButton.Yes:
                    return
            report = os.path.splitext(dest)[0] + '_relatorio.csv' if self.csv_check.isChecked() else ''
            report_txt = os.path.splitext(dest)[0] + '_relatorio.txt' if self.txt_check.isChecked() else ''
            task = EvaluationTask([e['path'] for e in self.entries], config, dest, report,
                                  self.title_edit.text(), self.author_edit.text(), self._task_finished, report_txt=report_txt)
            self._task = task
            self.execute_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.close_button.setEnabled(False)
            self.status.setText('Avaliação em execução no gerenciador de tarefas do QGIS…')
            QgsApplication.taskManager().addTask(task)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, 'GeoSAGA — Configuração incompleta', str(exc))

    def cancel_task(self):
        if self._task:
            self._task.cancel()
            self.status.setText('Cancelamento solicitado…')

    def _task_finished(self, success, task):
        self._task = None
        self.execute_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        if not success:
            text = task.error or ('Operação cancelada.' if task.isCanceled() else 'Falha na avaliação.')
            self.status.setText(text)
            QMessageBox.warning(self, 'GeoSAGA — Execução não concluída', text)
            return
        summary = task.summary or {}
        msg = f'Resultado salvo em:\n{task.destination}\n\nPixels avaliados: {summary.get("pixels_validos", 0):,}'
        if task.report:
            msg += f'\nRelatório CSV: {task.report}'
        if task.report_txt:
            msg += f'\nRelatório TXT: {task.report_txt}'
        if self.load_check.isChecked() or self.temporary_check.isChecked():
            layer = self.iface.addRasterLayer(task.destination, self.title_edit.text().strip() or 'Vista Saga — Avaliação')
            if not layer or not layer.isValid():
                msg += '\n(Atenção: não foi possível adicionar o raster ao QGIS.)'
        self.status.setText('Avaliação concluída. O resultado foi salvo em GeoTIFF.')
        QMessageBox.information(self, 'GeoSAGA — Avaliação concluída', msg)

    def _serialize(self, dest):
        self._save_current_notes()
        base = os.path.dirname(os.path.abspath(dest))
        entries = []
        for e in self.entries:
            try:
                relative = os.path.relpath(e['path'], base)
            except ValueError:
                relative = e['path']
            entries.append({'arquivo': relative, 'nome': e['name'], 'peso': e['weight'],
                            'notas': e['notes'], 'bloqueadas': e['blocked']})
        return {'formato': 'geosaga-avaliacao', 'versao': self.PROJECT_VERSION,
                'titulo': self.title_edit.text(), 'autor': self.author_edit.text(),
                'escala': self._current_scale(), 'camadas': entries}

    def save_project(self):
        suggestion = self.project_path or os.path.join(os.path.expanduser('~'), 'avaliacao.geosaga.json')
        filename, _ = QFileDialog.getSaveFileName(self, 'Salvar projeto GeoSAGA', suggestion,
                                                  'Projetos GeoSAGA (*.geosaga.json)')
        if not filename:
            return
        if not filename.lower().endswith('.geosaga.json'):
            filename += '.geosaga.json'
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(self._serialize(filename), file, ensure_ascii=False, indent=2)
            self.project_path = filename
            self.status.setText('Projeto salvo: ' + filename)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, 'GeoSAGA', f'Falha ao salvar projeto:\n{exc}')

    def new_project(self):
        if self._task:
            return
        if self.entries and QMessageBox.question(self, 'Novo projeto',
            'Descartar a configuração atual (se não estiver salva)?') != QMessageBox.StandardButton.Yes:
            return
        self.entries.clear()
        self.class_table.setRowCount(0)
        self.current_index = -1
        self.project_path = ''
        self.title_edit.clear()
        self.author_edit.clear()
        self.scale_combo.setCurrentIndex(0)
        self._render_maps()
        self.output_edit.clear()
        self.status.setText('Novo projeto criado.')

    def open_project(self):
        if self._task:
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir projeto GeoSAGA', '',
                                              'Projetos GeoSAGA (*.geosaga.json *.json)')
        if not path:
            return
        try:
            if os.path.getsize(path) > 5_000_000:
                raise ValueError('Arquivo de projeto excessivamente grande.')
            with open(path, encoding='utf-8') as handle:
                project = json.load(handle)
            if project.get('formato') != 'geosaga-avaliacao' or project.get('versao') != self.PROJECT_VERSION:
                raise ValueError('Formato ou versão do projeto não suportados.')
            layers = project.get('camadas', [])
            if not isinstance(layers, list) or len(layers) > 50:
                raise ValueError('Lista de camadas inválida.')
            candidates = []
            for rec in layers:
                source = rec['arquivo']
                resolved = os.path.normpath(os.path.join(os.path.dirname(path), source))
                if not os.path.isfile(resolved):
                    raise ValueError(f'Raster não encontrado: {resolved}')
                candidates.append((rec, resolved))
            if self.entries and QMessageBox.question(self, 'Carregar projeto',
                    'Substituir a configuração atual pelo projeto salvo?') != QMessageBox.StandardButton.Yes:
                return
            self.entries = []
            self.current_index = -1
            self.class_table.setRowCount(0)
            self.title_edit.setText(str(project.get('titulo', '')))
            self.author_edit.setText(str(project.get('autor', '')))
            scale_pos = self.scale_combo.findData(project.get('escala', 10))
            if scale_pos >= 0:
                self.scale_combo.setCurrentIndex(scale_pos)
            self.project_path = path
            for rec, resolved in candidates:
                existing = next((candidate_layer for candidate_layer in QgsProject.instance().mapLayers().values()
                                 if isinstance(candidate_layer, QgsRasterLayer) and
                                 candidate_layer.source().split('|', 1)[0] == resolved), None)
                layer = existing or self.iface.addRasterLayer(resolved, rec.get('nome', Path(resolved).stem))
                if layer and layer.isValid():
                    if not self._add_layer(layer, rec, select=False):
                        continue
            self._render_maps(select=0 if self.entries else None)
            self.status.setText(f'Projeto carregado: {len(self.entries)} mapa(s).')
            self.refresh_available()
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, 'GeoSAGA — Projeto inválido', str(exc))

    def closeEvent(self, event):
        if any(getattr(getattr(self, name, None), 'running', False)
               for name in ('_vector_dialog', '_overlay_dialog')):
            QMessageBox.information(self, 'Avaliação em andamento',
                                    'Aguarde a conclusão da avaliação vetorial antes de fechar.')
            event.ignore()
            return
        if self._task:
            QMessageBox.information(self, 'GeoSAGA',
                                    'A avaliação está em andamento. Cancele ou conclua antes de fechar.')
            event.ignore()
        else:
            self._save_current_notes()
            event.accept()
