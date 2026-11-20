"""Inventário de dicas (1.6.0): lista botões, campos, caixas de marcar e listas sem dica num módulo.

Uso, na raiz do repositório (QGIS real, sem interface):
    QT_QPA_PLATFORM=offscreen python tests/qgis/tooltip_inventory.py                # módulos concluídos
    QT_QPA_PLATFORM=offscreen python tests/qgis/tooltip_inventory.py evaluation_dialog EvaluationDialog
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
    QAbstractButton, QAbstractSpinBox, QComboBox, QLineEdit, QListWidget, QTabBar, QTabWidget,
)

KINDS = (QAbstractButton, QLineEdit, QComboBox, QAbstractSpinBox, QListWidget)


# Peças internas do Qt/QGIS: botão de canto da tabela, botão de limpar do campo de texto, setas das abas.
INTERNAL_CLASSES = ('QTableCornerButton', 'QLineEditIconButton', 'QTabBar', 'QgsFilterLineEdit')


def _internal(widget):
    if widget.metaObject().className() in INTERNAL_CLASSES:
        return True
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, (QComboBox, QAbstractSpinBox, QTabBar)) or parent.inherits('QgsFileWidget'):
            return True
        parent = parent.parentWidget()
    return False


def missing(dialog):
    found = []
    for kind in KINDS:
        for widget in dialog.findChildren(kind):
            if _internal(widget) or widget.toolTip().strip():
                continue
            label = getattr(widget, 'text', lambda: '')() if isinstance(widget, QAbstractButton) else ''
            found.append((type(widget).__name__, widget.objectName(), label,
                          getattr(widget, 'placeholderText', lambda: '')()))
    return found


# Módulos com dicas completas (1.6.0); cada lote acrescenta os seus.
DONE = [('signature_dialog', 'SignatureDialog'), ('evaluation_dialog', 'EvaluationDialog')]


def main(module, cls):
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
    rows = missing(dialog)
    for row in rows:
        print('\t'.join(str(x) for x in row))
    print(f'{module}: {len(rows)} sem dica')
    return 1 if rows else 0


if __name__ == '__main__':
    targets = [tuple(sys.argv[1:3])] if len(sys.argv) >= 3 else DONE
    code = max(main(module, cls) for module, cls in targets)
    app.exitQgis()
    sys.exit(code)
