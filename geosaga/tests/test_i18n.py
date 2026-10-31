"""Testes sem QGIS para catálogos e seleção de idioma."""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from geosaga.i18n import normalize_language, translate_for_locale


class TestI18n(unittest.TestCase):
    def test_qgis_locale_normalization(self):
        self.assertEqual(normalize_language("pt_BR"), "pt")
        self.assertEqual(normalize_language("en_US"), "en")
        self.assertEqual(normalize_language("es-ES"), "es")

    def test_portuguese_source(self):
        self.assertEqual(translate_for_locale("Avaliação", "pt_BR"), "Avaliação")

    def test_english_catalog(self):
        self.assertEqual(translate_for_locale("Avaliação", "en_US"), "Evaluation")
        self.assertEqual(translate_for_locale("Sequenciador de Mapas", "en_GB"), "Map sequencer")

    def test_untranslated_language_uses_english(self):
        self.assertEqual(translate_for_locale("Avaliação", "de_DE"), "Evaluation")

    def test_unknown_text_is_preserved(self):
        self.assertEqual(translate_for_locale("geosaga:avaliacao", "en_US"), "geosaga:avaliacao")


if __name__ == "__main__":
    unittest.main()
