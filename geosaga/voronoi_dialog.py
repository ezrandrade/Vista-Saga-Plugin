"""Interface QGIS 4 para Análises Voronoi (quatro modalidades)."""
from pathlib import Path
from math import isfinite

from qgis.PyQt.QtCore import Qt, pyqtSlot
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDoubleSpinBox,
    QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QProgressDialog, QPushButton,
    QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QScrollArea, QWidget, QFrame,
)
from qgis.core import (
    Qgis, QgsApplication, QgsTask, QgsCoordinateTransform, QgsFillSymbol, QgsPalettedRasterRenderer,
    QgsProject, QgsRasterLayer, QgsVectorLayer, QgsCategorizedSymbolRenderer,
    QgsRendererCategory, QgsWkbTypes, QgsGeometry, QgsPointXY,
)
from qgis.gui import QgsMapLayerComboBox

from .ui_shared import temporary_destination
from .voronoi_core import Generator
from .voronoi_engine import grid_from_extent, run_voronoi
from .voronoi_vector import save_simple_voronoi


class VoronoiRasterTask(QgsTask):
    """Executa APENAS dados isolados do raster, sem Qt/UI ou QgsMapLayer em run().

    Signals/progress são administrados pelo QgsTask; a UI é atualizada apenas
    no método finished(), que o QGIS invoca na thread principal.
    """
    def __init__(self, points, destination, wkt, transform, width, height, mode, vectorize, friction_path=None, friction_components=None):
        super().__init__('Vista Saga — Voronoi raster', QgsTask.CanCancel)
        self.points = tuple(points)  # Generator é uma dataclass simples, sem QObject.
        self.destination = str(destination)
        self.wkt = str(wkt)
        self.transform = tuple(transform)
        self.width = int(width)
        self.height = int(height)
        self.mode = str(mode)
        self.vectorize = bool(vectorize)
        self.friction_path = str(friction_path) if friction_path else None
        self.friction_components = tuple(dict(spec) for spec in friction_components) if friction_components else None
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
            )
            return not self.isCanceled()
        except InterruptedError:
            return False
        except Exception as exc:
            self.error = str(exc)
            return False

    def finished(self, success):
        # Não chamar UI se o complemento já tiver sido descarregado.
        callback = self.ui_callback
        self.ui_callback = None
        if callback is not None:
            callback(self, bool(success))


class VoronoiDialog(QDialog):
    """Quatro modalidades disponíveis; atrito e massa+atrito experimentais."""
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self._busy = False
        self._task = None
        self._progress_dialog = None
        self.setWindowTitle('Vista Saga Plugin — Análises Voronoi')
        self.setModal(False)
        self.setMinimumSize(630, 450)
        self.resize(760, 605)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)
        intro = QLabel('Delimite áreas de influência: Simples, com Massa, com Atrito e com Massa e Atrito. '
                       'Os modelos que utilizam atrito ainda exigem validação com o Vista SAGA original.')
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # Na interface de atrito múltiplo, a altura natural dos controles
        # ultrapassa a janela no Windows/Qt6. A área rolável impede que
        # widgets fiquem comprimidos ou inacessíveis; os botões de execução
        # permanecem visíveis fora dela.
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_contents = QWidget(scroll)
        content_layout = QVBoxLayout(scroll_contents)
        content_layout.setContentsMargins(0, 0, 4, 0)
        content_layout.setSpacing(9)
        scroll.setWidget(scroll_contents)
        layout.addWidget(scroll, 1)

        options = QGroupBox('1. Modelo de influência')
        model_form = QFormLayout(options)
        self.mode = QComboBox()
        self.mode.addItems(['Simples', 'Com Massa',
                            'Com Atrito (experimental)',
                            'Com Massa e Atrito (experimental)'])
        self.mode.currentIndexChanged.connect(self._update_mode)
        model_form.addRow('Modalidade:',self.mode)
        self.method_note = QLabel('Simples: o ponto mais próximo assume cada célula da grade.')
        self.method_note.setWordWrap(True)
        model_form.addRow('Método:',self.method_note)
        content_layout.addWidget(options)

        inputs = QGroupBox('2. Dados de entrada')
        form = QFormLayout(inputs)
        self.point_layer = QgsMapLayerComboBox()
        self.point_layer.setAllowEmptyLayer(True)
        self.point_layer.setShowCrs(True)
        self.point_layer.setFilters(Qgis.LayerFilter.VectorLayer)
        self.point_layer.layerChanged.connect(self._refresh_fields)
        form.addRow('Pontos geradores:',self.point_layer)
        self.label_field = QComboBox()
        self.label_field.addItem('(usar ID da feição)',None)
        form.addRow('Identificação do ponto:',self.label_field)
        self.mass_field = QComboBox()
        self.mass_field.setEnabled(False)
        self.mass_label=QLabel('Campo de massa:')
        form.addRow(self.mass_label,self.mass_field)
        self.grid_layer = QgsMapLayerComboBox()
        self.grid_layer.setAllowEmptyLayer(True)
        self.grid_layer.setFilters(Qgis.LayerFilter.RasterLayer)
        self.grid_layer.setShowCrs(True)
        self.grid_layer.layerChanged.connect(self._update_grid)
        self.grid_layer.setToolTip('Opcional: utilize a extensão, resolução e SRC de um raster de referência.')
        self.grid_label=QLabel('Raster de referência:')
        form.addRow(self.grid_label,self.grid_layer)
        self.friction_layer = QgsMapLayerComboBox()
        self.friction_layer.setAllowEmptyLayer(True)
        self.friction_layer.setFilters(Qgis.LayerFilter.RasterLayer)
        self.friction_layer.setShowCrs(True)
        self.friction_label = QLabel('Superfície de atrito:')
        self.friction_layer.setToolTip('GeoTIFF monobanda com valores >= 0; zero tem custo basal 1; NoData é barreira.')
        form.addRow(self.friction_label,self.friction_layer)
        self.multi_friction = QCheckBox('Combinar múltiplas superfícies de atrito (pesos e notas)')
        self.multi_friction.toggled.connect(self._on_multi_friction_toggled)
        form.addRow('', self.multi_friction)
        self.friction_stack_group = QGroupBox('Superfícies integradas')
        stack_box = QVBoxLayout(self.friction_stack_group)
        self.friction_stack_summary = QLabel('Nenhuma superfície selecionada.')
        self.friction_stack_summary.setWordWrap(True)
        stack_box.addWidget(self.friction_stack_summary)
        self.stack_manage = QPushButton('Selecionar e configurar superfícies…')
        self.stack_manage.clicked.connect(self._manage_friction_layers)
        stack_box.addWidget(self.stack_manage)
        form.addRow('', self.friction_stack_group)

        # A seleção e a edição de massas/atritos ficam em um diálogo próprio.
        # Na 0.8.3 a tabela estava diretamente no formulário, e a janela
        # sem rolagem podia exibir apenas o título "Superfícies integradas".
        self.friction_stack_dialog = QDialog(self)
        self.friction_stack_dialog.setWindowTitle('Superfícies de atrito — seleção e pesos')
        self.friction_stack_dialog.resize(840, 475)
        stack_dialog_box = QVBoxLayout(self.friction_stack_dialog)
        stack_hint = QLabel('Selecione até 12 rasters. Edite o peso positivo e, se necessário, as notas '
                            'por classe (ex.: 1=2;2=8) dando dois cliques nas células. '
                            'Sem notas, serão usados os valores originais. '
                            'NoData em qualquer mapa será barreira.')
        stack_hint.setWordWrap(True)
        stack_dialog_box.addWidget(stack_hint)
        self.friction_stack_table = QTableWidget(0, 3)
        self.friction_stack_table.setHorizontalHeaderLabels(['Camada raster', 'Peso', 'Notas por classe (opcional)'])
        self.friction_stack_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.friction_stack_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.friction_stack_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.friction_stack_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.friction_stack_table.horizontalHeader().resizeSection(1, 85)
        self.friction_stack_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        stack_dialog_box.addWidget(self.friction_stack_table, 1)
        stack_buttons = QHBoxLayout()
        self.stack_add = QPushButton('Adicionar camadas do QGIS…')
        self.stack_add.clicked.connect(self._add_friction_layers)
        stack_buttons.addWidget(self.stack_add)
        self.stack_add_files = QPushButton('Adicionar arquivos GeoTIFF…')
        self.stack_add_files.clicked.connect(self._add_friction_files)
        stack_buttons.addWidget(self.stack_add_files)
        self.stack_remove = QPushButton('Remover selecionadas')
        self.stack_remove.clicked.connect(self._remove_friction_layers)
        stack_buttons.addWidget(self.stack_remove)
        stack_buttons.addStretch(1)
        stack_dialog_box.addLayout(stack_buttons)
        stack_close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        stack_close.rejected.connect(self.friction_stack_dialog.accept)
        stack_dialog_box.addWidget(stack_close)
        self.extent_mode=QComboBox()
        self.extent_mode.addItem('Extensão visível no QGIS','canvas')
        self.extent_mode.addItem('Extensão de camada poligonal','polygon')
        self.extent_mode.addItem('Extensão manual (coordenadas do SRC)','manual')
        self.extent_mode.addItem('Extensão dos pontos + margem','points')
        self.extent_mode.addItem('Grade de raster de referência','reference')
        self.extent_mode.currentIndexChanged.connect(self._update_extent)
        form.addRow('Extensão da análise:',self.extent_mode)
        self.extent_label = form.labelForField(self.extent_mode)
        self.area_layer=QgsMapLayerComboBox()
        self.area_layer.setAllowEmptyLayer(True)
        self.area_layer.setFilters(Qgis.LayerFilter.VectorLayer)
        self.area_label=QLabel('Área poligonal:')
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
        self.resolution.setSuffix(' unidades do SRC')
        self.resolution_label=QLabel('Resolução raster:')
        form.addRow(self.resolution_label,self.resolution)
        self.grid_note = QLabel('O Voronoi vetorial direto é limitado pela extensão escolhida; '
                                'não exige massa, raster de referência nem resolução.')
        self.grid_note.setWordWrap(True)
        form.addRow('',self.grid_note)
        content_layout.addWidget(inputs)

        output = QGroupBox('3. Resultado')
        outform = QFormLayout(output)
        self.output_type=QComboBox()
        self.output_type.addItem('GeoTIFF (raster)', 'raster')
        self.output_type.addItem('GeoPackage (vetor direto — Simples)', 'direct')
        self.output_type.addItem('GeoTIFF + GeoPackage (poligonização)', 'both')
        self.output_type.currentIndexChanged.connect(self._update_output)
        outform.addRow('Formato de saída:',self.output_type)
        self.temp_output = QCheckBox('Resultado temporário (adicionar ao QGIS)')
        self.temp_output.setChecked(True)
        self.temp_output.toggled.connect(self._update_output)
        outform.addRow('',self.temp_output)
        path_box = QHBoxLayout()
        self.path_output = QLineEdit()
        self.path_output.setPlaceholderText('Voronoi_Espacial.tif')
        self.path_output.setEnabled(False)
        path_box.addWidget(self.path_output,1)
        self.path_button = QPushButton('…')
        self.path_button.setEnabled(False)
        self.path_button.clicked.connect(self._choose_output)
        path_box.addWidget(self.path_button)
        self.path_label=QLabel('Arquivo de saída:')
        outform.addRow(self.path_label,path_box)
        self.load_project = QCheckBox('Adicionar resultados ao projeto QGIS')
        self.load_project.setChecked(True)
        outform.addRow('',self.load_project)
        hint = QLabel('CSV e TXT são produzidos automaticamente. '
                      'Resultados temporários precisam ser salvos antes de fechar o QGIS.')
        hint.setWordWrap(True)
        outform.addRow('',hint)
        content_layout.addWidget(output)
        content_layout.addStretch(1)
        self.status = QLabel('Selecione a camada de pontos geradores.')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.run_button = QPushButton('Gerar Voronoi')
        self.run_button.clicked.connect(self._run)
        buttons.addWidget(self.run_button)
        self.close_button = QPushButton('Fechar')
        self.close_button.clicked.connect(self.close)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)
        self._refresh_fields()
        self._update_mode()
        self._update_extent()
        self._update_output()

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
            QMessageBox.warning(self, 'Superfícies de atrito', 'Não há camadas raster carregadas no QGIS.')
            return
        chooser = QDialog(self)
        chooser.setWindowTitle('Adicionar superfícies de atrito')
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
            self.friction_stack_dialog, 'Selecionar GeoTIFFs de atrito', '',
            'GeoTIFF (*.tif *.tiff);;Todos os arquivos (*.*)')
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
                    QMessageBox.warning(self, 'Superfícies de atrito',
                                        f'O raster não pôde ser aberto: {path}')
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
            QMessageBox.warning(self, 'Superfícies de atrito', 'Limite de 12 superfícies por análise.')
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

    def _refresh_fields(self, *_):
        layer = self.point_layer.currentLayer()
        self.label_field.clear()
        self.label_field.addItem('(usar ID da feição)',None)
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
        multi = friction and self.multi_friction.isChecked()
        self.friction_layer.setVisible(friction and not multi)
        self.friction_label.setVisible(friction and not multi)
        self.multi_friction.setVisible(friction)
        self.friction_stack_group.setVisible(multi)
        self.extent_mode.setVisible(not friction)
        self.extent_label.setVisible(not friction)
        self._update_extent()
        if friction:
            title = 'Com Massa e Atrito' if weighted else 'Com Atrito'
            formula = 'D × soma(1 + atrito) / massa' if weighted else 'D × soma(1 + atrito)'
            self.method_note.setText(title + ' (experimental): minimizar ' + formula +
                                     ' em segmento reto; NoData é barreira. Grade do raster de atrito.')
        elif weighted:
            self.method_note.setText('Com Massa: maximiza M/d; selecione campo numérico positivo.')
        else:
            self.method_note.setText('Simples: menor distância euclidiana; sem massa nem atrito.')
        self.output_type.model().item(1).setEnabled(not (weighted or friction))
        if (weighted or friction) and self.output_type.currentData() == 'direct':
            self.output_type.setCurrentIndex(0)
        self._update_output()

    def _update_grid(self, *_):
        self._update_output()

    def _update_extent(self, *_):
        choice=self.extent_mode.currentData()
        use_polygon=choice=='polygon' and self.mode.currentIndex() not in (2,3)
        self.area_layer.setVisible(use_polygon)
        self.area_label.setVisible(use_polygon)
        manual=choice=='manual' and self.mode.currentIndex() not in (2,3)
        for widget,label in zip(self.manual_bounds,self.manual_labels):
            widget.setVisible(manual)
            label.setVisible(manual)
        self._update_output()

    def _update_output(self, *_):
        direct=self.output_type.currentData()=='direct'
        friction=self.mode.currentIndex() in (2,3)
        raster=not direct
        reference=self.extent_mode.currentData()=='reference' if hasattr(self,'extent_mode') else False
        self.grid_layer.setVisible(raster and reference and not friction)
        self.grid_label.setVisible(raster and reference and not friction)
        self.resolution.setVisible(raster and not reference and not friction)
        self.resolution_label.setVisible(raster and not reference and not friction)
        self.resolution.setEnabled(raster and not reference and not friction)
        self.path_output.setEnabled(not self.temp_output.isChecked())
        self.path_button.setEnabled(not self.temp_output.isChecked())
        self.path_output.setPlaceholderText('Analises_Voronoi.gpkg' if direct else 'Analises_Voronoi.tif')
        self.extent_mode.model().item(4).setEnabled(raster)
        if direct and reference:
            self.extent_mode.setCurrentIndex(0)
        if self.path_output.text() and (self.path_output.text().lower().endswith('.gpkg') != direct):
            self.path_output.clear()
        self.grid_note.setText('Com Atrito: extensão, resolução e SRC herdados do raster de resistência; '
                               'a grade não será reprojetada.' if friction else
                               ('Vetor direto: polígonos exatos recortados à extensão e à área poligonal.'
                                if direct else 'Raster: resolução necessária. A extensão poligonal define o retângulo envolvente.'))

    def _choose_output(self):
        direct=self.output_type.currentData()=='direct'
        suffix='.gpkg' if direct else '.tif'
        path,_=QFileDialog.getSaveFileName(self,'Salvar Voronoi',
                   self.path_output.text().strip() or 'Analises_Voronoi'+suffix,
                   'GeoPackage (*.gpkg)' if direct else 'GeoTIFF (*.tif)')
        if path:
            if not path.lower().endswith(suffix): path+=suffix
            self.path_output.setText(path)

    def _get_generators(self, target_crs):
        layer = self.point_layer.currentLayer()
        if layer is None or not layer.isValid() or not isinstance(layer,QgsVectorLayer):
            raise ValueError('Selecione uma camada vetorial válida com pontos.')
        if QgsWkbTypes.geometryType(layer.wkbType()) != QgsWkbTypes.PointGeometry:
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
                if len(locations) > 1: name += f' — parte {part_index+1}'
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
            if QgsWkbTypes.geometryType(layer.wkbType())!=QgsWkbTypes.PolygonGeometry:
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

    def _get_grid(self, point_layer, points):
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
        crs=point_layer.crs()
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
            QMessageBox.warning(self,'Análises Voronoi','Selecione uma camada de pontos.')
            return
        self._busy=True
        self.run_button.setEnabled(False)
        self.close_button.setEnabled(False)
        dialog=QProgressDialog('Calculando áreas de influência…','Cancelar',0,100,self)
        dialog.setWindowModality(Qt.WindowModality.NonModal)
        dialog.setMinimumDuration(0)
        dialog.setAutoClose(False)
        dialog.setValue(0)
        asynchronous = False
        try:
            direct=self.output_type.currentData()=='direct'
            if direct:
                crs=layer.crs()
                if not crs.isValid() or crs.isGeographic():
                    raise ValueError('Reprojete os pontos para um SRC projetado antes da análise.')
                points=self._get_generators(crs)
                bounds,study=self._analysis_extent(crs,points)
                if bounds is None:
                    bounds=(min(p.x for p in points),min(p.y for p in points),
                            max(p.x for p in points),max(p.y for p in points))
                    margin=max(1.0,.10*max(bounds[2]-bounds[0],bounds[3]-bounds[1]))
                    bounds=(bounds[0]-margin,bounds[1]-margin,bounds[2]+margin,bounds[3]+margin)
                suffix='.gpkg'
            else:
                friction_mode = self.mode.currentIndex() in (2,3)
                friction_path = None
                friction_components = None
                reference = None
                if friction_mode:
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
                suffix='.tif'
            destination=(temporary_destination('voronoi_espacial',suffix) if self.temp_output.isChecked()
                         else self.path_output.text().strip())
            if not destination or not destination.lower().endswith(suffix):
                raise ValueError(f'Escolha um arquivo de saída {suffix}.')
            def progress(value):
                dialog.setValue(int(value))
                QApplication.processEvents()
            if direct:
                if self.mode.currentIndex()!=0:
                    raise ValueError('Vetor direto disponível somente para Voronoi Simples nesta versão.')
                import os
                forbidden=[layer.source().split('|')[0]]
                if self.extent_mode.currentData()=='polygon':
                    study_layer=self.area_layer.currentLayer()
                    if study_layer is not None:
                        forbidden.append(study_layer.source().split('|')[0])
                for source in forbidden:
                    if source and os.path.isfile(source) and (
                      os.path.normcase(os.path.realpath(source))==os.path.normcase(os.path.realpath(destination))):
                        raise ValueError('A saída não pode substituir uma camada de entrada.')
                result=save_simple_voronoi(points,bounds,destination,crs.toWkt(),
                    study_geometry=study,progress=progress,cancelled=dialog.wasCanceled)
            else:
                if not self.temp_output.isChecked() and reference is not None:
                    from .raster_engine import file_source
                    import os
                    input_path=file_source(reference.source())
                    if os.path.normcase(os.path.realpath(input_path))==os.path.normcase(os.path.realpath(destination)):
                        raise ValueError('O resultado não pode substituir o raster de referência.')
                task = VoronoiRasterTask(
                    points, destination, wkt, transform, width, height,
                    mode=('mass_friction' if self.mode.currentIndex()==3 else
                          'friction' if self.mode.currentIndex()==2 else
                          'mass' if self.mode.currentIndex()==1 else 'simple'),
                    vectorize=self.output_type.currentData()=='both',
                    friction_path=friction_path if friction_mode else None,
                    friction_components=friction_components if friction_mode else None)
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
            if self.load_project.isChecked() or self.temp_output.isChecked():
                self._load_output(result)
            if direct:
                self.status.setText(f'Voronoi vetorial concluído: {len(result["rows"])} regiões.')
            else:
                self.status.setText(f'Voronoi concluído: {len(points)} centros; '
                                    f'{result["pixels_valid"]:,} pixels classificados.')
            QMessageBox.information(self,'Voronoi concluído',
                 ('GeoPackage vetorial direto, CSV e TXT produzidos.' if direct else
                  'GeoTIFF, CSV e TXT produzidos. '+('GeoPackage gerado.' if result['gpkg'] else ''))+
                 ('\nSaída temporária: salve antes de fechar o QGIS.' if self.temp_output.isChecked()
                  else '\nResultado: '+destination))
        except InterruptedError:
            self.status.setText('Processamento cancelado; os dados de entrada foram preservados.')
        except Exception as exc:
            self.status.setText('Falha na execução; revise os parâmetros.')
            QMessageBox.critical(self,'Voronoi não concluído',str(exc))
        finally:
            if not asynchronous:
                dialog.close()
                self._busy=False
                self.run_button.setEnabled(True)
                self.close_button.setEnabled(True)

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
                if self.load_project.isChecked() or self.temp_output.isChecked():
                    self._load_output(task.result)
                self.status.setText(
                    f'Voronoi concluído: {len(task.points)} centros; '
                    f'{task.result["pixels_valid"]:,} pixels classificados.')
                QMessageBox.information(self,'Voronoi concluído',
                    'GeoTIFF, CSV e TXT produzidos. '
                    + ('GeoPackage gerado.' if task.result.get('gpkg') else '')
                    + ('\nSaída temporária: salve antes de fechar o QGIS.'
                       if self.temp_output.isChecked() else '\nResultado: '+task.destination))
            except Exception as exc:
                self.status.setText('Resultado criado, mas não foi possível carregar no QGIS.')
                QMessageBox.warning(self, 'Voronoi — carregar resultado', str(exc))
        elif task.error:
            self.status.setText('Falha na execução; revise os parâmetros.')
            QMessageBox.critical(self, 'Voronoi não concluído', task.error)
        else:
            self.status.setText('Processamento cancelado; dados de entrada preservados.')

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
        if result['gpkg']:
            vector = QgsVectorLayer(result['gpkg']+'|layername=voronoi_espacial',
                                    'Análises Voronoi — polígonos','ogr')
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
