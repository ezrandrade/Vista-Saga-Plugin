"""Testes do plano temporal e dos contratos de interface, sem PyQGIS."""
import unittest
from pathlib import Path
from geosaga.sequence_plan import extract_year, temporal_key, temporal_frames, safe_png_name

ROOT = Path(__file__).resolve().parents[1]


class SequencePlan087(unittest.TestCase):
    def test_extract_year_legacy(self):
        self.assertEqual(extract_year('mapa_1985_teste'), '1985')
        self.assertEqual(extract_year('2030_2090'), '2030')
        self.assertEqual(extract_year('sem ano'), '')

    def test_numeric_order_and_single_mode(self):
        frames = temporal_frames('VECTOR', 'ano', [2024, 2000, 1985, 2024, None])
        self.assertEqual([f['date'] for f in frames], ['1985', '2000', '2024'])
        self.assertEqual([f['temporal']['values'] for f in frames], [(1985,), (2000,), (2024,)])
        self.assertTrue(all(f['layers'] == ['VECTOR'] for f in frames))

    def test_cumulative_vector_plus_raster(self):
        frames = temporal_frames('V', 'ano', [2000, 1985, 2024], True, base_layers=['R'])
        self.assertEqual(frames[0]['temporal']['values'], (1985,))
        self.assertEqual(frames[-1]['temporal']['values'], (1985, 2000, 2024))
        self.assertEqual(frames[-1]['layers'], ['V', 'R'])

    def test_date_values_order(self):
        frames = temporal_frames('V', 'date', ['2024-01-01', '1985-01-03', '2000-09-15'])
        self.assertEqual([f['date'] for f in frames],
                         ['1985-01-03', '2000-09-15', '2024-01-01'])

    def test_insufficient_or_oversized(self):
        with self.assertRaisesRegex(ValueError, 'pelo menos dois'):
            temporal_frames('V', 'ano', [2024, 2024])
        with self.assertRaisesRegex(ValueError, 'mais de 2'):
            temporal_frames('V', 'ano', [1, 2, 3], max_frames=2)

    def test_png_safe_name(self):
        self.assertEqual(safe_png_name(1, '1985'), 'quadro_001_1985.png')
        self.assertEqual(safe_png_name(2, '../../a:b'), 'quadro_002_a_b.png')

    def test_ui_three_tabs_and_no_original_mutations(self):
        gui = (ROOT / 'image_sequence_dialog.py').read_text(encoding='utf-8')
        for snippet in (
            "'Raster'", "'Vetorial'", "'Misto'", 'self._mode_entries',
            'QScrollArea(self)', 'def _add_mixed', 'def _add_temporal',
            'def _temporal_layer', 'source.materialize(',
            'Qgis.FeatureRequestFlag.NoGeometry',
            'filtered.setRenderer(source.renderer().clone())',
            'filtered.setLabeling(source.labeling().clone())',
            "image.save(str(staging), 'PNG')", 'def _render(', 'def _add(',
        ):
            self.assertIn(snippet, gui, snippet)
        self.assertNotIn('source.setSubsetString(', gui)
        self.assertNotIn('QgsProject.instance().addMapLayer', gui)

    def test_names_public(self):
        self.assertIn('Sequenciador de Mapas', (ROOT / 'plugin.py').read_text())
        self.assertIn('Sequenciador de Mapas', (ROOT / 'home_dialog.py').read_text())
        self.assertIn('version=1.0.2', (ROOT / 'metadata.txt').read_text())
        self.assertIn('name=Vista Saga Plugin', (ROOT / 'metadata.txt').read_text())


if __name__ == '__main__':
    unittest.main()
