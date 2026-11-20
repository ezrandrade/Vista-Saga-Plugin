"""Janela da Assinatura 1.5.0 (estrutura do código, sem PyQGIS).

Decisões do autor (20/11/2026): lista de mapas com a referência no topo; seleção por classes (raster) e
pela seleção do QGIS (vetor); "Resultado por feição" ligado por padrão; saídas TXT e CSV no padrão do
plugin, sem as caixas "temporário"/"carregar" e sem o GeoPackage das áreas.
"""
import ast
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / 'signature_dialog.py'


class AssinaturaJanela150(unittest.TestCase):
    def setUp(self):
        self.code = SRC.read_text(encoding='utf-8')
        self.tree = ast.parse(self.code)

    def test_usa_o_motor_novo(self):
        self.assertIn('from .signature_raster import', self.code)
        self.assertIn('from .signature_vector import', self.code)
        self.assertNotIn('signature_engine', self.code)

    def test_sem_caixas_antigas_nem_geopackage(self):
        for old in ('temporary_check', 'add_project', 'gpkg', 'GeoPackage', 'areas_select'):
            self.assertNotIn(old, self.code, old)

    def test_resultado_por_feicao_ligado(self):
        self.assertIn('self.per_feature.setChecked(True)', self.code)

    def test_selecao_vetorial_vem_do_qgis(self):
        self.assertIn('selectedFeatures()', self.code)
        self.assertIn('selectionChanged.connect', self.code)
        self.assertIn('layer.selectAll()', self.code)

    def test_referencia_no_topo_com_mover(self):
        self.assertIn("tr('Mover para cima')", self.code)
        self.assertIn("tr('Mover para baixo')", self.code)
        self.assertIn("'1. Mapas - o primeiro é a referência'", self.code)

    def test_menu_e_processing_legado(self):
        import os, sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import _support
        base = SRC.parent
        self.assertIn(('Assinatura', 'open_signature'), _support.menu_entries())
        self.assertIn('self.addAlgorithm(AssinaturaAlgorithm())', (base / 'provider.py').read_text(encoding='utf-8'))
        legacy = (base / 'algorithms' / 'assinatura.py').read_text(encoding='utf-8')
        self.assertIn("return 'assinatura'", legacy)  # identificador geosaga:assinatura preservado
        self.assertIn('Qgis.ProcessingAlgorithmFlag.Deprecated', legacy)  # obsoleto e oculto (1.5.0)
        self.assertFalse((base / 'signature_engine.py').exists())  # motor antigo retirado

    def test_remover_todas(self):
        self.assertIn("tr('Remover todas')", self.code)
        self.assertIn('def _remove_all(self, mode):', self.code)

    def test_botoes_e_campos_com_dica(self):
        """Todo QPushButton criado na janela recebe dica (setToolTip), exceto os do rodapé padrão já cobertos."""
        names = set()
        for node in ast.walk(self.tree):
            if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                    and getattr(node.value.func, 'id', '') == 'QPushButton'):
                target = node.targets[0]
                names.add(ast.unparse(target))
        self.assertTrue(names)
        for name in names:
            self.assertIn(f'{name}.setToolTip(', self.code, name)


if __name__ == '__main__':
    unittest.main()
