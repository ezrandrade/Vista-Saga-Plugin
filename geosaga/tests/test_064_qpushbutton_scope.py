"""Regressão estática do escopo QPushButton na montagem da guia de sobreposição."""
import ast
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'vector_overlay_dialog.py'

class QPushButtonScopeRegression(unittest.TestCase):
    def test_button_imported_at_module_level_without_local_shadowing(self):
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        module_imports = [a.name for node in tree.body if isinstance(node, ast.ImportFrom) for a in node.names]
        self.assertIn('QPushButton', module_imports)
        cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == 'VectorOverlayEvaluationDialog')
        # Os botões da seção de camadas são criados no gancho _build_source_controls.
        build = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == '_build_source_controls')
        self.assertFalse(any(isinstance(x, ast.ImportFrom) and any(a.name == 'QPushButton' for a in x.names) for x in ast.walk(build)))
        self.assertFalse(any(isinstance(x, ast.Name) and x.id == 'QPushButton' and isinstance(x.ctx, (ast.Store, ast.Del)) for x in ast.walk(build)))
        self.assertTrue(any(isinstance(x, ast.Name) and x.id == 'QPushButton' and isinstance(x.ctx, ast.Load) for x in ast.walk(build)))

if __name__ == '__main__':
    unittest.main()
