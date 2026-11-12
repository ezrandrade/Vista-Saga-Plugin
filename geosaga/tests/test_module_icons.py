"""Ícones dos módulos no menu suspenso: um SVG válido e seguro para cada módulo.

Lê plugin.py pela estrutura (AST), sem PyQGIS: MODULES (método de cada módulo)
e MODULE_ICONS (método → arquivo em icons/modulos/).
"""
import ast
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / 'icons' / 'modulos'


def _plugin_constants():
    tree = ast.parse((ROOT / 'plugin.py').read_text(encoding='utf-8'))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ('MODULES', 'MODULE_ICONS'):
                found[node.targets[0].id] = ast.literal_eval(node.value)
    return found['MODULES'], found['MODULE_ICONS']


class ModuleIconTests(unittest.TestCase):
    def setUp(self):
        self.modules, self.icons = _plugin_constants()

    def test_every_menu_module_has_an_icon(self):
        methods = [entry[4] for entry in self.modules]
        self.assertEqual(sorted(self.icons), sorted(methods))

    def test_icon_files_exist_and_are_distinct(self):
        names = list(self.icons.values())
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            with self.subTest(icone=name):
                self.assertTrue((ICON_DIR / name).is_file(), f'Ícone ausente: {name}')

    def test_icons_are_safe_square_svg(self):
        forbidden = ('<script', 'xlink:href', ' href=', '<image', '<foreignObject', 'onload', 'url(http')
        for name in self.icons.values():
            with self.subTest(icone=name):
                text = (ICON_DIR / name).read_text(encoding='utf-8')
                root = ET.fromstring(text)
                self.assertEqual(root.tag, '{http://www.w3.org/2000/svg}svg')
                box = [float(v) for v in root.get('viewBox', '').split()]
                self.assertEqual(len(box), 4, 'viewBox ausente')
                self.assertEqual(box[2], box[3], 'ícone deve ser quadrado')
                for token in forbidden:
                    self.assertNotIn(token, text)


if __name__ == '__main__':
    unittest.main()
