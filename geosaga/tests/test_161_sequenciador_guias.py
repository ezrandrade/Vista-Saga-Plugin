"""Sequenciador de Mapas: guias com a mesma altura, compacta (1.4.2, decisão do autor).

Histórico: na 1.4.1 a guia Raster ficava com um espaço vazio grande (a área das guias tinha a altura da
guia Mista, alongada pelos textos explicativos); a tentativa de altura por guia fazia a lista de quadros
subir e descer ao trocar de guia. Na 1.4.2, os textos explicativos das guias Vetorial e Mista viraram
dicas (tooltips), e o QTabWidget padrão dá a mesma altura, agora compacta, às três guias.
"""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def source(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return f.read()


class GuiasDoSequenciador161(unittest.TestCase):
    def test_mesma_altura_nas_tres_guias(self):
        code = source('image_sequence_dialog.py')
        self.assertIn('self.tabs = QTabWidget()', code)
        self.assertNotIn('CurrentPageTabs', code)          # sem altura por guia

    def test_textos_explicativos_viraram_dicas(self):
        code = source('image_sequence_dialog.py')
        self.assertNotIn('explanation = QLabel(', code)
        self.assertIn('temporal_button.setToolTip(self.vector_hint)', code)
        self.assertIn('temporal_button.setToolTip(self.mixed_hint)', code)
        self.assertIn('self.tabs.setTabToolTip(1, self.vector_hint)', code)
        self.assertIn('self.tabs.setTabToolTip(2, self.mixed_hint)', code)


if __name__ == '__main__':
    unittest.main()
