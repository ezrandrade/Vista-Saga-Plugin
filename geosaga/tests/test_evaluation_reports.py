"""Testa CSV/TXT de combinações sem dependências PyQGIS/GDAL."""
import csv
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import numpy as np

from geosaga.evaluation_reports import (
    final_note, add_raster_combinations, create_reports)


class EvaluationReportsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.criteria = [
            {'name': 'Pedologia', 'weight': 33, 'notes': {'1': 1, '2': 4},
             'labels': {'1': 'Latossolo', '2': 'Argissolo'}, 'excluded': {'0'}},
            {'name': 'Geomorfologia', 'weight': 33, 'notes': {'3': 5}, 'excluded': set()},
            {'name': 'Uso', 'weight': 34, 'notes': {'4': 1}, 'excluded': set()},
        ]

    def test_legacy_grouping_does_not_round_underlying_score(self):
        self.assertEqual(final_note(2.32), 2)
        self.assertEqual(final_note(2.65), 3)
        self.assertEqual(final_note(0.5), 1)
        self.assertEqual(final_note(0), 0)
        with self.assertRaises(ValueError):
            final_note(float('nan'))

    def test_raster_counts_only_evaluated_pixels(self):
        raster_a = np.array([[1, 1, 2], [1, 2, 2]])
        raster_b = np.array([[3, 3, 3], [3, 3, 3]])
        raster_c = np.array([[4, 4, 4], [4, 4, 4]])
        mask = np.array([[1, 0, 1], [1, 0, 1]], dtype=bool)
        combos = Counter()
        add_raster_combinations(combos, [raster_a, raster_b, raster_c], mask)
        self.assertEqual(combos, {('1', '3', '4'): 2, ('2', '3', '4'): 2})
        with self.assertRaisesRegex(ValueError, 'ultrapassou'):
            add_raster_combinations(Counter(), [raster_a, raster_b, raster_c], mask, limit=1)

    def test_txt_csv_have_all_classes_counts_areas_and_percentages(self):
        txt = self.base / 'carta_relatorio.txt'
        csvpath = self.base / 'carta_relatorio.csv'
        create_reports(str(txt), str(csvpath),
            combinations={('1', '3', '4'): (3, None), ('2', '3', '4'): (2, None)},
            criteria=self.criteria, total_units=8, valid_units=5,
            area_per_unit_ha=0.01, title='Teste Avaliação', unit_label='Pixels')
        full = txt.read_text(encoding='utf-8-sig')
        self.assertIn('Relatório de Combinações', full)
        self.assertIn('Combinações que originaram a nota final', full)
        self.assertIn('Latossolo', full)
        self.assertIn('3\t0.03', full)
        self.assertIn('CRITERIOS E REGRAS DE AVALIACAO', full)
        self.assertIn('BLOQUEADA' if False else 'SIM', full)
        with csvpath.open(encoding='utf-8-sig', newline='') as handle:
            rows = list(csv.reader(handle, delimiter=';'))
        self.assertIn(['Total de unidades', '8'], rows)
        self.assertIn(['Unidades avaliadas', '5'], rows)
        data = [r for r in rows if len(r) == 13 and r[2] == 'Uso']
        self.assertEqual(sum(int(r[9]) for r in data), 5)
        self.assertAlmostEqual(sum(float(r[10]) for r in data), 0.05)
        self.assertAlmostEqual(sum(float(r[12]) for r in data), 62.5)

    def test_vector_percentages_use_area_not_feature_count(self):
        criteria = [{'name': 'Solo', 'weight': 100, 'notes': {'A': 1, 'B': 4}}]
        path = self.base / 'vetor.csv'
        create_reports('', str(path), combinations={('A',): (2, 1.5), ('B',): (1, 3.0)},
                       criteria=criteria, total_units=4, valid_units=3,
                       total_area_ha=5.0, unit_label='Feições', invalid_area_ha=.5)
        with path.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.reader(f, delimiter=';'))
        data = [r for r in rows if len(r) == 13 and r[2] == 'Solo']
        self.assertEqual(len(data), 2)
        self.assertEqual([float(r[12]) for r in data], [30.0, 60.0])
        self.assertEqual([float(r[11]) for r in data], [100.0, 100.0])

    def test_geographic_raster_does_not_assume_hectares(self):
        path = self.base / 'geografico.txt'
        create_reports(str(path), '', combinations={('1',): (2, None)},
                       criteria=[{'name': 'A', 'weight': 100, 'notes': {'1': 5}}],
                       total_units=2, valid_units=2, unit_label='Pixels')
        self.assertIn('Não calculada: SRC sem unidades lineares métricas',
                      path.read_text(encoding='utf-8-sig'))

    def test_mismatch_rejects_unsafe_report(self):
        with self.assertRaisesRegex(ValueError, 'Inconsistência'):
            create_reports(str(self.base/'bad.txt'), '', combinations={('1',): (2, None)},
                           criteria=[{'name': 'A', 'weight': 100, 'notes': {'1': 5}}],
                           total_units=3, valid_units=3)

    def test_zero_valid_units(self):
        path = self.base / 'vazio.txt'
        create_reports(str(path), '', combinations={},
                       criteria=[{'name': 'A', 'weight': 100, 'notes': {'1': 5}}],
                       total_units=5, valid_units=0, area_per_unit_ha=.01)
        self.assertIn('Unidades avaliadas: 0', path.read_text(encoding='utf-8-sig'))


if __name__ == '__main__':
    unittest.main()
