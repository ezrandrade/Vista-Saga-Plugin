"""Testes independentes de QGIS/GDAL para assinatura ambiental."""
import csv
import tempfile
import unittest
from pathlib import Path
from geosaga.signature_core import (category_code, summarize_area,
                                    write_signature_reports)
from geosaga.signature_engine import _outpaths


class SignatureCoreTest(unittest.TestCase):
    def test_codes_include_zero_and_numeric_floats(self):
        self.assertEqual(category_code(0.0), '0')
        self.assertEqual(category_code(3.0), '3')
        self.assertEqual(category_code(1.25), '1.25')
        self.assertEqual(category_code(' Pasto '), 'Pasto')
        self.assertIsNone(category_code(''))
        self.assertIsNone(category_code(float('nan')))

    def test_qgis_null_like_values(self):
        class NullValue:
            def isNull(self):
                return True
        self.assertIsNone(category_code(NullValue()))

    def test_raster_counts_percent_area(self):
        rows, area = summarize_area(7, 'Área A', {0: 10, 1: 30, 2: 60},
                                    kind='raster', pixel_ha=.01,
                                    thematic_names={'0': 'Não classificado', '1': 'Pasto'},
                                    area_aoi_ha=2.0)
        self.assertEqual([r['pixels'] for r in rows], [10, 30, 60])
        self.assertEqual(rows[0]['label'], 'Não classificado')
        self.assertAlmostEqual(rows[1]['area_ha'], .30)
        self.assertAlmostEqual(sum(r['percentage'] for r in rows), 100)
        self.assertAlmostEqual(area['coverage_pct'], 50)
        self.assertEqual(area['dominant'], '2')

    def test_vector_areas_and_text_codes(self):
        rows, info = summarize_area(2, 'Setor B', {'Floresta': 12.5, 'Pastagem': 37.5},
                                    kind='vector', area_aoi_ha=60)
        self.assertIsNone(rows[0]['pixels'])
        self.assertAlmostEqual(sum(r['area_ha'] for r in rows), 50)
        self.assertAlmostEqual(info['coverage_pct'], 83.333333333)
        self.assertEqual(info['dominant'], 'Pastagem')

    def test_geographic_raster_doesnt_guess_area(self):
        rows, s = summarize_area(1, 'X', {'1': 5}, kind='raster',
                                  pixel_ha=None, area_aoi_ha=12)
        self.assertIsNone(rows[0]['area_ha'])
        self.assertIsNone(s['analyzed_ha'])
        self.assertIsNone(s['coverage_pct'])

    def test_empty_polygon(self):
        rows, info = summarize_area(3, 'Vazio', {}, kind='vector', area_aoi_ha=10)
        self.assertEqual(rows, [])
        self.assertEqual(info['classes'], 0)
        self.assertEqual(info['coverage_pct'], 0)

    def test_invalid_category_and_negative_count(self):
        with self.assertRaises(ValueError):
            summarize_area('a', 'b', {'1': -1}, kind='raster')
        with self.assertRaises(ValueError):
            summarize_area('a', 'b', {'1': float('nan')}, kind='raster')

    def test_reports_and_encoding(self):
        rows, summary = summarize_area(1, 'Água e várzea', {1: 10, 2: 20},
                                       kind='raster', pixel_ha=.1,
                                       thematic_names={'1': 'Área inundada'}, area_aoi_ha=5)
        with tempfile.TemporaryDirectory() as d:
            csvpath = str(Path(d)/'f.csv')
            txt = str(Path(d)/'f.txt')
            write_signature_reports(csvpath, txt, [summary], rows, title='Pesquisa',
                                    theme='Uso', mode='raster', crs='EPSG:31985')
            with open(csvpath, encoding='utf-8-sig', newline='') as f:
                result = list(csv.DictReader(f, delimiter=';'))
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['CLASSE'], 'Área inundada')
            self.assertEqual(result[0]['PIXELS'], '10')
            self.assertEqual(result[0]['AREA_HA'], '1.000000')
            self.assertIn('Água e várzea', Path(txt).read_text(encoding='utf-8'))

    def test_outputs(self):
        self.assertEqual(_outpaths('/tmp/a.csv'),
                         ('/tmp/a.csv', '/tmp/a_resumo.txt', '/tmp/a_areas.gpkg'))

    def test_ui_wiring(self):
        base = Path(__file__).resolve().parents[1]
        plugin = (base/'plugin.py').read_text(encoding='utf-8')
        home = (base/'home_dialog.py').read_text(encoding='utf-8')
        self.assertIn("'Assinatura', self.open_signature", plugin)
        self.assertIn('self.plugin.open_signature', home)
        self.assertNotIn("self.plugin.open_algorithm('assinatura')", home)
        self.assertIn('self.addAlgorithm(AssinaturaAlgorithm())',
                      (base/'provider.py').read_text(encoding='utf-8'))
