"""Regression tests for the QGIS quality-scan findings F402, E741, F811."""
import ast
from pathlib import Path
import unittest
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


class StyleScanRegressionTests(unittest.TestCase):
    def test_qcheckbox_not_imported_twice(self):
        # Desde a 1.2.0 a Combinação não usa caixas de seleção; o que importa é
        # não voltar a haver importação duplicada (achado F811).
        tree = ast.parse((ROOT / 'combination_dialog.py').read_text(encoding='utf-8'))
        imports = [(node, alias) for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom)
                   for alias in node.names if alias.name == 'QCheckBox']
        self.assertLessEqual(len(imports), 1)
        for node, _alias in imports:
            self.assertEqual(node.module, 'qgis.PyQt.QtWidgets')
            self.assertIn(node, tree.body)

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
        _support.assert_release_version(self)
