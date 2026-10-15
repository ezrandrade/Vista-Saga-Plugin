"""Testes unitários Monitoria Ambiental sem depender da instalação QGIS/GDAL."""
import csv
import os
from pathlib import Path
import tempfile
import unittest
from collections import Counter
from unittest.mock import patch

import numpy as np

from geosaga.monitoring_core import (combine_block, transitions_summary,
                                      write_monitoring_reports)
from geosaga.monitoring_engine import (_same_grid, _install_outputs)


class TestMonitoringCore(unittest.TestCase):
    def setUp(self):
        self.a = np.array([[1, 1, 2], [-9999, 0, 3]], dtype=np.int16)
        self.b = np.array([[2, 1, 2], [1, 0, 2]], dtype=np.int16)

    def test_counts_and_zero_legitimate(self):
        counts = Counter()
        total = combine_block(counts, self.a, self.b, -9999, None)
        self.assertEqual(total, 5)
        self.assertEqual(counts[(0., 0.)], 1)
        self.assertEqual(counts[(1., 2.)], 1)
        self.assertNotIn((-9999., 1.), counts)

    def test_transitions_stable_ids_and_permanence(self):
        counts = Counter()
        combine_block(counts, self.a, self.b, -9999, None)
        report = transitions_summary(counts, 6, hectare_pixel=.01)
        self.assertEqual(report['validos'], 5)
        self.assertEqual(report['invalidos'], 1)
        self.assertEqual(report['permanencias'], 3)
        self.assertEqual(report['mudancas'], 2)
        self.assertEqual(report['ids'][(0., 0.)], 1)
        self.assertAlmostEqual(report['pct_mudanca'], 40)
        self.assertAlmostEqual(report['area_valida_ha'], .05)
        self.assertAlmostEqual(sum(r['percentual'] for r in report['linhas']), 100)

    def test_nan_and_nodata(self):
        counts = Counter()
        a = np.array([[-1., np.nan, 5.]])
        b = np.array([[4., 1., 5.]])
        self.assertEqual(combine_block(counts, a, b, -1, None), 1)
        self.assertEqual(counts, {(5., 5.): 1})

    def test_no_common_raises(self):
        with self.assertRaisesRegex(ValueError, 'Não existem transições'):
            transitions_summary(Counter(), 4)

    def test_matrix_csv_totals_and_text(self):
        counts = Counter()
        combine_block(counts, self.a, self.b, -9999, None)
        report = transitions_summary(counts, 6, None)
        with tempfile.TemporaryDirectory() as d:
            files = [str(Path(d) / p) for p in ('transition.csv', 'matrix.csv', 'summary.txt')]
            write_monitoring_reports(*files, report, title='Teste', before_label='1985', after_label='2024')
            with open(files[1], encoding='utf-8-sig', newline='') as f:
                table = list(csv.reader(f, delimiter=';'))
            self.assertEqual(table[-1][-1], '5')
            self.assertEqual(sum(int(v) for v in table[-1][1:-1]), 5)
            self.assertEqual([str(i) for i in (0, 1, 2)], table[0][1:-1])
            with open(files[0], encoding='utf-8-sig', newline='') as f:
                details = list(csv.DictReader(f, delimiter=';'))
            self.assertEqual(len(details), 5)
            self.assertEqual({r['SITUACAO'] for r in details}, {'Permanência', 'Mudança'})
            self.assertEqual(sum(int(r['PIXELS']) for r in details), 5)
            report_text = Path(files[2]).read_text(encoding='utf8')
            self.assertIn('Período inicial: 1985', report_text)
            self.assertIn('Período final: 2024', report_text)
            self.assertIn('Área válida (ha): Indisponível', report_text)

    def test_projected_area_report(self):
        summary = transitions_summary({(1., 2.): 2}, 3, hectare_pixel=.25)
        with tempfile.TemporaryDirectory() as d:
            files = [str(Path(d) / p) for p in ('a.csv', 'b.csv', 'c.txt')]
            write_monitoring_reports(*files, summary)
            self.assertIn('0.500000', Path(files[2]).read_text(encoding='utf8'))


class TestMonitoringOutputs(unittest.TestCase):
    def test_atomic_replacement_success(self):
        with tempfile.TemporaryDirectory() as d:
            originals = [str(Path(d) / f'out{i}.txt') for i in range(3)]
            staged = [str(Path(d) / f'stage{i}.txt') for i in range(3)]
            for path in originals:
                Path(path).write_text('old')
            for path in staged:
                Path(path).write_text('new')
            _install_outputs(staged, originals)
            self.assertTrue(all(Path(p).read_text() == 'new' for p in originals))
            self.assertFalse(any(Path(s).exists() for s in staged))

    def test_atomic_rollback_after_failure(self):
        with tempfile.TemporaryDirectory() as d:
            originals = [str(Path(d) / f'out{i}.txt') for i in range(3)]
            staged = [str(Path(d) / f'stage{i}.txt') for i in range(3)]
            for path in originals:
                Path(path).write_text('old')
            for path in staged:
                Path(path).write_text('new')
            real_replace = os.replace
            def fail_on_second_staged(src, dst):
                if src == staged[1]:
                    raise OSError('Falha simulada no segundo resultado')
                return real_replace(src, dst)
            with patch('geosaga.monitoring_engine.os.replace', side_effect=fail_on_second_staged):
                with self.assertRaisesRegex(OSError, 'simulada'):
                    _install_outputs(staged, originals)
            self.assertTrue(all(Path(p).read_text() == 'old' for p in originals))


class TestMonitoringWiring(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_home_uses_own_monitoring_window(self):
        home = (self.ROOT / 'home_dialog.py').read_text(encoding='utf8')
        self.assertIn('self.plugin.open_monitoring', home)
        self.assertNotIn("open_algorithm('monitoria')", home)

    def test_legacy_processing_still_available(self):
        provider = (self.ROOT / 'provider.py').read_text(encoding='utf8')
        plugin = (self.ROOT / 'plugin.py').read_text(encoding='utf8')
        self.assertIn('self.addAlgorithm(MonitoriaAlgorithm())', provider)
        self.assertIn('def open_monitoring', plugin)
        self.assertIn('def open_algorithm', plugin)
        self.assertIn('self.monitoring_dialog = None', plugin)

    def test_ui_cancels_task_on_unload(self):
        plugin = (self.ROOT / 'plugin.py').read_text(encoding='utf8')
        self.assertIn('task.callback = None', plugin)
        self.assertIn('task.cancel()', plugin)


if __name__ == '__main__':
    unittest.main()
