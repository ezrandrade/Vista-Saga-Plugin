"""Verifica invariante de consolidação sem executar PyQGIS."""
from pathlib import Path
import unittest
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

class SpatialConsolidationTests(unittest.TestCase):
    def test_menu_has_spatial_assessment_without_processing_duplicate(self):
        entries = _support.menu_entries()
        self.assertIn(('Avaliação', 'open_interactive'), entries)
        self.assertNotIn('Avaliação Ambiental - Processing', [title for title, _ in entries])
        self.assertIn(('Monitoria', 'open_monitoring'), entries)
        self.assertIn(('Assinatura', 'open_signature'), entries)

    def test_home_dialog_uses_new_name_and_panel(self):
        source = (ROOT / 'home_dialog.py').read_text(encoding='utf8')
        self.assertIn("'Avaliação'", source)
        self.assertIn("'Vista Saga Plugin - Painel de módulos'", source)

    def test_project_format_compatibility(self):
        source = (ROOT / 'evaluation_dialog.py').read_text(encoding='utf8')
        self.assertIn("'formato': 'geosaga-avaliacao'", source)
        self.assertIn("'Vista Saga Plugin - Avaliação'", source)

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
        _support.assert_release_version(self)
