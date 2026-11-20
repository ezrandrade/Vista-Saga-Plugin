"""Combinação de Mapas: interface própria, compacta, QGIS 4.x/Qt6.

As listas permitem empilhar rasteres ou polígonos sem alterar as camadas do QGIS.
O processamento vetorial permanece no thread gráfico por usar PyQGIS.
"""
from .i18n import tr
from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QProgressDialog, QPushButton, QTabWidget, QVBoxLayout, QWidget, QAbstractItemView,
)
from qgis.core import (Qgis, QgsProject, QgsRasterLayer, QgsVectorLayer,
                       QgsPalettedRasterRenderer, QgsCategorizedSymbolRenderer,
                       QgsRendererCategory, QgsFillSymbol)
from qgis.gui import QgsMapLayerComboBox

from .ui_shared import (choose_project_layers, layer_name, materialize_in_memory, result_name,
                        temporary_destination)
from .ui_shared import RUN_TEXT, FooterStatus, report_outcome
from .errors import log_exception


RASTER_RESULT_HINT = (
    'Em branco, o mapa é gravado num arquivo temporário e carregado no QGIS (o QGIS não '
    'mantém rasters em memória; salve-o antes de fechar o QGIS). Com um arquivo indicado, '
    'ele é salvo em disco e carregado no QGIS. Além do mapa, são gerados _combinacoes.csv e '
    '_resumo.txt; sem arquivo indicado, eles ficam na pasta temporária do QGIS. Os dados de '
    'entrada permanecem inalterados.')

VECTOR_RESULT_HINT = (
    'Em branco, o resultado é carregado no QGIS como camada temporária em memória (salve-a '
    'antes de fechar o QGIS). Com um arquivo indicado, ele é salvo em disco e carregado no '
    'QGIS. Além do mapa, são gerados _combinacoes.csv e _resumo.txt; sem arquivo indicado, '
    'eles ficam na pasta temporária do QGIS. Somente a cobertura comum é combinada. Os '
    'dados de entrada permanecem inalterados.')


class CombinationDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self._busy = False
        self._sources = [[], []]
        self._file_layers = []
        self.setWindowTitle(tr('Vista Saga Plugin - Combinação de Mapas'))
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
        for idx, title in enumerate(('Raster', 'Vetorial')):
            page = QWidget()
            self.pages.append(page)
            self.tabs.addTab(page, tr(title))
            body = QVBoxLayout(page)
            hint = QLabel(tr('Selecione dois ou mais mapas categóricos. '
                          'Cada associação observada recebe um código, sem pesos ou notas.'))
            hint.setWordWrap(True)
            body.addWidget(hint)
            source_group = QGroupBox(tr('Mapas de entrada - em ordem de combinação'))
            sf = QFormLayout(source_group)
            choose = QgsMapLayerComboBox()
            choose.setAllowEmptyLayer(True)
            choose.setShowCrs(True)
            choose.setFilters(Qgis.LayerFilter.RasterLayer if idx == 0 else Qgis.LayerFilter.VectorLayer)
            choose.setToolTip(tr('Camada carregada no QGIS a acrescentar à lista.'))
            sf.addRow(tr('Camada no QGIS:'), choose)
            setattr(self, f'select_{idx}', choose)
            input_buttons = QHBoxLayout()
            append = QPushButton(tr('Adicionar camada selecionada'))
            append.setToolTip(tr('Acrescenta à lista a camada escolhida acima.'))
            append.clicked.connect(lambda checked=False, i=idx: self._add_project(i))
            load = QPushButton(tr('Adicionar arquivos…'))
            load.setToolTip(tr('Acrescenta mapas raster em arquivo.') if idx == 0 else
                            tr('Acrescenta mapas vetoriais em arquivo.'))
            load.clicked.connect(lambda checked=False, i=idx: self._add_files(i))
            input_buttons.addWidget(append)
            bulk = QPushButton(tr('Adicionar várias do QGIS…'))
            bulk.setToolTip(tr('Escolhe várias camadas carregadas no QGIS de uma vez.'))
            bulk.clicked.connect(lambda checked=False, i=idx: self._add_project_many(i))
            input_buttons.addWidget(bulk)
            input_buttons.addWidget(load)
            input_buttons.addStretch(1)
            sf.addRow('', input_buttons)
            stack = QListWidget()
            stack.setAlternatingRowColors(True)
            stack.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            stack.setMinimumHeight(110)
            stack.setToolTip(tr('Mapas a combinar, na ordem da combinação.'))
            setattr(self, f'list_{idx}', stack)
            sf.addRow(tr('Camadas adicionadas:'), stack)
            controls = QHBoxLayout()
            rem = QPushButton(tr('Remover selecionadas'))
            rem.setToolTip(tr('Retira da lista os mapas selecionados.'))
            rem.clicked.connect(lambda checked=False, i=idx: self._remove(i))
            up = QPushButton(tr('Mover para cima'))
            up.setToolTip(tr('Sobe o mapa selecionado na ordem de combinação.'))
            up.clicked.connect(lambda checked=False, i=idx: self._move(i,-1))
            down = QPushButton(tr('Mover para baixo'))
            down.setToolTip(tr('Desce o mapa selecionado na ordem de combinação.'))
            down.clicked.connect(lambda checked=False, i=idx: self._move(i,1))
            controls.addWidget(rem)
            controls.addWidget(up)
            controls.addWidget(down)
            controls.addStretch(1)
            sf.addRow('', controls)
            body.addWidget(source_group)

            if idx == 1:
                # Os campos valem para a camada selecionada na lista (alteração
                # imediata) ou, sem seleção na lista, para a camada do menu
                # suspenso que será adicionada em seguida.
                fields = QGroupBox(tr('Campos de classe e legenda'))
                ff = QFormLayout(fields)
                self.fields_target = QLabel()
                self.fields_target.setWordWrap(True)
                field = QComboBox()
                legend = QComboBox()
                field.setToolTip(tr('Campo com a classe de cada polígono da camada.'))
                legend.setToolTip(tr('Campo opcional com o nome da classe, usado na legenda.'))
                setattr(self, 'class_field', field)
                setattr(self, 'legend_field', legend)
                ff.addRow(tr('Camada:'), self.fields_target)
                ff.addRow(tr('Campo de classe:'), field)
                ff.addRow(tr('Campo da legenda (opcional):'), legend)
                self._editing_row = None
                self._filling_fields = False
                choose.layerChanged.connect(self._dropdown_changed)
                stack.itemSelectionChanged.connect(self._list_selection_changed)
                field.currentIndexChanged.connect(self._field_edited)
                legend.currentIndexChanged.connect(self._field_edited)
                body.insertWidget(2, fields)
                self._update_fields()
            output_group = QGroupBox(tr('Resultado'))
            out = QFormLayout(output_group)
            path = QLineEdit()
            # Em branco: resultado temporário (vetor em memória; raster em arquivo
            # temporário, pois o QGIS não mantém rasters em memória). Preenchido:
            # salvo nesse arquivo. Nos dois casos, o resultado é carregado no QGIS.
            path.setPlaceholderText(tr('[Arquivo temporário]' if idx == 0
                                       else '[Camada temporária em memória]'))
            path.setClearButtonEnabled(True)
            path.setToolTip(tr('Arquivo do resultado. Em branco, o resultado fica temporário e é carregado no QGIS.'))
            setattr(self, f'output_{idx}', path)
            row = QHBoxLayout()
            row.addWidget(path,1)
            browse = QPushButton(tr('Salvar como…'))
            browse.setToolTip(tr('Escolhe onde salvar o resultado.'))
            browse.clicked.connect(lambda checked=False,i=idx: self._save_as(i))
            row.addWidget(browse)
            out.addRow(tr('Salvar em:'),row)
            note = QLabel(tr(RASTER_RESULT_HINT if idx == 0 else VECTOR_RESULT_HINT))
            note.setWordWrap(True)
            out.addRow('', note)
            body.addWidget(output_group)
            body.addStretch(1)
        control = QHBoxLayout()
        self.status = FooterStatus(tr('Adicione pelo menos dois mapas para combinar.'))
        self.status.setWordWrap(True)
        control.addStretch(1)
        self.start = QPushButton(tr(RUN_TEXT))
        self.start.setToolTip(tr('Combina os mapas e grava o mapa combinado e os relatórios.'))
        self.start.clicked.connect(self.run)
        control.addWidget(self.start)
        self.close_button = QPushButton(tr('Fechar'))
        self.close_button.setToolTip(tr('Fecha a janela da Combinação de Mapas.'))
        self.close_button.clicked.connect(self.close)
        control.addWidget(self.close_button)
        layout.addLayout(control)

    def _fill_fields(self, layer, field=None, legend=None):
        """Preenche as listas de campos; sem campo dado, usa os nomes preferidos."""
        self._filling_fields = True
        try:
            self.class_field.clear()
            self.legend_field.clear()
            self.legend_field.addItem(tr('(usar classe como legenda)'), '')
            if not (isinstance(layer, QgsVectorLayer) and layer.isValid()):
                return
            names = layer.fields().names()
            self.class_field.addItems(names)
            for name in names:
                self.legend_field.addItem(name, name)
            if field is None:
                field = next((n for n in ('CODIGO','CLASSE','USO','TIPO_USO','TIPOS_USO')
                              if n in names), None)
                legend = next((n for n in ('LEGENDA','NOME','DESCRICAO') if n in names), '')
            if field in names:
                self.class_field.setCurrentText(field)
            index = self.legend_field.findData(legend or '')
            self.legend_field.setCurrentIndex(max(index, 0))
        finally:
            self._filling_fields = False

    def _update_fields(self, *args):
        """Campos da camada do menu suspenso (próxima a ser adicionada)."""
        if not hasattr(self, 'class_field'):
            return
        self._editing_row = None
        layer = self.select_1.currentLayer()
        self._fill_fields(layer)
        valid = isinstance(layer, QgsVectorLayer) and layer.isValid()
        self.fields_target.setText(
            tr('{name} (próxima a adicionar)').format(name=layer.name()) if valid
            else tr('Selecione uma camada no menu acima ou na lista de camadas adicionadas.'))
        self.class_field.setEnabled(valid)
        self.legend_field.setEnabled(valid)

    def _dropdown_changed(self, *args):
        listbox = self.list_1
        listbox.blockSignals(True)
        listbox.clearSelection()
        listbox.blockSignals(False)
        self._update_fields()

    def _list_selection_changed(self):
        rows = sorted({self.list_1.row(item) for item in self.list_1.selectedItems()})
        if not rows:
            self._update_fields()
            return
        if len(rows) > 1:
            self._editing_row = None
            self._fill_fields(None)
            self.fields_target.setText(tr('Selecione uma única camada da lista para alterar seus campos.'))
            self.class_field.setEnabled(False)
            self.legend_field.setEnabled(False)
            return
        row = rows[0]
        layer, field, legend = self._sources[1][row]
        self._editing_row = row
        self._fill_fields(layer, field, legend)
        self.fields_target.setText(tr('{name} (na lista; a alteração vale imediatamente)').format(
            name=layer.name()))
        self.class_field.setEnabled(True)
        self.legend_field.setEnabled(True)

    def _field_edited(self, *args):
        row = getattr(self, '_editing_row', None)
        if self._filling_fields or row is None or row >= len(self._sources[1]):
            return
        field = self.class_field.currentText()
        if not field:
            return
        layer = self._sources[1][row][0]
        legend = self.legend_field.currentData() or ''
        self._sources[1][row] = (layer, field, legend)
        item = self.list_1.item(row)
        if item is not None:
            item.setText(self._item_label(1, row + 1, layer, field, legend))

    def _add_project(self, mode):
        layer = getattr(self, f'select_{mode}').currentLayer()
        if layer is None:
            QMessageBox.warning(self,tr('Combinação'),tr('Selecione uma camada carregada no QGIS.'))
            return
        if mode and self._editing_row is not None:
            # Os campos mostrados são de uma camada da lista: volta para a camada
            # do menu e pede a conferência antes de adicionar.
            self._dropdown_changed()
            QMessageBox.information(self, tr('Combinação'),
                tr('Os campos agora são os da camada “{name}”. Confira o campo de classe e '
                   'clique de novo em “Adicionar camada selecionada”.').format(name=layer.name()))
            return
        field = self.class_field.currentText() if mode else ''
        legend = self.legend_field.currentData() if mode else ''
        self._append(mode, layer, field, legend)

    def _add_project_many(self, mode):
        layers = choose_project_layers(self, 'raster' if mode == 0 else 'vector',
                                       'Adicionar vários mapas à combinação')
        for layer in layers:
            if self._already_listed(mode, layer):
                continue
            if mode == 1:
                fields = layer.fields().names()
                if not fields:
                    continue
                preferred = next((n for n in ('CODIGO', 'CLASSE', 'USO', 'TIPO_USO', 'TIPOS_USO')
                                  if n in fields), fields[0])
                from qgis.PyQt.QtWidgets import QInputDialog
                field, ok = QInputDialog.getItem(self, tr('Campo de classe - ') + layer.name(),
                    tr('Campo:'), fields, fields.index(preferred), False)
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
        paths, _ = QFileDialog.getOpenFileNames(self,tr('Adicionar mapas'), '', masks)
        for path in paths:
            layer = (QgsRasterLayer(path,Path(path).stem,'gdal') if mode == 0 else
                     QgsVectorLayer(path,Path(path).stem,'ogr'))
            if not layer.isValid():
                QMessageBox.warning(self,tr('Arquivo inválido'),tr(f'Não foi possível abrir: {path}'))
                continue
            if self._already_listed(mode, layer):
                continue
            if mode == 1:
                # Para arquivos escolhidos no disco, oferecer escolha de campos.
                names = layer.fields().names()
                if not names:
                    QMessageBox.warning(self,tr('Arquivo inválido'),tr(f'Camada sem campos: {path}'))
                    continue
                field, ok = self._choose_field(names, f'Classe temática - {Path(path).name}')
                if not ok:
                    continue
                label, ok = self._choose_field(['(usar classe como legenda)']+names,
                                                f'Legenda - {Path(path).name}')
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
        return QInputDialog.getItem(self,title,tr('Campo:'),fields,0,False)

    def _append(self, mode, layer, field, legend):
        if not layer.isValid():
            QMessageBox.warning(self,tr('Combinação'),tr('Camada inválida.'))
            return
        if mode == 1 and not isinstance(layer,QgsVectorLayer):
            QMessageBox.warning(self,tr('Combinação'),tr('É necessária uma camada vetorial.'))
            return
        if mode == 0 and not isinstance(layer,QgsRasterLayer):
            QMessageBox.warning(self,tr('Combinação'),tr('É necessária uma camada raster.'))
            return
        if mode == 1 and not field:
            QMessageBox.warning(self,tr('Combinação'),tr('Escolha um campo de classe antes de adicionar.'))
            return
        if self._already_listed(mode, layer):
            return
        self._sources[mode].append((layer,field,legend or ''))
        self._refresh(mode)

    def _already_listed(self, mode, layer):
        """Cada camada entra uma única vez na combinação; avisa e devolve True se repetida.

        A comparação é pela fonte, e não pelo objeto: a mesma camada adicionada
        pelo projeto e pelo arquivo em disco também é recusada.
        """
        for listed, field, _legend in self._sources[mode]:
            if listed.source() != layer.source():
                continue
            if mode == 1:
                message = tr('A camada “{name}” já está na combinação, com o campo {field}. '
                             'Cada camada pode entrar uma única vez. Para usar outro atributo, '
                             'selecione-a na lista e troque o campo de classe.'
                             ).format(name=layer.name(), field=field)
            else:
                message = tr('A camada “{name}” já está na combinação. '
                             'Cada camada pode entrar uma única vez.').format(name=layer.name())
            QMessageBox.warning(self, tr('Camada repetida'), message)
            return True
        return False

    @staticmethod
    def _item_label(mode, index, layer, field, legend):
        label = f'{index:02d} - {layer.name()}'
        if mode:
            label += f'  •  {field}' + (f'  •  {legend}' if legend else '')
        return label

    def _refresh(self,mode):
        widget = getattr(self, f'list_{mode}')
        widget.clear()
        for index, (layer,field,legend) in enumerate(self._sources[mode],1):
            widget.addItem(QListWidgetItem(self._item_label(mode, index, layer, field, legend)))
        if mode == 1:
            self._list_selection_changed()
        self.status.setText(tr('{count} mapas na modalidade selecionada.').format(count=len(self._sources[mode])))

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
        answer, _ = QFileDialog.getSaveFileName(self,tr('Resultado da combinação'),
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
        chosen = getattr(self,f'output_{mode}').text().strip()
        temporary = not chosen
        dest = (temporary_destination(result_name('Combinação de Mapas', 'Raster' if mode == 0 else 'Vetorial'),
                                      '.tif' if mode == 0 else '.gpkg')
                if temporary else chosen)
        if len(selected)<2:
            QMessageBox.warning(self,tr('Combinação'),tr('Adicione pelo menos dois mapas para combinar.'))
            return
        stem = str(Path(dest).with_suffix(''))
        targets = (dest,stem+'_combinacoes.csv',stem+'_resumo.txt')
        if any(Path(file).exists() for file in targets):
            confirm = QMessageBox.question(self,tr('Substituir arquivos?'),
                           tr('Há resultados existentes. Substituir mapa e relatórios associados?'),
                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                           QMessageBox.StandardButton.No)
            if confirm != QMessageBox.StandardButton.Yes:
                return
        self._busy = True
        self.start.setEnabled(False)
        self.close_button.setEnabled(False)
        pg = QProgressDialog(tr('Combinando mapas…'),tr('Cancelar'),0,100,self)
        pg.setWindowTitle(self.window().windowTitle())  # título da janela do módulo (1.4.1)
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
            # O resultado é sempre carregado no QGIS.
            if mode == 0:
                layer = QgsRasterLayer(result['output'],layer_name(result['output']),'gdal')
                if layer.isValid() and len(result['rows']) <= 75:
                    import colorsys
                    classes = []
                    for row in result['rows']:
                        rgb = colorsys.hsv_to_rgb((row['id']*.61803398875)%1,.48,.85)
                        col = QColor(*[int(x*255) for x in rgb])
                        classes.append(QgsPalettedRasterRenderer.Class(row['id'],col,row['legend'][:120]))
                    layer.setRenderer(QgsPalettedRasterRenderer(layer.dataProvider(),1,classes))
            else:
                uri = result['output']+'|layername=combinacao_mapas'
                layer = (materialize_in_memory(uri, layer_name(uri)) if temporary
                         else QgsVectorLayer(uri, layer_name(uri), 'ogr'))
                if layer is None:
                    raise RuntimeError('Não foi possível carregar o resultado no QGIS.')
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
            where = (tr('camada temporária em memória') if temporary and mode == 1 else
                     tr('arquivo temporário') if temporary else dest)
            self.status.setText(tr('Concluído: {count} combinações. Resultado: {where}.').format(
                count=result['combinations'], where=where))
            message = self.status.text() + '\n\n' + tr(f"Combinações observadas: {result['combinations']}\n"
                                                        f"Relatórios: {result['csv']} e {result['txt']}")
            slivers = [s for s in result.get('slivers', ()) if s['count']]
            if slivers:
                message += '\n\n' + tr('Lascas toleradas (largura média abaixo de 1 cm), registradas no resumo:')
                for item in slivers:
                    message += '\n' + tr('{0}: {1} lascas, {2} m² de área duplicada').format(
                        item['name'], item['count'], f"{item['area_m2']:.4f}")
            residues = result.get('residues') or {}
            if residues.get('count'):
                message += '\n\n' + tr('Resíduos (largura média abaixo de 1 cm) incorporados ao vizinho: '
                                        '{0} ({1} m²).').format(residues['merged'], f"{residues['merged_m2']:.4f}")
                if residues.get('removed'):
                    message += '\n' + tr('Resíduos sem vizinho, excluídos: {0} ({1} m²).').format(
                        residues['removed'], f"{residues['removed_m2']:.4f}")
            QMessageBox.information(self,tr('Combinação concluída'), message)
        except InterruptedError:
            report_outcome(self.status, 'Combinação de Mapas', tr('Processamento cancelado, sem alterar as entradas.'), 'warning')
        except Exception as exc:
            log_exception()
            QMessageBox.critical(self,tr('Falha na combinação'),tr(str(exc)))
            self.status.setText(tr('Falha na combinação; revise os parâmetros.'))
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
