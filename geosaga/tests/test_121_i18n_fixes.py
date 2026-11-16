"""Correções da 1.2.1: textos do Sequenciador traduzidos e texto do botão avançado do Conversor."""
import unittest
from pathlib import Path

from geosaga.i18n import translate_for_locale

ROOT = Path(__file__).resolve().parents[1]


class SequencerTexts(unittest.TestCase):
    def test_frame_list_labels_translated(self):
        for key, en, es in (('Sem data', 'No date', 'Sin fecha'), ('sobre', 'over', 'sobre'),
                            ('[campo temporal]', '[temporal field]', '[campo temporal]')):
            self.assertEqual(translate_for_locale(key, 'en'), en)
            self.assertEqual(translate_for_locale(key, 'es'), es)
        src = (ROOT / 'image_sequence_dialog.py').read_text(encoding='utf-8')
        self.assertIn("tr('Sem data')", src)
        self.assertIn("tr('[campo temporal]')", src)
        self.assertNotIn("' sobre '.join", src)

    def test_export_messages_use_templates(self):
        src = (ROOT / 'image_sequence_dialog.py').read_text(encoding='utf-8')
        self.assertNotIn("tr(f'", src)
        self.assertNotIn("tr('GIF salvo em:\\n'+", src)
        for key in ('com quantização GIF', 'com cores preservadas', 'GIF salvo em:', 'Quadros PNG: {0}',
                    'GIF quantizado para 256 cores.', 'Paleta GIF preservada.'):
            self.assertNotEqual(translate_for_locale(key, 'en'), key)


class ConverterAdvancedButton(unittest.TestCase):
    def test_toggle_shows_text(self):
        src = (ROOT / 'rs2_dialog.py').read_text(encoding='utf-8')
        self.assertIn('self.advanced_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)', src)


if __name__ == '__main__':
    unittest.main()
