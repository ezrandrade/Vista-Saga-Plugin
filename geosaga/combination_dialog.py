"""Combinação de Mapas: interface própria, compacta, QGIS 4.x/Qt6.

As listas permitem empilhar rasteres ou polígonos sem alterar as camadas do QGIS.
O processamento vetorial permanece no thread gráfico por usar PyQGIS.
"""
from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QProgressDialog, QPushButton, QTabWidget, QVBoxLayout, QWidget, QCheckBox, QAbstractItemView,
)
from qgis.core import (Qgis, QgsProject, QgsRasterLayer, QgsVectorLayer,
                       QgsPalettedRasterRenderer, QgsCategorizedSymbolRenderer,
                       QgsRendererCategory, QgsFillSymbol)
from qgis.gui import QgsMapLayerComboBox

from .combination_core import normalized_code
from .ui_shared import choose_project_layers, temporary_destination


class CombinationDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self._busy = False
        self._sources = [[], []]
        self._file_layers = []
        self.setWindowTitle('Vista Saga Plugin — Combinação de Mapas')
        self.setModal(False)
        self.setMinimumSize(650, 450)
        self.resize(790, 565)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,10)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.pages = []
        for idx, title in enumerate(('Combinação raster', 'Combinação vetorial')):
            page = QWidget()
            self.pages.append(page)
            self.tabs.addTab(page, title)
            body = QVBoxLayout(page)
            hint = QLabel('Selecione dois ou mais mapas categóricos. '
                          'Cada associação observada recebe um código, sem pesos ou notas.')
            hint.setWordWrap(True)
            body.addWidget(hint)
            source_group = QGroupBox('Mapas de entrada — em ordem de combinação')
            sf = QFormLayout(source_group)
            choose = QgsMapLayerComboBox()
            choose.setAllowEmptyLayer(True)
            choose.setShowCrs(True)
            choose.setFilters(Qgis.LayerFilter.RasterLayer if idx == 0 else Qgis.LayerFilter.VectorLayer)
            sf.addRow('Camada no QGIS:', choose)
            setattr(self, f'select_{idx}', choose)
            input_buttons = QHBoxLayout()
            append = QPushButton('Adicionar camada')
            append.clicked.connect(lambda checked=False, i=idx: self._add_project(i))
            load = QPushButton('Adicionar arquivos…')
            load.clicked.connect(lambda checked=False, i=idx: self._add_files(i))
            input_buttons.addWidget(append)
            bulk = QPushButton('Adicionar várias do QGIS…')
            bulk.clicked.connect(lambda checked=False, i=idx: self._add_project_many(i))
            input_buttons.addWidget(bulk)
            input_buttons.addWidget(load)
            input_buttons.addStretch(1)
            sf.addRow('', input_buttons)
            stack = QListWidget()
            stack.setAlternatingRowColors(True)
            stack.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            stack.setMinimumHeight(110)
            setattr(self, f'list_{idx}', stack)
            sf.addRow('Camadas adicionadas:', stack)
            controls = QHBoxLayout()
            rem = QPushButton('Remover selecionadas')
            rem.clicked.connect(lambda checked=False, i=idx: self._remove(i))
            up = QPushButton('Subir')
            up.clicked.connect(lambda checked=False, i=idx: self._move(i,-1))
            down = QPushButton('Descer')
            down.clicked.connect(lambda checked=False, i=idx: self._move(i,1))
            controls.addWidget(rem)
            controls.addWidget(up)
            controls.addWidget(down)
            controls.addStretch(1)
            sf.addRow('', controls)
            body.addWidget(source_group)

            if idx == 1:
                fields = QGroupBox('Classificação da próxima camada vetorial')
                ff = QFormLayout(fields)
                field = QComboBox()
                legend = QComboBox()
                setattr(self, 'class_field', field)
                setattr(self, 'legend_field', legend)
                ff.addRow('Campo de classe:', field)
                ff.addRow('Campo da legenda (opcional):', legend)
                choose.layerChanged.connect(self._update_fields)
                body.insertWidget(2, fields)
                self._update_fields()
            output_group = QGroupBox('Resultado')
            out = QFormLayout(output_group)
            path = QLineEdit()
            path.setPlaceholderText('GeoTIFF com IDs de combinação' if idx == 0 else 'GeoPackage de polígonos combinados')
            setattr(self, f'output_{idx}', path)
            row = QHBoxLayout()
            row.addWidget(path,1)
            browse = QPushButton('Salvar como…')
            browse.clicked.connect(lambda checked=False,i=idx: self._save_as(i))
            row.addWidget(browse)
            out.addRow('Arquivo:',row)
            note = QLabel('Além do mapa, serão gerados _combinacoes.csv e _resumo.txt. '
                          'No modo vetorial, somente a cobertura comum será combinada. '
                          'Os dados de entrada permanecerão inalterados.')
            note.setWordWrap(True)
            out.addRow('', note)
            body.addWidget(output_group)
            from qgis.PyQt.QtWidgets import QCheckBox
            temporary = QCheckBox('Saída temporária no QGIS (salvar depois se desejar)')
            temporary.setChecked(True)
            temporary.setToolTip('Raster e GeoPackage ficam no diretório temporário da sessão, não apenas na RAM.')
            setattr(self, f'temporary_{idx}', temporary)
            body.addWidget(temporary)
            path.setEnabled(False)
            browse.setEnabled(False)
            temporary.toggled.connect(lambda active, p=path, b=browse:
                                     (p.setEnabled(not active), b.setEnabled(not active)))
            body.addStretch(1)
        self.add_project = QCheckBox('Carregar resultado no projeto QGIS')
        self.add_project.setChecked(True)
        layout.addWidget(self.add_project)
        control = QHBoxLayout()
        self.status = QLabel('Adicione pelo menos dois mapas para combinar.')
        self.status.setWordWrap(True)
        control.addWidget(self.status,1)
        self.start = QPushButton('Combinar mapas')
        self.start.clicked.connect(self.run)
        control.addWidget(self.start)
        self.close_button = QPushButton('Fechar')
        self.close_button.clicked.connect(self.close)
        control.addWidget(self.close_button)
        layout.addLayout(control)

    def _update_fields(self, *args):
        if not hasattr(self, 'class_field'):
            return
        self.class_field.clear()
        self.legend_field.clear()
        self.legend_field.addItem('(usar classe como legenda)', '')
        layer = self.select_1.currentLayer()
        if isinstance(layer, QgsVectorLayer) and layer.isValid():
            names = layer.fields().names()
            self.class_field.addItems(names)
            for name in names:
                self.legend_field.addItem(name, name)
            for name in ('CODIGO','CLASSE','USO','TIPO_USO','TIPOS_USO'):
                if name in names:
                    self.class_field.setCurrentText(name)
                    break
            for name in ('LEGENDA','NOME','DESCRICAO'):
                if name in names:
                    self.legend_field.setCurrentIndex(self.legend_field.findData(name))
                    break

    def _add_project(self, mode):
        layer = getattr(self, f'select_{mode}').currentLayer()
        if layer is None:
            QMessageBox.warning(self,'Combinação','Selecione uma camada carregada no QGIS.')
            return
        field = self.class_field.currentText() if mode else ''
        legend = self.legend_field.currentData() if mode else ''
        self._append(mode, layer, field, legend)

    def _add_project_many(self, mode):
        layers = choose_project_layers(self, 'raster' if mode == 0 else 'vector',
                                       'Adicionar vários mapas à combinação')
        for layer in layers:
            if mode == 1:
                fields = layer.fields().names()
                if not fields:
                    continue
                preferred = next((n for n in ('CODIGO', 'CLASSE', 'USO', 'TIPO_USO', 'TIPOS_USO')
                                  if n in fields), fields[0])
                from qgis.PyQt.QtWidgets import QInputDialog
                field, ok = QInputDialog.getItem(self, 'Campo de classe — ' + layer.name(),
                    'Campo:', fields, fields.index(preferred), False)
                if not ok:
                    continue
                preferred_label = next((n for n in ('LEGENDA','NOME','DESCRICAO')
                                        if n in fields), '')
                legend = preferred_label
            else:
                field, legend = '', ''
            self._append(mode, layer, field, legend)

    def _add_files(self, mode):
        masks = ('Mapas raster (*.tif *.tiff);;Todos (*.*)' if mode == 0 else
                 'Vetores (*.gpkg *.shp *.geojson *.fgb);;Todos (*.*)')
        paths, _ = QFileDialog.getOpenFileNames(self,'Adicionar mapas', '', masks)
        for path in paths:
            layer = (QgsRasterLayer(path,Path(path).stem,'gdal') if mode == 0 else
                     QgsVectorLayer(path,Path(path).stem,'ogr'))
            if not layer.isValid():
                QMessageBox.warning(self,'Arquivo inválido',f'Não foi possível abrir: {path}')
                continue
            if mode == 1:
                # Para arquivos escolhidos no disco, oferecer escolha de campos.
                names = layer.fields().names()
                if not names:
                    QMessageBox.warning(self,'Arquivo inválido',f'Camada sem campos: {path}')
                    continue
                field, ok = self._choose_field(names, f'Classe temática — {Path(path).name}')
                if not ok:
                    continue
                label, ok = self._choose_field(['(usar classe como legenda)']+names,
                                                f'Legenda — {Path(path).name}')
                if not ok:
                    continue
                if label == '(usar classe como legenda)':
                    label = ''
            else:
                field, label = '', ''
            self._file_layers.append(layer)
            self._append(mode,layer,field,label)

    def _choose_field(self, fields, title):
        from qgis.PyQt.QtWidgets import QInputDialog
        return QInputDialog.getItem(self,title,'Campo:',fields,0,False)

    def _append(self, mode, layer, field, legend):
        if not layer.isValid():
            QMessageBox.warning(self,'Combinação','Camada inválida.')
            return
        if mode == 1 and not isinstance(layer,QgsVectorLayer):
            QMessageBox.warning(self,'Combinação','É necessária uma camada vetorial.')
            return
        if mode == 0 and not isinstance(layer,QgsRasterLayer):
            QMessageBox.warning(self,'Combinação','É necessária uma camada raster.')
            return
        if mode == 1 and not field:
            QMessageBox.warning(self,'Combinação','Escolha um campo de classe antes de adicionar.')
            return
        if any(record[0].source() == layer.source() for record in self._sources[mode]):
            QMessageBox.warning(self,'Combinação','Esta camada já está na lista.')
            return
        self._sources[mode].append((layer,field,legend or ''))
        self._refresh(mode)

    def _refresh(self,mode):
        widget = getattr(self, f'list_{mode}')
        widget.clear()
        for index, (layer,field,legend) in enumerate(self._sources[mode],1):
            label = f'{index:02d} — {layer.name()}'
            if mode:
                label += f'  •  {field}' + (f'  •  {legend}' if legend else '')
            widget.addItem(QListWidgetItem(label))
        self.status.setText(f'{len(self._sources[mode])} mapas na modalidade selecionada.')

    def _remove(self,mode):
        rows = sorted({getattr(self,f'list_{mode}').row(item)
                       for item in getattr(self,f'list_{mode}').selectedItems()}, reverse=True)
        for row in rows:
            self._sources[mode].pop(row)
        if rows:
            self._refresh(mode)

    def _move(self,mode,delta):
        listbox = getattr(self,f'list_{mode}')
        row = listbox.currentRow()
        target = row+delta
        if row < 0 or target < 0 or target >= len(self._sources[mode]):
            return
        self._sources[mode][row],self._sources[mode][target] = self._sources[mode][target],self._sources[mode][row]
        self._refresh(mode)
        listbox.setCurrentRow(target)

    def _save_as(self,mode):
        path = getattr(self,f'output_{mode}')
        ext = '.tif' if mode == 0 else '.gpkg'
        filter_ = 'GeoTIFF (*.tif)' if mode == 0 else 'GeoPackage (*.gpkg)'
        answer, _ = QFileDialog.getSaveFileName(self,'Resultado da combinação',
                                                 path.text().strip() or f'combinacao{ext}',filter_)
        if answer:
            if not answer.lower().endswith((('.tif','.tiff') if mode == 0 else ('.gpkg',))):
                answer += ext
            path.setText(answer)

    def run(self):
        if self._busy:
            return
        mode = self.tabs.currentIndex()
        selected = self._sources[mode]
        temporary = getattr(self, f'temporary_{mode}').isChecked()
        dest = (temporary_destination('combinacao', '.tif' if mode == 0 else '.gpkg')
                if temporary else getattr(self,f'output_{mode}').text().strip())
        if len(selected)<2 or not dest:
            QMessageBox.warning(self,'Combinação','Adicione dois ou mais mapas e informe a saída.')
            return
        stem = str(Path(dest).with_suffix(''))
        targets = (dest,stem+'_combinacoes.csv',stem+'_resumo.txt')
        if any(Path(file).exists() for file in targets):
            confirm = QMessageBox.question(self,'Substituir arquivos?',
                           'Há resultados existentes. Substituir mapa e relatórios associados?',
                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                           QMessageBox.StandardButton.No)
            if confirm != QMessageBox.StandardButton.Yes:
                return
        self._busy = True
        self.start.setEnabled(False)
        self.close_button.setEnabled(False)
        pg = QProgressDialog('Combinando mapas…','Cancelar',0,100,self)
        pg.setWindowModality(Qt.WindowModality.WindowModal)
        pg.setMinimumDuration(0)
        pg.setAutoClose(False)
        pg.setValue(0)
        try:
            def notify(percentage):
                if percentage is not None:
                    pg.setValue(int(percentage))
                QApplication.processEvents()
            cancelled = pg.wasCanceled
            if mode == 0:
                from .combination_raster import run_raster_combination
                from .raster_engine import file_source
                paths = [file_source(layer.source()) for layer,_,_ in selected]
                result = run_raster_combination(paths,dest,progress=notify,cancelled=cancelled)
            else:
                from .combination_vector import run_vector_combination
                result = run_vector_combination([x[0] for x in selected],
                    [x[1] for x in selected],[x[2] for x in selected],dest,
                    progress=notify,cancelled=cancelled)
            if self.add_project.isChecked() or temporary:
                if mode == 0:
                    layer = QgsRasterLayer(result['output'],'Combinação de Mapas','gdal')
                    if layer.isValid() and len(result['rows']) <= 75:
                        import colorsys
                        classes = []
                        for row in result['rows']:
                            rgb = colorsys.hsv_to_rgb((row['id']*.61803398875)%1,.48,.85)
                            col = QColor(*[int(x*255) for x in rgb])
                            classes.append(QgsPalettedRasterRenderer.Class(row['id'],col,row['legend'][:120]))
                        layer.setRenderer(QgsPalettedRasterRenderer(layer.dataProvider(),1,classes))
                else:
                    layer = QgsVectorLayer(result['output']+'|layername=combinacao_mapas',
                                           'Combinação de Mapas','ogr')
                    if layer.isValid() and len(result['rows']) <= 75:
                        import colorsys
                        classes = []
                        for row in result['rows']:
                            rgb = colorsys.hsv_to_rgb((row['id']*.61803398875)%1,.48,.85)
                            c = '#'+''.join(f'{int(255*v):02X}' for v in rgb)
                            sym = QgsFillSymbol.createSimple({'color':c, 'outline_width':'0.12'})
                            classes.append(QgsRendererCategory(row['id'],sym,row['legend'][:120]))
                        layer.setRenderer(QgsCategorizedSymbolRenderer('ID_COMB',classes))
                if layer.isValid():
                    QgsProject.instance().addMapLayer(layer)
            self.status.setText(f"Concluído: {result['combinations']} combinações. "
                                + ('Resultado temporário no QGIS.' if temporary else f'Arquivo: {dest}'))
            QMessageBox.information(self,'Combinação concluída',
                f"Combinações observadas: {result['combinations']}\n"
                f"Relatórios: {result['csv']} e {result['txt']}")
        except InterruptedError:
            self.status.setText('Processamento cancelado, sem alterar as entradas.')
        except Exception as exc:
            QMessageBox.critical(self,'Falha na combinação',str(exc))
            self.status.setText('Falha na combinação; revise os parâmetros.')
        finally:
            pg.close()
            self._busy = False
            self.start.setEnabled(True)
            self.close_button.setEnabled(True)

    def closeEvent(self,event):
        if self._busy:
            event.ignore()
        else:
            event.accept()
