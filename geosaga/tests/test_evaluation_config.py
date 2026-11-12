"""Arquivo de pesos e notas das avaliações vetoriais (sem PyQGIS)."""
import json
import os
import tempfile
import unittest
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support  # noqa: E402,F401

from geosaga import evaluation_config as cfg  # noqa: E402
from geosaga.ui_shared import looks_numeric  # noqa: E402


def criterion(counts):
    return {'field': 'C01', 'counts': dict(counts), 'weight': 0., 'notes': {}, 'excluded': set()}


class EvaluationConfigTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.layer = os.path.join(self.folder, 'dados', 'solos.gpkg')

    def records(self):
        return [{'camada': 'Solos', 'fonte': self.layer + '|layername=solos', 'campo': 'CLASSE',
                 'peso': 60, 'notas': {'1': 7, 'Argissolo': 3.5}, 'nao_avaliar': {'99'}},
                {'camada': 'Uso', 'fonte': self.layer + '|layername=uso', 'campo': 'USO',
                 'peso': 40, 'notas': {'A': 10}, 'nao_avaliar': set()}]

    def test_round_trip_keeps_weights_scores_and_relative_sources(self):
        path = os.path.join(self.folder, 'av' + cfg.SUFFIX)
        data = cfg.build_config('sobreposicao', 10, self.records(), self.folder)
        self.assertEqual(data['criterios'][0]['fonte'], 'dados/solos.gpkg|layername=solos')
        cfg.write_config(path, data)
        self.assertFalse(os.path.exists(path + '.tmp'))
        loaded = cfg.read_config(path, 'sobreposicao')
        self.assertEqual(loaded['escala'], 10)
        first = loaded['criterios'][0]
        self.assertEqual(first['fonte'], os.path.normpath(self.layer) + '|layername=solos')
        self.assertEqual(first['notas'], {'1': 7.0, 'Argissolo': 3.5})
        self.assertEqual(first['nao_avaliar'], {'99'})
        self.assertEqual(first['peso'], 60.0)

    def test_modalities_are_not_mixed(self):
        data = cfg.build_config('atributos', 10, self.records(), self.folder)
        with self.assertRaisesRegex(ValueError, 'outra modalidade'):
            cfg.parse_config(data, 'sobreposicao', self.folder)
        raster = {'formato': 'geosaga-avaliacao', 'versao': 1}
        with self.assertRaisesRegex(ValueError, 'guia Raster'):
            cfg.parse_config(raster, 'atributos', self.folder)

    def test_rejects_scores_outside_scale_and_conflicts(self):
        data = cfg.build_config('atributos', 10, self.records(), self.folder)
        data['criterios'][0]['notas']['1'] = 11
        with self.assertRaisesRegex(ValueError, 'fora da escala'):
            cfg.parse_config(data, 'atributos', self.folder)
        data = cfg.build_config('atributos', 10, self.records(), self.folder)
        data['criterios'][0]['nao_avaliar'] = ['1']
        with self.assertRaisesRegex(ValueError, 'ao mesmo tempo'):
            cfg.parse_config(data, 'atributos', self.folder)

    def test_apply_saved_reports_obsolete_and_pending_classes(self):
        saved = cfg.parse_config(cfg.build_config('atributos', 10, self.records(), self.folder),
                                 'atributos', self.folder)['criterios'][0]
        current = criterion({'1': 5, '2': 3, '99': 1})
        obsolete, pending = cfg.apply_saved(current, saved)
        self.assertEqual(current['weight'], 60.0)
        self.assertEqual(current['notes'], {'1': 7.0})
        self.assertEqual(current['excluded'], {'99'})
        self.assertEqual(obsolete, {'Argissolo'})
        self.assertEqual(pending, {'2'})

    def test_config_is_written_next_to_result(self):
        dest = os.path.join(self.folder, 'resultado.gpkg')
        self.assertEqual(cfg.config_path_for(dest),
                         os.path.join(self.folder, 'resultado_pesos_notas.geosaga.json'))

    def test_source_comparison(self):
        self.assertTrue(cfg.same_source(self.layer + '|layername=a',
                                        os.path.join(self.folder, 'dados', '.', 'solos.gpkg') + '|layername=a'))
        self.assertFalse(cfg.same_source(self.layer + '|layername=a', self.layer + '|layername=b'))
        self.assertFalse(cfg.same_source('', ''))

    def test_numeric_alignment_rule(self):
        for value in ('1', '-3.5', '0,25', '12.'):
            self.assertTrue(looks_numeric(value), value)
        for value in ('Floresta', '1a', 'Classe 2', ''):
            self.assertFalse(looks_numeric(value), value)


if __name__ == '__main__':
    unittest.main()
