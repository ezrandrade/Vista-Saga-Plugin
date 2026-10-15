"""Regressão de Monitoria vetorial independente de QGIS / GDAL."""
import csv
import math
import tempfile
import unittest
from pathlib import Path

from geosaga.vector_monitoring_core import (aggregate_transitions, make_transition,
                                            transition_identity, write_reports)


class VectorMonitoringCoreTests(unittest.TestCase):
    def test_stable_by_code(self):
        self.assertEqual('Permanência', make_transition('1', '1')['situacao'])

    def test_change_by_code(self):
        row = make_transition('1', '2')
        self.assertEqual('Mudança', row['situacao'])
        self.assertIn('Deixou de ser', row['legenda'])
        self.assertIn('Tornou-se', row['legenda'])

    def test_textual_identity(self):
        row = make_transition('1', '9', '  Mata  ', 'mata')
        self.assertEqual('Permanência', row['situacao'])
        self.assertEqual('NOMES', row['comparacao'])

    def test_labels_override_same_codes(self):
        self.assertFalse(transition_identity('1', '1', 'Floresta', 'Pastagem'))

    def test_missing_label_falls_back_to_code(self):
        self.assertTrue(transition_identity('1', '1', 'Floresta', ''))

    def test_aggregate_area(self):
        rows = [(1, make_transition('1', '1', 'Mata', 'Mata'), 50),
                (2, make_transition('1', '2', 'Mata', 'Pasto'), 100),
                (3, make_transition('1', '2', 'Mata', 'Pasto'), 50)]
        result = aggregate_transitions(iter(rows))
        self.assertEqual(3, result['feicoes'])
        self.assertEqual(2, len(result['linhas']))
        self.assertAlmostEqual(200 / 10000, result['area_total_ha'])
        self.assertAlmostEqual(25, result['pct_permanencia'])
        self.assertAlmostEqual(75, result['pct_mudanca'])
        self.assertAlmostEqual(100, sum(r['pct_area'] for r in result['linhas']))

    def test_invalid_area(self):
        for value in (-1, float('nan'), float('inf')):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    aggregate_transitions([(1, make_transition('1', '1'), value)])

    def test_empty(self):
        with self.assertRaises(ValueError):
            aggregate_transitions([])

    def test_zero_only(self):
        with self.assertRaises(ValueError):
            aggregate_transitions([(1, make_transition('1', '1'), 0)])

    def test_csv_and_matrix_totals(self):
        rows = [(1, make_transition('A', 'A'), 10000),
                (2, make_transition('A', 'B'), 30000)]
        report = aggregate_transitions(rows)
        with tempfile.TemporaryDirectory() as directory:
            a = Path(directory) / 'transicoes.csv'
            b = Path(directory) / 'matriz.csv'
            c = Path(directory) / 'resumo.txt'
            write_reports(a, b, c, report, initial='1986', final='2016', crs='EPSG:31985')
            with a.open(encoding='utf-8-sig', newline='') as file:
                content = list(csv.DictReader(file, delimiter=';'))
            self.assertEqual(2, len(content))
            self.assertEqual(100, sum(float(row['PCT_AREA']) for row in content))
            with b.open(encoding='utf-8-sig', newline='') as file:
                matrix = list(csv.reader(file, delimiter=';'))
            self.assertEqual('4.000000', matrix[-1][-1])
            body = c.read_text(encoding='utf-8')
            self.assertIn('Mann–Kendall', body)
            self.assertIn('Área comum', body)

    def test_groups_by_named_classes(self):
        data = [(1, make_transition('1', '3', 'Mata', 'Urbano'), 200),
                (2, make_transition('1', '3', 'Mata', 'Urbano'), 200),
                (3, make_transition('1', '3', 'Pasto', 'Urbano'), 300)]
        out = aggregate_transitions(data)
        self.assertEqual(2, len(out['linhas']))
        self.assertAlmostEqual(700, out['area_total_m2'])


if __name__ == '__main__':
    unittest.main()
