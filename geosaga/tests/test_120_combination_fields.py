"""Campos do mapa vetorial combinado (1.2.0): COD_nn / LEG_nn, como no CSV."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'combination_vector.py').read_text(encoding='utf-8')


def _helper(name):
    tree = ast.parse(SOURCE)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = {}
    exec(compile(ast.Module([node], []), 'combination_vector', 'exec'), namespace)
    return namespace[name]


class CombinationFieldNames(unittest.TestCase):
    def test_names(self):
        self.assertEqual(_helper('code_field')(1), 'COD_01')
        self.assertEqual(_helper('legend_field')(12), 'LEG_12')

    def test_shapefile_limit_and_no_old_names(self):
        self.assertLessEqual(len(_helper('code_field')(99)), 10)
        self.assertNotIn("f'C{", SOURCE)
        self.assertNotIn("f'L{", SOURCE)


if __name__ == '__main__':
    unittest.main()
