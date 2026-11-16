"""Tolerância de lascas na Combinação vetorial (1.2.0).

Regra: sobreposição entre polígonos de uma mesma camada só bloqueia se algum
pedaço tiver largura média (2 × área ÷ perímetro) de pelo menos 1 cm; lascas mais
finas são mantidas e a área duplicada vai para o _resumo.txt. Dados sintéticos.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geosaga.combination_core import (  # noqa: E402
    SLIVER_WIDTH_M, mean_width, classify_overlap, sliver_report_lines,
    write_combination_reports, composition_rows)

ROOT = Path(__file__).resolve().parents[1]

try:
    from shapely.geometry import box
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False


class SliverRuleTests(unittest.TestCase):
    def test_threshold_is_one_centimetre(self):
        self.assertEqual(SLIVER_WIDTH_M, 0.01)

    def test_mean_width_of_strip_and_square(self):
        # faixa de 700 m × 0,04 mm: largura média ~0,04 mm
        self.assertAlmostEqual(mean_width(700 * 4e-5, 2 * (700 + 4e-5)), 4e-5, places=9)
        # quadrado de 1 m: s/2 = 0,5 m
        self.assertAlmostEqual(mean_width(1.0, 4.0), 0.5)
        self.assertEqual(mean_width(1.0, 0.0), 0.0)

    def test_thin_pieces_tolerated_thick_rejected(self):
        thin = (700 * 4e-5, 2 * (700 + 4e-5))      # lasca de 0,04 mm
        thick = (12.5, 2 * (25 + 0.5))              # faixa de 0,5 m
        tiny = (1e-16, 1e-6)                       # ruído numérico
        ok_area, slivers, bad_area, widest = classify_overlap([thin, tiny], SLIVER_WIDTH_M)
        self.assertEqual((slivers, bad_area, widest), (1, 0.0, 0.0))
        self.assertAlmostEqual(ok_area, 0.028)
        ok_area, slivers, bad_area, widest = classify_overlap([thin, thick], SLIVER_WIDTH_M)
        self.assertEqual(slivers, 1)
        self.assertAlmostEqual(bad_area, 12.5)
        self.assertAlmostEqual(widest, 12.5 * 2 / 51)

    def test_width_exactly_at_threshold_is_rejected(self):
        side = 2 * SLIVER_WIDTH_M                    # quadrado: largura média = lado/2
        _, slivers, bad, _ = classify_overlap([(side * side, 4 * side)], SLIVER_WIDTH_M)
        self.assertEqual(slivers, 0)
        self.assertGreater(bad, 0)

    def test_report_lines_and_summary(self):
        stats = [{'name': 'Renda', 'count': 296, 'area_m2': 0.0349},
                 {'name': 'Escolaridade', 'count': 0, 'area_m2': 0.0}]
        lines = sliver_report_lines(stats)
        self.assertIn('1 cm', lines[0])
        self.assertIn('Mapa 01 (Renda): 296 lascas, 0.034900 m²', lines[1])
        self.assertIn('Mapa 02 (Escolaridade): nenhuma lasca.', lines[2])
        rows = composition_rows({('1', 'A'): 10.0}, [{'1': 'Um'}, {'A': 'Alfa'}], vector=True)
        with tempfile.TemporaryDirectory() as folder:
            txt = Path(folder) / 'r.txt'
            write_combination_reports(str(Path(folder) / 'r.csv'), str(txt), rows,
                                      ['Renda', 'Escolaridade'], mode='Vetorial',
                                      crs='EPSG:31985', area_method='m²', notes=lines)
            text = txt.read_text(encoding='utf-8')
        self.assertIn('Tolerância de lascas', text)
        self.assertIn('296 lascas', text)

    def test_engine_uses_rule_and_lists_all_pairs(self):
        src = (ROOT / 'combination_vector.py').read_text(encoding='utf-8')
        self.assertIn('classify_overlap(pieces, tolerance)', src)
        self.assertIn('rejected.append(', src)
        self.assertIn('notes=sliver_report_lines(sliver_stats)', src)
        self.assertIn('fromUnitToUnitFactor', src)


@unittest.skipUnless(HAS_SHAPELY, 'Shapely ausente')
class SliverGeometryTests(unittest.TestCase):
    """Mesma regra aplicada a geometrias reais (GEOS, como no QGIS)."""

    def _pieces(self, a, b):
        x = a.intersection(b)
        parts = [g for g in getattr(x, 'geoms', [x]) if g.geom_type == 'Polygon']
        return [(g.area, g.length) for g in parts]

    def test_shared_border_with_coordinate_noise_is_tolerated(self):
        left = box(0, 0, 500.00004, 300)            # invade 0,04 mm o vizinho
        right = box(500, 0, 1000, 300)
        _, slivers, bad, _ = classify_overlap(self._pieces(left, right), SLIVER_WIDTH_M)
        self.assertEqual((slivers, bad), (1, 0.0))

    def test_real_overlap_is_rejected(self):
        left = box(0, 0, 501, 300)                  # invade 1 m o vizinho
        right = box(500, 0, 1000, 300)
        _, _, bad, widest = classify_overlap(self._pieces(left, right), SLIVER_WIDTH_M)
        self.assertAlmostEqual(bad, 300.0)
        self.assertGreater(widest, 0.9)


if __name__ == '__main__':
    unittest.main()
