"""Conversor RS2 / GeoTIFF do Vista Saga Plugin (QGIS 4.x + Qt6).

Suporte a arquivos locais, seleção de rasters do projeto, SRC nativo e lotes.
"""
from .i18n import tr
from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout,
    QFrame, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox,
    QPushButton, QProgressDialog, QScrollArea, QToolButton, QVBoxLayout, QWidget,
    QDoubleSpinBox, QSpinBox, QAbstractItemView,
)
from qgis.core import (Qgis, QgsCoordinateReferenceSystem, QgsProject, QgsSettings,
                       QgsRasterLayer, QgsVectorLayer, QgsMessageLog)
from qgis.gui import QgsMapLayerComboBox, QgsProjectionSelectionWidget

from .rs2_batch import prepare_batch, source_mode, alignment_warnings
from .ui_shared import use_tab_background, choose_project_layers, temporary_destination
from .rs2_format import RS2Reader
from .rs2_outputs import output_conflicts
from .rs2_vector import (VECTOR_FORMATS, convert_rs2_to_vector, vector_conflicts)
from .tiff_vector import convert_tif_to_vector, _legend
from .vector_raster import convert_vector_to_tif, split_vector_source
from .errors import log_exception
from .vector_rs2 import convert_vector_to_rs2


RS2_CRS_SETTING = 'VistaSagaPlugin/rs2_crs'
RS2_SOURCE_OPERATIONS = (0, 2)


class RS2ConverterDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle(tr('Vista Saga Plugin - Conversor de formatos'))
        self.setMinimumWidth(690)
        self.resize(750, 660)
        self.setModal(False)
        # SRC das operações com origem RS2 (0 e 2), lembrado entre sessões. O RS2 não
        # guarda SRC; a escolha é do usuário. Fica separado do SRC opcional de
        # GeoTIFF → Vetor (3), que substitui o SRC do TIFF e não deve herdar este.
        self._rs2_crs = QgsCoordinateReferenceSystem(
            str(QgsSettings().value(RS2_CRS_SETTING, '', type=str) or ''))
        self._other_crs = QgsCoordinateReferenceSystem()
        self._crs_group = None
        self._create_ui()

    def _create_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        holder = QWidget()
        root = QVBoxLayout(holder)
        root.setContentsMargins(9, 6, 9, 8)
        root.setSpacing(9)

        title = QLabel(tr('Conversor de formatos'))
        title.setStyleSheet('font-size: 16px; font-weight: 600;')
        root.addWidget(title)
        self.description = QLabel()
        self.description.setWordWrap(True)
        root.addWidget(self.description)

        operation_box = QGroupBox(tr('Operação'))
        operation_form = QFormLayout(operation_box)
        self.mode = QComboBox()
        self.mode.addItems([tr('RS2 → GeoTIFF (raster categórico)'),
                            tr('GeoTIFF → RS2 (formato Vista SAGA)'),
                            tr('RS2 → Vetor (polígonos)'),
                            tr('GeoTIFF → Vetor (polígonos)'),
                            tr('Vetor → GeoTIFF (rasterização)'),
                            tr('Vetor → RS2 (rasterização Vista SAGA)')])
        self.mode.currentIndexChanged.connect(self._mode_changed)
        operation_form.addRow(tr('Converter:'), self.mode)
        self.batch = QCheckBox(tr('Processar vários arquivos (lote)'))
        self.batch.toggled.connect(self._batch_changed)
        operation_form.addRow('', self.batch)
        root.addWidget(operation_box)

        self.single_group = QGroupBox(tr('Entrada'))
        single_form = QFormLayout(self.single_group)
        self.source = QLineEdit()
        self.source.setPlaceholderText(tr('Arquivo .rs2, .tif ou .tiff'))
        self.source.editingFinished.connect(self._sync_mode_with_source)
        self.source_button = QPushButton(tr('…'))
        self.source_button.setToolTip(tr('Selecionar arquivo no computador'))
        self.source_button.clicked.connect(self._browse_source)
        source_row = QHBoxLayout()
        source_row.addWidget(self.source, 1)
        source_row.addWidget(self.source_button)
        self.source_label = QLabel(tr('Arquivo de entrada:'))
        single_form.addRow(self.source_label, source_row)

        self.loaded_layers = QgsMapLayerComboBox()
        self.loaded_layers.setFilters(Qgis.LayerFilter.RasterLayer)
        self.loaded_layers.setAllowEmptyLayer(True)
        self.loaded_layers.setShowCrs(True)
        self.use_loaded = QPushButton(tr('Selecionar'))
        self.use_loaded.clicked.connect(self._use_layer)
        layer_row = QHBoxLayout()
        layer_row.addWidget(self.loaded_layers, 1)
        layer_row.addWidget(self.use_loaded)
        self.layer_label = QLabel(tr('Camada do projeto:'))
        single_form.addRow(self.layer_label, layer_row)
        self.vector_field = QComboBox()
        self.vector_field.setToolTip(tr('Atributo cujos valores serão gravados nas células do GeoTIFF.'))
        self.vector_field_label = QLabel(tr('Campo para rasterizar:'))
        single_form.addRow(self.vector_field_label, self.vector_field)
        self.pixel_size = QDoubleSpinBox()
        self.pixel_size.setDecimals(8)
        self.pixel_size.setRange(0.00000001, 100000000.0)
        self.pixel_size.setValue(10.0)
        self.pixel_size.setSuffix(tr(' unidades do SRC'))
        self.pixel_size.setToolTip(tr('Tamanho do pixel nas unidades do SRC do vetor; para SRC métrico, em metros.'))
        self.pixel_size_label = QLabel(tr('Tamanho do pixel:'))
        single_form.addRow(self.pixel_size_label, self.pixel_size)
        root.addWidget(self.single_group)

        self.batch_group = QGroupBox(tr('Arquivos do lote'))
        batch_layout = QVBoxLayout(self.batch_group)
        self.batch_list = QListWidget()
        self.batch_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.batch_list.setMinimumHeight(105)
        self.batch_list.setToolTip(tr('Um arquivo por linha. Selecione para remover.'))
        batch_layout.addWidget(self.batch_list)
        line = QHBoxLayout()
        self.add_files = QPushButton(tr('Adicionar arquivos…'))
        self.add_files.clicked.connect(self._browse_batch)
        self.add_layer = QPushButton(tr('Adicionar camada'))
        self.add_layer.clicked.connect(self._add_loaded_layer)
        self.add_many_loaded = QPushButton(tr('Adicionar várias do QGIS…'))
        self.add_many_loaded.clicked.connect(self._add_many_loaded_layers)
        self.batch_loaded_layers = QgsMapLayerComboBox()
        self.batch_loaded_layers.setFilters(Qgis.LayerFilter.RasterLayer)
        self.batch_loaded_layers.setAllowEmptyLayer(True)
        self.remove_files = QPushButton(tr('Remover selecionados'))
        self.remove_files.clicked.connect(self._remove_batch)
        line.addWidget(self.add_files)
        line.addWidget(self.remove_files)
        batch_layout.addLayout(line)
        batch_layer_row = QHBoxLayout()
        batch_layer_row.addWidget(self.batch_loaded_layers, 1)
        batch_layer_row.addWidget(self.add_layer)
        batch_layer_row.addWidget(self.add_many_loaded)
        self.batch_layer_widget = QWidget()
        self.batch_layer_widget.setLayout(batch_layer_row)
        batch_layout.addWidget(self.batch_layer_widget)
        root.addWidget(self.batch_group)
        self.batch_label = QLabel(tr('Arquivos do lote:'))  # compatibilidade com teste antigo

        self.output_group = QGroupBox(tr('Saída'))
        output_form = QFormLayout(self.output_group)
        self.destination = QLineEdit()
        self.destination.setPlaceholderText(tr('Informe o arquivo de saída'))
        self.dest_button = QPushButton(tr('…'))
        self.dest_button.setToolTip(tr('Selecionar destino'))
        self.dest_button.clicked.connect(self._browse_destination)
        dest_row = QHBoxLayout()
        dest_row.addWidget(self.destination, 1)
        dest_row.addWidget(self.dest_button)
        self.dest_label = QLabel(tr('Arquivo de saída:'))
        self.destination_row = QWidget()
        self.destination_row.setLayout(dest_row)
        output_form.addRow(self.dest_label, self.destination_row)

        self.batch_folder = QLineEdit()
        self.batch_folder.setPlaceholderText(tr('Pasta de saída dos arquivos convertidos'))
        self.batch_folder_button = QPushButton(tr('…'))
        self.batch_folder_button.clicked.connect(self._browse_folder)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.batch_folder, 1)
        folder_row.addWidget(self.batch_folder_button)
        self.folder_label = QLabel(tr('Pasta de saída:'))
        self.folder_row = QWidget()
        self.folder_row.setLayout(folder_row)
        output_form.addRow(self.folder_label, self.folder_row)

        self.vector_format = QComboBox()
        for extension, (_, label) in VECTOR_FORMATS.items():
            self.vector_format.addItem(f'{label} (*{extension})', extension)
        self.vector_format.currentIndexChanged.connect(self._vector_format_changed)
        self.vector_label = QLabel(tr('Formato vetorial:'))
        output_form.addRow(self.vector_label, self.vector_format)
        self.temporary_check = QCheckBox(tr('Resultado temporário no QGIS (pode ser salvo posteriormente)'))
        self.temporary_check.setChecked(True)
        self.temporary_check.toggled.connect(self._temp_changed)
        output_form.addRow('', self.temporary_check)
        root.addWidget(self.output_group)

        self.options_box = QGroupBox(tr('Sistema de referência e carregamento'))
        options_form = QFormLayout(self.options_box)
        self.crs_widget = QgsProjectionSelectionWidget()
        self.crs_widget.setOptionVisible(QgsProjectionSelectionWidget.CrsOption.CrsNotSet, True)
        self.crs_widget.setNotSetText(tr('Não definido - atribuir posteriormente'))
        self.crs_widget.setCrs(QgsCoordinateReferenceSystem())
        self.crs_widget.setDialogTitle(tr('Selecione o SRC confirmado do RS2'))
        self.crs_label = QLabel(tr('SRC do RS2:'))
        options_form.addRow(self.crs_label, self.crs_widget)
        self.add_to_project = QCheckBox(tr('Adicionar resultado ao projeto QGIS'))
        self.add_to_project.setChecked(True)
        options_form.addRow('', self.add_to_project)
        root.addWidget(self.options_box)

        self.advanced_toggle = QToolButton()
        self.advanced_toggle.setText(tr('Mostrar opções avançadas'))
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setChecked(False)
        self.advanced_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.advanced_toggle.toggled.connect(self._toggle_advanced)
        root.addWidget(self.advanced_toggle)
        self.advanced_panel = QGroupBox(tr('Opções avançadas'))
        advanced = QFormLayout(self.advanced_panel)
        self.reference = QLineEdit()
        self.reference.setPlaceholderText(tr('Opcional: recupera classes de TIFF RGB legado'))
        self.reference_button = QPushButton(tr('…'))
        self.reference_button.clicked.connect(self._browse_reference)
        ref_row = QHBoxLayout()
        ref_row.addWidget(self.reference, 1)
        ref_row.addWidget(self.reference_button)
        self.reference_label = QLabel(tr('RS2 de referência (RGB):'))
        self.reference_row = QWidget()
        self.reference_row.setLayout(ref_row)
        advanced.addRow(self.reference_label, self.reference_row)
        self.manual_bounds = QLineEdit()
        self.manual_bounds.setPlaceholderText(tr('xmin, ymin, xmax, ymax'))
        self.manual_bounds.setToolTip(tr('Somente quando o TIFF não tem georreferenciamento.'))
        self.bounds_label = QLabel(tr('Extensão manual:'))
        advanced.addRow(self.bounds_label, self.manual_bounds)
        self.background_nodata = QCheckBox(tr('Tratar a classe 0 como NoData'))
        self.background_nodata.setChecked(True)
        advanced.addRow('', self.background_nodata)
        self.vector_skip_background = QCheckBox(tr('Não criar polígonos da classe 0 (FUNDO)'))
        self.vector_skip_background.setToolTip(tr('Em rasters Float contínuos, 0 válido é preservado; apenas NoData é excluído.'))
        self.vector_skip_background.setChecked(True)
        advanced.addRow('', self.vector_skip_background)
        self.vector_all_touched = QCheckBox(tr('Rasterizar todas as células tocadas pelas feições (ALL_TOUCHED)'))
        self.vector_all_touched.setChecked(False)
        advanced.addRow('', self.vector_all_touched)
        self.rs2_code_mode = QComboBox()
        self.rs2_code_mode.addItem(tr('Automático (preservar os códigos; renumerar só 0 ou acima de 32768)'), 'auto')
        self.rs2_code_mode.addItem(tr('Preservar os códigos originais'), 'preserve')
        self.rs2_code_mode.addItem(tr('Renumerar sequencialmente (1..n)'), 'renumber')
        self.rs2_code_mode.setToolTip(
            tr('Campos inteiros: o RS2 exige códigos consecutivos a partir de 0 (FUNDO). '
            'A correspondência entre códigos originais e RS2 fica no arquivo .rs2.json.'))
        self.rs2_code_mode_label = QLabel(tr('Códigos RS2:'))
        advanced.addRow(self.rs2_code_mode_label, self.rs2_code_mode)
        self.float_classes_label = QLabel(tr('Classes para TIFF contínuo:'))
        self.float_classes = QSpinBox()
        self.float_classes.setRange(2, 20)
        self.float_classes.setValue(5)
        self.float_classes.setToolTip(
            tr('Apenas para GeoTIFF Float32/Float64: intervalos de igual amplitude. '
            'Células sem dados são excluídas. O TIFF original não é alterado.'))
        advanced.addRow(self.float_classes_label, self.float_classes)
        self.vector_connectivity = QComboBox()
        self.vector_connectivity.addItems([tr('4 vizinhos (lados)'), tr('8 vizinhos (lados e diagonais)')])
        self.connectivity_label = QLabel(tr('Contiguidade:'))
        advanced.addRow(self.connectivity_label, self.vector_connectivity)
        self.advanced_panel.hide()
        root.addWidget(self.advanced_panel)

        self.footer_hint = QLabel()
        self.footer_hint.setWordWrap(True)
        self.footer_hint.setStyleSheet('color: palette(mid);')
        root.addWidget(self.footer_hint)
        root.addStretch()
        scroll.setWidget(holder)
        use_tab_background(scroll)
        outer.addWidget(scroll, 1)

        actions = QHBoxLayout()
        self.inspect_button = QPushButton(tr('Propriedades RS2…'))
        self.inspect_button.clicked.connect(self._inspect)
        actions.addWidget(self.inspect_button)
        actions.addStretch(1)
        self.convert_button = QPushButton(tr('Executar'))
        self.convert_button.setDefault(True)
        self.convert_button.clicked.connect(self._convert)
        actions.addWidget(self.convert_button)
        close = QPushButton(tr('Fechar'))
        close.clicked.connect(self.close)
        actions.addWidget(close)
        outer.addLayout(actions)
        self._batch_changed()

    def _toggle_advanced(self, opened):
        self.advanced_panel.setVisible(opened)
        self.advanced_toggle.setArrowType(
            Qt.ArrowType.DownArrow if opened else Qt.ArrowType.RightArrow)
        self.advanced_toggle.setText(
            tr('Ocultar opções avançadas' if opened else 'Mostrar opções avançadas'))

    def _temp_changed(self, *_):
        persistent = not self.temporary_check.isChecked()
        for widget in (self.destination, self.dest_button, self.batch_folder, self.batch_folder_button):
            widget.setEnabled(persistent)
        if self.temporary_check.isChecked():
            self.add_to_project.setChecked(True)

    def _swap_crs_for_mode(self, operation):
        """Mantém um SRC para as operações com origem RS2 e outro para as demais."""
        group = 'rs2' if operation in RS2_SOURCE_OPERATIONS else 'other'
        if group == self._crs_group:
            return
        if self._crs_group == 'rs2':
            self._rs2_crs = self.crs_widget.crs()
        elif self._crs_group == 'other':
            self._other_crs = self.crs_widget.crs()
        self.crs_widget.setCrs(self._rs2_crs if group == 'rs2' else self._other_crs)
        self._crs_group = group

    def _apply_sidecar_crs(self):
        """Preenche o SRC registrado no .rs2.json do RS2 de entrada, quando existir."""
        if self.mode.currentIndex() not in RS2_SOURCE_OPERATIONS:
            return
        from .rs2_converter import sidecar_epsg
        epsg = sidecar_epsg(self.source.text().strip())
        if not epsg:
            return
        crs = QgsCoordinateReferenceSystem(epsg)
        if crs.isValid() and crs != self.crs_widget.crs():
            self.crs_widget.setCrs(crs)
            self.iface.messageBar().pushMessage(
                'Vista Saga Plugin',
                tr('SRC {0} obtido do arquivo .rs2.json do RS2 de entrada.').format(epsg),
                Qgis.MessageLevel.Info, 6)

    def _remember_rs2_crs(self):
        crs = self.crs_widget.crs()
        if self.mode.currentIndex() in RS2_SOURCE_OPERATIONS and crs.isValid():
            QgsSettings().setValue(RS2_CRS_SETTING, crs.authid())

    def _mode_changed(self, *_):
        operation = self.mode.currentIndex()
        self._swap_crs_for_mode(operation)
        writes_rs2 = operation in (1, 5)
        if writes_rs2 and self.temporary_check.isChecked():
            self.temporary_check.setChecked(False)
        self.temporary_check.setEnabled(not writes_rs2)
        self._temp_changed()
        to_tif, to_rs2, to_vector = operation == 0, operation == 1, operation in (2, 3)
        vector_to_rs2 = operation == 5
        from_vector = operation in (4, 5)
        tif_source = operation in (1, 3)
        if from_vector and self.batch.isChecked():
            self.batch.setChecked(False)
        self.batch.setEnabled(not from_vector)
        self.source.setPlaceholderText(
            tr('Vetor local (.gpkg, .shp, .geojson, .fgb)' if from_vector else
            'Arquivo .rs2, .tif ou .tiff'))
        self.layer_label.setText(tr('Camada vetorial do projeto:' if from_vector else 'Camada do projeto:'))
        many = self.batch.isChecked()
        self.loaded_layers.setFilters(Qgis.LayerFilter.VectorLayer if from_vector else Qgis.LayerFilter.RasterLayer)
        self.batch_loaded_layers.setFilters(Qgis.LayerFilter.RasterLayer)
        for widget in (self.crs_widget, self.crs_label):
            widget.setVisible(not to_rs2 and not from_vector)
        self.add_to_project.setVisible(not writes_rs2)
        for widget in (self.vector_field, self.vector_field_label, self.pixel_size, self.pixel_size_label):
            widget.setVisible(from_vector)
        self.vector_all_touched.setVisible(from_vector)
        self.rs2_code_mode.setVisible(vector_to_rs2)
        self.rs2_code_mode_label.setVisible(vector_to_rs2)
        self.crs_label.setText(tr('SRC da saída (opcional):' if operation == 3 else 'SRC do RS2:'))
        self.crs_widget.setDialogTitle(tr('SRC de saída (atribuição, sem reprojeção)'
                                       if operation == 3 else 'Selecione o SRC confirmado do RS2'))
        self.options_box.setVisible(not writes_rs2)
        self.inspect_button.setEnabled(operation in (0, 2) and not many)
        for widget in (self.layer_label, self.loaded_layers, self.use_loaded):
            widget.setVisible((tif_source or from_vector) and not many)
        self.batch_layer_widget.setVisible(tif_source)
        for widget in (self.reference_label, self.reference_row):
            widget.setVisible(writes_rs2 and not many)
        self.reference_label.setText(tr('RS2 de referência (grade):' if vector_to_rs2
                                        else 'RS2 de referência (RGB):'))
        self.reference.setPlaceholderText(
            tr('Opcional: copia origem, resolução e dimensões de um RS2 da mesma área'
               if vector_to_rs2 else 'Opcional: recupera classes de TIFF RGB legado'))
        for widget in (self.manual_bounds, self.bounds_label):
            widget.setVisible(tif_source)
        self.background_nodata.setVisible(to_tif)
        self.vector_skip_background.setVisible(to_vector)
        self.float_classes.setVisible(operation == 3)
        self.float_classes_label.setVisible(operation == 3)
        self.vector_connectivity.setVisible(to_vector)
        self.connectivity_label.setVisible(to_vector)
        self.vector_format.setVisible(to_vector)
        self.vector_label.setVisible(to_vector)
        self.description.setText((
            tr('Converte os códigos e legendas RS2 para um raster categórico de uma banda.' if to_tif else
            'Cria um RS2 a partir dos valores de um TIFF categórico ou das cores de um TIFF RGB.' if to_rs2 else
            'Rasteriza uma camada vetorial por atributo diretamente no formato RS2 do Vista SAGA.' if vector_to_rs2 else
            'Rasteriza uma camada vetorial por atributo, mantendo o SRC e os nomes das categorias.' if from_vector else
            'Gera polígonos contíguos por classe, com atributos CODIGO, CLASSE e COR_HEX.')
        ))
        self.footer_hint.setText((
            tr('O SRC não é identificado inequivocamente pelo RS2: selecione apenas se confirmado. '
            'Os códigos das classes são preservados.' if to_tif else
            'TIFFs RGB sem referência RS2 recebem códigos novos por cor; a referência é opcional. '
            'O TIFF precisa ter coordenadas ou uma extensão informada.' if to_rs2 else
            'A vetorização preserva a grade e as categorias RS2, sem reamostragem. '
            'Cada região contígua torna-se um polígono; mapas fragmentados podem gerar arquivos grandes. '
            'O SRC é opcional, mas deve ser confirmado.' if operation == 2 else
            'Para TIFF categórico, preserva os códigos; para RGB, cria códigos por cor HEX. '
            'Para TIFF contínuo Float32/Float64, forma intervalos de igual amplitude '
            '(quantidade em Opções avançadas), sem alterar o raster original. '
            'Valores NoData são excluídos; os limites constam nos campos VALOR_MIN e VALOR_MAX. '
            'O SRC vem do TIFF, salvo escolha explícita.' if operation == 3 else
            'Exige SRC projetado (por exemplo, UTM), sem reprojeção. Sem RS2 de referência, o pixel '
            'deve ser inteiro e a grade é alinhada a múltiplos dele; com referência (Opções avançadas), '
            'a grade do RS2 indicado é copiada para permitir cruzamentos célula a célula. '
            'Use campo inteiro ou textual; fundo = 0. O SRC fica apenas no arquivo .rs2.json.' if vector_to_rs2 else
            'Informe o campo e a resolução nas unidades do SRC de origem (metros se projetado em metros). '
            'SRC geográfico: resolução em graus. Área pela extensão do vetor; fundo = 0. '
            'SRC original preservado, sem reprojeção.')
        ))
        for widget in (self.reference, self.reference_button):
            widget.setEnabled(writes_rs2 and not many)
        self.manual_bounds.setEnabled(tif_source)
        if not many and self.source.text().strip():
            desired = ('.rs2' if writes_rs2 else '.tif' if (to_tif or from_vector)
                       else self.vector_format.currentData())
            output = self.destination.text().strip()
            if not output or Path(output).suffix.lower() != desired:
                self.destination.setText(
                    self._suggest_output(Path(self.source.text().strip()), operation))

    def _batch_changed(self, *_):
        many = self.batch.isChecked()
        self.single_group.setVisible(not many)
        self.batch_group.setVisible(many)
        self.dest_label.setVisible(not many)
        self.destination_row.setVisible(not many)
        self.folder_label.setVisible(many)
        self.folder_row.setVisible(many)
        self._mode_changed()

    def _vector_format_changed(self, *_):
        if self.mode.currentIndex() not in (2, 3) or not self.destination.text().strip():
            return
        path = Path(self.destination.text().strip())
        if path.suffix.lower() in VECTOR_FORMATS:
            self.destination.setText(str(path.with_suffix(self.vector_format.currentData())))

    def _sync_mode_with_source(self):
        raw = self.source.text().strip()
        filename = Path(raw.split('|', 1)[0])
        if filename.suffix.lower() in ('.gpkg', '.shp', '.geojson', '.json', '.fgb'):
            if self.mode.currentIndex() not in (4, 5):
                self.mode.setCurrentIndex(4)
            self._update_vector_fields()
            if not self.destination.text().strip():
                self.destination.setText(self._suggest_output(filename, self.mode.currentIndex()))
            return
        try:
            input_type = source_mode(filename)
        except Exception:
            return
        current = self.mode.currentIndex()
        if input_type == 1 and current not in (1, 3):
            self.mode.setCurrentIndex(1)
        elif input_type == 0 and current not in (0, 2):
            self.mode.setCurrentIndex(0)
        if not self.destination.text().strip():
            self.destination.setText(self._suggest_output(filename, self.mode.currentIndex()))

    def _suggest_output(self, file, operation):
        if operation == 0:
            return str(file.with_name(file.stem + '_categorias.tif'))
        if operation == 1:
            return str(file.with_name(file.stem + '_convertido.rs2'))
        if operation == 4:
            return str(file.with_name(file.stem + '_raster.tif'))
        if operation == 5:
            return str(file.with_name(file.stem + '_vetor.rs2'))
        return str(file.with_name(file.stem + '_poligonos' + self.vector_format.currentData()))

    def _set_source(self, filename):
        self.source.setText(filename)
        self.reference.clear()
        self._sync_mode_with_source()
        self.destination.setText(self._suggest_output(Path(filename.split('|', 1)[0]), self.mode.currentIndex()))
        self._apply_sidecar_crs()

    def _update_vector_fields(self):
        if self.mode.currentIndex() not in (4, 5):
            return
        previous = self.vector_field.currentText()
        self.vector_field.clear()
        text = self.source.text().strip()
        if not text:
            return
        layer = QgsVectorLayer(text, 'Fonte vetorial', 'ogr')
        if not layer.isValid():
            return
        if (self.mode.currentIndex() == 4 and layer.crs().isGeographic()
                and self.pixel_size.value() == 10.0):
            self.pixel_size.setValue(0.0001)  # exemplo de resolução em graus, editável
        fields = [field.name() for field in layer.fields()]
        self.vector_field.addItems(fields)
        if previous in fields:
            self.vector_field.setCurrentText(previous)
        elif 'CODIGO' in fields:
            self.vector_field.setCurrentText('CODIGO')
        elif fields:
            available = [field for field in fields if field.lower() not in ('fid', 'id', 'ogc_fid')]
            self.vector_field.setCurrentText(available[0] if available else fields[0])

    @staticmethod
    def _layer_path(layer):
        if layer is None or not layer.isValid():
            raise ValueError('Selecione uma camada raster válida do projeto.')
        # O QGIS pode carregar camadas virtuais, remotas, de banco ou de VRT.
        # Somente TIFF local sem parâmetros auxiliares pode ser usado diretamente.
        source = layer.source()
        path = Path(source)
        if path.suffix.lower() not in ('.tif', '.tiff') or not path.is_file():
            raise ValueError('Esta camada não é um TIFF local em disco. '
                             'Exporte-a para GeoTIFF no QGIS antes de utilizá-la.')
        return str(path)

    def _use_layer(self):
        try:
            if self.mode.currentIndex() in (4, 5):
                layer = self.loaded_layers.currentLayer()
                if layer is None or not isinstance(layer, QgsVectorLayer) or not layer.isValid():
                    raise ValueError('Selecione uma camada vetorial válida do projeto.')
                split_vector_source(layer.source())
                self._set_source(layer.source())
            else:
                self._set_source(self._layer_path(self.loaded_layers.currentLayer()))
        except ValueError as exc:
            QMessageBox.warning(self, tr('Camada raster'), tr(str(exc)))

    def _add_many_loaded_layers(self):
        layers = choose_project_layers(self, 'raster', 'Adicionar vários rasters do projeto')
        paths = []
        for layer in layers:
            try:
                paths.append(self._layer_path(layer))
            except ValueError as exc:
                QMessageBox.warning(self, tr('Camada ignorada'), tr(str(exc)))
        if paths:
            self._add_to_batch(paths)

    def _add_loaded_layer(self):
        try:
            self._add_to_batch([self._layer_path(self.batch_loaded_layers.currentLayer())])
        except ValueError as exc:
            QMessageBox.warning(self, tr('Camada raster'), tr(str(exc)))

    def _browse_source(self):
        pattern = ('Vetores (*.gpkg *.shp *.geojson *.json *.fgb)' if self.mode.currentIndex() in (4, 5) else
                   'GeoTIFF (*.tif *.tiff)' if self.mode.currentIndex() in (1, 3) else
                   'Vista SAGA (*.rs2)')
        filename, _ = QFileDialog.getOpenFileName(self, tr('Selecionar arquivo de entrada'), '', pattern)
        if filename:
            self._set_source(filename)

    def _browse_batch(self):
        names, _ = QFileDialog.getOpenFileNames(self, tr('Adicionar rasters ao lote'), '',
                                                ('GeoTIFF (*.tif *.tiff)' if self.mode.currentIndex() in (1, 3) else 'Vista SAGA (*.rs2)'))
        if names:
            self._add_to_batch(names)

    def _add_to_batch(self, names):
        current = self.mode.currentIndex()
        expected = 1 if current in (1, 3) else 0
        if any(source_mode(filename) != expected for filename in names):
            QMessageBox.warning(self, tr('Entrada do lote'),
                tr('Os arquivos selecionados não correspondem à operação atual. '
                'Use TIFF para operações de origem GeoTIFF e RS2 para operações de origem RS2.'))
            return
        present = {self.batch_list.item(i).text() for i in range(self.batch_list.count())}
        for filename in names:
            if filename not in present:
                self.batch_list.addItem(filename)
                present.add(filename)

    def _remove_batch(self):
        for item in self.batch_list.selectedItems():
            self.batch_list.takeItem(self.batch_list.row(item))

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr('Escolha a pasta de saída'),
                                                  self.batch_folder.text())
        if folder:
            self.batch_folder.setText(folder)

    def _browse_destination(self):
        operation = self.mode.currentIndex()
        ext = '.rs2' if operation in (1, 5) else '.tif' if operation in (0, 4) else self.vector_format.currentData()
        if operation in (0, 4):
            filt = 'GeoTIFF (*.tif)'
        elif operation in (1, 5):
            filt = 'Vista SAGA (*.rs2)'
        else:
            filt = f'{self.vector_format.currentText()}'
        filename, _ = QFileDialog.getSaveFileName(self, tr('Arquivo de saída'),
                                                   self.destination.text(), filt)
        if filename:
            path = Path(filename)
            if path.suffix.lower() != ext:
                filename = str(path.with_suffix(ext))
            self.destination.setText(filename)

    def _browse_reference(self):
        filename, _ = QFileDialog.getOpenFileName(self, tr('RS2 original de referência'), '',
                                                'Vista SAGA (*.rs2)')
        if filename:
            self.reference.setText(filename)

    def _inspect(self):
        try:
            h = RS2Reader(self.source.text().strip()).header
            classes = '\n'.join(f'  {code}: {label}' for code, label, _ in h.legend()[:16])
            if len(h.labels) > 16:
                classes += '\n  ...'
            QMessageBox.information(self, tr('Propriedades do RS2'),
                tr(f'Dimensões: {h.width} × {h.height}\n'
                f'Resolução: {h.pixel_x:g} × {h.pixel_y:g}\n'
                f'X: {h.xmin} - {h.xmax}\nY: {h.ymin} - {h.ymax}\n'
                f'Categorias: {h.num_classes}\n\n{classes}\n\n'
                'SRC não identificado no cabeçalho RS2.'))
        except Exception as exc:
            log_exception()
            QMessageBox.critical(self, tr('Falha na leitura do RS2'), tr(str(exc)))

    def _epsg(self):
        if self.mode.currentIndex() in (1, 4, 5):
            return ''
        crs = self.crs_widget.crs()
        if not crs.isValid():
            return ''
        if (self.mode.currentIndex() == 3 or not crs.isGeographic()) and crs.authid().upper().startswith('EPSG:'):
            return crs.authid().upper()
        if self.mode.currentIndex() == 3:
            raise ValueError('Selecione um SRC EPSG válido ou deixe o campo não definido '
                             'para preservar o SRC do GeoTIFF.')
        raise ValueError('O RS2 exige um SRC projetado com código EPSG, '
                         'ou a opção “Não definido”. Não é possível atribuir '
                         'um SRC geográfico à grade RS2 sem reprojeção.')

    def _plans(self):
        operation = self.mode.currentIndex()
        if self.batch.isChecked():
            sources = [self.batch_list.item(i).text() for i in range(self.batch_list.count())]
            folder = (str(Path(temporary_destination('lote', '.tmp')).parent)
                      if self.temporary_check.isChecked() and operation != 1
                      else self.batch_folder.text().strip())
            _, plans, _ = prepare_batch(
                sources, folder,
                self.manual_bounds.text().strip() or None,
                operation=operation, vector_extension=self.vector_format.currentData())
            return operation, plans
        ext = ('.tif' if operation in (0, 4) else '.rs2' if operation in (1, 5)
               else self.vector_format.currentData())
        output_file = (temporary_destination('conversao', ext)
                       if self.temporary_check.isChecked() and operation not in (1, 5)
                       else self.destination.text().strip())
        if operation in (4, 5):
            source_uri = self.source.text().strip()
            source_file, _, _ = split_vector_source(source_uri)
            field = self.vector_field.currentText().strip()
            if not field:
                raise ValueError('Selecione o campo do vetor que fornecerá os valores dos pixels.')
            if not output_file:
                raise ValueError('Informe o RS2 de saída.' if operation == 5
                                 else 'Informe o GeoTIFF de saída.')
            target = Path(output_file)
            if target.suffix.lower() != ext:
                raise ValueError(f'Esta rasterização deve produzir um arquivo {ext}.')
            if source_file.resolve() == target.resolve():
                raise ValueError('A saída não pode sobrescrever a entrada.')
            reference = self.reference.text().strip()
            if operation == 5 and reference:
                if not Path(reference).is_file():
                    raise ValueError('O RS2 de referência não foi encontrado.')
                if Path(reference).resolve() == target.resolve():
                    raise ValueError('A saída não pode substituir o RS2 de referência.')
            return operation, [(source_uri, target)]
        source = Path(self.source.text().strip())
        if not source.is_file():
            raise ValueError('Selecione um arquivo raster existente.')
        input_mode = source_mode(source)
        if (input_mode == 1) != (operation in (1, 3)):
            raise ValueError('O tipo do arquivo não corresponde à operação escolhida.')
        if not output_file:
            raise ValueError('Informe o caminho da saída.')
        target = Path(output_file)
        expected = '.tif' if operation == 0 else '.rs2' if operation == 1 else self.vector_format.currentData()
        if target.suffix.lower() != expected:
            raise ValueError(f'Esta operação produz {expected}; corrija a extensão da saída.')
        if target.resolve() == source.resolve():
            raise ValueError('A saída não pode sobrescrever a entrada.')
        if (operation == 1 and self.reference.text().strip() and
                target.resolve() == Path(self.reference.text().strip()).resolve()):
            raise ValueError('A saída não pode substituir o RS2 de referência.')
        return operation, [(source, target)]

    @staticmethod
    def _style_vector(layer, rs2_source, omit_background):
        # Simbologia categorizada nativa: o campo HEX permanece no arquivo.
        # Falhas cosméticas não devem impedir a conversão ou abrir a camada.
        try:
            from qgis.PyQt.QtGui import QColor
            from qgis.core import (QgsCategorizedSymbolRenderer,
                                   QgsRendererCategory, QgsFillSymbol)
            from .rs2_vector import class_attributes
            categories = []
            header = RS2Reader(rs2_source).header
            for code, label, color in class_attributes(header):
                if omit_background and code == header.background_code:
                    continue
                symbol = QgsFillSymbol.createSimple({
                    'color': QColor(color).name(),
                    'outline_color': '70,70,70,255',
                    'outline_width': '0.1',
                })
                categories.append(QgsRendererCategory(code, symbol, label))
            layer.setRenderer(QgsCategorizedSymbolRenderer('CODIGO', categories))
            layer.triggerRepaint()
        except Exception as exc:
            # Falha de simbologia não invalida o vetor exportado; registrar o erro.
            log_exception()
            QgsMessageLog.logMessage(
                tr(f'Não foi possível aplicar a simbologia RS2 ao vetor: {exc}'),
                'Vista Saga Plugin', Qgis.MessageLevel.Warning,
            )

    @staticmethod
    def _style_tiff_vector(layer, tif_source, omit_background):
        """Aplica cores categóricas documentadas no TIFF; sem paleta, mantém estilo padrão."""
        try:
            from osgeo import gdal
            from qgis.core import QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsFillSymbol
            ds = gdal.Open(str(tif_source), gdal.GA_ReadOnly)
            if ds is None:
                return
            if ds.RasterCount == 1:
                band = ds.GetRasterBand(1)
                from .monitoring_vector import find_monitoring_transitions, monitoring_color
                transitions = find_monitoring_transitions(tif_source, band)
                mapping = ({code: (row['legenda'], monitoring_color(
                           code, row['situacao'] == 'Mudança'))
                           for code, row in transitions.items()} if transitions
                           else _legend(tif_source, band))
            elif ds.RasterCount in (3, 4):
                from .rs2_rgb import discover_rgb_palette
                labels, colors = discover_rgb_palette(ds, max_colors=256)
                mapping = {i: (label, '#' + ''.join(f'{int(c):02X}' for c in color[:3]))
                           for i, (label, color) in enumerate(zip(labels, colors))}
            else:
                return
            ds = None
            items = [(code, label, color) for code, (label, color) in mapping.items()
                     if color and (code != 0 or not omit_background)]
            # A simbologia completa pode ser excessiva em rasters com milhares de categorias.
            if not items or len(items) > 256:
                return
            categories = [QgsRendererCategory(code,
                QgsFillSymbol.createSimple({'color': color,
                                            'outline_color': '70,70,70,255',
                                            'outline_width': '0.1'}), label)
                for code, label, color in items]
            layer.setRenderer(QgsCategorizedSymbolRenderer('CODIGO', categories))
            layer.triggerRepaint()
        except Exception as exc:
            # A simbologia é opcional: manter o vetor e registrar a falha.
            log_exception()
            QgsMessageLog.logMessage(
                tr(f'Não foi possível aplicar a simbologia do GeoTIFF ao vetor: {exc}'),
                'Vista Saga Plugin', Qgis.MessageLevel.Warning,
            )

    @staticmethod
    def _vector_rs2_notes(summary):
        """Avisos metodológicos da rasterização Vetor → RS2 para o relatório final."""
        notes = []
        if summary.get('overlap_cells'):
            notes.append(tr(f"{summary['overlap_cells']} célula(s) cobertas por mais de uma feição; "
                         'prevaleceu a última feição processada. Corrija sobreposições se '
                         'as classes conflitarem.'))
        if summary.get('code_mode') == 'renumber':
            notes.append(tr('Códigos renumerados para 1..n; a correspondência com os valores '
                         'originais está no arquivo .rs2.json.'))
        if summary.get('skipped_features'):
            notes.append(tr(f"{summary['skipped_features']} feição(ões) ignorada(s) por geometria "
                         'vazia ou atributo nulo.'))
        empty = summary.get('empty_classes') or []
        if empty:
            notes.append(tr(f'{len(empty)} classe(s) sem nenhuma célula na resolução escolhida, '
                         f"omitida(s) da legenda RS2 (por exemplo: {', '.join(empty[:3])}). "
                         'Reduza o pixel ou use ALL_TOUCHED.'))
        return notes

    def _convert(self):
        try:
            operation, plans = self._plans()
            epsg = self._epsg()
        except Exception as exc:
            log_exception()
            QMessageBox.warning(self, tr('Conferir parâmetros'), tr(str(exc)))
            return
        total = len(plans)
        crs_by_source = {}
        if operation in RS2_SOURCE_OPERATIONS:
            # SRC escolhido no campo; sem ele, o SRC registrado no .rs2.json de cada RS2.
            from .rs2_converter import sidecar_epsg
            crs_by_source = {str(source): epsg or sidecar_epsg(source) for source, _ in plans}
            missing = [Path(str(source)).name for source, _ in plans if not crs_by_source[str(source)]]
            if missing:
                listed = '\n'.join('• ' + name for name in missing[:8])
                if len(missing) > 8:
                    listed += '\n' + tr('… e mais {count} arquivos.').format(count=len(missing) - 8)
                answer = QMessageBox.question(
                    self, tr('Saída sem SRC'),
                    tr('O RS2 não registra o sistema de referência. Sem um SRC escolhido no campo '
                       '"SRC do RS2", as saídas terão coordenadas, mas SRC desconhecido no QGIS:')
                    + '\n\n' + listed + '\n\n' + tr('Continuar sem SRC?'),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)
                if answer != QMessageBox.StandardButton.Yes:
                    return
            from_sidecar = sorted({crs for source, crs in crs_by_source.items() if crs and not epsg})
        if self.batch.isChecked() and total > 1:
            warnings = alignment_warnings(
                [source for source, _ in plans],
                (self.manual_bounds.text().strip() or None) if operation in (1, 3) else None)
            if warnings:
                lines = '\n'.join('• ' + warning for warning in warnings[:8])
                if len(warnings) > 8:
                    lines += f'\n… e mais {len(warnings)-8} arquivos.'
                answer = QMessageBox.question(
                    self, tr('Atenção: grades deslocadas'),
                    tr('Os mapas possuem mesmas dimensões e resolução, mas nem '
                    'todos apresentam a mesma localização espacial:\n\n' + lines +
                    '\n\nA conversão de cada arquivo será feita sem alteração '
                    'das coordenadas. Para análises integradas será necessário '
                    'verificar o alinhamento das grades. Continuar?'),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)
                if answer != QMessageBox.StandardButton.Yes:
                    return
        if operation in (0, 2, 3, 4):
            loaded = {str(Path(layer.source().split('|', 1)[0]).resolve())
                      for layer in QgsProject.instance().mapLayers().values()
                      if isinstance(layer, (QgsRasterLayer, QgsVectorLayer)) and layer.isValid()}
            blocked = [str(dest) for _, dest in plans
                       if dest.exists() and str(dest.resolve()) in loaded]
            if blocked:
                QMessageBox.warning(
                    self, tr('Arquivo de saída aberto no QGIS'),
                    tr('Um ou mais arquivos de saída já estão carregados no projeto. '
                    'No Windows, o QGIS/GDAL pode manter esses arquivos bloqueados. '
                    'Remova temporariamente as camadas de saída do projeto, '
                    'ou escolha outra pasta/nome antes de sobrescrevê-los:\n\n' +
                    '\n'.join(blocked[:8])))
                return
        conflicts = []
        for _, dest in plans:
            if operation in (0, 4):
                conflicts.extend(output_conflicts(dest))
            elif operation in (2, 3):
                conflicts.extend(vector_conflicts(dest))
            else:
                for p in (dest, Path(str(dest) + '.rs2.json')):
                    if p.exists():
                        conflicts.append(p)
        if conflicts:
            preview = '\n'.join('• ' + str(p.name) for p in conflicts[:9])
            if len(conflicts) > 9:
                preview += f'\n… e outros {len(conflicts) - 9} arquivos.'
            answer = QMessageBox.question(
                self, tr('Sobrescrever saídas e arquivos auxiliares'),
                tr(f'{len(conflicts)} arquivo(s) existente(s) serão substituídos ou '
                f'removidos para evitar metadados obsoletos:\n\n{preview}\n\n'
                'Deseja continuar?'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
        if operation == 1 and not self.batch.isChecked() and not self.reference.text().strip():
            # Aviso apenas para TIFF RGB; monobanda não perde seus códigos.
            try:
                from osgeo import gdal
                ds = gdal.Open(str(plans[0][0]), gdal.GA_ReadOnly)
                if ds is None:
                    raise ValueError('Não foi possível abrir o TIFF.')
                n = ds.RasterCount
                ds = None
                if n in (3, 4):
                    answer = QMessageBox.question(
                        self, tr('TIFF RGB: códigos novos'),
                        tr('Sem o RS2 de referência, cada cor HEX receberá código novo '
                        'e nome genérico. Os códigos históricos não serão recuperados. '
                        'Deseja continuar?'),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No)
                    if answer != QMessageBox.StandardButton.Yes:
                        return
            except Exception as exc:
                log_exception()
                QMessageBox.warning(self, tr('Entrada TIFF'), tr(str(exc)))
                return
        progress = QProgressDialog(tr('Convertendo mapas…'), tr('Cancelar'), 0, 100, self)
        progress.setWindowTitle(tr('Vista Saga Plugin - conversor'))
        progress.setMinimumDuration(0)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        completed, failures, notes = [], [], []
        if operation in RS2_SOURCE_OPERATIONS:
            self._remember_rs2_crs()
            if from_sidecar:
                notes.append(tr('SRC obtido do arquivo .rs2.json: {0}.').format(', '.join(from_sidecar)))
        try:
            from .rs2_converter import convert_rs2_to_tif, convert_tif_to_rs2
            for i, (source, dest) in enumerate(plans):
                if progress.wasCanceled():
                    break
                progress.setLabelText(tr(f"Arquivo {i+1}/{total}: {Path(str(source).split('|')[0]).name}"))

                def on_progress(done, height, item=i):
                    progress.setValue(round(100 * (item + done / max(height, 1)) / total))
                    QCoreApplication.processEvents()
                    return not progress.wasCanceled()

                try:
                    if operation == 0:
                        result = convert_rs2_to_tif(source, dest, crs_by_source[str(source)], on_progress,
                                                    self.background_nodata.isChecked())
                        if self.add_to_project.isChecked() or self.temporary_check.isChecked():
                            layer = QgsRasterLayer(str(result), Path(result).stem)
                            if layer.isValid():
                                QgsProject.instance().addMapLayer(layer)
                    elif operation == 1:
                        reference = None if self.batch.isChecked() else self.reference.text().strip() or None
                        result = convert_tif_to_rs2(source, dest, on_progress, reference,
                                                    self.manual_bounds.text().strip() or None)
                    elif operation == 2:
                        result = convert_rs2_to_vector(
                            source, dest, crs_by_source[str(source)], on_progress,
                            self.vector_skip_background.isChecked(),
                            self.vector_connectivity.currentIndex() == 1)
                        if self.add_to_project.isChecked() or self.temporary_check.isChecked():
                            layer = QgsVectorLayer(str(result), Path(result).stem, 'ogr')
                            if layer.isValid():
                                self._style_vector(
                                    layer, source, self.vector_skip_background.isChecked())
                                QgsProject.instance().addMapLayer(layer)
                    elif operation == 3:
                        result = convert_tif_to_vector(
                            source, dest, epsg, on_progress,
                            self.vector_skip_background.isChecked(),
                            self.vector_connectivity.currentIndex() == 1,
                            self.manual_bounds.text().strip() or None,
                            continuous_classes=self.float_classes.value())
                        if self.add_to_project.isChecked() or self.temporary_check.isChecked():
                            layer = QgsVectorLayer(str(result), Path(result).stem, 'ogr')
                            if layer.isValid():
                                self._style_tiff_vector(layer, source, self.vector_skip_background.isChecked())
                                QgsProject.instance().addMapLayer(layer)
                    elif operation == 5:
                        result = convert_vector_to_rs2(
                            source, dest, self.vector_field.currentText(),
                            self.pixel_size.value(), on_progress,
                            self.vector_all_touched.isChecked(),
                            self.reference.text().strip() or None,
                            self.rs2_code_mode.currentData())
                        notes.extend(self._vector_rs2_notes(result.summary))
                    else:
                        result = convert_vector_to_tif(
                            source, dest, self.vector_field.currentText(),
                            self.pixel_size.value(), on_progress,
                            self.vector_all_touched.isChecked())
                        if self.add_to_project.isChecked() or self.temporary_check.isChecked():
                            layer = QgsRasterLayer(str(result), Path(result).stem)
                            if layer.isValid():
                                QgsProject.instance().addMapLayer(layer)
                    completed.append(str(result))
                except Exception as exc:
                    log_exception()
                    failures.append(f"{Path(str(source).split('|')[0]).name}: {tr(str(exc))}")
                    # Não impede processar os outros arquivos no lote.
            progress.setValue(100)
        finally:
            progress.close()
        report = tr('Convertidos com sucesso: {done} de {total}.').format(done=len(completed), total=total)
        if failures:
            report += '\n\n' + tr('Falhas:') + '\n' + '\n'.join(tr(item) for item in failures[:12])
            if len(failures) > 12:
                report += '\n' + tr('… e mais {count} falhas.').format(count=len(failures) - 12)
        if len(completed) < total and not failures:
            report += '\n\n' + tr('Processamento cancelado antes do término.')
        if notes:
            report += '\n\n' + tr('Atenção:') + '\n' + '\n'.join('• ' + note for note in notes)
        if completed:
            report += '\n\n' + tr('Saída: {path}').format(path=Path(completed[0]).parent)
        if failures:
            QMessageBox.warning(self, tr('Conversão parcialmente concluída'), tr(report))
        else:
            QMessageBox.information(self, tr('Conversão concluída'), tr(report))
