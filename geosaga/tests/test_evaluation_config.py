"""Arquivo de pesos e notas das avaliações vetoriais (sem PyQGIS)."""
import json
import os
import tempfile
import unittest
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support  # noqa: E402,F401

from geosaga import evaluation_config as cfg  # noqa: E402
from geosaga.ui_shared import class_sort_key, looks_numeric  # noqa: E402
from pathlib import Path  # noqa: E402


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

    def test_class_order_is_numeric_then_text(self):
        keys = ['11', 'Floresta', '2', 'agua', '1.5', '-1']
        self.assertEqual(sorted(keys, key=class_sort_key), ['-1', '1.5', '2', '11', 'agua', 'Floresta'])

    def test_three_tabs_share_sort_tab_navigation_and_background(self):
        root = Path(__file__).resolve().parents[1]
        raster = (root / 'evaluation_dialog.py').read_text(encoding='utf-8')
        vector = (root / 'vector_evaluation_dialog.py').read_text(encoding='utf-8')
        for text in (raster, vector):
            self.assertIn('HeaderSort(', text)
            self.assertEqual(text.count('install_column_tab_navigation('), 2)
            self.assertIn('.installEventFilter(self._score_tab)', text)
            self.assertIn('.installEventFilter(self._weight_tab)', text)
        self.assertNotIn('title_edit', raster)
        self.assertNotIn('author_edit', raster)

    def test_every_scroll_area_uses_tab_background(self):
        """Toda área com rolagem dentro de guia usa o fundo padrão do QGIS."""
        import re
        root = Path(__file__).resolve().parents[1]
        for path in root.glob('*.py'):
            text = path.read_text(encoding='utf-8')
            for match in re.finditer(r'^(\s*)([\w.]+)\.setWidget\(\w+\)\n(.*)$', text, re.M):
                self.assertEqual(match.group(3).strip(), f'use_tab_background({match.group(2)})',
                                 f'{path.name}: {match.group(0).strip()}')

    def test_no_em_dash_in_interface_strings(self):
        """Travessão só no marcador de nota indefinida (“—”), nunca em texto de interface."""
        import io
        import json
        import tokenize
        root = Path(__file__).resolve().parents[1]
        found = []
        for path in list(root.glob('*.py')) + list((root / 'algorithms').glob('*.py')):
            src = path.read_text(encoding='utf-8')
            kinds = {tokenize.STRING} | ({tokenize.FSTRING_MIDDLE} if hasattr(tokenize, 'FSTRING_MIDDLE') else set())
            for tok in tokenize.generate_tokens(io.StringIO(src).readline):
                if (tok.type in kinds and '—' in tok.string and not tok.string.startswith(('"""', "'''"))
                        and '“—”' not in tok.string and tok.string not in ("'—'", '"—"')):
                    found.append(f'{path.name}:{tok.start[0]}')
        for lang in ('en', 'es'):
            catalog = json.loads((root / 'i18n' / f'{lang}.json').read_text(encoding='utf-8'))
            found += [f'{lang}.json: {k[:40]}' for k, v in catalog.items()
                      if '“—”' not in k and ('—' in k or '—' in v)]
        self.assertEqual(found, [])

    def test_weights_are_not_distributed_automatically(self):
        root = Path(__file__).resolve().parents[1]
        raster = (root / 'evaluation_dialog.py').read_text(encoding='utf-8')
        vector = (root / 'vector_evaluation_dialog.py').read_text(encoding='utf-8')
        self.assertEqual(raster.count('self._assign_equal_weights()'), 1)  # só no botão
        self.assertEqual(vector.count('self._distribute()'), 1)
        for text, method in ((raster, 'def distribute_weights'), (vector, 'def distribute_weights')):
            body = text.split(method, 1)[1].split('\n    def ', 1)[0]
            self.assertTrue('_assign_equal_weights()' in body or '_distribute()' in body)


if __name__ == '__main__':
    unittest.main()
