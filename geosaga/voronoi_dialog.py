"""Interface QGIS 4 para Análises Voronoi (quatro modalidades)."""
from .i18n import tr
from pathlib import Path
import os
from math import isfinite

from qgis.PyQt.QtCore import Qt, pyqtSlot
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDoubleSpinBox,
    QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QProgressDialog, QPushButton,
    QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QScrollArea, QWidget, QFrame, QTabWidget,
)
from qgis.core import (
    Qgis, QgsApplication, QgsTask, QgsCoordinateTransform, QgsFillSymbol, QgsPalettedRasterRenderer,
    QgsProject, QgsRasterLayer, QgsVectorLayer, QgsCategorizedSymbolRenderer,
    QgsRendererCategory, QgsWkbTypes, QgsGeometry,
)
from qgis.gui import QgsMapLayerComboBox

from .ui_shared import use_tab_background, temporary_destination, materialize_in_memory
from .voronoi_core import Generator
from .voronoi_engine import grid_from_extent, run_voronoi
from .voronoi_vector import save_vector_voronoi
from .voronoi_output import VECTOR_FORMATS, layer_uri, output_family, vector_extension
from .errors import log_exception


def _is_null(value):
    """NULL do QGIS: None no PyQt6; QVariant nulo em versões que ainda o expõem."""
    if value is None:
        return True
    is_null = getattr(value, 'isNull', None)
    return bool(is_null()) if callable(is_null) else False


RASTER_RESULT_HINT = (
    'Em branco, o mapa é gravado num arquivo temporário e carregado no QGIS (o QGIS não '
    'mantém rasters em memória; salve-o antes de fechar o QGIS). Com um arquivo indicado, '
    'ele é salvo em disco e carregado no QGIS. Além do mapa, são gerados _centros.csv e '
    '_resumo.txt; sem arquivo indicado, eles ficam na pasta temporária do QGIS.')

VECTOR_RESULT_HINT = (
    'Em branco, o resultado é carregado no QGIS como camada temporária em memória (salve-a '
    'antes de fechar o QGIS). Com um arquivo indicado (GeoPackage, Shapefile, GeoJSON ou '
    'FlatGeobuf), ele é salvo em disco e carregado no QGIS. Além do mapa, são gerados '
    '_centros.csv e _resumo.txt; sem arquivo indicado, eles ficam na pasta temporária do QGIS.')


class _WrapLabel(QLabel):
    """Rótulo com quebra de linha cuja altura acompanha a largura real.

    Dentro de QScrollArea, o QLabel comum informa a altura calculada para uma
    largura estreita e deixa folgas grandes acima e abaixo do texto.
    """
    def __init__(self, text=''):
        super().__init__(text)
        self.setWordWrap(True)

    def _fit(self, hint):
        if self.width() > 50:
            hint.setHeight(self.heightForWidth(self.width()))
        return hint

    def sizeHint(self):
        return self._fit(super().sizeHint())

    def minimumSizeHint(self):
        return self._fit(super().minimumSizeHint())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateGeometry()


class VoronoiRasterTask(QgsTask):
    """Executa APENAS dados isolados do raster, sem Qt/UI ou QgsMapLayer em run().

    Signals/progress são administrados pelo QgsTask; a UI é atualizada apenas
    no método finished(), que o QGIS invoca na thread principal.
    """
    def __init__(self, points, destination, wkt, transform, width, height, mode, vectorize, friction_path=None, friction_components=None,
                 vector_format='.gpkg', keep_raster=True, friction_vector=None):
        super().__init__('Vista Saga - Voronoi raster', QgsTask.Flag.CanCancel)
        self.points = tuple(points)  # Generator é uma dataclass simples, sem QObject.
        self.destination = str(destination)
        self.wkt = str(wkt)
        self.transform = tuple(transform)
        self.width = int(width)
        self.height = int(height)
        self.mode = str(mode)
        self.vectorize = bool(vectorize)
        self.vector_format = str(vector_format)
        self.keep_raster = bool(keep_raster)
        self.friction_path = str(friction_path) if friction_path else None
        self.friction_components = tuple(dict(spec) for spec in friction_components) if friction_components else None
        # Atrito vetorial: WKB e notas já extraídos na thread principal (sem QgsVectorLayer aqui).
        self.friction_vector = dict(friction_vector) if friction_vector else None
        self.result = None
        self.error = None
        self.ui_callback = None

    def run(self):
        try:
            self.result = run_voronoi(
                self.points, self.destination, self.wkt, self.transform,
                self.width, self.height, mode=self.mode, vectorize=self.vectorize,
                progress=self.setProgress, cancelled=self.isCanceled,
                friction_path=self.friction_path, friction_components=self.friction_components,
                vector_format=self.vector_format, keep_raster=self.keep_raster,
                friction_vector=self.friction_vector,
            )
            return not self.isCanceled()
        except InterruptedError:
            return False
        except Exception as exc:
            log_exception()
            self.error = str(exc)
            return False

    def finished(self, success):
        # Não chamar UI se o complemento já tiver sido descarregado.
        callback = self.ui_callback
        self.ui_callback = None
        if callback is not None:
            callback(self, bool(success))


class VoronoiVectorTask(QgsTask):
    """Vetor direto com atrito em segundo plano (1.4.0-dev5): pode levar minutos com dados reais.

    Só dados isolados (WKB, notas, pontos); nada de QgsMapLayer em run(). Progresso em porcentagem
    pelo QgsTask e cancelamento pelo botão do diálogo ou do gerenciador de tarefas do QGIS.
    """
    def __init__(self, points, bounds, destination, wkt, mode, study_geometry, friction_spec):
        super().__init__('Vista Saga - Voronoi vetorial com atrito', QgsTask.Flag.CanCancel)
        self.points = tuple(points)
        self.bounds = tuple(float(v) for v in bounds)
        self.destination = str(destination)
        self.wkt = str(wkt)
        self.mode = str(mode)
        self.study_geometry = QgsGeometry(study_geometry) if study_geometry is not None else None
        self.friction_spec = dict(friction_spec)
        self.result = None
        self.error = None
        self.ui_callback = None

    def run(self):
        try:
            self.result = save_vector_voronoi(
                self.points, self.bounds, self.destination, self.wkt, mode=self.mode,
                study_geometry=self.study_geometry, progress=self.setProgress, cancelled=self.isCanceled,
                friction_features=self.friction_spec['features'], search_spacing=None,
                friction_info=self.friction_spec)
            return not self.isCanceled()
        except InterruptedError:
            return False
        except Exception as exc:
            log_exception()
            self.error = str(exc)
            return False

    def finished(self, success):
        callback = self.ui_callback
        self.ui_callback = None
        if callback is not None:
            callback(self, bool(success))


class VoronoiDialog(QDialog):
    """Quatro modalidades no modelo do Vista SAGA; atrito raster ou vetorial (1.4.0)."""
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self._busy = False
        self._task = None
        self._progress_dialog = None
        self.setWindowTitle(tr('Vista Saga Plugin - Análises Voronoi'))
        self.setModal(False)
        self.setMinimumSize(630, 450)
        self.resize(760, 605)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        # Guias "Raster" e "Vetorial", como na Combinação de Mapas e na Monitoria.
        # Modelo e dados de entrada são os mesmos nas duas guias: os grupos
        # acompanham a guia ativa (_tab_changed); só o resultado é próprio de cada uma.
        # A área rolável impede controles comprimidos com o atrito múltiplo.
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self._pages = []
        for title in ('Raster', 'Vetorial'):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            holder = QWidget()
            body = QVBoxLayout(holder)
            body.setContentsMargins(9, 9, 9, 9)  # mesma margem interna das guias da Combinação
            body.setSpacing(6)
            scroll.setWidget(holder)
            use_tab_background(scroll)
            self.tabs.addTab(scroll, tr(title))
            self._pages.append(body)
        content_layout = self._pages[0]
        self.intro = _WrapLabel(tr('Delimite áreas de influência: Simples, com Massa, com Atrito e com Massa e Atrito, '
                            'nos modelos do Vista SAGA original (massa como M/d²).'))
        self.intro.setWordWrap(True)
        content_layout.addWidget(self.intro)

        options = QGroupBox(tr('Modelo de influência'))
        model_form = QFormLayout(options)
        self.mode = QComboBox()
        self.mode.addItems([tr('Simples'), tr('Com Massa'),
                            tr('Com Atrito'),
                            tr('Com Massa e Atrito')])
        self.mode.currentIndexChanged.connect(self._update_mode)
        model_form.addRow(tr('Modalidade:'),self.mode)
        self.method_note = _WrapLabel(tr('Simples: o ponto mais próximo assume cada célula da grade.'))
        self.method_note.setWordWrap(True)
        model_form.addRow(tr('Método:'),self.method_note)
        content_layout.addWidget(options)

        inputs = QGroupBox(tr('Dados de entrada'))
        form = QFormLayout(inputs)
        self.point_layer = QgsMapLayerComboBox()
        self.point_layer.setAllowEmptyLayer(True)
        self.point_layer.setShowCrs(True)
        self.point_layer.setFilters(Qgis.LayerFilter.VectorLayer)
        self.point_layer.layerChanged.connect(self._refresh_fields)
        form.addRow(tr('Pontos geradores:'),self.point_layer)
        self.label_field = QComboBox()
        self.label_field.addItem(tr('(usar ID da feição)'),None)
        form.addRow(tr('Identificação do ponto:'),self.label_field)
        self.mass_field = QComboBox()
        self.mass_field.setEnabled(False)
        self.mass_label=QLabel(tr('Campo de massa:'))
        form.addRow(self.mass_label,self.mass_field)
        self.grid_layer = QgsMapLayerComboBox()
        self.grid_layer.setAllowEmptyLayer(True)
        self.grid_layer.setFilters(Qgis.LayerFilter.RasterLayer)
        self.grid_layer.setShowCrs(True)
        self.grid_layer.layerChanged.connect(self._update_grid)
        self.grid_layer.setToolTip(tr('Opcional: utilize a extensão, resolução e SRC de um raster de referência.'))
        self.grid_label=QLabel(tr('Raster de referência:'))
        form.addRow(self.grid_label,self.grid_layer)
        # 1.4.0: a superfície de atrito pode ser raster (notas nas células) ou vetorial
        # (polígonos com nota por classe ou por coluna, rasterizados na grade da análise).
        self.friction_kind = QComboBox()
        self.friction_kind.addItem(tr('Raster'), 'raster')
        self.friction_kind.addItem(tr('Vetorial (polígonos)'), 'vector')
        self.friction_kind.currentIndexChanged.connect(self._update_mode)
        self.friction_kind_label = QLabel(tr('Tipo de superfície:'))
        form.addRow(self.friction_kind_label, self.friction_kind)
        self.friction_layer = QgsMapLayerComboBox()
        self.friction_layer.setAllowEmptyLayer(True)
        self.friction_layer.setFilters(Qgis.LayerFilter.RasterLayer)
        self.friction_layer.setShowCrs(True)
        self.friction_label = QLabel(tr('Superfície de atrito:'))
        self.friction_layer.setToolTip(tr('GeoTIFF monobanda: o valor de cada célula é a nota de atrito (> 0); NoData é barreira.'))
        form.addRow(self.friction_label,self.friction_layer)
        self.friction_vector_layer = QgsMapLayerComboBox()
        self.friction_vector_layer.setAllowEmptyLayer(True)
        self.friction_vector_layer.setFilters(Qgis.LayerFilter.PolygonLayer)
        self.friction_vector_layer.setShowCrs(True)
        self.friction_vector_layer.layerChanged.connect(self._refresh_friction_fields)
        self.friction_vector_label = QLabel(tr('Polígonos de atrito:'))
        form.addRow(self.friction_vector_label, self.friction_vector_layer)
        self.friction_rating_field = QComboBox()
        self.friction_rating_field.setToolTip(tr('Coluna numérica com a nota de atrito de cada polígono (> 0). '
                                                 'Área sem polígono e feições com a coluna vazia são barreira.'))
        self.friction_rating_label = QLabel(tr('Coluna de atrito:'))
        form.addRow(self.friction_rating_label, self.friction_rating_field)
        self.multi_friction = QCheckBox(tr('Combinar múltiplas superfícies de atrito (pesos e notas)'))
        self.multi_friction.toggled.connect(self._on_multi_friction_toggled)
        form.addRow('', self.multi_friction)
        self.friction_stack_group = QGroupBox(tr('Superfícies integradas'))
        stack_box = QVBoxLayout(self.friction_stack_group)
        self.friction_stack_summary = QLabel(tr('Nenhuma superfície selecionada.'))
        self.friction_stack_summary.setWordWrap(True)
        stack_box.addWidget(self.friction_stack_summary)
        self.stack_manage = QPushButton(tr('Selecionar e configurar superfícies…'))
        self.stack_manage.clicked.connect(self._manage_friction_layers)
        stack_box.addWidget(self.stack_manage)
        form.addRow('', self.friction_stack_group)

        # A seleção e a edição de massas/atritos ficam em um diálogo próprio.
        # Na 0.8.3 a tabela estava diretamente no formulário, e a janela
        # sem rolagem podia exibir apenas o título "Superfícies integradas".
        self.friction_stack_dialog = QDialog(self)
        self.friction_stack_dialog.setWindowTitle(tr('Superfícies de atrito - seleção e pesos'))
        self.friction_stack_dialog.resize(840, 475)
        stack_dialog_box = QVBoxLayout(self.friction_stack_dialog)
        stack_hint = QLabel(tr('Selecione até 12 rasters. Edite o peso positivo e, se necessário, as notas '
                            'por classe (ex.: 1=2;2=8) dando dois cliques nas células. '
                            'Sem notas, serão usados os valores originais. '
                            'NoData em qualquer mapa será barreira.'))
        stack_hint.setWordWrap(True)
        stack_dialog_box.addWidget(stack_hint)
        self.friction_stack_table = QTableWidget(0, 3)
        self.friction_stack_table.setHorizontalHeaderLabels([tr('Camada raster'), tr('Peso'), tr('Notas por classe (opcional)')])
        self.friction_stack_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.friction_stack_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.friction_stack_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.friction_stack_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.friction_stack_table.horizontalHeader().resizeSection(1, 85)
        self.friction_stack_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        stack_dialog_box.addWidget(self.friction_stack_table, 1)
        stack_buttons = QHBoxLayout()
        self.stack_add = QPushButton(tr('Adicionar camadas do QGIS…'))
        self.stack_add.clicked.connect(self._add_friction_layers)
        stack_buttons.addWidget(self.stack_add)
        self.stack_add_files = QPushButton(tr('Adicionar arquivos GeoTIFF…'))
        self.stack_add_files.clicked.connect(self._add_friction_files)
        stack_buttons.addWidget(self.stack_add_files)
        self.stack_remove = QPushButton(tr('Remover selecionadas'))
        self.stack_remove.clicked.connect(self._remove_friction_layers)
        stack_buttons.addWidget(self.stack_remove)
        stack_buttons.addStretch(1)
        stack_dialog_box.addLayout(stack_buttons)
        stack_close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        stack_close.rejected.connect(self.friction_stack_dialog.accept)
        stack_dialog_box.addWidget(stack_close)
        self.extent_mode=QComboBox()
        self.extent_mode.addItem(tr('Extensão visível no QGIS'),'canvas')
        self.extent_mode.addItem(tr('Extensão de camada poligonal'),'polygon')
        self.extent_mode.addItem(tr('Extensão manual (coordenadas do SRC)'),'manual')
        self.extent_mode.addItem(tr('Extensão dos pontos + margem'),'points')
        self.extent_mode.addItem(tr('Grade de raster de referência'),'reference')
        self.extent_mode.currentIndexChanged.connect(self._update_extent)
        form.addRow(tr('Extensão da análise:'),self.extent_mode)
        self.extent_label = form.labelForField(self.extent_mode)
        self.area_layer=QgsMapLayerComboBox()
        self.area_layer.setAllowEmptyLayer(True)
        self.area_layer.setFilters(Qgis.LayerFilter.VectorLayer)
        self.area_label=QLabel(tr('Área poligonal:'))
        form.addRow(self.area_label,self.area_layer)
        self.manual_bounds=[]
        for label in ('X mínimo:','Y mínimo:','X máximo:','Y máximo:'):
            widget=QDoubleSpinBox()
            widget.setDecimals(6)
            widget.setRange(-1.0e12,1.0e12)
            widget.setSingleStep(100.)
            self.manual_bounds.append(widget)
            form.addRow(label,widget)
        self.manual_labels=[form.labelForField(widget) for widget in self.manual_bounds]

        self.resolution = QDoubleSpinBox()
        self.resolution.setDecimals(4)
        self.resolution.setRange(.0001, 100_000_000.)
        self.resolution.setValue(100.)
        self.resolution.setSuffix(tr(' unidades do SRC'))
        self.resolution_label=QLabel(tr('Resolução raster:'))
        form.addRow(self.resolution_label,self.resolution)
        self.grid_note = _WrapLabel(tr('O Voronoi vetorial direto é limitado pela extensão escolhida; '
                                'não exige raster de referência nem resolução.'))
        self.grid_note.setWordWrap(True)
        form.addRow('',self.grid_note)
        content_layout.addWidget(inputs)

        self._shared = [self.intro, options, inputs]
        self._shared_page = 0
        # "Salvar em": em branco, resultado temporário (raster em arquivo
        # temporário; vetor em camada temporária em memória); preenchido, salvo.
        # Nos dois casos o resultado é carregado no QGIS.
        self.output_edits = []
        for idx in (0, 1):
            group = QGroupBox(tr('Resultado'))
            out = QFormLayout(group)
            edit = QLineEdit()
            edit.setPlaceholderText(tr('[Arquivo temporário]' if idx == 0
                                       else '[Camada temporária em memória]'))
            edit.setClearButtonEnabled(True)
            row = QHBoxLayout()
            row.addWidget(edit, 1)
            browse = QPushButton(tr('Salvar como…'))
            browse.clicked.connect(lambda checked=False, i=idx: self._choose_output(i))
            row.addWidget(browse)
            out.addRow(tr('Salvar em:'), row)
            note = _WrapLabel(tr(RASTER_RESULT_HINT if idx == 0 else VECTOR_RESULT_HINT))
            out.addRow('', note)
            self._pages[idx].addWidget(group)
            self._pages[idx].addStretch(1)
            self.output_edits.append(edit)
        self.tabs.currentChanged.connect(self._tab_changed)
        control = QHBoxLayout()
        self.status = QLabel(tr('Selecione a camada de pontos geradores.'))
        self.status.setWordWrap(True)
        control.addWidget(self.status, 1)
        self.run_button = QPushButton(tr('Gerar Voronoi'))
        self.run_button.clicked.connect(self._run)
        control.addWidget(self.run_button)
        self.close_button = QPushButton(tr('Fechar'))
        self.close_button.clicked.connect(self.close)
        control.addWidget(self.close_button)
        layout.addLayout(control)
        self._temporary = True
        self._refresh_fields()
        # A camada de polígonos pode já vir selecionada (sem sinal de troca): preenche as colunas.
        self._refresh_friction_fields()
        self._update_mode()
        self._update_extent()
        self._update_output()

    def _tab_changed(self, index):
        """Leva modelo e dados de entrada para a guia ativa, preservando o preenchimento."""
        if index not in (0, 1) or index == self._shared_page:
            return
        for widget in self._shared:
            self._pages[self._shared_page].removeWidget(widget)
        for position, widget in enumerate(self._shared):
            self._pages[index].insertWidget(position, widget)
        self._shared_page = index
        self._update_mode()

    def _kind(self):
        return 'raster' if self.tabs.currentIndex() == 0 else 'vector'

    def _on_multi_friction_toggled(self, checked):
        self._update_mode()
        # Abrir a seleção imediatamente no primeiro uso evita que a pessoa
        # precise procurar controles ocultos ao habilitar a opção.
        if checked and self.mode.currentIndex() in (2, 3) and not self.friction_stack_table.rowCount():
            self._manage_friction_layers()

    def _manage_friction_layers(self):
        if self._busy:
            return
        self.friction_stack_dialog.exec()
        self._update_friction_summary()

    def _update_friction_summary(self):
        count = self.friction_stack_table.rowCount()
        if not count:
            message = 'Nenhuma superfície selecionada. Clique em “Selecionar e configurar superfícies…”.'
        else:
            message = f'{count} superfície(s) selecionada(s). Clique para editar pesos e notas.'
        self.friction_stack_summary.setText(message)

    def _add_friction_layers(self):
        layers = [layer for layer in QgsProject.instance().mapLayers().values()
                  if isinstance(layer, QgsRasterLayer) and layer.isValid()]
        if not layers:
            QMessageBox.warning(self, tr('Superfícies de atrito'), tr('Não há camadas raster carregadas no QGIS.'))
            return
        chooser = QDialog(self)
        chooser.setWindowTitle(tr('Adicionar superfícies de atrito'))
        chooser.resize(430, 340)
        layout = QVBoxLayout(chooser)
        list_widget = QListWidget()
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for layer in sorted(layers, key=lambda lyr: lyr.name().lower()):
            item = QListWidgetItem(layer.name())
            item.setData(Qt.ItemDataRole.UserRole, layer.id())
            list_widget.addItem(item)
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(chooser.accept)
        buttons.rejected.connect(chooser.reject)
        layout.addWidget(buttons)
        if chooser.exec() != QDialog.DialogCode.Accepted:
            return
        for item in list_widget.selectedItems():
            layer_id = item.data(Qt.ItemDataRole.UserRole)
            layer = QgsProject.instance().mapLayer(layer_id)
            if layer is None:
                continue
            if not self._append_friction_layer(layer):
                break
        self._update_friction_summary()

    def _add_friction_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self.friction_stack_dialog, tr('Selecionar GeoTIFFs de atrito'), '',
            tr('GeoTIFF (*.tif *.tiff);;Todos os arquivos (*.*)'))
        if not files:
            return
        from .raster_engine import file_source
        import os
        project = QgsProject.instance()
        loaded_by_source = {
            os.path.normcase(os.path.abspath(file_source(layer.source()))): layer
            for layer in project.mapLayers().values()
            if isinstance(layer, QgsRasterLayer) and layer.isValid()
        }
        for path in files:
            normpath = os.path.normcase(os.path.abspath(path))
            layer = loaded_by_source.get(normpath)
            new_layer = layer is None
            if new_layer:
                layer = QgsRasterLayer(path, Path(path).stem, 'gdal')
                if not layer.isValid():
                    QMessageBox.warning(self, tr('Superfícies de atrito'),
                                        tr(f'O raster não pôde ser aberto: {path}'))
                    continue
            if not self._append_friction_layer(layer):
                break
            if new_layer:
                project.addMapLayer(layer)
                loaded_by_source[normpath] = layer
        self._update_friction_summary()

    def _append_friction_layer(self, layer):
        ids = {self.friction_stack_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
               for row in range(self.friction_stack_table.rowCount())}
        if layer.id() in ids:
            return True  # Já presente: não duplicar.
        if self.friction_stack_table.rowCount() >= 12:
            QMessageBox.warning(self, tr('Superfícies de atrito'), tr('Limite de 12 superfícies por análise.'))
            return False
        row = self.friction_stack_table.rowCount()
        self.friction_stack_table.insertRow(row)
        name = QTableWidgetItem(layer.name())
        name.setData(Qt.ItemDataRole.UserRole, layer.id())
        name.setFlags(name.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.friction_stack_table.setItem(row, 0, name)
        self.friction_stack_table.setItem(row, 1, QTableWidgetItem('1'))
        self.friction_stack_table.setItem(row, 2, QTableWidgetItem(''))
        self._update_friction_summary()
        return True

    def _remove_friction_layers(self):
        rows = sorted({index.row() for index in self.friction_stack_table.selectedIndexes()},
                      reverse=True)
        for row in rows:
            self.friction_stack_table.removeRow(row)
        self._update_friction_summary()

    def _friction_components_from_ui(self):
        from .raster_engine import file_source
        from .voronoi_friction_stack import parse_class_notes
        comps = []
        for row in range(self.friction_stack_table.rowCount()):
            item = self.friction_stack_table.item(row, 0)
            layer = QgsProject.instance().mapLayer(item.data(Qt.ItemDataRole.UserRole)) if item else None
            if layer is None or not layer.isValid():
                raise ValueError('Uma superfície foi removida do projeto; atualize a lista.')
            try:
                weight = float(self.friction_stack_table.item(row, 1).text().replace(',', '.'))
            except (ValueError, AttributeError):
                raise ValueError(f'Peso inválido na linha {row+1}.') from None
            if not isfinite(weight) or weight <= 0:
                raise ValueError(f'Informe peso positivo para a camada {layer.name()}.')
            notes_item = self.friction_stack_table.item(row, 2)
            notes = notes_item.text().strip() if notes_item else ''
            parse_class_notes(notes)
            comps.append({'path': file_source(layer.source()), 'weight': weight, 'notes': notes,
                          'layer_id': layer.id()})
        if not comps:
            raise ValueError('Adicione ao menos uma superfície de atrito à lista.')
        if len(comps) > 12:
            raise ValueError('Limite de 12 superfícies de atrito.')
        return comps

    # ------------------------------------------------------ atrito vetorial (1.4.0)
    def _vector_friction(self):
        """Atrito por polígonos: sempre na guia Vetorial (vetor direto, modelo contínuo); na guia
        Raster, quando escolhido em "Tipo de superfície" (polígonos convertidos em notas na grade)."""
        return self.mode.currentIndex() in (2, 3) and (
            self._kind() == 'vector' or self.friction_kind.currentData() == 'vector')

    def _refresh_friction_fields(self, *_):
        layer = self.friction_vector_layer.currentLayer()
        previous = self.friction_rating_field.currentData()
        self.friction_rating_field.clear()
        if isinstance(layer, QgsVectorLayer):
            for field in layer.fields():
                if field.isNumeric():
                    self.friction_rating_field.addItem(field.name(), field.name())
            index = self.friction_rating_field.findData(previous) if previous else -1
            if index < 0:
                names = [self.friction_rating_field.itemData(i) for i in range(self.friction_rating_field.count())]
                index = next((self.friction_rating_field.findData(name) for name in names
                              if str(name).upper() in ('ATRITO', 'NOTA', 'FRICTION', 'CUSTO')), -1)
            if index >= 0:
                self.friction_rating_field.setCurrentIndex(index)

    def _friction_vector_spec(self, crs):
        """Extrai WKB e nota (coluna de atrito) das feições, na thread principal; sem reprojeção.

        Área sem polígono e feições com a coluna vazia são barreira (decisão da 1.4.0).
        """
        from .voronoi_friction_vector import BARRIER, ratings_from_column
        layer = self.friction_vector_layer.currentLayer()
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            raise ValueError('Selecione a camada de polígonos de atrito.')
        if layer.crs() != crs:
            raise ValueError('Os polígonos de atrito precisam estar no SRC da análise ({0}); '
                             'reprojete a camada antes.'.format(crs.authid() or crs.description()))
        name = self.friction_rating_field.currentData()
        if not name:
            raise ValueError('Escolha a coluna de atrito.')
        geometries, values = [], []
        for feature in layer.getFeatures():
            geometry = feature.geometry()
            if geometry is None or geometry.isNull() or geometry.isEmpty():
                continue
            value = feature[name]
            geometries.append(bytes(geometry.asWkb()))
            values.append(None if _is_null(value) else value)
        if not geometries:
            raise ValueError('A camada de atrito não tem polígonos.')
        ratings = ratings_from_column(values)
        if all(rating is None for rating in ratings):
            raise ValueError('A coluna de atrito está vazia em todas as feições.')
        return {'features': list(zip(geometries, ratings)), 'outside': BARRIER,
                'layer_name': layer.name(), 'rating_field': name,
                'skipped': sum(1 for v in values if v is None), 'source': layer.source()}

    def _refresh_fields(self, *_):
        layer = self.point_layer.currentLayer()
        self.label_field.clear()
        self.label_field.addItem(tr('(usar ID da feição)'),None)
        self.mass_field.clear()
        if layer is None: return
        names = layer.fields().names()
        for name in names:
            self.label_field.addItem(name,name)
            self.mass_field.addItem(name,name)
        for target in ('NOME','NOME_CENTRO','NOME_UNID','NAME','IDENTIFICACAO'):
            for name in names:
                if name.upper() == target:
                    self.label_field.setCurrentIndex(self.label_field.findData(name))
                    break
        for target in ('MASSA','CAPACIDADE','LEITOS','VAGAS','MASS'):
            for name in names:
                if name.upper() == target:
                    self.mass_field.setCurrentIndex(self.mass_field.findData(name))
                    return

    def _update_mode(self, *_):
        weighted = self.mode.currentIndex() in (1,3)
        friction = self.mode.currentIndex() in (2,3)
        self.mass_field.setVisible(weighted)
        self.mass_label.setVisible(weighted)
        self.mass_field.setEnabled(weighted)
        vector_friction = self._vector_friction()
        raster_friction = friction and not vector_friction
        multi = raster_friction and self.multi_friction.isChecked()
        # Na guia Vetorial, o atrito é sempre vetorial (modelo contínuo): sem "Tipo de superfície".
        self.friction_kind.setVisible(friction and self._kind() == 'raster')
        self.friction_kind_label.setVisible(friction and self._kind() == 'raster')
        self.friction_layer.setVisible(raster_friction and not multi)
        self.friction_label.setVisible(raster_friction and not multi)
        self.multi_friction.setVisible(raster_friction)
        self.friction_stack_group.setVisible(multi)
        for widget in (self.friction_vector_layer, self.friction_vector_label,
                       self.friction_rating_field, self.friction_rating_label):
            widget.setVisible(vector_friction)
        # Atrito raster: a grade é a do próprio raster. Atrito vetorial: extensão e resolução da análise.
        self.extent_mode.setVisible(not raster_friction)
        self.extent_label.setVisible(not raster_friction)
        self._update_extent()
        if friction:
            if weighted:
                self.method_note.setText(tr('Com Massa e Atrito (modelo do Vista SAGA): menor custo acumulado '
                                            '(distância ao polo × nota × passo, na reta polo-célula) dividido '
                                            'pela massa, o que equivale a M/d²; NoData é barreira.'))
            else:
                self.method_note.setText(tr('Com Atrito (modelo do Vista SAGA): menor custo acumulado '
                                            '(distância ao polo × nota × passo, na reta polo-célula); '
                                            'NoData é barreira.'))
        elif weighted:
            self.method_note.setText(tr('Com Massa: maximiza M/d², como no Vista SAGA; selecione campo numérico positivo.'))
        else:
            self.method_note.setText(tr('Simples: menor distância euclidiana; sem massa nem atrito.'))
        self._update_output()

    def _update_grid(self, *_):
        self._update_output()

    def _update_extent(self, *_):
        choice=self.extent_mode.currentData()
        own_grid=self.mode.currentIndex() not in (2,3) or self._vector_friction()
        use_polygon=choice=='polygon' and own_grid
        self.area_layer.setVisible(use_polygon)
        self.area_label.setVisible(use_polygon)
        manual=choice=='manual' and own_grid
        for widget,label in zip(self.manual_bounds,self.manual_labels):
            widget.setVisible(manual)
            label.setVisible(manual)
        self._update_output()

    def _output_suffix(self):
        """Extensão da saída da guia ativa (vetor temporário: GeoPackage)."""
        if self._kind() == 'raster':
            return '.tif'
        chosen = self.output_edits[1].text().strip()
        extension = os.path.splitext(chosen)[1].lower()
        return extension if extension in VECTOR_FORMATS else '.gpkg'

    def _update_output(self, *_):
        if not hasattr(self, 'output_edits'):
            return  # ainda montando a janela
        vector = self._kind() == 'vector'
        friction = self.mode.currentIndex() in (2,3)
        vector_friction = self._vector_friction()
        raster_friction = friction and not vector_friction
        reference = self.extent_mode.currentData() == 'reference'
        # Resolução só na guia Raster (grade da análise). Na guia Vetorial com atrito, o espaçamento da
        # busca é automático desde a 1.4.0 (decisão do autor): o campo não aparece.
        gridded = not vector and not raster_friction
        self.grid_layer.setVisible(gridded and reference and not vector)
        self.grid_label.setVisible(gridded and reference and not vector)
        self.resolution.setVisible(gridded and not reference)
        self.resolution_label.setVisible(gridded and not reference)
        self.resolution.setEnabled(gridded and not reference)
        self.extent_mode.model().item(4).setEnabled(not vector)
        if vector and reference:
            self.extent_mode.setCurrentIndex(0)
        if vector and vector_friction:
            note = ('Vetor direto com atrito (modelo contínuo): fronteiras traçadas sem grade, com tolerância '
                    'de 0,5 m e conferência automática; o detalhamento da busca é escolhido pelos dados e '
                    'informado no resumo. Área sem polígono e coluna vazia: barreira.')
        elif vector_friction:
            note = ('Atrito vetorial: os polígonos são convertidos em notas na grade da análise (extensão e '
                    'resolução escolhidas), pelo centro de cada célula; área sem polígono e coluna vazia: '
                    'barreira. O resultado segue essa grade.')
        elif friction:
            note = ('Com Atrito: extensão, resolução e SRC herdados do raster de atrito; '
                    'a grade não será reprojetada.')
        elif vector and self.mode.currentIndex() == 1:
            note = ('Vetor direto com massa: fronteiras exatas (círculos de Apolônio), arcos com '
                    'desvio máximo de 1 cm, recortadas à extensão e à área poligonal.')
        elif vector:
            note = 'Vetor direto: polígonos exatos recortados à extensão e à área poligonal.'
        else:
            note = 'Raster: resolução necessária. A extensão poligonal define o retângulo envolvente.'
        self.grid_note.setText(tr(note))

    def _choose_output(self, index):
        """"Salvar como…": formato pelo filtro do diálogo, como no QGIS."""
        edit = self.output_edits[index]
        if index == 0:
            filters = ['GeoTIFF (*.tif *.tiff)']
            default = '.tif'
        else:
            filters = [f'{label} (*{extension})' for extension, (_, label) in VECTOR_FORMATS.items()]
            default = self._output_suffix() if edit.text().strip() else '.gpkg'
        current = edit.text().strip() or 'Analises_Voronoi' + default
        selected = next((item for item in filters if default in item), filters[0])
        path, chosen_filter = QFileDialog.getSaveFileName(
            self, tr('Salvar Voronoi'), current, ';;'.join(filters), selected)
        if not path:
            return
        extension = os.path.splitext(path)[1].lower()
        allowed = ('.tif', '.tiff') if index == 0 else tuple(VECTOR_FORMATS)
        if extension not in allowed:
            match = next((ext for ext in allowed if f'*{ext}' in (chosen_filter or '')), allowed[0])
            path += match
        edit.setText(path)

    def _get_generators(self, target_crs):
        layer = self.point_layer.currentLayer()
        if layer is None or not layer.isValid() or not isinstance(layer,QgsVectorLayer):
            raise ValueError('Selecione uma camada vetorial válida com pontos.')
        if QgsWkbTypes.geometryType(layer.wkbType()) != QgsWkbTypes.GeometryType.PointGeometry:
            raise ValueError('O Voronoi necessita de uma camada de pontos; geometrias não pontuais não são aceitas.')
        if not layer.crs().isValid() or not target_crs.isValid():
            raise ValueError('A camada de pontos e a grade precisam ter SRC definido.')
        transform = None
        if layer.crs() != target_crs:
            transform = QgsCoordinateTransform(layer.crs(),target_crs,QgsProject.instance())
        mass_name = self.mass_field.currentData() if self.mode.currentIndex() in (1,3) else None
        if self.mode.currentIndex() in (1,3) and not mass_name:
            raise ValueError('Selecione o campo numérico da massa.')
        label_name = self.label_field.currentData()
        points = []
        for feature in layer.getFeatures():
            geom = feature.geometry()
            if geom.isNull() or geom.isEmpty():
                continue
            if transform is not None:
                geom = type(geom)(geom)
                geom.transform(transform)
            locations = geom.asMultiPoint() if geom.isMultipart() else [geom.asPoint()]
            for part_index, position in enumerate(locations):
                value = feature[mass_name] if mass_name else 1.0
                if value is None:
                    raise ValueError(f'Massa ausente na feição {feature.id()}.')
                try: mass = float(value)
                except (TypeError, ValueError):
                    raise ValueError(f'Massa não numérica na feição {feature.id()}.') from None
                # Campos de nome opcionais; feições multipartes recebem IDs próprios.
                try: name = str(feature[label_name]) if label_name else f'Feição {feature.id()}'
                except (KeyError, TypeError): name = f'Feição {feature.id()}'
                if len(locations) > 1: name += f' - parte {part_index+1}'
                points.append(Generator(len(points)+1,float(position.x()),float(position.y()),mass,name))
        return points

    def _analysis_extent(self, target_crs, points):
        from qgis.core import QgsCoordinateTransform
        choice=self.extent_mode.currentData()
        study=None
        if choice=='points':
            return None,None
        if choice=='manual':
            bounds=tuple(spin.value() for spin in self.manual_bounds)
        elif choice=='canvas':
            canvas=self.iface.mapCanvas()
            rect=canvas.extent()
            source=canvas.mapSettings().destinationCrs()
            if not source.isValid():
                raise ValueError('O SRC do mapa do QGIS não está definido.')
            if source != target_crs:
                rect=QgsCoordinateTransform(source,target_crs,QgsProject.instance()).transformBoundingBox(rect)
            bounds=(rect.xMinimum(),rect.yMinimum(),rect.xMaximum(),rect.yMaximum())
        elif choice=='polygon':
            layer=self.area_layer.currentLayer()
            if layer is None or not layer.isValid() or not isinstance(layer,QgsVectorLayer):
                raise ValueError('Selecione a camada de polígonos que define a área de estudo.')
            if QgsWkbTypes.geometryType(layer.wkbType())!=QgsWkbTypes.GeometryType.PolygonGeometry:
                raise ValueError('A área de estudo deve ser poligonal.')
            if not layer.crs().isValid():
                raise ValueError('Defina o SRC da área de estudo.')
            transform=(QgsCoordinateTransform(layer.crs(),target_crs,QgsProject.instance())
                       if layer.crs()!=target_crs else None)
            geoms=[]
            for feature in layer.getFeatures():
                geom=QgsGeometry(feature.geometry())
                if geom.isNull() or geom.isEmpty(): continue
                if transform is not None: geom.transform(transform)
                if not geom.isGeosValid():
                    raise ValueError('A área de estudo possui geometrias inválidas; corrija-as antes de prosseguir.')
                geoms.append(geom)
            if not geoms:
                raise ValueError('A camada de estudo não contém polígonos válidos.')
            study=QgsGeometry.unaryUnion(geoms)
            if study.isNull() or study.isEmpty() or not study.isGeosValid():
                raise ValueError('A geometria unificada da área de estudo é inválida.')
            rect=study.boundingBox()
            bounds=(rect.xMinimum(),rect.yMinimum(),rect.xMaximum(),rect.yMaximum())
        else:
            raise ValueError('Escolha uma extensão válida para a análise.')
        if bounds[0]>=bounds[2] or bounds[1]>=bounds[3]:
            raise ValueError('Extensão inválida: os máximos precisam superar os mínimos.')
        return bounds,study

    def _get_grid(self, point_layer, points, crs=None):
        """Grade da análise; ``crs`` substitui o SRC dos pontos (atrito vetorial: o da camada)."""
        reference=self.grid_layer.currentLayer()
        if self.extent_mode.currentData()=='reference':
            if reference is None:
                raise ValueError('Escolha um raster de referência ou altere a extensão.')
            from osgeo import gdal
            from .raster_engine import file_source
            path=file_source(reference.source())
            dataset=gdal.Open(path,gdal.GA_ReadOnly)
            if dataset is None:
                raise ValueError('Raster de referência inválido; escolha um GeoTIFF acessível.')
            data=(dataset.GetGeoTransform(),dataset.RasterXSize,dataset.RasterYSize,
                  reference.crs(),dataset.GetProjectionRef())
            dataset=None
            return data
        crs=crs if crs is not None else point_layer.crs()
        if not crs.isValid():
            raise ValueError('Defina o SRC dos pontos antes do processamento.')
        bounds,study=self._analysis_extent(crs,points)
        if bounds is None:
            bounds=(min(p.x for p in points),min(p.y for p in points),
                    max(p.x for p in points),max(p.y for p in points))
            t,width,height=grid_from_extent(bounds,self.resolution.value())
        else:
            from .voronoi_engine import grid_from_bbox
            t,width,height=grid_from_bbox(bounds,self.resolution.value())
        return t,width,height,crs,crs.toWkt()

    @pyqtSlot(float)
    def _on_raster_task_progress(self, percent):
        """Atualiza QProgressDialog no thread da interface; QgsTask emite float.

        QProgressDialog.setValue exige int no Qt6. Sinais pendentes após
        cancelamento/fechamento da tarefa são ignorados.
        """
        if self._task is None or self._progress_dialog is None:
            return
        if not isfinite(percent):
            return
        value = max(0, min(100, int(round(percent))))
        self._progress_dialog.setValue(value)

    def _run(self):
        if self._busy: return
        layer=self.point_layer.currentLayer()
        if layer is None:
            QMessageBox.warning(self,tr('Análises Voronoi'),tr('Selecione uma camada de pontos.'))
            return
        kind=self._kind()
        chosen=self.output_edits[self.tabs.currentIndex()].text().strip()
        if chosen:
            stem=os.path.splitext(chosen)[0]
            existing=[path for path in output_family(chosen)+[stem+'_centros.csv',stem+'_resumo.txt']
                      if os.path.exists(path)]
            if existing and QMessageBox.question(
                    self,tr('Substituir arquivos?'),
                    tr('Há resultados existentes. Substituir mapa e relatórios associados?'),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
        self._temporary=not chosen
        self._busy=True
        self.run_button.setEnabled(False)
        self.close_button.setEnabled(False)
        dialog=QProgressDialog(tr('Calculando áreas de influência…'),tr('Cancelar'),0,100,self)
        dialog.setWindowModality(Qt.WindowModality.NonModal)
        dialog.setMinimumDuration(0)
        dialog.setAutoClose(False)
        dialog.setValue(0)
        asynchronous = False
        try:
            # Vetorial: exato (sem grade) no Simples e Com Massa; com atrito, na grade do atrito.
            # Guia Vetorial: vetor direto nas quatro modalidades (com atrito, modelo contínuo).
            direct=kind=='vector'
            friction_spec=None
            if direct:
                if self.mode.currentIndex() in (2,3):
                    friction_layer=self.friction_vector_layer.currentLayer()
                    if not isinstance(friction_layer,QgsVectorLayer) or not friction_layer.isValid():
                        raise ValueError('Selecione a camada de polígonos de atrito.')
                    crs=friction_layer.crs()
                    if not crs.isValid() or crs.isGeographic():
                        raise ValueError('Os polígonos de atrito exigem SRC projetado.')
                else:
                    crs=layer.crs()
                    if not crs.isValid() or crs.isGeographic():
                        raise ValueError('Reprojete os pontos para um SRC projetado antes da análise.')
                points=self._get_generators(crs)
                if self.mode.currentIndex() in (2,3):
                    friction_spec=self._friction_vector_spec(crs)
                bounds,study=self._analysis_extent(crs,points)
                if bounds is None:
                    bounds=(min(p.x for p in points),min(p.y for p in points),
                            max(p.x for p in points),max(p.y for p in points))
                    margin=max(1.0,.10*max(bounds[2]-bounds[0],bounds[3]-bounds[1]))
                    bounds=(bounds[0]-margin,bounds[1]-margin,bounds[2]+margin,bounds[3]+margin)
            else:
                friction_mode = self.mode.currentIndex() in (2,3)
                friction_path = None
                friction_components = None
                friction_vector = None
                reference = None
                if friction_mode and self._vector_friction():
                    friction_vector_layer = self.friction_vector_layer.currentLayer()
                    if not isinstance(friction_vector_layer, QgsVectorLayer) or not friction_vector_layer.isValid():
                        raise ValueError('Selecione a camada de polígonos de atrito.')
                    crs = friction_vector_layer.crs()
                    if not crs.isValid() or crs.isGeographic():
                        raise ValueError('Os polígonos de atrito exigem SRC projetado.')
                    points = self._get_generators(crs)
                    if self.extent_mode.currentData() == 'reference':
                        reference = self.grid_layer.currentLayer()
                    transform, width, height, grid_crs, wkt = self._get_grid(layer, points, crs=crs)
                    if grid_crs != crs:
                        raise ValueError('O raster de referência precisa estar no SRC dos polígonos de atrito.')
                    wkt = crs.toWkt()
                    friction_vector = self._friction_vector_spec(crs)
                elif friction_mode:
                    if self.multi_friction.isChecked():
                        friction_components = self._friction_components_from_ui()
                        first_id = friction_components[0]['layer_id']
                        friction_layer = QgsProject.instance().mapLayer(first_id)
                    else:
                        friction_layer = self.friction_layer.currentLayer()
                    if friction_layer is None or not friction_layer.isValid():
                        raise ValueError('Selecione uma superfície raster de atrito.')
                    from osgeo import gdal
                    from .raster_engine import file_source
                    friction_path = file_source(friction_layer.source())
                    source = gdal.Open(friction_path, gdal.GA_ReadOnly)
                    if source is None or source.RasterCount != 1:
                        raise ValueError('O atrito deve ser um GeoTIFF monobanda acessível no disco.')
                    crs = friction_layer.crs()
                    if not crs.isValid() or crs.isGeographic():
                        raise ValueError('O raster de atrito exige SRC projetado.')
                    points = self._get_generators(crs)
                    transform = source.GetGeoTransform()
                    width, height = source.RasterXSize, source.RasterYSize
                    wkt = source.GetProjectionRef()
                    source = None
                else:
                    reference=self.grid_layer.currentLayer() if self.extent_mode.currentData()=='reference' else None
                    crs=reference.crs() if reference is not None else layer.crs()
                    if not crs.isValid() or crs.isGeographic():
                        raise ValueError('A análise exige SRC projetado. Reprojete os dados.')
                    points=self._get_generators(crs)
                    transform,width,height,crs,wkt=self._get_grid(layer,points)
            if kind=='raster':
                suffix='.tif'
                if chosen and not chosen.lower().endswith(('.tif','.tiff')):
                    raise ValueError('Escolha um arquivo de saída {0}.'.format('.tif'))
            else:
                suffix=vector_extension(chosen) if chosen else '.gpkg'
            destination=chosen or temporary_destination('voronoi_espacial',suffix)
            prefix=os.path.splitext(destination)[0]
            # Vetorial com atrito: o GeoTIFF de cálculo usa o mesmo nome-base e é descartado.
            raster_destination=None if direct else (prefix+'.tif' if kind=='vector' else destination)
            vector_destination=destination if kind=='vector' else None
            outputs=[vector_destination or raster_destination]
            def same_file(first, second):
                return os.path.normcase(os.path.realpath(first))==os.path.normcase(os.path.realpath(second))
            forbidden=[layer.source().split('|')[0]]
            if self._vector_friction() and self.friction_vector_layer.currentLayer() is not None:
                forbidden.append(self.friction_vector_layer.currentLayer().source().split('|')[0])
            if self.extent_mode.currentData()=='polygon' and (self.mode.currentIndex() not in (2,3)
                                                              or self._vector_friction()):
                study_layer=self.area_layer.currentLayer()
                if study_layer is not None:
                    forbidden.append(study_layer.source().split('|')[0])
            for source in forbidden:
                if source and os.path.isfile(source) and any(same_file(source,path) for path in outputs):
                    raise ValueError('A saída não pode substituir uma camada de entrada.')
            def progress(value):
                dialog.setValue(int(value))
                QApplication.processEvents()
            if direct and friction_spec:
                # Com atrito, o vetor direto pode levar minutos: tarefa em segundo plano, com progresso.
                task = VoronoiVectorTask(points, bounds, destination, crs.toWkt(),
                                         'mass_friction' if self.mode.currentIndex()==3 else 'friction',
                                         study, friction_spec)
                task.ui_callback = self._on_raster_task_finished
                task.progressChanged.connect(self._on_raster_task_progress)
                dialog.canceled.connect(task.cancel)
                self._task = task
                self._progress_dialog = dialog
                try:
                    QgsApplication.taskManager().addTask(task)
                except Exception:
                    self._task = None
                    self._progress_dialog = None
                    task.ui_callback = None
                    raise
                asynchronous = True
                return
            if direct:
                result=save_vector_voronoi(points,bounds,destination,crs.toWkt(),
                    mode='mass' if self.mode.currentIndex()==1 else 'simple',
                    study_geometry=study,progress=progress,cancelled=dialog.wasCanceled)
            else:
                if reference is not None:
                    from .raster_engine import file_source
                    input_path=file_source(reference.source())
                    if any(same_file(input_path,path) for path in outputs):
                        raise ValueError('O resultado não pode substituir o raster de referência.')
                task = VoronoiRasterTask(
                    points, raster_destination, wkt, transform, width, height,
                    mode=('mass_friction' if self.mode.currentIndex()==3 else
                          'friction' if self.mode.currentIndex()==2 else
                          'mass' if self.mode.currentIndex()==1 else 'simple'),
                    vectorize=kind=='vector',
                    friction_path=friction_path if friction_mode and not friction_vector else None,
                    friction_components=friction_components if friction_mode else None,
                    friction_vector=friction_vector if friction_mode else None,
                    vector_format=suffix if kind=='vector' else '.gpkg',
                    keep_raster=kind=='raster')
                # Recebe o resultado na thread principal; NUNCA processEvents()
                # nem acesso ao QGIS/Qt no worker raster.
                task.ui_callback = self._on_raster_task_finished
                task.progressChanged.connect(self._on_raster_task_progress)
                dialog.canceled.connect(task.cancel)
                self._task = task
                self._progress_dialog = dialog
                try:
                    QgsApplication.taskManager().addTask(task)
                except Exception:
                    self._task = None
                    self._progress_dialog = None
                    task.ui_callback = None
                    raise
                asynchronous = True
                return
            self._load_output(result)
            if direct:
                self.status.setText(tr('Voronoi vetorial concluído: {count} regiões.').format(count=len(result["rows"])))
            else:
                self.status.setText(tr(f'Voronoi concluído: {len(points)} centros; '
                                    f'{result["pixels_valid"]:,} pixels classificados.'))
            QMessageBox.information(self,tr('Voronoi concluído'),self._result_message(result))
        except InterruptedError:
            self.status.setText(tr('Processamento cancelado; os dados de entrada foram preservados.'))
        except Exception as exc:
            log_exception()
            self.status.setText(tr('Falha na execução; revise os parâmetros.'))
            QMessageBox.critical(self,tr('Voronoi não concluído'),tr(str(exc)))
        finally:
            if not asynchronous:
                dialog.close()
                self._busy=False
                self.run_button.setEnabled(True)
                self.close_button.setEnabled(True)

    def _result_message(self, result):
        """Resumo das saídas produzidas (GeoTIFF e/ou camada vetorial, CSV e TXT)."""
        vector=result.get('vector') or result.get('gpkg')
        label=VECTOR_FORMATS[os.path.splitext(vector)[1].lower()][1] if vector else ''
        if result.get('output') and vector:
            text=tr('GeoTIFF, camada vetorial ({0}), CSV e TXT produzidos.').format(label)
        elif vector:
            text=tr('Camada vetorial ({0}), CSV e TXT produzidos.').format(label)
        else:
            text=tr('GeoTIFF, CSV e TXT produzidos.')
        if self._temporary:
            return text+'\n'+tr('Saída temporária: salve antes de fechar o QGIS.')
        return text+'\n'+tr('Resultado: {0}').format(result.get('output') or vector)

    def _on_raster_task_finished(self, task, success):
        """QgsTask.finished chama este método na thread principal do QGIS."""
        if self._task is not task:
            return
        dialog = self._progress_dialog
        self._task = None
        self._progress_dialog = None
        if dialog is not None:
            dialog.close()
            dialog.deleteLater()
        self._busy = False
        self.run_button.setEnabled(True)
        self.close_button.setEnabled(True)
        if success and task.result:
            try:
                self._load_output(task.result)
                if task.result.get('vector_direct'):
                    self.status.setText(tr('Voronoi vetorial concluído: {count} regiões.').format(
                        count=len(task.result['rows'])))
                else:
                    self.status.setText(
                        tr(f'Voronoi concluído: {len(task.points)} centros; '
                        f'{task.result["pixels_valid"]:,} pixels classificados.'))
                QMessageBox.information(self,tr('Voronoi concluído'),self._result_message(task.result))
            except Exception as exc:
                log_exception()
                self.status.setText(tr('Resultado criado, mas não foi possível carregar no QGIS.'))
                QMessageBox.warning(self, tr('Voronoi - carregar resultado'), tr(str(exc)))
        elif task.error:
            self.status.setText(tr('Falha na execução; revise os parâmetros.'))
            QMessageBox.critical(self, tr('Voronoi não concluído'), tr(task.error))
        else:
            self.status.setText(tr('Processamento cancelado; dados de entrada preservados.'))

    def shutdown(self):
        """Impede callback em janelas descartadas ao descarregar o plugin."""
        if self._task is not None:
            self._task.ui_callback = None
            self._task.cancel()
            self._task = None
        if self._progress_dialog is not None:
            self._progress_dialog.close()
            self._progress_dialog = None

    def closeEvent(self, event):
        if self._busy:
            event.ignore()
            return
        super().closeEvent(event)

    def _load_output(self,result):
        import colorsys
        raster = (QgsRasterLayer(result['output'],'Análises Voronoi','gdal')
                  if result.get('output') else None)
        if raster is not None and raster.isValid():
            if len(result['rows']) <= 75:
                categories = []
                for r in result['rows']:
                    rgb = colorsys.hsv_to_rgb((r['ID']*.61803398875)%1,.5,.85)
                    c = QColor(*[int(v*255) for v in rgb])
                    categories.append(QgsPalettedRasterRenderer.Class(r['ID'],c,r['CENTRO'][:120]))
                raster.setRenderer(QgsPalettedRasterRenderer(raster.dataProvider(),1,categories))
            QgsProject.instance().addMapLayer(raster)
        vector_path = result.get('vector') or result.get('gpkg')
        if vector_path:
            # Padrão do plugin: sem arquivo indicado, camada temporária em memória.
            vector = (materialize_in_memory(layer_uri(vector_path), 'Análises Voronoi')
                      if self._temporary else
                      QgsVectorLayer(layer_uri(vector_path), 'Análises Voronoi', 'ogr'))
            if vector is None:
                raise RuntimeError('Não foi possível carregar o resultado no QGIS.')
            if vector.isValid():
                if len(result['rows']) <= 75:
                    cats = []
                    for r in result['rows']:
                        rgb = colorsys.hsv_to_rgb((r['ID']*.61803398875)%1,.5,.85)
                        color = '#'+''.join(f'{int(v*255):02X}' for v in rgb)
                        symbol = QgsFillSymbol.createSimple({'color':color,'outline_width':'0.12'})
                        cats.append(QgsRendererCategory(r['ID'],symbol,r['CENTRO'][:120]))
                    vector.setRenderer(QgsCategorizedSymbolRenderer('CENTRO_ID',cats))
                QgsProject.instance().addMapLayer(vector)
