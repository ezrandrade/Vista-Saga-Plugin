"""Convenções visuais compartilhadas entre os módulos (QGIS 4.x / Qt6).

Uma saída *temporária* é armazenada no diretório temporário da sessão, e
carregada no projeto QGIS após o cálculo. Para rasteres e GeoPackages volumosos
não se utiliza um vetor inteiramente em RAM: isso evita esgotar memória.
O usuário deve exportar/salvar a camada para persistência.
"""
from pathlib import Path
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
    layers = sorted((lyr for lyr in QgsProject.instance().mapLayers().values()
                     if isinstance(lyr, expected) and lyr.isValid()),
                    key=lambda ly: ly.name().casefold())
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.resize(600, 430)
    body = QVBoxLayout(dlg)
    body.addWidget(QLabel('Selecione várias camadas com Ctrl/Shift ou use Selecionar todas.'))
    items = QListWidget()
    items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    for layer in layers:
        item = QListWidgetItem(layer.name())
        item.setData(Qt.ItemDataRole.UserRole, layer.id())
        items.addItem(item)
    body.addWidget(items)
    actions = QHBoxLayout()
    select_all = QPushButton('Selecionar todas')
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
    checkbox = QCheckBox(label)
    checkbox.setChecked(True)
    checkbox.setToolTip(
        'O QGIS abrirá o resultado automaticamente. O arquivo e os relatórios ficam '\
        'no armazenamento temporário da sessão; exporte o resultado antes de fechar o QGIS.')
    layout.addWidget(checkbox)
    path_input.setEnabled(False)
    checkbox.toggled.connect(lambda enabled: path_input.setEnabled(not enabled))
    return checkbox


def output_destination(temporary_checked, path_value, prefix, suffix):
    return temporary_destination(prefix, suffix) if temporary_checked else path_value.strip()
