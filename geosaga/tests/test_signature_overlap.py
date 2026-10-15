"""Testes geométricos opcionais sem dependência de PyQGIS.

A geometria de teste replica a interface pública necessária (unaryUnion,
intersection, difference e boundingBox) usando GEOS via shapely, se disponível.
A execução no próprio QGIS é coberta por integration_signature_overlap_qgis.py.
"""
import csv
import tempfile
import unittest
from pathlib import Path
from geosaga.signature_core import summarize_area, write_signature_reports
from geosaga.signature_engine import _resolve_class_geometries

try:
    from shapely.geometry import box
    from shapely.ops import unary_union
except ImportError:
    box = None
    unary_union = None


class FakeGeometry:
    def __init__(self, shape):
        self.shape = shape

    @classmethod
    def unaryUnion(cls, values):
        return cls(unary_union([v.shape for v in values]))

    def isNull(self):
        return self.shape is None

    def isEmpty(self):
        return self.shape.is_empty

    def boundingBox(self):
        return self

    def intersects(self, other):
        return self.shape.intersects(other.shape)

    def intersection(self, other):
        return FakeGeometry(self.shape.intersection(other.shape))

    def difference(self, other):
        return FakeGeometry(self.shape.difference(other.shape))

    def area(self):
        return self.shape.area


def g(x1, y1, x2, y2):
    return FakeGeometry(box(x1, y1, x2, y2))


@unittest.skipIf(box is None, 'Shapely não instalado (teste geométrico opcional)')
class SignatureOverlapTests(unittest.TestCase):
    def test_same_class_overlap_dissolves(self):
        total, conflict = _resolve_class_geometries(
            {'A': [g(0,0,10,10), g(5,0,15,10)]},
            FakeGeometry.area, geometry_class=FakeGeometry)
        self.assertAlmostEqual(total['A'], .015)
        self.assertEqual(conflict, 0.0)

    def test_different_classes_only_unique_area_counted(self):
        total, conflict = _resolve_class_geometries(
            {'A': [g(0,0,10,10)], 'B': [g(5,0,15,10)]},
            FakeGeometry.area, geometry_class=FakeGeometry)
        self.assertAlmostEqual(total['A'], .005)
        self.assertAlmostEqual(total['B'], .005)
        self.assertAlmostEqual(conflict, .005)
        self.assertAlmostEqual(sum(total.values()) + conflict, .015)

    def test_strict_policy_rejects_conflict(self):
        with self.assertRaisesRegex(ValueError, 'classes temáticas diferentes'):
            _resolve_class_geometries(
                {'A': [g(0,0,10,10)], 'B': [g(5,0,15,10)]},
                FakeGeometry.area, overlap_policy='strict', geometry_class=FakeGeometry)

    def test_touched_edges_not_conflict(self):
        total, conflict = _resolve_class_geometries(
            {'A': [g(0,0,10,10)], 'B': [g(10,0,20,10)]},
            FakeGeometry.area, geometry_class=FakeGeometry)
        self.assertEqual(conflict, 0)
        self.assertAlmostEqual(total['A'], .01)
        self.assertAlmostEqual(total['B'], .01)

    def test_three_class_overlap_no_double_count_conflict(self):
        total, conflict = _resolve_class_geometries(
            {'A': [g(0,0,10,10)], 'B': [g(2,0,12,10)], 'C': [g(4,0,14,10)]},
            FakeGeometry.area, geometry_class=FakeGeometry)
        self.assertAlmostEqual(conflict, .01)  # 2..12: 100 m2
        self.assertAlmostEqual(total['A'], .002)
        self.assertAlmostEqual(total['B'], 0, delta=1e-12) if 'B' in total else None
        self.assertAlmostEqual(total['C'], .002)
        self.assertAlmostEqual(sum(total.values()) + conflict, .014)

    def test_report_conflict_and_zero_valid_area(self):
        _, info = summarize_area(1, 'Teste', {}, kind='vector', area_aoi_ha=.015)
        info['conflict_ha'] = .015
        info['conflict_pct'] = 100.0
        with tempfile.TemporaryDirectory() as d:
            csvpath, txtpath = str(Path(d)/'out.csv'), str(Path(d)/'out.txt')
            write_signature_reports(csvpath, txtpath, [info], [], mode='vector')
            with open(csvpath, encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f, delimiter=';'))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['AREA_CONFLITO_HA'], '0.015000')
            self.assertEqual(rows[0]['PCT_CONFLITO_AOI'], '100.000000')
            self.assertIn('Área ambígua', Path(txtpath).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
