"""Verificações estáticas da integração gráfica; homologação Qt apenas no QGIS."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VectorOverlayWiringTests(unittest.TestCase):
    def test_raster_window_has_multi_layer_button(self):
        text = (ROOT / 'evaluation_dialog.py').read_text()
        self.assertIn("'Vetorial (Sobreposição)'", text)
        self.assertIn('def open_vector_overlay(self):', text)

    def test_original_attribute_dialog_is_preserved(self):
        text = (ROOT / 'vector_evaluation_dialog.py').read_text()
        self.assertIn('evaluate_vector_layer(', text)
        # As guias substituíram o botão que abria a sobreposição em outra janela.
        self.assertNotIn('Empilhar camadas vetoriais independentes…', text)

    def test_changing_selector_does_not_erase_stack(self):
        text = (ROOT / 'vector_overlay_dialog.py').read_text()
        method = text.split('def _layer_changed', 1)[1].split('\n    def ', 1)[0]
        self.assertNotIn('self.criteria.clear()', method)
        self.assertNotIn('self._populate_fields()', method)  # sem seletor de camada

    def test_overlay_is_geometry_intersection_not_union(self):
        text = (ROOT / 'vector_overlay_engine.py').read_text()
        self.assertIn("processing.run('native:intersection'", text)
        self.assertNotIn("processing.run('native:union'", text)


if __name__ == '__main__':
    unittest.main()
