"""Regressão 0.6.5: as abas da Assinatura não devem ocupar toda a janela."""
from pathlib import Path
import unittest
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support  # noqa: E402

SRC = Path(__file__).resolve().parents[1]

class SignatureTabLayoutTest(unittest.TestCase):
    def test_compact_tabs(self):
        source = (SRC / 'signature_dialog.py').read_text(encoding='utf-8')
        self.assertIn('self.type_tabs = QTabBar()', source)
        self.assertIn('self.type_tabs.setExpanding(False)', source)
        self.assertLess(source.index("self.type_tabs.addTab(tr('Vetorial'))"),
                        source.index('self.type_tabs.setExpanding(False)'))
        self.assertLess(source.index('self.type_tabs.setExpanding(False)'),
                        source.index('root.addWidget(self.type_tabs)'))

    def test_version(self):
        _support.assert_release_version(self)

if __name__ == '__main__':
    unittest.main()
