"""Regras de combinação independentes da interface QGIS.

Convertido de pytest para unittest: o restante do projeto usa unittest.
"""
import csv
from collections import Counter
from pathlib import Path
import tempfile
import unittest

from geosaga.combination_core import (
    normalized_code, canonical_keys, combination_index, composition_rows,
    read_combination_legend, write_combination_reports, MAX_COMBINATIONS,
)


class CombinationCoreTests(unittest.TestCase):
    def _tmp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        return Path(folder.name)

    def test_normalization(self):
        assert normalized_code(3.0) == '3'
        assert normalized_code(-2) == '-2'
        assert normalized_code(' Floresta ') == 'Floresta'
        assert normalized_code(0) == '0'
        assert normalized_code(float('nan')) is None
        assert normalized_code('  ') is None
        with self.assertRaisesRegex(ValueError, 'classes discretas'):
            normalized_code(3.14)

    def test_stable_codes_independent_order(self):
        before = {('10','3'):4, ('2','5'):1, ('2','2'):2}
        other = dict(reversed(list(before.items())))
        assert combination_index(before) == combination_index(other)
        assert list(combination_index(before)) == [('2','2'),('2','5'),('10','3')]

    def test_empty_and_limit(self):
        with self.assertRaises(ValueError): combination_index({})
        with self.assertRaises(ValueError): combination_index({(str(i),):1 for i in range(MAX_COMBINATIONS+1)})

    def test_raster_percent_areas(self):
        counts = Counter({('1','0'):3,('2','1'):1})
        rows = composition_rows(counts,[{'1':'Mata','2':'Área urbana'}, {'0':'Pastagem','1':'Rocha'}],pixel_area_m2=100)
        assert {r['legend'] for r in rows} == {'Mata | Pastagem','Área urbana | Rocha'}
        self.assertAlmostEqual(sum(r['percent'] for r in rows), 100)
        self.assertAlmostEqual(sum(r['area_ha'] for r in rows), .04)
        assert sum(r['pixels'] for r in rows) == 4

    def test_vector_areas(self):
        rows = composition_rows({('A','B'):12500.,('A','C'):7500.},
                                [{'A':'Argissolos'},{'B':'Pastagem','C':'Agricultura'}],vector=True)
        assert sum(row['area_ha'] for row in rows) == 2
        assert {row['percent'] for row in rows} == {62.5,37.5}
        assert all(r['pixels'] is None for r in rows)

    def test_reports_round_trip(self):
        tmp_path = self._tmp()
        rows = composition_rows({('1','5'):7,('3','0'):2},
                                [{'1':'Tabuleiro','3':'Encosta'}, {'5':'Floresta','0':'Urbano'}],
                                pixel_area_m2=100)
        csv_file, txt_file = tmp_path/'test_combinacoes.csv', tmp_path/'test_resumo.txt'
        write_combination_reports(csv_file,txt_file,rows,['Geologia','Uso'],mode='Raster',
                                  crs='EPSG:31985',area_method='Pixel × 100m²')
        parsed = read_combination_legend(csv_file)
        assert parsed == {r['id']:r['legend'] for r in rows}
        content = txt_file.read_text(encoding='utf-8')
        assert 'Combinações observadas: 2' in content
        assert '100.000000%' in content
        with csv_file.open(encoding='utf-8-sig') as fp:
            assert 'COD_01' in next(csv.reader(fp,delimiter=';'))

    def test_invalid_csv_rejected(self):
        tmp_path = self._tmp()
        path=tmp_path/'broken.csv'
        path.write_text('ID_COMB;LEGENDA\n1;Floresta\n1;Outra\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'duplicado'):
            read_combination_legend(path)

    def test_no_area_for_geographic_raster(self):
        rows = composition_rows({('1','1'):9},[{},{}],pixel_area_m2=None)
        assert rows[0]['area_ha'] is None
        assert rows[0]['percent'] == 100


if __name__ == '__main__':
    unittest.main()
