"""Interface compacta da Assinatura Espacial: composição de classes por área.

QGIS 4.x / Qt6; seleção de camadas do projeto ou arquivos locais. A rotina
PyQGIS roda no thread da GUI para evitar acesso inseguro a QgsVectorLayer.
"""
from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QApplication, QAbstractItemView, QComboBox, QDialog, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressDialog,
    QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    QHeaderView, QCheckBox, QScrollArea, QFrame, QTabBar, QListWidget,
    QAbstractItemView,
)
from qgis.core import Qgis, QgsProject, QgsRasterLayer, QgsVectorLayer
from qgis.gui import QgsMapLayerComboBox

from .ui_shared import temporary_destination, choose_project_layers
from .signature_engine import run_signature, validate_signature, _outpaths


class SignatureDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self._busy = False
        self._files = {}
        self._area_stack = []
        self._merged_areas = None
        self.setModal(False)
        self.setWindowTitle('Vista Saga Plugin — Assinatura Espacial')
        self.resize(800, 530)
        self.setMinimumSize(690, 440)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(7)
        self.type_tabs = QTabBar()
        self.type_tabs.addTab('Raster')
        self.type_tabs.addTab('Vetorial')
        # Igualar o comportamento compacto das abas dos demais módulos.
        # O padrão de QTabBar expande as abas pela largura disponível.
        self.type_tabs.setExpanding(False)
        root.addWidget(self.type_tabs)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        cfg = QWidget()
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setFrameShape(QFrame.Shape.NoFrame)
        config_scroll.setWidget(cfg)
        result_tab = QWidget()
        self.tabs.addTab(config_scroll, 'Configuração')
        self.tabs.addTab(result_tab, 'Resultados')
        layout = QVBoxLayout(cfg)
        layout.setSpacing(9)
        mode_group = QGroupBox('Mapa temático')
        mf = QFormLayout(mode_group)
        self.mode = QComboBox()
        self.mode.addItem('Raster categórico (GeoTIFF)', 'raster')
        self.mode.addItem('Polígonos temáticos (vetor)', 'vector')
        self.mode.currentIndexChanged.connect(self._mode_changed)
        self.type_tabs.currentChanged.connect(self.mode.setCurrentIndex)
        self.theme_select = QgsMapLayerComboBox()
        self.theme_select.setAllowEmptyLayer(True)
        self.theme_select.setShowCrs(True)
        mf.addRow('Camada QGIS:', self.theme_select)
        row = QHBoxLayout()
        self.theme_file = QLineEdit()
        self.theme_file.setPlaceholderText('Ou selecionar arquivo local…')
        self.theme_file.editingFinished.connect(self._refresh_fields)
        row.addWidget(self.theme_file, 1)
        btn = QPushButton('Arquivo…')
        btn.clicked.connect(self._choose_theme)
        row.addWidget(btn)
        mf.addRow('Ou arquivo:', row)
        self.class_field = QComboBox()
        self.class_label = QComboBox()
        mf.addRow('Campo de classe:', self.class_field)
        mf.addRow('Campo com nome da classe:', self.class_label)
        self.theme_select.layerChanged.connect(lambda layer: self._refresh_fields())
        layout.addWidget(mode_group)

        region = QGroupBox('Áreas de análise')
        rf = QFormLayout(region)
        self.areas_select = QgsMapLayerComboBox()
        self.areas_select.setFilters(Qgis.LayerFilter.VectorLayer)
        self.areas_select.setAllowEmptyLayer(True)
        self.areas_select.setShowCrs(True)
        rf.addRow('Camada de polígonos:', self.areas_select)
        row2 = QHBoxLayout()
        self.areas_file = QLineEdit()
        self.areas_file.setPlaceholderText('Ou arquivo GPKG, SHP, GeoJSON, FGB…')
        self.areas_file.editingFinished.connect(self._refresh_area_fields)
        row2.addWidget(self.areas_file, 1)
        btn2 = QPushButton('Arquivo…')
        btn2.clicked.connect(self._choose_areas)
        row2.addWidget(btn2)
        rf.addRow('Ou arquivo:', row2)
        self.area_name_field = QComboBox()
        rf.addRow('Identificação dos polígonos:', self.area_name_field)
        stack_buttons = QHBoxLayout()
        add_areas = QPushButton('Adicionar várias áreas do QGIS…')
        add_areas.clicked.connect(self._add_area_layers)
        remove_areas = QPushButton('Remover selecionadas')
        remove_areas.clicked.connect(self._remove_area_layers)
        stack_buttons.addWidget(add_areas)
        stack_buttons.addWidget(remove_areas)
        rf.addRow('', stack_buttons)
        self.areas_stack_list = QListWidget()
        self.areas_stack_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.areas_stack_list.setMaximumHeight(95)
        rf.addRow('Áreas adicionadas:', self.areas_stack_list)
        areas_stack_help = QLabel('Quando há camadas na lista, todas as feições poligonais dessas camadas '
             'serão avaliadas, com identificação da camada de origem. '
             'A seleção individual acima continua disponível quando a lista estiver vazia.')
        areas_stack_help.setWordWrap(True)
        rf.addRow('', areas_stack_help)
        explain = QLabel('Cada polígono recebe uma assinatura individual. Regiões sobrepostas '
                         'são analisadas separadamente e não devem ter suas áreas somadas.')
        explain.setWordWrap(True)
        rf.addRow('', explain)
        self.areas_select.layerChanged.connect(lambda layer: self._refresh_area_fields())
        layout.addWidget(region)

        self.overlap_group = QGroupBox('Sobreposição entre classes (somente vetor)')
        overlap_form = QFormLayout(self.overlap_group)
        self.overlap_policy = QComboBox()
        self.overlap_policy.addItem('Unir classes iguais e excluir áreas ambíguas (recomendado)', 'exclude')
        self.overlap_policy.addItem('Interromper se classes diferentes se sobrepuserem', 'strict')
        overlap_form.addRow('Tratamento:', self.overlap_policy)
        help_overlap = QLabel('Polígonos sobrepostos da mesma categoria contam apenas uma vez. '
            'Quando classes distintas ocupam o mesmo local, a área conflitante não é '
            'atribuída a nenhuma delas e aparece no relatório TXT/CSV e no GeoPackage.')
        help_overlap.setWordWrap(True)
        overlap_form.addRow('', help_overlap)
        layout.addWidget(self.overlap_group)

        dest_box = QGroupBox('Saída e relatórios')
        df = QFormLayout(dest_box)
        self.title = QLineEdit()
        self.title.setPlaceholderText('Ex.: Composição temática de áreas de preservação')
        df.addRow('Título:', self.title)
        outrow = QHBoxLayout()
        self.path = QLineEdit()
        self.path.setPlaceholderText('Caminho do CSV principal (.csv)')
        outrow.addWidget(self.path, 1)
        btn3 = QPushButton('Salvar como…')
        btn3.clicked.connect(self._choose_output)
        outrow.addWidget(btn3)
        df.addRow('Relatório CSV:', outrow)
        self.temporary_check = QCheckBox('Resultado temporário no QGIS (pode salvar depois)')
        self.temporary_check.setChecked(True)
        df.addRow('', self.temporary_check)
        self.path.setEnabled(False)
        self.temporary_check.toggled.connect(lambda active: self.path.setEnabled(not active))
        hint = QLabel('Além do CSV serão produzidos _resumo.txt e _areas.gpkg. '
                      'Este último contém polígonos, classe predominante e áreas. '
                      'Arquivos existentes serão substituídos apenas com sua confirmação.')
        hint.setWordWrap(True)
        df.addRow('', hint)
        self.add_project = QCheckBox('Carregar GeoPackage das áreas no QGIS')
        self.add_project.setChecked(True)
        df.addRow('', self.add_project)
        layout.addWidget(dest_box)
        layout.addStretch(1)

        rlayout = QVBoxLayout(result_tab)
        self.summary = QLabel('Nenhuma assinatura executada nesta sessão.')
        self.summary.setWordWrap(True)
        rlayout.addWidget(self.summary)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['Área', 'Classe', 'Pixels', 'Área (ha)', '% da classe'])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        rlayout.addWidget(self.table, 1)

        controls = QHBoxLayout()
        self.status = QLabel('Selecione um mapa temático e uma camada de polígonos.')
        self.status.setWordWrap(True)
        controls.addWidget(self.status, 1)
        self.run_button = QPushButton('Calcular assinatura')
        self.run_button.clicked.connect(self.run)
        controls.addWidget(self.run_button)
        close = QPushButton('Fechar')
        close.clicked.connect(self.close)
        controls.addWidget(close)
        root.addLayout(controls)
        self._mode_changed()
        self._refresh_area_fields()

    def _mode_changed(self):
        mode = self.mode.currentData()
        self.theme_select.setFilters(Qgis.LayerFilter.RasterLayer if mode == 'raster'
                                     else Qgis.LayerFilter.VectorLayer)
        self.class_field.setEnabled(mode == 'vector')
        self.class_label.setEnabled(mode == 'vector')
        self.overlap_group.setVisible(mode == 'vector')
        # Não reutilizar arquivo de modo incompatível ao trocar raster/vetor.
        self.theme_file.clear()
        self._refresh_fields()

    def _make_file_layer(self, path, mode):
        key = (path, mode)
        if key not in self._files:
            if mode == 'raster':
                layer = QgsRasterLayer(path, Path(path).stem, 'gdal')
            else:
                layer = QgsVectorLayer(path, Path(path.split('|')[0]).stem, 'ogr')
            self._files[key] = layer
        return self._files[key]

    def _thematic(self):
        path = self.theme_file.text().strip()
        return self._make_file_layer(path, self.mode.currentData()) if path else self.theme_select.currentLayer()

    def _add_area_layers(self):
        from qgis.core import Qgis
        layers = choose_project_layers(self, 'vector', 'Adicionar camadas de áreas de análise')
        existing = {ly.id() for ly in self._area_stack}
        for layer in layers:
            if layer.id() in existing:
                continue
            if layer.geometryType() != Qgis.GeometryType.Polygon:
                QMessageBox.warning(self, 'Área não poligonal',
                                    'Ignorando camada que não contém polígonos: ' + layer.name())
                continue
            self._area_stack.append(layer)
            existing.add(layer.id())
        self._refresh_area_stack()

    def _remove_area_layers(self):
        rows = sorted((self.areas_stack_list.row(item)
                       for item in self.areas_stack_list.selectedItems()), reverse=True)
        for row in rows:
            self._area_stack.pop(row)
        self._refresh_area_stack()

    def _refresh_area_stack(self):
        self.areas_stack_list.clear()
        for layer in self._area_stack:
            self.areas_stack_list.addItem(layer.name())
        self._merged_areas = None

    def _areas(self):
        if self._area_stack:
            return self._combine_area_layers()
        path = self.areas_file.text().strip()
        return self._make_file_layer(path, 'vector') if path else self.areas_select.currentLayer()

    def _combine_area_layers(self):
        """Compor AOIs na memória sem mesclar feições nem somar áreas sobrepostas."""
        from qgis.core import Qgis, QgsVectorLayer, QgsFeature, QgsField, QgsGeometry
        from qgis.PyQt.QtCore import QVariant
        layers = self._area_stack
        if not layers:
            return None
        first = layers[0]
        if not first.isValid() or not first.crs().isValid():
            raise ValueError('A primeira camada de áreas não possui SRC válido.')
        for layer in layers:
            if not layer.isValid() or layer.isEditable():
                raise ValueError('Camada de áreas inválida ou com edição pendente: ' + layer.name())
            if layer.geometryType() != Qgis.GeometryType.Polygon or layer.crs() != first.crs():
                raise ValueError('As camadas de áreas devem ser poligonais e possuir o mesmo SRC.')
        merged = QgsVectorLayer('MultiPolygon', 'Áreas de análise — múltiplas camadas', 'memory')
        merged.setCrs(first.crs())
        provider = merged.dataProvider()
        provider.addAttributes([QgsField('VS_ORIGEM', QVariant.String),
                                QgsField('VS_NOME', QVariant.String)])
        merged.updateFields()
        batch = []
        for layer in layers:
            candidates = [f for f in ('NOME','NAME','AREA_NOME','IDENTIF','CODIGO')
                          if f in layer.fields().names()]
            field_name = candidates[0] if candidates else ''
            for source in layer.getFeatures():
                geom = QgsGeometry(source.geometry())
                if geom.isNull() or geom.isEmpty():
                    continue
                if not geom.isGeosValid():
                    raise ValueError('Área com geometria inválida em ' + layer.name())
                geom.convertToMultiType()
                out = QgsFeature(merged.fields())
                out.setGeometry(geom)
                value = str(source[field_name]) if field_name else str(source.id())
                out.setAttributes([layer.name(), value])
                batch.append(out)
        if not batch:
            raise ValueError('As camadas de áreas não contêm feições válidas.')
        ok, _ = provider.addFeatures(batch)
        if not ok:
            raise ValueError('Falha ao montar as áreas temporárias para Assinatura.')
        merged.updateExtents()
        self._merged_areas = merged   # manter a camada viva até o final da análise
        return merged

    def _refresh_fields(self):
        current = self.class_field.currentText()
        label = self.class_label.currentData()
        self.class_field.clear()
        self.class_label.clear()
        self.class_label.addItem('(usar classe como legenda)', '')
        if self.mode.currentData() == 'raster':
            return
        layer = self._thematic()
        if layer and layer.isValid() and isinstance(layer, QgsVectorLayer):
            names = layer.fields().names()
            self.class_field.addItems(names)
            for name in names:
                self.class_label.addItem(name, name)
            for candidate in (current, 'CODIGO', 'CLASSE', 'USO', 'TIPO_USO'):
                if candidate in names:
                    self.class_field.setCurrentText(candidate)
                    break
            if label in names:
                self.class_label.setCurrentIndex(self.class_label.findData(label))
            else:
                for candidate in ('NOME', 'LEGENDA', 'DESCRICAO'):
                    if candidate in names and candidate != self.class_field.currentText():
                        self.class_label.setCurrentIndex(self.class_label.findData(candidate))
                        break

    def _refresh_area_fields(self):
        old = self.area_name_field.currentData()
        self.area_name_field.clear()
        self.area_name_field.addItem('(usar ID de cada feição)', '')
        layer = self._areas()
        if layer and layer.isValid() and isinstance(layer, QgsVectorLayer):
            names = layer.fields().names()
            for name in names:
                self.area_name_field.addItem(name, name)
            if old in names:
                self.area_name_field.setCurrentIndex(self.area_name_field.findData(old))
            else:
                for candidate in ('NOME', 'NAME', 'AREA_NOME', 'IDENTIF', 'CODIGO'):
                    if candidate in names:
                        self.area_name_field.setCurrentIndex(self.area_name_field.findData(candidate))
                        break

    def _choose_theme(self):
        filterstr = ('GeoTIFF (*.tif *.tiff);;Todos os arquivos (*)' if self.mode.currentData() == 'raster'
                     else 'Vetor (*.gpkg *.shp *.geojson *.fgb);;Todos os arquivos (*)')
        path, _ = QFileDialog.getOpenFileName(self, 'Mapa temático', '', filterstr)
        if path:
            self.theme_file.setText(path)
            self._refresh_fields()

    def _choose_areas(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Áreas de análise', '',
            'Vetores (*.gpkg *.shp *.geojson *.fgb);;Todos os arquivos (*)')
        if path:
            self.areas_file.setText(path)
            self._refresh_area_fields()

    def _choose_output(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Relatório de Assinatura',
            self.path.text().strip() or 'assinatura.csv', 'CSV (*.csv)')
        if path:
            self.path.setText(path if path.lower().endswith('.csv') else path + '.csv')

    def run(self):
        if self._busy:
            return
        try:
            thematic, areas = self._thematic(), self._areas()
        except ValueError as exc:
            QMessageBox.warning(self, 'Áreas de análise', str(exc))
            return
        mode = self.mode.currentData()
        field = self.class_field.currentText() if mode == 'vector' else ''
        label_field = self.class_label.currentData() or ''
        area_name = 'VS_NOME' if self._area_stack else self.area_name_field.currentData() or ''
        path = (temporary_destination('assinatura', '.csv')
                if self.temporary_check.isChecked() else self.path.text().strip())
        try:
            validate_signature(thematic, areas, mode, field, path, label_field, area_name)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, 'Assinatura — Verificar entrada', str(exc))
            return
        existing = [p for p in _outpaths(path) if Path(p).exists()]
        if existing:
            answer = QMessageBox.question(
                self, 'Substituir saídas',
                'Os seguintes resultados já existem:\n' + '\n'.join(existing) +
                '\n\nDeseja substituí-los? Os anteriores serão restaurados em caso de falha.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
        self._busy = True
        self.run_button.setEnabled(False)
        popup = QProgressDialog('Calculando as assinaturas…', 'Cancelar', 0, 100, self)
        popup.setWindowTitle('Vista Saga — Assinatura Espacial')
        popup.setWindowModality(Qt.WindowModality.WindowModal)
        popup.setMinimumDuration(0)
        popup.setValue(0)
        popup.show()
        def update(value):
            popup.setValue(max(0, min(100, int(value))))
            QApplication.processEvents()
        def cancelled():
            QApplication.processEvents()
            return popup.wasCanceled()
        try:
            result = run_signature(thematic, areas, mode, field, path,
                name_field=label_field, area_name_field=area_name,
                title=self.title.text().strip(), progress=update, cancelled=cancelled,
                overlap_policy=self.overlap_policy.currentData())
            self.summary.setText(
                f"Concluído. {len(result['areas'])} áreas e {len(result['rows'])} "
                f"ocorrências de classes.\nCSV: {result['csv']}\nTXT: {result['txt']}\n"
                f"GeoPackage: {result['gpkg']}\n{result['note']}")
            self.table.setRowCount(min(len(result['rows']), 2000))
            for i, record in enumerate(result['rows'][:2000]):
                for j, value in enumerate((record['area_name'], record['label'],
                                           record['pixels'] if record['pixels'] is not None else '',
                                           '' if record['area_ha'] is None else f"{record['area_ha']:.4f}",
                                           f"{record['percentage']:.2f}")):
                    self.table.setItem(i, j, QTableWidgetItem(str(value)))
            self.tabs.setCurrentIndex(1)
            if result['note'].startswith('ATENÇÃO:'):
                QMessageBox.warning(self, 'Assinatura — Áreas conflitantes', result['note'])
            self.status.setText('Assinatura calculada. Relatórios disponíveis na pasta escolhida.')
            if self.add_project.isChecked() or self.temporary_check.isChecked():
                from qgis.core import QgsVectorLayer
                new_layer = QgsVectorLayer(result['gpkg'] + '|layername=assinatura_areas',
                                           'Assinatura — áreas', 'ogr')
                if new_layer.isValid():
                    QgsProject.instance().addMapLayer(new_layer)
                else:
                    QMessageBox.warning(self, 'Assinatura',
                                        'Relatórios gravados, mas não foi possível carregar o GeoPackage.')
        except InterruptedError:
            self.status.setText('Operação cancelada; arquivos anteriores preservados.')
        except Exception as exc:
            self.status.setText('A assinatura não foi concluída.')
            QMessageBox.critical(self, 'Assinatura — Falha', str(exc))
        finally:
            popup.close()
            self._busy = False
            self.run_button.setEnabled(True)
