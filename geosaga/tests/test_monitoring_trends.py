"""Regressões 0.4.1: legendas legíveis e MK com séries temporais válidas."""
from collections import Counter
import csv
from pathlib import Path
import tempfile
import unittest

from geosaga.monitoring_trends import mk_test, temporal_rows
from geosaga.monitoring_core import (transitions_summary, write_monitoring_reports,
                                     write_mk_csv, append_mk_txt)
from geosaga.monitoring_engine import _read_legend_lookup


class MKTests(unittest.TestCase):
    def test_increasing_exact_p_five_years(self):
        mk = mk_test([1986, 1991, 1996, 2001, 2006], [1, 2, 3, 4, 5])
        self.assertEqual(mk['s'], 10)
        self.assertAlmostEqual(mk['p'], 2/120)
        self.assertAlmostEqual(mk['sen'], 0.2)
        self.assertEqual(mk['direcao'], 'crescimento')

    def test_decreasing_exact_p(self):
        mk = mk_test([2000, 2005, 2010, 2015, 2020], [100, 80, 60, 40, 20])
        self.assertEqual(mk['s'], -10)
        self.assertAlmostEqual(mk['p'], 2/120)
        self.assertAlmostEqual(mk['sen'], -4.0)

    def test_constant_series_and_ties(self):
        mk = mk_test([2000, 2001, 2002, 2003, 2004], [0, 0, 0, 0, 0])
        self.assertEqual(mk['p'], 1.)
        self.assertEqual(mk['sen'], 0.)
        self.assertEqual(mk['metodo'], 'constante')

    def test_ties_exhaustive(self):
        mk = mk_test([1, 2, 3, 4, 5], [1, 1, 2, 2, 3])
        self.assertGreater(mk['p'], 0)
        self.assertLessEqual(mk['p'], 1.)

    def test_asymptotic_eight(self):
        mk = mk_test(list(range(2000, 2008)), list(range(8)))
        self.assertGreater(mk['z'], 0)
        self.assertLess(mk['p'], 0.05)
        self.assertEqual(mk['metodo'], 'normal_aproximado_bilateral')

    def test_reject_only_two_dates(self):
        with self.assertRaisesRegex(ValueError, 'pelo menos 5'):
            mk_test([1986, 2016], [20, 35])

    def test_reject_unsorted(self):
        with self.assertRaisesRegex(ValueError, 'crescentes'):
            mk_test([2000, 2004, 2002, 2003, 2005], [0, 1, 2, 3, 4])

    def test_common_pixels_percentage(self):
        years = [1985, 1990, 1995, 2000, 2005]
        counts = [Counter({1: i, 2: 10-i}) for i in range(1, 6)]
        rows = temporal_rows(years, counts, 10)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['pct'], [10, 20, 30, 40, 50])
        self.assertEqual(rows[1]['pct'], [90, 80, 70, 60, 50])


class ReportingTests(unittest.TestCase):
    def test_labels_have_correct_initial_and_final(self):
        summary = transitions_summary(Counter({(1, 2): 3, (3, 3): 2}), 5,
            before_names={1: 'Pastagem', 3: 'Mata'},
            after_names={2: 'Urbanização', 3: 'Mata'})
        first = summary['linhas'][0]
        self.assertEqual(first['legenda'],
            'Deixou de ser: Pastagem | Tornou-se: Urbanização')
        self.assertEqual(summary['linhas'][1]['legenda'], 'Permaneceu: Mata')

    def test_names_override_code_for_permanence(self):
        s = transitions_summary(Counter({(1,1):3, (2,3):4}), 7,
            before_names={1:'Pastagem', 2:'Floresta'},
            after_names={1:'Área urbana', 3:'Floresta'})
        self.assertEqual(s['permanencias'], 4)
        self.assertEqual(s['mudancas'], 3)
        self.assertEqual(s['linhas'][0]['situacao'], 'Mudança')
        self.assertEqual(s['linhas'][1]['legenda'], 'Permaneceu: Floresta')

    def test_csv_and_txt_descriptive(self):
        summary = transitions_summary(Counter({(1, 2): 1}), 1,
            before_names={1: 'Pastagem'}, after_names={2: 'Área urbanizada'})
        with tempfile.TemporaryDirectory() as d:
            p = [str(Path(d)/f) for f in ('t.csv', 'm.csv', 's.txt')]
            write_monitoring_reports(*p, summary)
            with open(p[0], newline='', encoding='utf-8-sig') as f:
                rows = list(csv.DictReader(f, delimiter=';'))
            self.assertEqual(rows[0]['DEIXOU_DE_SER'], 'Pastagem')
            self.assertEqual(rows[0]['TORNOU_SE'], 'Área urbanizada')
            self.assertIn('Tornou-se: Área urbanizada', Path(p[2]).read_text('utf8'))

    def test_mk_not_applicable_two_dates(self):
        with tempfile.TemporaryDirectory() as d:
            csvpath = Path(d)/'mk.csv'
            txtpath = Path(d)/'summary.txt'
            txtpath.write_text('Mapa válido\n', encoding='utf8')
            series = {'status':'nao_aplicavel', 'n':2,
                      'mensagem': 'Não aplicável a duas observações.'}
            write_mk_csv(csvpath, series)
            append_mk_txt(txtpath, series)
            with csvpath.open(encoding='utf-8-sig', newline='') as f:
                row = list(csv.DictReader(f, delimiter=';'))[0]
            self.assertEqual(row['STATUS'], 'NAO_APLICAVEL')
            self.assertEqual(row['MK_P_BILATERAL'], '')
            self.assertIn('Não aplicável', txtpath.read_text('utf8'))

    def test_mk_valid_csv(self):
        years = [1986, 1991, 1996, 2001, 2006]
        counts = [Counter({1: i, 2: 10-i}) for i in range(1, 6)]
        series = {'status':'calculado', 'anos':years, 'validos':10,
                  'linhas':temporal_rows(years, counts, 10)}
        with tempfile.TemporaryDirectory() as d:
            csvpath = Path(d)/'mk.csv'
            write_mk_csv(csvpath, series)
            with csvpath.open(encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f, delimiter=';'))
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(r['STATUS']=='CALCULADO' for r in rows))
            self.assertTrue(all(float(r['MK_P_BILATERAL']) < .05 for r in rows))

    def test_manual_lookup_per_period(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'leg.csv'
            path.write_text('PERIODO;CODIGO;CLASSE\n1986;1;Pastagem\n2016;1;Urbanização\n', encoding='utf8')
            a, b = _read_legend_lookup(str(path), '1986', '2016')
            self.assertEqual(a[1], 'Pastagem')
            self.assertEqual(b[1], 'Urbanização')

    def test_invalid_lookup(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'leg.csv'
            path.write_text('CODIGO;CLASSE\n1;Pasto\n', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'PERIODO'):
                _read_legend_lookup(str(path), '1986', '2016')


if __name__ == '__main__':
    unittest.main()
