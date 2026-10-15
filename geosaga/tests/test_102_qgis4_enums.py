"""Checks explicitly scoped Qt6/QGIS4 enum namespaces after six scan findings."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTATIONS = {
    'evaluation_task.py': ['QgsTask.Flag.CanCancel'],
    'monitoring_task.py': ['QgsTask.Flag.CanCancel'],
    'voronoi_dialog.py': [
        'QgsTask.Flag.CanCancel',
        'QgsWkbTypes.GeometryType.PointGeometry',
        'QgsWkbTypes.GeometryType.PolygonGeometry',
    ],
    'rs2_dialog.py': ['QgsProjectionSelectionWidget.CrsOption.CrsNotSet'],
}
OLD = (
    ('QgsTask', 'CanCancel'),
    ('QgsWkbTypes', 'PointGeometry'),
    ('QgsWkbTypes', 'PolygonGeometry'),
    ('QgsProjectionSelectionWidget', 'CrsNotSet'),
)

def chain(node):
    parts=[]
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node=node.value
    if isinstance(node,ast.Name):
        parts.append(node.id)
        return '.'.join(reversed(parts))
    return None

class Qgis4EnumCompatibilityTests(unittest.TestCase):
    def test_expected_qualified_enums(self):
        for file,items in EXPECTATIONS.items():
            tree=ast.parse((ROOT/file).read_text(encoding='utf-8'))
            chains={chain(n) for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
            for item in items:
                with self.subTest(file=file, expression=item):
                    self.assertIn(item,chains)

    def test_legacy_direct_enum_members_absent_in_all_plugin_code(self):
        for path in ROOT.rglob('*.py'):
            if 'tests' in path.parts:
                continue
            tree=ast.parse(path.read_text(encoding='utf-8'))
            chains={chain(n) for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
            for base,member in OLD:
                with self.subTest(file=path.name, member=member):
                    self.assertNotIn(base+'.'+member,chains)

    def test_expected_total_six_sites(self):
        self.assertEqual(sum(map(len, EXPECTATIONS.values())),6)
