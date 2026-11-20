"""Janela da Assinatura (1.5.0): mapa de referência + mapas assinados.

Modelo do Vista SAGA, com as decisões do autor de 20/11/2026 (``docs/ASSINATURA_150_PROPOSTA.md``):
lista de mapas com a referência no topo; seleção na referência (classes marcadas no raster, seleção do
QGIS no vetor); todos os mapas da lista assinados dentro do limite; resultado da união e, opcionalmente,
por feição; relatórios TXT e CSV. As contas ficam em ``signature_raster`` e ``signature_vector``; as
camadas do QGIS são lidas aqui, no thread da GUI.
"""
import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QProgressDialog, QPushButton, QScrollArea, QTabBar, QTableWidget, QTabWidget,
    QVBoxLayout, QWidget,
)
from qgis.core import Qgis, QgsProject, QgsRasterLayer, QgsVectorLayer, QgsWkbTypes
from qgis.gui import QgsMapLayerComboBox

from .errors import log_exception
from .i18n import tr
from .signature_model import is_special
from .ui_shared import (
    RUN_TEXT, FooterStatus, choose_project_layers, enable_table_copy, open_polygon_files, report_outcome,
    table_item, temporary_destination, use_tab_background, vector_start_directory,
)

RASTER, VECTOR = 0, 1
NAME_CANDIDATES = ('NOME', 'NAME', 'BAIRRO', 'AREA_NOME', 'IDENTIF', 'CODIGO')
CLASS_CANDIDATES = ('CODIGO', 'CLASSE', 'COD', 'USO', 'TIPO_USO', 'CLASS')
LABEL_CANDIDATES = ('NOME', 'LEGENDA', 'DESCRICAO', 'LABEL', 'NAME')
RASTER_FILES = 'Mapas raster (*.tif *.tiff *.rs2 *.img *.vrt);;Todos os arquivos (*)'
RESULT_COLUMNS = ['Mapa', 'Cat. - Legenda', 'Total pixels', 'Total ha', 'Pixels asn.', 'Área asn. ha',
                  '% Área asn.', '% Categoria']


def _plain(value):
    """Valor de classe vindo do QGIS: inteiro quando for número inteiro; ``None`` para nulo."""
    if value is None:
        return None
    if hasattr(value, 'isNull') and value.isNull():
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        return int(value) if value.is_integer() else value
    if isinstance(value, int):
        return value
    text = str(value).strip()
    return text or None


class SignatureDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self._busy = False
        self._raster = []   # [{'path', 'crs'}]
        self._vector = []   # [{'layer', 'class_field', 'label_field'}]
        self._ref_classes = []
        self._watched = None
        self._filling = False
        self._result = None
        self.setModal(False)
        self.setWindowTitle(tr('Vista Saga Plugin - Assinatura'))
        self.resize(820, 620)
        self.setMinimumSize(700, 480)
        self._build_ui()

    # ------------------------------------------------------------------ interface
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(7)
        self.type_tabs = QTabBar()
        self.type_tabs.addTab(tr('Raster'))
        self.type_tabs.addTab(tr('Vetorial'))
        self.type_tabs.setExpanding(False)
        root.addWidget(self.type_tabs)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        config = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(config)
        use_tab_background(scroll)
        self.tabs.addTab(scroll, tr('Configuração'))
        results = QWidget()
        self.tabs.addTab(results, tr('Resultados'))

        layout = QVBoxLayout(config)
        layout.setSpacing(9)
        # Um grupo por guia, mostrado ou oculto (o leiaute recalcula a altura de cada um).
        self.mode_groups = [(self._maps_group(RASTER), self._raster_selection_group()),
                            (self._maps_group(VECTOR), self._vector_selection_group())]
        for maps_group, selection_group in self.mode_groups:
            layout.addWidget(maps_group)
        for maps_group, selection_group in self.mode_groups:
            layout.addWidget(selection_group)
        layout.addWidget(self._options_group())
        layout.addWidget(self._output_group())
        layout.addStretch(1)
        self._build_results(results)

        controls = QHBoxLayout()
        self.status = FooterStatus(tr('Adicione os mapas; o primeiro da lista é a referência.'))
        controls.addStretch(1)
        self.run_button = QPushButton(tr(RUN_TEXT))
        self.run_button.setToolTip(tr('Calcula a assinatura de todos os mapas da lista dentro da seleção feita '
                                      'no mapa de referência e grava os relatórios TXT e CSV.'))
        self.run_button.clicked.connect(self.run)
        controls.addWidget(self.run_button)
        close = QPushButton(tr('Fechar'))
        close.setToolTip(tr('Fecha a janela. Os relatórios já gravados são mantidos.'))
        close.clicked.connect(self.close)
        controls.addWidget(close)
        root.addLayout(controls)
        self.type_tabs.currentChanged.connect(self._mode_changed)
        self._mode_changed(RASTER)

    def _maps_group(self, mode):
        group = QGroupBox(tr('1. Mapas - o primeiro é a referência'))
        group.setToolTip(tr('Todos os mapas da lista são assinados, inclusive a referência. A seleção é '
                            'feita no primeiro mapa da lista (a referência), como o mapa de cima no Vista SAGA.'))
        form = QFormLayout(group)
        choose = QgsMapLayerComboBox()
        choose.setAllowEmptyLayer(True)
        choose.setShowCrs(True)
        choose.setFilters(Qgis.LayerFilter.RasterLayer if mode == RASTER else Qgis.LayerFilter.PolygonLayer)
        choose.setToolTip(tr('Camada carregada no QGIS a acrescentar à lista.'))
        form.addRow(tr('Camada no QGIS:'), choose)
        buttons = QHBoxLayout()
        add = QPushButton(tr('Adicionar camada selecionada'))
        add.setToolTip(tr('Acrescenta à lista a camada escolhida acima.'))
        add.clicked.connect(lambda _c=False, m=mode: self._add_current(m))
        many = QPushButton(tr('Adicionar várias do QGIS…'))
        many.setToolTip(tr('Escolhe várias camadas carregadas no QGIS de uma vez.'))
        many.clicked.connect(lambda _c=False, m=mode: self._add_many(m))
        files = QPushButton(tr('Adicionar arquivos…'))
        files.setToolTip(tr('Acrescenta mapas em arquivo. Na guia Raster aceita GeoTIFF e outros formatos do '
                            'GDAL, e também RS2.') if mode == RASTER else
                         tr('Acrescenta mapas em arquivo; eles são carregados no QGIS, onde a seleção é feita.'))
        files.clicked.connect(lambda _c=False, m=mode: self._add_files(m))
        for button in (add, many, files):
            buttons.addWidget(button)
        buttons.addStretch(1)
        form.addRow('', buttons)
        listing = QListWidget()
        listing.setAlternatingRowColors(True)
        listing.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        listing.setMinimumHeight(100)
        listing.setToolTip(tr('Mapas assinados, na ordem do relatório. O primeiro é a referência.'))
        form.addRow(tr('Mapas:'), listing)
        order = QHBoxLayout()
        remove = QPushButton(tr('Remover selecionadas'))
        remove.setToolTip(tr('Retira da lista os mapas selecionados (não altera o projeto do QGIS).'))
        remove.clicked.connect(lambda _c=False, m=mode: self._remove(m))
        remove_all = QPushButton(tr('Remover todas'))
        remove_all.setToolTip(tr('Esvazia a lista de mapas desta guia (não altera o projeto do QGIS).'))
        remove_all.clicked.connect(lambda _c=False, m=mode: self._remove_all(m))
        up = QPushButton(tr('Mover para cima'))
        up.setToolTip(tr('Sobe o mapa selecionado; o mapa do topo é a referência.'))
        up.clicked.connect(lambda _c=False, m=mode: self._move(m, -1))
        down = QPushButton(tr('Mover para baixo'))
        down.setToolTip(tr('Desce o mapa selecionado na lista.'))
        down.clicked.connect(lambda _c=False, m=mode: self._move(m, 1))
        for button in (remove, remove_all, up, down):
            order.addWidget(button)
        order.addStretch(1)
        form.addRow('', order)
        if mode == RASTER:
            self.raster_choose, self.raster_list = choose, listing
        else:
            self.vector_choose, self.vector_list = choose, listing
            self.fields_target = QLabel(tr('Selecione um mapa na lista.'))
            self.class_field = QComboBox()
            self.class_field.setToolTip(tr('Campo com a classe de cada polígono do mapa selecionado na lista.'))
            self.label_field = QComboBox()
            self.label_field.setToolTip(tr('Campo opcional com o nome da classe; sem ele, a classe serve de '
                                           'legenda.'))
            form.addRow(tr('Campos de:'), self.fields_target)
            form.addRow(tr('Campo de classe:'), self.class_field)
            form.addRow(tr('Campo da legenda (opcional):'), self.label_field)
            listing.itemSelectionChanged.connect(self._vector_item_selected)
            self.class_field.currentIndexChanged.connect(self._fields_edited)
            self.label_field.currentIndexChanged.connect(self._fields_edited)
        return group

    def _raster_selection_group(self):
        group = QGroupBox(tr('2. Seleção na referência'))
        group.setToolTip(tr('Cada classe marcada entra inteira no limite. Marcar todas equivale a "Assinar o '
                            'mapa inteiro" do Vista SAGA, inclusive o FUNDO.'))
        box = QVBoxLayout(group)
        self.class_list = QListWidget()
        self.class_list.setMinimumHeight(130)
        self.class_list.setToolTip(tr('Classes do mapa de referência, com o número de células.'))
        box.addWidget(self.class_list)
        row = QHBoxLayout()
        mark = QPushButton(tr('Marcar todas'))
        mark.setToolTip(tr('Marca todas as classes da referência (o mapa inteiro).'))
        mark.clicked.connect(lambda: self._check_all(True))
        clear = QPushButton(tr('Desmarcar todas'))
        clear.setToolTip(tr('Desmarca todas as classes da referência.'))
        clear.clicked.connect(lambda: self._check_all(False))
        row.addWidget(mark)
        row.addWidget(clear)
        row.addStretch(1)
        box.addLayout(row)
        return group

    def _vector_selection_group(self):
        group = QGroupBox(tr('2. Seleção na referência'))
        group.setToolTip(tr('Selecione as feições na camada de referência com as ferramentas de seleção do QGIS '
                            '(selecionar, desselecionar, selecionar por expressão).'))
        form = QFormLayout(group)
        how = QLabel(tr('Selecione as feições da camada de referência no mapa do QGIS; a janela fica aberta '
                        'enquanto você seleciona.'))
        how.setWordWrap(True)
        form.addRow(how)
        self.selection_info = QLabel()
        self.selection_info.setWordWrap(True)
        form.addRow(tr('Selecionadas:'), self.selection_info)
        row = QHBoxLayout()
        on_map = QPushButton(tr('Selecionar no mapa'))
        on_map.setToolTip(tr('Torna a camada de referência a camada ativa e liga a ferramenta de seleção do '
                             'QGIS: clique nas feições no mapa (Ctrl+clique acrescenta ou retira uma feição).'))
        on_map.clicked.connect(self._select_on_map)
        select_all = QPushButton(tr('Selecionar todas'))
        select_all.setToolTip(tr('Seleciona todas as feições da camada de referência (o mapa inteiro).'))
        select_all.clicked.connect(self._select_all_features)
        clear = QPushButton(tr('Desselecionar todas'))
        clear.setToolTip(tr('Limpa a seleção da camada de referência.'))
        clear.clicked.connect(self._clear_selection)
        for button in (on_map, select_all, clear):
            row.addWidget(button)
        row.addStretch(1)
        form.addRow('', row)
        self.feature_name = QComboBox()
        self.feature_name.setToolTip(tr('Campo que dá nome a cada feição no resultado por feição.'))
        form.addRow(tr('Nome da feição:'), self.feature_name)
        return group

    def _options_group(self):
        group = QGroupBox(tr('3. Opções'))
        form = QFormLayout(group)
        self.per_feature = QCheckBox(tr('Resultado por feição'))
        self.per_feature.setChecked(True)
        self.per_feature.setToolTip(tr('Além da união da seleção, calcula um resultado para cada feição '
                                       'selecionada (no raster, para cada classe marcada).'))
        form.addRow('', self.per_feature)
        self.overlap_label = QLabel(tr('Sobreposição entre classes:'))
        self.overlap_policy = QComboBox()
        self.overlap_policy.addItem(tr('Excluir a região ambígua e informá-la'), 'exclude')
        self.overlap_policy.addItem(tr('Interromper a execução'), 'strict')
        self.overlap_policy.setToolTip(tr('Quando classes diferentes do mesmo mapa ocupam o mesmo lugar. Polígonos '
                                          'sobrepostos da mesma classe sempre contam uma vez.'))
        form.addRow(self.overlap_label, self.overlap_policy)
        return group

    def _output_group(self):
        group = QGroupBox(tr('4. Resultado'))
        form = QFormLayout(group)
        self.title = QLineEdit()
        self.title.setToolTip(tr('Título opcional, gravado no relatório TXT.'))
        form.addRow(tr('Título:'), self.title)
        row = QHBoxLayout()
        self.path = QLineEdit()
        self.path.setPlaceholderText(tr('[Arquivo temporário]'))
        self.path.setClearButtonEnabled(True)
        self.path.setToolTip(tr('Relatório CSV; o TXT é gravado ao lado, com o mesmo nome. Em branco, os dois '
                                'ficam na pasta temporária do QGIS.'))
        row.addWidget(self.path, 1)
        browse = QPushButton(tr('Salvar como…'))
        browse.setToolTip(tr('Escolhe onde gravar os relatórios.'))
        browse.clicked.connect(self._save_as)
        row.addWidget(browse)
        form.addRow(tr('Salvar em:'), row)
        return group

    def _build_results(self, page):
        box = QVBoxLayout(page)
        self.summary = QLabel(tr('Nenhuma assinatura executada nesta sessão.'))
        self.summary.setWordWrap(True)
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(self.summary)
        row = QHBoxLayout()
        row.addWidget(QLabel(tr('Recorte:')))
        self.cut_choice = QComboBox()
        self.cut_choice.setToolTip(tr('União da seleção ou uma feição (classe, no raster).'))
        self.cut_choice.currentIndexChanged.connect(self._show_cut)
        row.addWidget(self.cut_choice, 1)
        box.addLayout(row)
        self.table = QTableWidget(0, len(RESULT_COLUMNS))
        self.table.setHorizontalHeaderLabels([tr(c) for c in RESULT_COLUMNS])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        enable_table_copy(self.table)
        box.addWidget(self.table, 1)

    def _mode_changed(self, index):
        mode = RASTER if index == RASTER else VECTOR
        for index_group, groups in enumerate(self.mode_groups):
            for group in groups:
                group.setVisible(index_group == mode)
        self.overlap_label.setVisible(mode == VECTOR)
        self.overlap_policy.setVisible(mode == VECTOR)
        self._refresh_reference()

    def _mode(self):
        return RASTER if self.type_tabs.currentIndex() == RASTER else VECTOR

    # ------------------------------------------------------------------ lista de mapas
    def _add_current(self, mode):
        layer = (self.raster_choose if mode == RASTER else self.vector_choose).currentLayer()
        if layer is None:
            QMessageBox.information(self, tr('Assinatura'), tr('Escolha uma camada do QGIS.'))
            return
        self._append_layer(mode, layer)
        self._refresh_list(mode)

    def _add_many(self, mode):
        for layer in choose_project_layers(self, 'raster' if mode == RASTER else 'polygon',
                                           tr('Adicionar mapas à Assinatura')):
            self._append_layer(mode, layer)
        self._refresh_list(mode)

    def _add_files(self, mode):
        if mode == VECTOR:
            layers, warnings = open_polygon_files(self, tr('Adicionar mapas vetoriais'), vector_start_directory())
            for layer in layers:
                self._append_layer(VECTOR, layer)
            if warnings:
                QMessageBox.warning(self, tr('Assinatura'), '\n'.join(warnings))
            self._refresh_list(VECTOR)
            return
        paths, _ = QFileDialog.getOpenFileNames(self, tr('Adicionar mapas raster'), '', tr(RASTER_FILES))
        for path in paths:
            self._append_raster(path)
        self._refresh_list(RASTER)

    def _append_layer(self, mode, layer):
        if mode == RASTER:
            if not isinstance(layer, QgsRasterLayer) or not layer.isValid():
                return
            path = layer.source().split('|', 1)[0]
            if not os.path.isfile(path):
                QMessageBox.warning(self, tr('Assinatura'), tr('A camada {0} não está num arquivo local; exporte-a '
                                                               'para GeoTIFF.').format(layer.name()))
                return
            self._append_raster(path, layer.crs().authid() or layer.crs().toWkt(), layer.id())
            return
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return
        if QgsWkbTypes.geometryType(layer.wkbType()) != Qgis.GeometryType.Polygon:
            QMessageBox.warning(self, tr('Assinatura'), tr('A camada {0} não é de polígonos.').format(layer.name()))
            return
        if any(e['layer'].id() == layer.id() for e in self._vector):
            return
        names = layer.fields().names()
        class_field = next((n for n in CLASS_CANDIDATES if n in names), names[0] if names else '')
        label_field = next((n for n in LABEL_CANDIDATES if n in names and n != class_field), '')
        self._vector.append({'layer': layer, 'class_field': class_field, 'label_field': label_field})

    def _append_raster(self, path, crs='', layer_id=''):
        path = os.path.abspath(path)
        if any(os.path.normcase(e['path']) == os.path.normcase(path) for e in self._raster):
            return
        if path.lower().endswith('.rs2') and not crs:
            from .rs2_converter import sidecar_epsg
            crs = sidecar_epsg(path)
            if not crs:
                crs = self._ask_crs(os.path.basename(path))
                if not crs:
                    return
        self._raster.append({'path': path, 'crs': crs, 'layer_id': layer_id})

    def _open_raster(self, entry):
        """Mapa raster da lista, com os nomes das classes do estilo da camada, se ela estiver no projeto."""
        from .signature_raster import open_raster_map
        return open_raster_map(entry['path'], crs=entry['crs'], labels=self._style_labels(entry))

    @staticmethod
    def _style_labels(entry):
        """{código: nome} da simbologia "Paletado/Valores únicos" da camada no QGIS; vazio se não houver."""
        layer = QgsProject.instance().mapLayer(entry.get('layer_id') or '')
        renderer = layer.renderer() if isinstance(layer, QgsRasterLayer) else None
        if renderer is None or not hasattr(renderer, 'classes'):
            return {}
        labels = {}
        for item in renderer.classes():
            value = float(item.value)
            if value.is_integer() and item.label:
                labels[int(value)] = item.label
        return labels

    def _ask_crs(self, name):
        from qgis.gui import QgsProjectionSelectionDialog
        dialog = QgsProjectionSelectionDialog(self)
        dialog.setWindowTitle(tr('SRC do RS2 {0}').format(name))
        try:
            dialog.setMessage(tr('O RS2 não registra SRC. Confirme o SRC projetado, em metros, deste mapa.'))
        except AttributeError:
            pass
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.crs().isValid():
            return ''
        return dialog.crs().authid() or dialog.crs().toWkt()

    def _entries(self, mode):
        return self._raster if mode == RASTER else self._vector

    def _list(self, mode):
        return self.raster_list if mode == RASTER else self.vector_list

    def _remove(self, mode):
        listing = self._list(mode)
        rows = sorted((listing.row(item) for item in listing.selectedItems()), reverse=True)
        for row in rows:
            self._entries(mode).pop(row)
        self._refresh_list(mode)

    def _remove_all(self, mode):
        self._entries(mode).clear()
        self._refresh_list(mode)

    def _move(self, mode, delta):
        listing, entries = self._list(mode), self._entries(mode)
        row = listing.currentRow()
        target = row + delta
        if row < 0 or not 0 <= target < len(entries):
            return
        entries[row], entries[target] = entries[target], entries[row]
        self._refresh_list(mode)
        listing.setCurrentRow(target)

    def _refresh_list(self, mode):
        listing = self._list(mode)
        listing.clear()
        for i, entry in enumerate(self._entries(mode)):
            if mode == RASTER:
                text = os.path.basename(entry['path'])
                if entry['path'].lower().endswith('.rs2') and len(entry['crs']) < 30:
                    text += f' ({entry["crs"]})'
            else:
                text = entry['layer'].name()
            if i == 0:
                text = tr('{0} - referência').format(text)
            listing.addItem(QListWidgetItem(f'{i + 1}. {text}'))
        if mode == VECTOR:
            self._vector_item_selected()
        self._refresh_reference()

    # ------------------------------------------------------------------ campos (vetor)
    def _vector_item_selected(self):
        row = self.vector_list.currentRow()
        entry = self._vector[row] if 0 <= row < len(self._vector) and self.vector_list.selectedItems() else None
        self._filling = True
        self.class_field.clear()
        self.label_field.clear()
        self.label_field.addItem(tr('(usar a classe como legenda)'), '')
        if entry is None:
            self.fields_target.setText(tr('Selecione um mapa na lista.'))
        else:
            self.fields_target.setText(entry['layer'].name())
            names = entry['layer'].fields().names()
            self.class_field.addItems(names)
            for name in names:
                self.label_field.addItem(name, name)
            self.class_field.setCurrentText(entry['class_field'])
            self.label_field.setCurrentIndex(max(0, self.label_field.findData(entry['label_field'])))
        self.class_field.setEnabled(entry is not None)
        self.label_field.setEnabled(entry is not None)
        self._filling = False

    def _fields_edited(self, *_args):
        if self._filling:
            return
        row = self.vector_list.currentRow()
        if 0 <= row < len(self._vector):
            self._vector[row]['class_field'] = self.class_field.currentText()
            self._vector[row]['label_field'] = self.label_field.currentData() or ''

    # ------------------------------------------------------------------ referência
    def _refresh_reference(self):
        if self._mode() == RASTER:
            self._refresh_raster_classes()
        else:
            self._watch_reference()

    def _refresh_raster_classes(self):
        checked = {key for key, item in zip(self._ref_classes, self._class_items()) if
                   item.checkState() == Qt.CheckState.Checked}
        self.class_list.clear()
        self._ref_classes = []
        if not self._raster:
            self.class_list.addItem(tr('Adicione o mapa de referência à lista.'))
            return
        entry = self._raster[0]
        try:
            from .signature_raster import scan_reference_classes
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                classes = scan_reference_classes(self._open_raster(entry))
            finally:
                QApplication.restoreOverrideCursor()
        except Exception as exc:
            log_exception()
            self.class_list.addItem(tr(str(exc)))
            return
        for key, label, cells in classes:
            text = label if is_special(key) else f'{key} - {label}'
            item = QListWidgetItem(tr('{0} ({1} células)').format(text, cells))
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if key in checked else Qt.CheckState.Unchecked)
            self.class_list.addItem(item)
            self._ref_classes.append(key)

    def _class_items(self):
        return [self.class_list.item(i) for i in range(self.class_list.count())]

    def _check_all(self, state):
        for item in self._class_items()[:len(self._ref_classes)]:
            item.setCheckState(Qt.CheckState.Checked if state else Qt.CheckState.Unchecked)

    def _selected_classes(self):
        return [key for key, item in zip(self._ref_classes, self._class_items())
                if item.checkState() == Qt.CheckState.Checked]

    def _reference_layer(self):
        return self._vector[0]['layer'] if self._vector else None

    def _watch_reference(self):
        layer = self._reference_layer()
        if self._watched is not None and self._watched is not layer:
            try:
                self._watched.selectionChanged.disconnect(self._update_selection_info)
            except (TypeError, RuntimeError):
                pass
            self._watched = None
        if layer is not None and self._watched is None:
            layer.selectionChanged.connect(self._update_selection_info)
            self._watched = layer
        old = self.feature_name.currentData()
        self.feature_name.clear()
        self.feature_name.addItem(tr('(usar o ID da feição)'), '')
        if layer is not None:
            names = layer.fields().names()
            for name in names:
                self.feature_name.addItem(name, name)
            wanted = old if old in names else next((n for n in NAME_CANDIDATES if n in names), '')
            self.feature_name.setCurrentIndex(max(0, self.feature_name.findData(wanted)))
        self._update_selection_info()

    def _update_selection_info(self, *_args):
        layer = self._reference_layer()
        if layer is None:
            self.selection_info.setText(tr('Adicione o mapa de referência à lista.'))
        else:
            self.selection_info.setText(tr('Feições selecionadas em {0}: {1}.').format(
                layer.name(), layer.selectedFeatureCount()))

    def _select_all_features(self):
        layer = self._reference_layer()
        if layer is not None:
            layer.selectAll()

    def _clear_selection(self):
        layer = self._reference_layer()
        if layer is not None:
            layer.removeSelection()

    def _select_on_map(self):
        """A ferramenta de seleção do QGIS age sobre a camada ativa: ativa a referência e liga a ferramenta."""
        layer = self._reference_layer()
        if layer is None:
            QMessageBox.information(self, tr('Assinatura'), tr('Adicione o mapa de referência à lista.'))
            return
        if self.iface is None:
            return
        self.iface.setActiveLayer(layer)
        for name in ('actionSelect', 'actionSelectRectangle'):
            getter = getattr(self.iface, name, None)
            if getter is not None:
                getter().trigger()
                break
        self.iface.mapCanvas().setFocus()
        report_outcome(None, 'Assinatura', tr('Selecione no mapa as feições de {0}; a janela da Assinatura continua '
                                              'aberta.').format(layer.name()), 'info', self.iface)

    # ------------------------------------------------------------------ execução
    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, tr('Relatórios da Assinatura'),
                                              self.path.text().strip() or 'assinatura.csv', 'CSV (*.csv)')
        if path:
            self.path.setText(path if path.lower().endswith('.csv') else path + '.csv')

    def _destinations(self):
        csv_path = self.path.text().strip() or temporary_destination('assinatura', '.csv')
        if not csv_path.lower().endswith('.csv'):
            csv_path += '.csv'
        folder = os.path.dirname(os.path.abspath(csv_path))
        if not os.path.isdir(folder):
            raise ValueError('Pasta de saída inexistente.')
        return csv_path, os.path.splitext(csv_path)[0] + '.txt'

    def _vector_inputs(self):
        from .signature_vector import VectorMap
        if not self._vector:
            raise ValueError('Adicione pelo menos um mapa à lista.')
        maps = []
        for entry in self._vector:
            layer = entry['layer']
            if not layer.isValid():
                raise ValueError(f'A camada {layer.name()} não está mais disponível.')
            if layer.isEditable():
                raise ValueError(f'Salve ou descarte as edições pendentes da camada {layer.name()}.')
            names = layer.fields().names()
            if entry['class_field'] not in names:
                raise ValueError(f'Escolha o campo de classe da camada {layer.name()}.')
            label = entry['label_field'] if entry['label_field'] in names else ''
            features = []
            for feature in layer.getFeatures():
                geometry = feature.geometry()
                if geometry is None or geometry.isEmpty():
                    continue
                features.append((feature.id(), bytes(geometry.asWkb()), _plain(feature[entry['class_field']]),
                                 _plain(feature[label]) if label else None))
            maps.append(VectorMap(layer.name(), layer.crs().toWkt(), features))
        reference = self._vector[0]['layer']
        name_field = self.feature_name.currentData() or ''
        selected = []
        for feature in sorted(reference.selectedFeatures(), key=lambda f: f.id()):
            geometry = feature.geometry()
            if geometry is None or geometry.isEmpty():
                continue
            name = _plain(feature[name_field]) if name_field else None
            selected.append((feature.id(), name if name is not None else feature.id(), bytes(geometry.asWkb())))
        if not selected:
            raise ValueError(f'Nenhuma feição selecionada em {reference.name()}. Use "Selecionar no mapa" e clique '
                             'nas feições no mapa do QGIS, ou "Selecionar todas".')
        return maps, selected

    def run(self):
        if self._busy:
            return
        mode = self._mode()
        try:
            csv_path, txt_path = self._destinations()
            if mode == VECTOR:
                maps, selected = self._vector_inputs()
            else:
                if not self._raster:
                    raise ValueError('Adicione pelo menos um mapa à lista.')
                selected = self._selected_classes()
                if not selected:
                    raise ValueError('Selecione pelo menos uma classe do mapa de referência.')
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, tr('Assinatura - Verificar entrada'), tr(str(exc)))
            return
        self._busy = True
        self.run_button.setEnabled(False)
        popup = QProgressDialog(tr('Calculando a assinatura…'), tr('Cancelar'), 0, 100, self)
        popup.setWindowTitle(self.window().windowTitle())
        popup.setWindowModality(Qt.WindowModality.WindowModal)
        popup.setMinimumDuration(0)
        popup.setValue(0)
        popup.show()

        def progress(fraction):
            popup.setValue(max(0, min(100, int(round(100 * fraction)))))
            QApplication.processEvents()

        def cancelled():
            QApplication.processEvents()
            return popup.wasCanceled()

        try:
            if mode == RASTER:
                from .signature_raster import run_raster_signature
                maps = [self._open_raster(e) for e in self._raster]
                result = run_raster_signature(maps, selected, per_feature=self.per_feature.isChecked(),
                                              progress=progress, cancelled=cancelled)
                overlap = ''
            else:
                from .signature_vector import run_vector_signature
                policy = self.overlap_policy.currentData()
                result = run_vector_signature(maps, selected, per_feature=self.per_feature.isChecked(),
                                              overlap=policy, progress=progress, cancelled=cancelled)
                overlap = ('excluir a região ambígua e informá-la' if policy == 'exclude'
                           else 'interromper a execução')
            from .signature_reports import write_csv, write_txt
            write_csv(csv_path, result)
            write_txt(txt_path, result, title=self.title.text().strip(), overlap=overlap)
            self._show_result(result, csv_path, txt_path)
            report_outcome(self.status, 'Assinatura', tr('Assinatura calculada. Relatórios: {0}').format(txt_path),
                           'success', self.iface)
        except InterruptedError:
            report_outcome(self.status, 'Assinatura', tr('Operação cancelada.'), 'warning', self.iface)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, tr('Assinatura - Verificar entrada'), tr(str(exc)))
        except Exception as exc:
            log_exception()
            report_outcome(self.status, 'Assinatura', tr('A assinatura não foi concluída.'), 'critical', self.iface)
            QMessageBox.critical(self, tr('Assinatura - Falha'), tr(str(exc)))
        finally:
            popup.close()
            self._busy = False
            self.run_button.setEnabled(True)

    # ------------------------------------------------------------------ resultados
    def _show_result(self, result, csv_path, txt_path):
        self._result = result
        lines = [tr('Concluído. Referência: {0}; {1} itens selecionados.').format(result.reference,
                                                                                 len(result.selection)),
                 tr('CSV: {0}').format(csv_path), tr('TXT: {0}').format(txt_path)]
        lines += [tr(w) for w in result.warnings]
        self.summary.setText('\n'.join(lines))
        self.cut_choice.blockSignals(True)
        self.cut_choice.clear()
        self.cut_choice.addItem(tr('União da seleção'))
        for cut in result.features:
            self.cut_choice.addItem(str(cut.name))
        self.cut_choice.blockSignals(False)
        raster = result.kind == 'raster'
        self.table.setColumnHidden(2, not raster)
        self.table.setColumnHidden(4, not raster)
        self._show_cut(0)
        self.tabs.setCurrentIndex(1)

    def _show_cut(self, index):
        if self._result is None or index < 0:
            return
        cut = self._result.union if index == 0 else self._result.features[index - 1]
        places = 2 if self._result.kind == 'raster' else 4
        rows = [(m.name, r) for m in cut.maps for r in m.rows]
        self.table.setRowCount(len(rows))
        for i, (name, row) in enumerate(rows):
            label = row.display if row.code_text else tr(row.label)
            values = [name, label, '' if row.total_cells is None else row.total_cells, f'{row.total_ha:.{places}f}',
                      '' if row.asn_cells is None else row.asn_cells, f'{row.asn_ha:.{places}f}',
                      f'{row.pct_area:.2f}', '' if row.pct_category is None else f'{row.pct_category:.2f}']
            for j, value in enumerate(values):
                self.table.setItem(i, j, table_item(value, numeric=j >= 2))
        self.table.resizeColumnsToContents()

    def closeEvent(self, event):
        if self._watched is not None:
            try:
                self._watched.selectionChanged.disconnect(self._update_selection_info)
            except (TypeError, RuntimeError):
                pass
            self._watched = None
        super().closeEvent(event)
