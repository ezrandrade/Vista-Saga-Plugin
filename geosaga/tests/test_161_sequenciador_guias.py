"""Sequenciador de Mapas (1.4.1-dev3): área das guias com a altura da guia aberta.

O QTabWidget assume a altura (e a altura mínima) da maior guia; a guia Raster, curta, ficava com um
espaço vazio grande abaixo dos botões. CurrentPageTabs troca a maior guia pela guia aberta.
"""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def source(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return f.read()


class GuiasDoSequenciador161(unittest.TestCase):
    def test_guias_com_altura_da_guia_aberta(self):
        code = source('image_sequence_dialog.py')
        self.assertIn('class CurrentPageTabs(QTabWidget):', code)
        self.assertIn('self.tabs = CurrentPageTabs()', code)
        self.assertIn('def sizeHint(self):', code)
        self.assertIn('def minimumSizeHint(self):', code)       # o mínimo também vinha da maior guia
        self.assertIn('QSizePolicy.Policy.Maximum', code)       # não cresce além da guia aberta
        self.assertIn('self.currentChanged.connect(lambda *_: self.updateGeometry())', code)
        # Texto quebrado (Vetorial, Mista): sem heightForWidth da maior guia, que deslocava a barra de abas.
        self.assertIn('def hasHeightForWidth(self):\n        return False', code)
        self.assertIn('page.heightForWidth(width)', code)


if __name__ == '__main__':
    unittest.main()
