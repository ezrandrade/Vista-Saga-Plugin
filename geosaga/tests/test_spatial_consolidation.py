"""Verifica invariante de consolidação sem executar PyQGIS."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SpatialConsolidationTests(unittest.TestCase):
    def test_menu_has_spatial_assessment_without_processing_duplicate(self):
        source = (ROOT / 'plugin.py').read_text(encoding='utf8')
        self.assertIn("self._add_menu_action('Avaliação', self.open_interactive)", source)
        self.assertNotIn("self._add_menu_action('Avaliação Ambiental — Processing'", source)
        self.assertIn("self._add_menu_action('Monitoria', self.open_monitoring)", source)
        self.assertIn("self._add_menu_action('Assinatura', self.open_signature)", source)

    def test_home_dialog_uses_new_name_and_panel(self):
        source = (ROOT / 'home_dialog.py').read_text(encoding='utf8')
        self.assertIn("'Avaliação'", source)
        self.assertIn("'Vista Saga Plugin — Painel de módulos'", source)

    def test_project_format_compatibility(self):
        source = (ROOT / 'evaluation_dialog.py').read_text(encoding='utf8')
        self.assertIn("'formato': 'geosaga-avaliacao'", source)
        self.assertIn("'Vista Saga Plugin — Avaliação'", source)

    def test_provider_legacy_id_stable(self):
        source = (ROOT / 'provider.py').read_text(encoding='utf8')
        self.assertIn('self.addAlgorithm(AvaliacaoAlgorithm())', source)
        source = (ROOT / 'algorithms' / 'avaliacao.py').read_text(encoding='utf8')
        self.assertIn("return 'avaliacao'", source)

    def test_public_brand_and_legacy_ids(self):
        menu = (ROOT / 'plugin.py').read_text(encoding='utf8')
        provider = (ROOT / 'provider.py').read_text(encoding='utf8')
        metadata = (ROOT / 'metadata.txt').read_text(encoding='utf8')
        panel = (ROOT / 'home_dialog.py').read_text(encoding='utf8')
        self.assertIn("MENU = 'Vista Saga Plugin'", menu)
        self.assertIn('name=Vista Saga Plugin\n', metadata)
        self.assertIn("return 'Vista Saga Plugin'", provider)
        self.assertIn("return 'geosaga'", provider)
        self.assertIn("QLabel('Vista Saga Plugin')", panel)

    def test_version(self):
        source = (ROOT / 'metadata.txt').read_text(encoding='utf8')
        self.assertIn('version=1.0.3', source)
