"""Inventário de dicas (1.6.0): lista botões, campos, caixas de marcar e listas sem dica num módulo.

Uso, na raiz do repositório (QGIS real, sem interface):
    QT_QPA_PLATFORM=offscreen python tests/qgis/tooltip_inventory.py                # módulos concluídos
    QT_QPA_PLATFORM=offscreen python tests/qgis/tooltip_inventory.py evaluation_dialog EvaluationDialog
    QT_QPA_PLATFORM=offscreen python tests/qgis/tooltip_inventory.py --lista dicas.md monitoring_dialog MonitoringDialog
O "--lista" grava, em português, uma tabela com o texto e a dica de cada widget (para revisão do autor).
Sai com código 1 se houver widget sem dica. Escopo (decisão do autor, 1.6.0): botões, campos, caixas de
marcar e listas; sem cabeçalhos de tabela nem abas. Ignora as partes internas de outros widgets (o campo de texto
de uma lista suspensa ou de um campo numérico) e o conteúdo dos diálogos de arquivo.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from qgis.core import QgsApplication  # noqa: E402

app = QgsApplication([], True)
app.initQgis()

from qgis.PyQt.QtWidgets import (  # noqa: E402
    QAbstractButton, QAbstractSpinBox, QComboBox, QLineEdit, QListWidget, QTabBar, QTabWidget, QWidget,
)

KINDS = (QAbstractButton, QLineEdit, QComboBox, QAbstractSpinBox, QListWidget)


# Peças internas do Qt/QGIS: botão de canto da tabela, botão de limpar do campo de texto, setas das abas.
INTERNAL_CLASSES = ('QTableCornerButton', 'QLineEditIconButton', 'QTabBar', 'QgsFilterLineEdit')


def _internal(widget):
    if widget.metaObject().className() in INTERNAL_CLASSES:
        return True
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, (QComboBox, QAbstractSpinBox, QTabBar)) or parent.inherits('QgsFileWidget') \
                or parent.inherits('QgsProjectionSelectionWidget'):
            return True
        parent = parent.parentWidget()
    return False


def _names(dialog):
    """{id(widget): nome do atributo} no diálogo e nos formulários embutidos (para identificar o widget)."""
    names = {}
    for owner in [dialog] + [w for w in dialog.findChildren(QWidget) if hasattr(w, '__dict__')]:
        for attr, value in vars(owner).items():
            if isinstance(value, QWidget):
                names.setdefault(id(value), attr)
    return names


def _label(widget):
    """Rótulo do QFormLayout em que o widget está, se houver."""
    from qgis.PyQt.QtWidgets import QFormLayout
    parent = widget.parentWidget()
    if parent is None or parent.layout() is None:
        return ''
    stack = [parent.layout()]
    while stack:
        layout = stack.pop()
        if isinstance(layout, QFormLayout):
            for row in range(layout.rowCount()):
                label_item = layout.itemAt(row, QFormLayout.ItemRole.LabelRole)
                field_item = layout.itemAt(row, QFormLayout.ItemRole.FieldRole)
                if field_item is None or label_item is None or label_item.widget() is None:
                    continue
                inner = field_item.widget() or field_item.layout()
                if inner is widget or (field_item.layout() is not None and
                                       field_item.layout().indexOf(widget) >= 0):
                    return label_item.widget().text()
        for i in range(layout.count()):
            if layout.itemAt(i).layout() is not None:
                stack.append(layout.itemAt(i).layout())
    return ''


def missing(dialog):
    names = _names(dialog)
    found = []
    for kind in KINDS:
        for widget in dialog.findChildren(kind):
            if _internal(widget) or widget.toolTip().strip():
                continue
            label = getattr(widget, 'text', lambda: '')() if isinstance(widget, QAbstractButton) else ''
            found.append((type(widget).__name__, names.get(id(widget), ''), _label(widget), label,
                          getattr(widget, 'placeholderText', lambda: '')()))
    return found


# Módulos com dicas completas (1.6.0): todos os sete.
DONE = [('signature_dialog', 'SignatureDialog'), ('evaluation_dialog', 'EvaluationDialog'),
        ('monitoring_dialog', 'MonitoringDialog'), ('voronoi_dialog', 'VoronoiDialog'),
        ('combination_dialog', 'CombinationDialog'), ('rs2_dialog', 'RS2ConverterDialog'),
        ('image_sequence_dialog', 'ImageSequenceDialog')]


def _open(module, cls):
    import importlib
    dialog_class = getattr(importlib.import_module(f'geosaga.{module}'), cls)
    dialog = dialog_class(None)
    dialog.show()
    app.processEvents()
    # Guias montadas sob demanda (ex.: as vetoriais da Avaliação): abrir todas antes de contar.
    for _round in range(2):
        for tabs in dialog.findChildren(QTabWidget) + dialog.findChildren(QTabBar):
            for index in range(tabs.count()):
                tabs.setCurrentIndex(index)
                app.processEvents()
    return dialog


def review_table(targets, path):
    """Tabela em português com módulo, tipo, rótulo/texto e dica de cada widget (sem repetições)."""
    from geosaga import i18n
    i18n.qgis_language = lambda: 'pt'
    lines = ['| Módulo | Widget | Rótulo ou texto | Dica |', '|---|---|---|---|']
    for module, cls in targets:
        dialog = _open(module, cls)
        seen = set()
        for kind in KINDS:
            for widget in dialog.findChildren(kind):
                if _internal(widget):
                    continue
                text = widget.text() if isinstance(widget, QAbstractButton) else (
                    _label(widget) or getattr(widget, 'placeholderText', lambda: '')())
                key = (type(widget).__name__, text, widget.toolTip())
                if key in seen:
                    continue
                seen.add(key)
                tip = widget.toolTip().replace('|', '/').replace('\n', ' ')
                lines.append(f'| {cls} | {type(widget).__name__.lstrip("Q")} | {text} | {tip} |')
        dialog.close()
    with open(path, 'w', encoding='utf-8') as stream:
        stream.write('\n'.join(lines) + '\n')


def main(module, cls):
    dialog = _open(module, cls)
    rows = missing(dialog)
    for row in rows:
        print('\t'.join(str(x) for x in row))
    print(f'{module}: {len(rows)} sem dica')
    return 1 if rows else 0


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '--lista':
        pairs = sys.argv[3:]
        review_table(list(zip(pairs[::2], pairs[1::2])) or DONE, sys.argv[2])
        app.exitQgis()
        sys.exit(0)
    targets = [tuple(sys.argv[1:3])] if len(sys.argv) >= 3 else DONE
    code = max(main(module, cls) for module, cls in targets)
    app.exitQgis()
    sys.exit(code)
