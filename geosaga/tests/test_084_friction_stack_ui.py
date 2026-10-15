"""Testes estáticos do contrato da GUI Qt6 do atrito múltiplo.

Não substituem o teste visual integrado no QGIS.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MultiFrictionUI084(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT/'voronoi_dialog.py').read_text(encoding='utf-8')

    def test_scrollable_main_form(self):
        self.assertIn('scroll = QScrollArea(self)', self.source)
        self.assertIn('scroll.setWidgetResizable(True)', self.source)
        self.assertIn('layout.addWidget(scroll, 1)', self.source)

    def test_dedicated_chooser_and_summary(self):
        for snippet in ('self.friction_stack_dialog = QDialog(self)',
                        'self.stack_manage = QPushButton',
                        'self.friction_stack_dialog.exec()',
                        'self._update_friction_summary()',
                        'self.friction_stack_summary = QLabel'):
            self.assertIn(snippet, self.source)

    def test_multi_selection_from_layers_or_files(self):
        self.assertIn('def _add_friction_layers(self):', self.source)
        self.assertIn('def _add_friction_files(self):', self.source)
        self.assertIn('getOpenFileNames(', self.source)
        self.assertIn('SelectionMode.MultiSelection', self.source)
        self.assertIn('def _remove_friction_layers(self):', self.source)
        self.assertIn('if layer.id() in ids:', self.source)

    def test_configuration_preserved(self):
        for snippet in ("'weight': weight", "'notes': notes", "'layer_id': layer.id()",
                        'self._friction_components_from_ui()', "if len(comps) > 12:"):
            self.assertIn(snippet, self.source)

    def test_automatic_chooser_on_enable(self):
        self.assertIn('self.multi_friction.toggled.connect(self._on_multi_friction_toggled)', self.source)
        self.assertIn('def _on_multi_friction_toggled(self, checked):', self.source)


if __name__ == '__main__':
    unittest.main()
