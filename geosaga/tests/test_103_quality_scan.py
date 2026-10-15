"""Regression tests for the QGIS quality-scan findings F402, E741, F811."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StyleScanRegressionTests(unittest.TestCase):
    def test_qcheckbox_import_only_once_at_module_scope(self):
        tree = ast.parse((ROOT / 'combination_dialog.py').read_text(encoding='utf-8'))
        imports = [(node, alias) for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom)
                   for alias in node.names if alias.name == 'QCheckBox']
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0][0].module, 'qgis.PyQt.QtWidgets')
        self.assertIn(imports[0][0], tree.body)

    def test_no_ambiguous_l_variable_in_evaluation_dialog(self):
        tree = ast.parse((ROOT / 'evaluation_dialog.py').read_text(encoding='utf-8'))
        names = [n for n in ast.walk(tree) if isinstance(n, ast.Name)
                 and isinstance(n.ctx, (ast.Store, ast.Del))]
        self.assertNotIn('l', [n.id for n in names])

    def test_signature_qabstractitemview_import_not_duplicated(self):
        tree = ast.parse((ROOT / 'signature_dialog.py').read_text(encoding='utf-8'))
        aliases = [alias.name for n in ast.walk(tree)
                   if isinstance(n, ast.ImportFrom)
                   for alias in n.names]
        self.assertEqual(aliases.count('QAbstractItemView'), 1)

    def test_release_version(self):
        self.assertEqual((ROOT / 'metadata.txt').read_text(encoding='utf-8').count('version=1.0.3'), 1)
