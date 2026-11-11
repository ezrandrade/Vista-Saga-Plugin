"""Regressão 0.6.5: as abas da Assinatura não devem ocupar toda a janela."""
from pathlib import Path
import re

from geosaga.tests._support import check_release_metadata, ui_text
import unittest

SRC = Path(__file__).resolve().parents[1]

class SignatureTabLayoutTest(unittest.TestCase):
    def test_compact_tabs(self):
        source = (SRC / 'signature_dialog.py').read_text(encoding='utf-8')
        self.assertIn('self.type_tabs = QTabBar()', source)
        self.assertIn('self.type_tabs.setExpanding(False)', source)
        vector_tab = re.search(r"self\.type_tabs\.addTab\(" + ui_text('Vetorial') + r"\)", source)
        self.assertIsNotNone(vector_tab)
        self.assertLess(vector_tab.start(), source.index('self.type_tabs.setExpanding(False)'))
        self.assertLess(source.index('self.type_tabs.setExpanding(False)'),
                        source.index('root.addWidget(self.type_tabs)'))

    def test_version(self):
        check_release_metadata(self)

if __name__ == '__main__':
    unittest.main()
