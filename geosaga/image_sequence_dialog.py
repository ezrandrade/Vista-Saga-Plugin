"""Sequenciador de Mapas do Vista Saga Plugin — Raster / Vetorial / Misto.

Renderiza quadros na thread principal pelo QgsMapRendererSequentialJob. Para
uma camada com campo temporal, usa QgsVectorLayer.materialize() e cópias das
configurações de simbologia/rotulagem, sem modificar a camada do projeto.
O GIF continua sendo gerado pelo codificador interno em Python puro.
"""
from pathlib import Path

from qgis.PyQt.QtCore import Qt, QSize, QRect
from qgis.PyQt.QtGui import QColor, QFont, QImage, QMovie, QPainter
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget,
    QMessageBox, QProgressDialog, QPushButton, QScrollArea, QSpinBox,
    QTabWidget, QVBoxLayout, QWidget,
)
from qgis.core import (
    Qgis, QgsCoordinateTransform, QgsExpression, QgsFeatureRequest,
    QgsMapRendererSequentialJob, QgsMapSettings, QgsProject,
    QgsRasterLayer, QgsRectangle, QgsVectorLayer,
)
from qgis.gui import QgsMapLayerComboBox

from .gif_codec import encode_gif
from .sequence_plan import extract_year, temporal_frames, safe_png_name
from .ui_shared import choose_project_layers


class ImageSequenceDialog(QDialog):
    """Mantém _add/_render para compatibilidade com testes da versão raster."""

    MODES = ('raster', 'vector', 'mixed')

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self._mode_entries = {key: [] for key in self.MODES}
        self.entries = self._mode_entries['raster']
        self.imported_layers = []
        self._busy = False
        self._movie = None
        self.setWindowTitle('Vista Saga Plugin — Sequenciador de Mapas')
        self.setModal(False)
        self.resize(850, 725)
        self.setMinimumWidth(700)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)
        panel = QWidget()
        scroll.setWidget(panel)
        root = QVBoxLayout(panel)
        root.setContentsMargins(10, 10, 10, 10)
        intro = QLabel('Organize mapas cronologicamente e exporte quadros de mesma extensão e SRC. '
                       'As abas possuem sequências independentes. O GIF não é georreferenciado.')
        intro.setWordWrap(True)
        root.addWidget(intro)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._raster_tab(), 'Raster')
        self.tabs.addTab(self._vector_tab(), 'Vetorial')
        self.tabs.addTab(self._mixed_tab(), 'Misto')
        self.tabs.currentChanged.connect(self._switch_mode)
        root.addWidget(self.tabs)

        sequence = QGroupBox('1. Sequência de quadros da aba selecionada')
        sf = QVBoxLayout(sequence)
        self.listbox = QListWidget()
        self.listbox.setAlternatingRowColors(True)
        self.listbox.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listbox.setMinimumHeight(115)
        sf.addWidget(self.listbox)
        controls = QHBoxLayout()
        for label, callback in (
            ('Remover', self._remove), ('Subir', lambda: self._move(-1)),
            ('Descer', lambda: self._move(1)), ('Editar data…', self._edit_date),
            ('Ordenar por data', self._sort),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            controls.addWidget(button)
        sf.addLayout(controls)
        root.addWidget(sequence)

        options = QGroupBox('2. Dimensões e composição')
        of = QFormLayout(options)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(200, 1600)
        self.width_spin.setValue(800)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(150, 1200)
        self.height_spin.setValue(450)
        row = QHBoxLayout()
        for widget in (QLabel('Largura:'), self.width_spin, QLabel('Altura:'), self.height_spin):
            row.addWidget(widget)
        row.addStretch(1)
        of.addRow('Pixels por quadro:', row)
        self.delay = QSpinBox()
        self.delay.setRange(20, 10000)
        self.delay.setSingleStep(100)
        self.delay.setValue(1000)
        self.delay.setSuffix(' ms / quadro')
        of.addRow('Duração:', self.delay)
        self.label_date = QCheckBox('Exibir data/período sobre o mapa')
        self.label_date.setChecked(True)
        self.label_name = QCheckBox('Exibir nome das camadas')
        self.label_legend = QCheckBox('Exibir legenda temática (até 10 categorias)')
        for box in (self.label_date, self.label_name, self.label_legend):
            of.addRow('', box)
        note = QLabel('Simbologia e rótulos são renderizados pelo QGIS. A paleta GIF preserva '
                      'até 256 cores; cenas mais complexas são quantizadas. PNGs mantêm as cores.')
        note.setWordWrap(True)
        of.addRow('', note)
        root.addWidget(options)

        output = QGroupBox('3. Saídas e prévia')
        fo = QFormLayout(output)
        path_row = QHBoxLayout()
        self.output = QLineEdit()
        self.output.setPlaceholderText('Sequencia_Temporal.gif')
        path_row.addWidget(self.output, 1)
        browse = QPushButton('Salvar como…')
        browse.clicked.connect(self._save_as)
        path_row.addWidget(browse)
        fo.addRow('GIF animado:', path_row)
        self.export_png = QCheckBox('Exportar também os quadros individuais em PNG')
        fo.addRow('', self.export_png)
        png_row = QHBoxLayout()
        self.png_directory = QLineEdit()
        self.png_directory.setPlaceholderText('Automático: pasta ao lado do GIF')
        png_row.addWidget(self.png_directory, 1)
        png_browse = QPushButton('Pasta…')
        png_browse.clicked.connect(self._choose_png_folder)
        png_row.addWidget(png_browse)
        fo.addRow('Pasta dos PNGs:', png_row)
        self.preview = QLabel('A prévia será exibida após a exportação.')
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(115)
        self.preview.setStyleSheet('border: 1px solid palette(mid);')
        fo.addRow('Prévia:', self.preview)
        root.addWidget(output)

        bottom = QHBoxLayout()
        self.status = QLabel('Adicione pelo menos dois quadros.')
        self.status.setWordWrap(True)
        bottom.addWidget(self.status, 1)
        self.run_button = QPushButton('Gerar GIF')
        self.run_button.clicked.connect(self._run)
        bottom.addWidget(self.run_button)
        self.close_button = QPushButton('Fechar')
        self.close_button.clicked.connect(self.close)
        bottom.addWidget(self.close_button)
        outer.addLayout(bottom)

    @staticmethod
    def _selector(filter_type):
        combo = QgsMapLayerComboBox()
        combo.setAllowEmptyLayer(True)
        combo.setFilters(filter_type)
        return combo

    def _raster_tab(self):
        page = QWidget()
        layout = QFormLayout(page)
        self.selected = self._selector(Qgis.LayerFilter.RasterLayer)
        layout.addRow('Camada raster:', self.selected)
        row = QHBoxLayout()
        for label, callback in (
            ('Adicionar', self._add_selected),
            ('Adicionar várias do QGIS…', self._add_multiple),
            ('Adicionar arquivos…', self._add_files),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            row.addWidget(button)
        layout.addRow('', row)
        return page

    def _vector_tab(self):
        page = QWidget()
        layout = QFormLayout(page)
        self.vector_selected = self._selector(Qgis.LayerFilter.VectorLayer)
        layout.addRow('Camada vetorial:', self.vector_selected)
        row = QHBoxLayout()
        for label, callback in (
            ('Adicionar', self._add_vector_selected),
            ('Adicionar várias do QGIS…', self._add_vector_multiple),
            ('Adicionar arquivos…', self._add_vector_files),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            row.addWidget(button)
        layout.addRow('', row)
        self.vector_field = QComboBox()
        layout.addRow('Campo temporal:', self.vector_field)
        self.vector_selected.layerChanged.connect(
            lambda *_: self._update_fields(self.vector_selected, self.vector_field))
        self._update_fields(self.vector_selected, self.vector_field)
        self.vector_cumulative = QCheckBox('Mostrar feições de todos os períodos anteriores (acumulativo)')
        layout.addRow('', self.vector_cumulative)
        temporal_button = QPushButton('Gerar quadros por valores do campo temporal')
        temporal_button.clicked.connect(self._add_vector_temporal)
        layout.addRow('', temporal_button)
        explanation = QLabel('A opção temporal cria quadros a partir de uma única camada vetorial, '
                             'sem alterar a camada original ou seus filtros no projeto.')
        explanation.setWordWrap(True)
        layout.addRow('', explanation)
        return page

    def _mixed_tab(self):
        page = QWidget()
        layout = QFormLayout(page)
        self.mixed_raster = self._selector(Qgis.LayerFilter.RasterLayer)
        self.mixed_vector = self._selector(Qgis.LayerFilter.VectorLayer)
        layout.addRow('Raster de fundo:', self.mixed_raster)
        layout.addRow('Vetor sobreposto:', self.mixed_vector)
        add_frame = QPushButton('Adicionar quadro misto (raster + vetor)')
        add_frame.clicked.connect(self._add_mixed)
        layout.addRow('', add_frame)
        self.mixed_field = QComboBox()
        layout.addRow('Campo temporal do vetor:', self.mixed_field)
        self.mixed_vector.layerChanged.connect(
            lambda *_: self._update_fields(self.mixed_vector, self.mixed_field))
        self._update_fields(self.mixed_vector, self.mixed_field)
        self.mixed_cumulative = QCheckBox('Manter vetores dos períodos anteriores (acumulativo)')
        layout.addRow('', self.mixed_cumulative)
        temporal_button = QPushButton('Gerar quadros pelo campo temporal + fundo raster fixo')
        temporal_button.clicked.connect(self._add_mixed_temporal)
        layout.addRow('', temporal_button)
        explanation = QLabel('Quadros mistos sobrepõem o vetor ao raster. É possível construir '
                             'uma série manual com diferentes pares ou usar um raster constante '
                             'e um vetor filtrado por data.')
        explanation.setWordWrap(True)
        layout.addRow('', explanation)
        return page

    def _mode(self):
        return self.MODES[self.tabs.currentIndex()]

    def _switch_mode(self, index):
        self.entries = self._mode_entries[self.MODES[index]]
        self._refresh()

    def _add_entry(self, layers, date='', temporal=None):
        if not layers or any(not layer or not layer.isValid() for layer in layers):
            QMessageBox.warning(self, 'Sequenciador', 'Selecione camadas válidas.')
            return
        if len(self.entries) >= 120:
            QMessageBox.warning(self, 'Sequenciador', 'Limite de 120 quadros por sequência.')
            return
        entry = {'layer': layers[0], 'layers': list(layers), 'date': date}
        if temporal is not None:
            entry['temporal'] = temporal
        self.entries.append(entry)
        self._refresh()

    def _add(self, layer):
        """Compatibilidade com o sequenciador raster anterior."""
        if not isinstance(layer, QgsRasterLayer) or not layer.isValid():
            QMessageBox.warning(self, 'Sequenciador', 'Selecione um mapa raster válido.')
            return
        self._add_entry([layer], extract_year(layer.name()))

    def _add_selected(self):
        layer = self.selected.currentLayer()
        if layer is not None:
            self._add(layer)
        else:
            QMessageBox.warning(self, 'Sequenciador', 'Selecione uma camada raster.')

    def _add_multiple(self):
        for layer in choose_project_layers(self, 'raster', 'Adicionar rasters à sequência'):
            self._add(layer)

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Selecionar mapas raster', '',
            'Rasters (*.tif *.tiff *.vrt *.png *.jpg *.jpeg);;Todos (*.*)')
        for path in paths:
            layer = QgsRasterLayer(path, Path(path).stem, 'gdal')
            if layer.isValid():
                self.imported_layers.append(layer)
                self._add(layer)
            else:
                QMessageBox.warning(self, 'Arquivo raster inválido', path)

    def _add_vector(self, layer):
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            QMessageBox.warning(self, 'Sequenciador', 'Selecione um vetor válido.')
            return
        self._add_entry([layer], extract_year(layer.name()))

    def _add_vector_selected(self):
        layer = self.vector_selected.currentLayer()
        if layer is None:
            QMessageBox.warning(self, 'Sequenciador', 'Selecione um vetor.')
        else:
            self._add_vector(layer)

    def _add_vector_multiple(self):
        for layer in choose_project_layers(self, 'vector', 'Adicionar vetores à sequência'):
            self._add_vector(layer)

    def _add_vector_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Selecionar dados vetoriais', '',
            'Vetores (*.gpkg *.geojson *.json *.shp *.kml);;Todos (*.*)')
        for path in paths:
            layer = QgsVectorLayer(path, Path(path).stem, 'ogr')
            if layer.isValid():
                self.imported_layers.append(layer)
                self._add_vector(layer)
            else:
                QMessageBox.warning(self, 'Arquivo vetorial inválido', path)

    @staticmethod
    def _update_fields(layer_combo, field_combo):
        field_combo.clear()
        layer = layer_combo.currentLayer()
        if isinstance(layer, QgsVectorLayer) and layer.isValid():
            for field in layer.fields():
                field_combo.addItem(field.name())
            for index in range(field_combo.count()):
                if field_combo.itemText(index).lower() in ('ano', 'year', 'data', 'date', 'periodo', 'período'):
                    field_combo.setCurrentIndex(index)
                    break

    def _add_mixed(self):
        raster, vector = self.mixed_raster.currentLayer(), self.mixed_vector.currentLayer()
        if not isinstance(raster, QgsRasterLayer) or not raster.isValid():
            QMessageBox.warning(self, 'Sequenciador', 'Selecione um raster de fundo válido.')
            return
        if not isinstance(vector, QgsVectorLayer) or not vector.isValid():
            QMessageBox.warning(self, 'Sequenciador', 'Selecione um vetor válido.')
            return
        self._add_entry([vector, raster], extract_year(vector.name()) or extract_year(raster.name()))

    def _add_temporal(self, source, field_combo, cumulative, background=()):
        if not isinstance(source, QgsVectorLayer) or not source.isValid():
            QMessageBox.warning(self, 'Sequenciador', 'Selecione uma camada vetorial válida.')
            return
        field = field_combo.currentText()
        if not field or source.fields().indexFromName(field) < 0:
            QMessageBox.warning(self, 'Sequenciador', 'Selecione um campo temporal válido.')
            return
        try:
            # Limite para evitar leitura ilimitada de fontes gigantes em uma ação da GUI.
            values = []
            for index, feature in enumerate(source.getFeatures(QgsFeatureRequest().setFlags(
                    Qgis.FeatureRequestFlag.NoGeometry))):
                if index >= 200_000:
                    raise ValueError('Mais de 200 mil feições: recorte a camada antes de gerar quadros.')
                values.append(feature[field])
            frames = temporal_frames(source, field, values, cumulative,
                                     base_layers=background, max_frames=120)
            if len(self.entries) + len(frames) > 120:
                raise ValueError('A sequência ultrapassaria 120 quadros.')
            self.entries.extend(frames)
            self._refresh()
        except Exception as exc:
            QMessageBox.warning(self, 'Sequenciador — campo temporal', str(exc))

    def _add_vector_temporal(self):
        self._add_temporal(self.vector_selected.currentLayer(), self.vector_field,
                           self.vector_cumulative.isChecked())

    def _add_mixed_temporal(self):
        raster = self.mixed_raster.currentLayer()
        if not isinstance(raster, QgsRasterLayer) or not raster.isValid():
            QMessageBox.warning(self, 'Sequenciador', 'Selecione um raster de fundo válido.')
            return
        self._add_temporal(self.mixed_vector.currentLayer(), self.mixed_field,
                           self.mixed_cumulative.isChecked(), background=(raster,))

    def _refresh(self):
        self.listbox.clear()
        for index, entry in enumerate(self.entries, 1):
            names = ' sobre '.join(layer.name() for layer in entry.get('layers', (entry['layer'],)))
            period = entry['date'] or 'Sem data'
            suffix = ' [campo temporal]' if entry.get('temporal') else ''
            self.listbox.addItem(f'{index:02d}.  {period} — {names}{suffix}')
        self.status.setText(f'{len(self.entries)} quadros na aba {self.tabs.tabText(self.tabs.currentIndex())}.')

    def _remove(self):
        for index in sorted((self.listbox.row(item) for item in self.listbox.selectedItems()), reverse=True):
            del self.entries[index]
        self._refresh()

    def _move(self, delta):
        row = self.listbox.currentRow()
        dest = row + delta
        if row < 0 or not 0 <= dest < len(self.entries):
            return
        self.entries[row], self.entries[dest] = self.entries[dest], self.entries[row]
        self._refresh()
        self.listbox.setCurrentRow(dest)

    def _edit_date(self):
        row = self.listbox.currentRow()
        if row < 0:
            return
        text, ok = QInputDialog.getText(self, 'Período do quadro', 'Ano ou data:',
                                        text=self.entries[row]['date'])
        if ok:
            self.entries[row]['date'] = text.strip()[:40]
            self._refresh()
            self.listbox.setCurrentRow(row)

    def _sort(self):
        self.entries.sort(key=lambda e: (not bool(e['date']), e['date']))
        self._refresh()

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, 'Salvar animação GIF', self.output.text() or 'Sequencia_Temporal.gif',
            'GIF animado (*.gif)')
        if path:
            self.output.setText(path if path.lower().endswith('.gif') else path + '.gif')

    def _choose_png_folder(self):
        path = QFileDialog.getExistingDirectory(self, 'Pasta para quadros PNG',
                                                self.png_directory.text() or '')
        if path:
            self.png_directory.setText(path)
            self.export_png.setChecked(True)

    def _shared_extent(self, crs):
        extent = None
        for entry in self.entries:
            for layer in entry.get('layers', [entry['layer']]):
                if not layer.isValid() or not layer.crs().isValid():
                    raise ValueError('Uma camada não é válida ou não possui SRC definido.')
                bounds = QgsRectangle(layer.extent())
                if layer.crs() != crs:
                    bounds = QgsCoordinateTransform(layer.crs(), crs,
                                    QgsProject.instance()).transformBoundingBox(bounds)
                if extent is None:
                    extent = bounds
                else:
                    extent.combineExtentWith(bounds)
        if extent is None:
            raise ValueError('A extensão espacial dos mapas é inválida.')
        # Uma camada pontual ou linear pode ter extensão sem largura/altura.
        if extent.width() <= 0 or extent.height() <= 0:
            pad = max(extent.width(), extent.height(), 1.0) / 20
            extent.grow(pad)
        return extent

    @staticmethod
    def _image_rgb(img):
        converted = img.convertToFormat(QImage.Format.Format_RGB888)
        width = converted.width()
        stride = converted.bytesPerLine()
        pointer = converted.constBits()
        try:
            raw = pointer.asstring(converted.sizeInBytes())
        except AttributeError:
            pointer.setsize(converted.sizeInBytes())
            raw = bytes(pointer)
        size = width * 3
        return b''.join(raw[row * stride:row * stride + size]
                        for row in range(converted.height()))

    @staticmethod
    def _temporal_layer(entry):
        spec = entry['temporal']
        source, field, values = spec['source'], spec['field'], spec['values']
        column = QgsExpression.quotedColumnRef(field)
        literals = [QgsExpression.quotedValue(value) for value in values]
        expression = f'{column} IN ({", ".join(literals)})'
        filtered = source.materialize(QgsFeatureRequest().setFilterExpression(expression))
        if not filtered or not filtered.isValid():
            raise ValueError('Não foi possível filtrar a camada vetorial por período.')
        if source.renderer() is not None:
            filtered.setRenderer(source.renderer().clone())
        if source.labeling() is not None:
            filtered.setLabeling(source.labeling().clone())
            filtered.setLabelsEnabled(source.labelsEnabled())
        filtered.setName(source.name())
        return filtered

    @staticmethod
    def _legend_entries(layer):
        if not hasattr(layer, 'renderer') or layer.renderer() is None:
            return []
        renderer = layer.renderer()
        if hasattr(renderer, 'categories'):
            items = renderer.categories()
        elif hasattr(renderer, 'ranges'):
            items = renderer.ranges()
        elif hasattr(renderer, 'classes'):
            items = renderer.classes()
        else:
            items = []
        entries = []
        for item in list(items)[:10]:
            label = getattr(item, 'label', None)
            label = label() if callable(label) else label
            symbol = getattr(item, 'symbol', None)
            symbol = symbol() if callable(symbol) else symbol
            color = getattr(item, 'color', None)
            color = color() if callable(color) else color
            if symbol is not None:
                color = symbol.color()
            if color is not None:
                entries.append((str(label or 'Classe'), QColor(color)))
        if not entries and hasattr(renderer, 'symbol'):
            symbol = renderer.symbol()
            if symbol:
                entries.append((layer.name(), symbol.color()))
        return entries

    def _render_image(self, entry, crs, extent, width, height):
        layers = list(entry.get('layers', (entry['layer'],)))
        if entry.get('temporal'):
            # Cópia independente: nunca alterar subsetString na camada do usuário.
            layers[0] = self._temporal_layer(entry)
        settings = QgsMapSettings()
        settings.setLayers(layers)  # ordem: vetor por cima, raster ao fundo
        settings.setDestinationCrs(crs)
        settings.setExtent(extent)
        settings.setOutputSize(QSize(width, height))
        settings.setBackgroundColor(QColor('white'))
        job = QgsMapRendererSequentialJob(settings)
        job.start()
        job.waitForFinished()
        image = job.renderedImage()
        if image.isNull():
            raise RuntimeError('O QGIS não conseguiu renderizar o quadro.')
        lines = []
        if self.label_date.isChecked() and entry['date']:
            lines.append(entry['date'])
        if self.label_name.isChecked():
            lines.append(' + '.join(layer.name() for layer in layers)[:80])
        legend = []
        if self.label_legend.isChecked():
            # Preferir classes da camada vetorial na composição mista.
            for layer in layers:
                legend = self._legend_entries(layer)
                if legend:
                    break
        if lines or legend:
            painter = QPainter(image)
            try:
                font = QFont()
                font.setPointSize(max(10, min(28, width // 45)))
                font.setBold(True)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                margin = 12
                lh = metrics.height() + 3
                if lines:
                    bw = min(width-16, max(metrics.horizontalAdvance(line) for line in lines) + margin*2)
                    bh = len(lines)*lh + margin
                    painter.fillRect(QRect(8, 8, bw, bh), QColor(255, 255, 255, 220))
                    painter.setPen(QColor('#202020'))
                    for i, line in enumerate(lines):
                        painter.drawText(8+margin, 8+margin//2+metrics.ascent()+i*lh, line)
                if legend:
                    legend_font = QFont(font)
                    legend_font.setBold(False)
                    legend_font.setPointSize(max(8, font.pointSize()-2))
                    painter.setFont(legend_font)
                    metrics = painter.fontMetrics()
                    lh = max(16, metrics.height()+2)
                    bw = min(width//2, 285)
                    bh = 12 + (len(legend)+1)*lh
                    bx = max(0, width-bw-10)
                    by = max(0, height-bh-10)
                    painter.fillRect(QRect(bx, by, bw, bh), QColor(255, 255, 255, 235))
                    painter.setPen(QColor('#202020'))
                    painter.drawText(bx+8, by+metrics.ascent()+4, 'Legenda')
                    for i, (name, color) in enumerate(legend):
                        cy = by+8+(i+1)*lh
                        painter.fillRect(QRect(bx+8, cy-8, 11, 11), color)
                        painter.drawText(bx+25, cy+1, name[:28])
            finally:
                painter.end()
        return image

    def _render(self, entry, crs, extent, width, height):
        return self._image_rgb(self._render_image(entry, crs, extent, width, height))

    def _run(self):
        if self._busy:
            return
        if len(self.entries) < 2:
            QMessageBox.warning(self, 'Sequenciador', 'Adicione pelo menos dois quadros.')
            return
        path = self.output.text().strip()
        if not path or not path.lower().endswith('.gif'):
            QMessageBox.warning(self, 'Sequenciador', 'Selecione um destino .gif.')
            return
        if any(not layer.isValid() for entry in self.entries
               for layer in entry.get('layers', [entry['layer']])):
            QMessageBox.warning(self, 'Sequenciador', 'Há uma camada inválida na sequência.')
            return
        width, height = self.width_spin.value(), self.height_spin.value()
        if width*height*len(self.entries) > 30_000_000:
            QMessageBox.warning(self, 'Sequenciador',
                'A sequência excede 30 milhões de pixels cumulativos. '
                'Reduza as dimensões ou divida a sequência.')
            return
        png_folder = None
        if self.export_png.isChecked():
            png_folder = Path(self.png_directory.text().strip() or
                              str(Path(path).with_suffix('')) + '_quadros_png')
            if png_folder.is_file():
                QMessageBox.warning(self, 'Sequenciador', 'O destino dos PNGs não é uma pasta.')
                return
        self._busy = True
        self.run_button.setEnabled(False)
        self.close_button.setEnabled(False)
        progress = QProgressDialog('Renderizando quadros…', 'Cancelar', 0, len(self.entries), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        frames = []
        png_paths = []
        try:
            crs = QgsProject.instance().crs()
            if not crs.isValid():
                crs = self.entries[0]['layer'].crs()
            if not crs.isValid():
                raise ValueError('Defina um SRC válido para o projeto ou para os mapas.')
            extent = self._shared_extent(crs)
            from qgis.PyQt.QtWidgets import QApplication
            for i, entry in enumerate(self.entries):
                QApplication.processEvents()
                if progress.wasCanceled():
                    raise InterruptedError('Exportação cancelada.')
                image = self._render_image(entry, crs, extent, width, height)
                frames.append(self._image_rgb(image))
                if png_folder is not None:
                    png_folder.mkdir(parents=True, exist_ok=True)
                    target = png_folder / safe_png_name(i+1, entry['date'])
                    staging = target.with_name(target.name + '.part')
                    if not image.save(str(staging), 'PNG'):
                        raise OSError('Não foi possível gravar o quadro PNG: '+str(target))
                    staging.replace(target)
                    png_paths.append(target)
                progress.setValue(i+1)
            if progress.wasCanceled():
                raise InterruptedError('Exportação cancelada.')
            if self._movie:
                self._movie.stop()
                self.preview.clear()
                self._movie = None
            result = encode_gif(path, frames, width, height,
                                delay_cs=max(2, self.delay.value()//10))
            self._movie = QMovie(result['path'])
            self._movie.setScaledSize(QSize(min(400, width), min(225, height)))
            self.preview.setMovie(self._movie)
            self._movie.start()
            note = 'com quantização GIF' if result['palette_quantized'] else 'com cores preservadas'
            self.status.setText(f'GIF criado com {len(frames)} quadros ({note}); '
                                f'{len(png_paths)} PNGs individuais.')
            QMessageBox.information(self, 'Sequenciador de Mapas',
                'GIF salvo em:\n'+str(result['path'])+'\n'+
                (f'Quadros PNG: {png_folder}\n' if png_folder is not None else '')+
                ('GIF quantizado para 256 cores.' if result['palette_quantized']
                 else 'Paleta GIF preservada.'))
        except InterruptedError:
            self.status.setText(f'Exportação cancelada. {len(png_paths)} PNGs podem permanecer '
                                'na pasta de destino; dados do projeto preservados.')
        except Exception as exc:
            self.status.setText('Falha na exportação; dados do projeto preservados.')
            QMessageBox.critical(self, 'Sequenciador de Mapas — erro', str(exc))
        finally:
            progress.close()
            self._busy = False
            self.run_button.setEnabled(True)
            self.close_button.setEnabled(True)

    def closeEvent(self, event):
        if self._busy:
            event.ignore()
        else:
            if self._movie:
                self._movie.stop()
            super().closeEvent(event)
