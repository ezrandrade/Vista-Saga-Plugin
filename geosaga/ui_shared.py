"""Convenções visuais compartilhadas entre os módulos (QGIS 4.x / Qt6).

Uma saída *temporária* é armazenada no diretório temporário da sessão, e
carregada no projeto QGIS após o cálculo. Para rasteres e GeoPackages volumosos
não se utiliza um vetor inteiramente em RAM: isso evita esgotar memória.
O usuário deve exportar/salvar a camada para persistência.
"""
from .i18n import tr

from pathlib import Path
import os
import tempfile


def temporary_destination(prefix, suffix):
    """Cria caminho único para o resultado e relatórios associados.

    Não mantém arquivos temporários em diretórios de entrada nem sobrescreve
    resultados de análises anteriores.
    """
    safe = ''.join(c if c.isalnum() or c in '-_' else '_' for c in prefix)[:48] or 'vista_saga'
    try:
        from qgis.core import QgsProcessingUtils
        return str(QgsProcessingUtils.generateTempFilename(safe + suffix))
    except (ImportError, AttributeError, RuntimeError):
        # Fallback para testes fora do QGIS; o QGIS normalmente administra
        # seu próprio diretório temporário de Processing.
        folder = Path(tempfile.mkdtemp(prefix='vista_saga_'))
        return str(folder / (safe + suffix))


def choose_project_layers(parent, layer_type, title='Selecionar camadas do QGIS'):
    """Seleção múltipla de camadas carregadas; nenhuma edição no QgsProject."""
    from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer
    from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QLabel, QListWidget,
                                    QListWidgetItem, QDialogButtonBox,
                                    QAbstractItemView, QPushButton, QHBoxLayout)
    from qgis.PyQt.QtCore import Qt
    expected = QgsRasterLayer if layer_type == 'raster' else QgsVectorLayer

    def accepted(lyr):
        if not isinstance(lyr, expected) or not lyr.isValid():
            return False
        if layer_type == 'polygon':
            from qgis.core import Qgis, QgsWkbTypes
            return QgsWkbTypes.geometryType(lyr.wkbType()) == Qgis.GeometryType.Polygon
        return True
    layers = sorted((lyr for lyr in QgsProject.instance().mapLayers().values() if accepted(lyr)),
                    key=lambda ly: ly.name().casefold())
    dlg = QDialog(parent)
    dlg.setWindowTitle(tr(title))
    dlg.resize(600, 430)
    body = QVBoxLayout(dlg)
    body.addWidget(QLabel(tr('Selecione várias camadas com Ctrl/Shift ou use Selecionar todas.')))
    items = QListWidget()
    items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    for layer in layers:
        item = QListWidgetItem(layer.name())
        item.setData(Qt.ItemDataRole.UserRole, layer.id())
        items.addItem(item)
    body.addWidget(items)
    actions = QHBoxLayout()
    select_all = QPushButton(tr('Selecionar todas'))
    select_all.clicked.connect(items.selectAll)
    actions.addWidget(select_all)
    actions.addStretch()
    body.addLayout(actions)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                               QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    body.addWidget(buttons)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return []
    selected = {i.data(Qt.ItemDataRole.UserRole) for i in items.selectedItems()}
    return [lyr for lyr in layers if lyr.id() in selected]


def attach_temporary_option(layout, path_input, label='Resultado temporário (carregar no QGIS)'):
    """Insere opção temporária; preservar o controle de saída persistente existente."""
    from qgis.PyQt.QtWidgets import QCheckBox
    checkbox = QCheckBox(tr(label))
    checkbox.setChecked(True)
    checkbox.setToolTip(
        tr('O QGIS abrirá o resultado automaticamente. O arquivo e os relatórios ficam '\
        'no armazenamento temporário da sessão; exporte o resultado antes de fechar o QGIS.'))
    layout.addWidget(checkbox)
    path_input.setEnabled(False)
    checkbox.toggled.connect(lambda enabled: path_input.setEnabled(not enabled))
    return checkbox


def output_destination(temporary_checked, path_value, prefix, suffix):
    return temporary_destination(prefix, suffix) if temporary_checked else path_value.strip()


# ---------------------------------------------------------------------------
# Padrão visual comum às guias da Avaliação (Raster e as duas vetoriais).
# Números alinhados à direita e textos à esquerda, como numa planilha: o
# alinhamento indica ao usuário se o valor é numérico.
# ---------------------------------------------------------------------------
import re as _re

_NUMBER = _re.compile(r'^\s*[+-]?(\d+([.,]\d*)?|[.,]\d+)\s*$')


def looks_numeric(value):
    """Verdadeiro para '12', '-3.5' ou '0,25'; falso para nomes de classe."""
    return bool(_NUMBER.match(str(value)))


def _number_alignment():
    from qgis.PyQt.QtCore import Qt
    return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter


def table_item(value, editable=False, numeric=None):
    """Célula de tabela; à direita quando o valor é numérico."""
    from qgis.PyQt.QtCore import Qt
    from qgis.PyQt.QtWidgets import QTableWidgetItem
    item = QTableWidgetItem(str(value))
    flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    if editable:
        flags |= Qt.ItemFlag.ItemIsEditable
    item.setFlags(flags)
    if numeric is None:
        numeric = looks_numeric(value)
    alignment = (_number_alignment() if numeric
                 else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    try:
        item.setTextAlignment(alignment)
    except TypeError:  # versões do PyQt6 que ainda exigem int
        item.setTextAlignment(int(getattr(alignment, 'value', alignment)))
    return item


def weight_spin(value, callback=None):
    from qgis.PyQt.QtWidgets import QDoubleSpinBox
    spin = QDoubleSpinBox()
    spin.setRange(0, 100)
    spin.setDecimals(2)
    # Peso 0 é inválido (todo critério precisa de peso > 0): aparece em branco,
    # para o usuário ver de imediato o que ainda falta digitar.
    spin.setSpecialValueText(' ')
    spin.setAlignment(_number_alignment())
    spin.setValue(float(value))
    if callback is not None:
        spin.valueChanged.connect(callback)
    return spin


def score_spin(scale, value=None):
    """Nota de 0 até a escala; o valor especial '—' (−1) significa 'sem nota'."""
    from qgis.PyQt.QtWidgets import QDoubleSpinBox
    spin = QDoubleSpinBox()
    spin.setRange(-1, scale)
    spin.setDecimals(2)
    spin.setSingleStep(1)
    spin.setSpecialValueText('—')
    spin.setAlignment(_number_alignment())
    spin.setValue(-1 if value is None else float(value))
    return spin


def centered_check(checked=False, tooltip=''):
    """Caixa de seleção centralizada na célula; devolve (contêiner, caixa)."""
    from qgis.PyQt.QtWidgets import QCheckBox, QHBoxLayout, QWidget
    box = QCheckBox()
    box.setChecked(bool(checked))
    if tooltip:
        box.setToolTip(tr(tooltip))
    holder = QWidget()
    row = QHBoxLayout(holder)
    row.setContentsMargins(0, 0, 0, 0)
    row.addStretch(1)
    row.addWidget(box)
    row.addStretch(1)
    return holder, box


def cell_check(table, row, column):
    from qgis.PyQt.QtWidgets import QCheckBox
    holder = table.cellWidget(row, column)
    if holder is None:
        return None
    return holder if isinstance(holder, QCheckBox) else holder.findChild(QCheckBox)


class OutputSection:
    """Seção '3. Resultado' idêntica nas três guias.

    Campo vazio: resultado temporário (camada em memória no vetor; arquivo
    temporário no raster, pois o QGIS não mantém rasters em memória).
    Campo preenchido: resultado salvo nesse arquivo. Em ambos os casos o
    resultado é carregado no QGIS.
    """

    def __init__(self, browse, placeholder, hint):
        from qgis.PyQt.QtWidgets import (QCheckBox, QGroupBox, QHBoxLayout, QLabel,
                                        QLineEdit, QPushButton, QVBoxLayout)
        self.group = QGroupBox(tr('3. Resultado'))
        layout = QVBoxLayout(self.group)
        row = QHBoxLayout()
        row.addWidget(QLabel(tr('Salvar em:')))
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(tr(placeholder))
        self.edit.setClearButtonEnabled(True)
        row.addWidget(self.edit, 1)
        browse_button = QPushButton(tr('Procurar…'))
        browse_button.clicked.connect(browse)
        row.addWidget(browse_button)
        layout.addLayout(row)
        reports = QHBoxLayout()
        self.csv_check = QCheckBox(tr('Relatório CSV (combinações, notas e áreas)'))
        self.csv_check.setChecked(True)
        self.txt_check = QCheckBox(tr('Relatório TXT (modelo Vista SAGA)'))
        self.txt_check.setChecked(True)
        reports.addWidget(self.csv_check)
        reports.addWidget(self.txt_check)
        reports.addStretch(1)
        layout.addLayout(reports)
        note = QLabel(tr(hint))
        note.setWordWrap(True)
        layout.addWidget(note)

    def path(self):
        return self.edit.text().strip()

    def is_temporary(self):
        return not self.path()


VECTOR_OUTPUT_HINT = (
    'Em branco, o resultado é carregado no QGIS como camada temporária em memória '
    '(salve-a antes de fechar o QGIS). Com um arquivo indicado, ele é salvo em disco e '
    'carregado no QGIS. Os pesos e as notas usados são gravados em '
    '*_pesos_notas.geosaga.json, que pode ser reaberto em “Abrir projeto…”. '
    'Sem arquivo indicado, relatórios e pesos ficam na pasta temporária do QGIS.')

RASTER_OUTPUT_HINT = (
    'Em branco, a carta é gravada num arquivo temporário e carregada no QGIS '
    '(o QGIS não mantém rasters em memória; salve-a antes de fechar o QGIS). Com um '
    'arquivo indicado, ela é salva em disco e carregada no QGIS. Os pesos e as notas '
    'usados são gravados em *_pesos_notas.geosaga.json, que pode ser reaberto em '
    '“Abrir projeto…”. Sem arquivo indicado, relatórios e pesos ficam na pasta '
    'temporária do QGIS.')


def materialize_in_memory(path, name):
    """Copia o GeoPackage gerado para uma camada em memória do QGIS.

    A cópia não depende do arquivo: o QGIS a trata como camada temporária
    (ícone de rascunho) e pede para salvá-la ao fechar o projeto.
    """
    from qgis.core import QgsFeatureRequest, QgsVectorLayer
    source = QgsVectorLayer(path, name, 'ogr')
    if not source.isValid():
        return None
    memory = source.materialize(QgsFeatureRequest())
    if memory is None or not memory.isValid():
        return None
    memory.setName(name)
    return memory


# ---------------------------------------------------------------------------
# Abertura de camadas vetoriais a partir de arquivos.
# ---------------------------------------------------------------------------
_LAST_DIR_KEY = 'VistaSaga/ultimaPastaVetorial'


def _file_directory(source):
    path = str(source or '').split('|', 1)[0]
    if path and os.path.isfile(path):
        return os.path.dirname(os.path.abspath(path))
    return ''


def vector_start_directory(preferred_sources=()):
    """Pasta inicial do diálogo de arquivos.

    Ordem: camadas já usadas nesta avaliação; camadas vetoriais carregadas no
    projeto QGIS (a mais recente primeiro); última pasta usada pelo plugin;
    última pasta vetorial do próprio QGIS; pasta do projeto; pasta pessoal.
    """
    for source in reversed(list(preferred_sources)):
        folder = _file_directory(source)
        if folder:
            return folder
    try:
        from qgis.core import QgsProject, QgsSettings, QgsVectorLayer
        project = QgsProject.instance()
        for layer in reversed(list(project.mapLayers().values())):
            if isinstance(layer, QgsVectorLayer) and layer.providerType() == 'ogr':
                folder = _file_directory(layer.source())
                if folder:
                    return folder
        settings = QgsSettings()
        for key in (_LAST_DIR_KEY, 'UI/lastVectorFileFilterDir'):
            folder = settings.value(key, '', type=str)
            if folder and os.path.isdir(folder):
                return folder
        if project.homePath() and os.path.isdir(project.homePath()):
            return project.homePath()
    except (ImportError, RuntimeError):
        pass
    return os.path.expanduser('~')


def remember_vector_directory(path):
    try:
        from qgis.core import QgsSettings
        QgsSettings().setValue(_LAST_DIR_KEY, os.path.dirname(os.path.abspath(path)))
    except (ImportError, RuntimeError):
        pass


VECTOR_FILE_FILTER = ('Camadas vetoriais (*.gpkg *.shp *.geojson *.json *.kml *.gml '
                      '*.sqlite *.tab *.fgb);;Todos os arquivos (*)')


def _project_layer_with_source(source):
    from qgis.core import QgsProject, QgsVectorLayer
    from .evaluation_config import same_source
    for layer in QgsProject.instance().mapLayers().values():
        if isinstance(layer, QgsVectorLayer) and layer.isValid() and same_source(layer.source(), source):
            return layer
    return None


def _polygon_sublayer_uris(path):
    """URIs das subcamadas poligonais (um GeoPackage pode ter várias)."""
    from qgis.core import Qgis, QgsProviderRegistry, QgsWkbTypes
    stem = os.path.splitext(os.path.basename(path))[0]
    try:
        details = QgsProviderRegistry.instance().querySublayers(path)
    except AttributeError:
        details = []
    found = []
    for detail in details:
        if detail.providerKey() != 'ogr' or detail.type() != Qgis.LayerType.Vector:
            continue
        if QgsWkbTypes.geometryType(detail.wkbType()) != Qgis.GeometryType.Polygon:
            continue
        found.append((detail.uri(), detail.name()))
    if not details:
        return [(path, stem)]
    if len(found) == 1:
        return [(found[0][0], stem)]
    return [(uri, f'{stem} - {name}' if name else stem) for uri, name in found]


def load_vector_source(source, name=''):
    """Reaproveita a camada já carregada no projeto ou a adiciona ao projeto."""
    from qgis.core import QgsProject, QgsVectorLayer
    existing = _project_layer_with_source(source)
    if existing is not None:
        return existing
    path = str(source).split('|', 1)[0]
    if not os.path.isfile(path):
        return None
    layer = QgsVectorLayer(source, name or os.path.splitext(os.path.basename(path))[0], 'ogr')
    if not layer.isValid():
        return None
    QgsProject.instance().addMapLayer(layer)
    return layer


def open_polygon_files(parent, title, start_dir, multiple=True):
    """Diálogo de arquivos -> camadas poligonais válidas, já no projeto QGIS.

    Devolve (camadas, avisos). Camadas já carregadas não são duplicadas.
    """
    from qgis.PyQt.QtWidgets import QFileDialog
    from qgis.core import QgsWkbTypes, Qgis
    if multiple:
        paths, _ = QFileDialog.getOpenFileNames(parent, tr(title), start_dir, tr(VECTOR_FILE_FILTER))
    else:
        path, _ = QFileDialog.getOpenFileName(parent, tr(title), start_dir, tr(VECTOR_FILE_FILTER))
        paths = [path] if path else []
    layers, warnings = [], []
    for path in paths:
        remember_vector_directory(path)
        uris = _polygon_sublayer_uris(path)
        if not uris:
            warnings.append(tr('{name}: nenhuma camada de polígonos.').format(name=os.path.basename(path)))
            continue
        for uri, name in uris:
            layer = load_vector_source(uri, name)
            if layer is None:
                warnings.append(tr('{name}: não foi possível abrir a camada.').format(name=name))
            elif QgsWkbTypes.geometryType(layer.wkbType()) != Qgis.GeometryType.Polygon:
                warnings.append(tr('{name}: a camada não é de polígonos.').format(name=layer.name()))
            else:
                layers.append(layer)
    return layers, warnings


# ---------------------------------------------------------------------------
# Navegação por TAB entre os campos numéricos de uma coluna (pesos ou notas).
# ---------------------------------------------------------------------------
def install_column_tab_navigation(table, column):
    """TAB/Shift+TAB saltam entre as caixas da coluna, com o valor já selecionado.

    Caixas desativadas (classes em “Não avaliar”) são puladas. Na primeira e na
    última linha, o TAB segue a ordem normal do formulário, para não prender
    quem navega só pelo teclado. Devolve o filtro: instale-o em cada caixa com
    ``spin.installEventFilter(filtro)``.
    """
    from qgis.PyQt.QtCore import QEvent, QObject, Qt, QTimer

    class ColumnTabFilter(QObject):
        def eventFilter(self, obj, event):
            kind = event.type()
            if kind == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                back = (event.key() == Qt.Key.Key_Backtab
                        or bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
                return self._jump(obj, -1 if back else 1)
            if kind == QEvent.Type.FocusIn and event.reason() in (
                    Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason):
                QTimer.singleShot(0, obj.selectAll)
            return False

        def _jump(self, current, step):
            rows = table.rowCount()
            row = next((r for r in range(rows) if table.cellWidget(r, column) is current), None)
            if row is None:
                return False
            target = row + step
            while 0 <= target < rows:
                spin = table.cellWidget(target, column)
                if spin is not None and spin.isEnabled():
                    table.scrollTo(table.model().index(target, column))
                    spin.setFocus(Qt.FocusReason.TabFocusReason)
                    QTimer.singleShot(0, spin.selectAll)
                    return True
                target += step
            return False

    return ColumnTabFilter(table)


# ---------------------------------------------------------------------------
# Ordenação das tabelas de classes pelo cabeçalho.
# ---------------------------------------------------------------------------
def class_sort_key(key):
    """Classes numéricas em ordem numérica (2 antes de 11); textos depois, A→Z."""
    try:
        return (0, float(str(key).replace(',', '.')), '')
    except (TypeError, ValueError, OverflowError):
        return (1, 0.0, str(key).casefold())


class HeaderSort:
    """Estado da ordenação: clicar de novo na mesma coluna inverte a ordem.

    As tabelas são reconstruídas na ordem pedida, em vez de usar a ordenação
    nativa do QTableWidget, que compara texto (colocaria “11” antes de “2”)
    e não conhece as caixas de nota e de “Não avaliar” dentro das células.
    """

    def __init__(self, table, sortable_columns, on_change):
        from qgis.PyQt.QtCore import Qt
        self.table = table
        self.columns = set(sortable_columns)
        self.column = 0
        self.descending = False
        self._on_change = on_change
        header = table.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        header.sectionClicked.connect(self._clicked)

    def _clicked(self, column):
        from qgis.PyQt.QtCore import Qt
        if column not in self.columns:
            self.table.horizontalHeader().setSortIndicator(
                self.column, Qt.SortOrder.DescendingOrder if self.descending else Qt.SortOrder.AscendingOrder)
            return
        self.descending = (not self.descending) if column == self.column else False
        self.column = column
        self.table.horizontalHeader().setSortIndicator(
            column, Qt.SortOrder.DescendingOrder if self.descending else Qt.SortOrder.AscendingOrder)
        self._on_change()

    def order(self, keys, key_functions):
        """Ordena `keys` com a função da coluna ativa (classe por padrão)."""
        function = key_functions.get(self.column, class_sort_key)
        return sorted(keys, key=function, reverse=self.descending)


def use_tab_background(scroll):
    """Fundo padrão da guia do QGIS numa área com rolagem.

    QScrollArea.setWidget liga o preenchimento do fundo com a cor da janela
    (cinza), o que destoa das guias montadas sem rolagem. Chamar logo após
    ``setWidget``: desligado o preenchimento, aparece o fundo da guia.
    """
    scroll.viewport().setAutoFillBackground(False)
    widget = scroll.widget()
    if widget is not None:
        widget.setAutoFillBackground(False)
