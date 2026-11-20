"""Nomes dos resultados (pedido do autor, 1.5.0), em todos os módulos.

Temporário: arquivo e camada com o nome "Módulo - operação". Salvo: a camada recebe o nome do arquivo.
"""
import ast
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIALOGS = ['evaluation_dialog.py', 'vector_evaluation_dialog.py', 'vector_overlay_dialog.py',
           'monitoring_dialog.py', 'vector_monitoring_dialog.py', 'voronoi_dialog.py',
           'combination_dialog.py', 'rs2_dialog.py', 'signature_dialog.py']
OLD_PREFIXES = ['voronoi_espacial', 'avaliacao_raster', 'avaliacao_atributos', 'avaliacao_sobreposicao',
                'monitoria_raster', 'monitoria_vetorial', "'combinacao'", "'conversao'", "'assinatura'"]
LOADERS = ('QgsRasterLayer', 'QgsVectorLayer', 'materialize_in_memory', 'addRasterLayer', 'addVectorLayer')
# Camadas internas de leitura de entradas (não são resultados nem vão para o projeto).
INTERNAL = {"QgsVectorLayer(text, 'Fonte vetorial', 'ogr')"}


class NomesResultados150(unittest.TestCase):
    def test_funcoes_de_nome(self):
        from geosaga.ui_shared import layer_name, result_name, temporary_destination
        self.assertEqual(result_name('Análises Voronoi', 'Com Atrito'), 'Análises Voronoi - Com Atrito')
        self.assertEqual(result_name('Assinatura'), 'Assinatura')
        self.assertEqual(layer_name('/dados/Bairros 2020.gpkg|layername=x'), 'Bairros 2020')
        path = temporary_destination(result_name('Avaliação', 'Vetorial (Atributos)'), '.gpkg')
        self.assertEqual(os.path.basename(path), 'Avaliação - Vetorial (Atributos).gpkg')
        self.assertEqual(layer_name(path), 'Avaliação - Vetorial (Atributos)')

    def test_sem_prefixos_tecnicos_nem_nomes_fixos(self):
        for name in DIALOGS:
            code = (ROOT / name).read_text(encoding='utf-8')
            calls = [ast.unparse(n) for n in ast.walk(ast.parse(code)) if isinstance(n, ast.Call)
                     and getattr(n.func, 'id', getattr(n.func, 'attr', '')) == 'temporary_destination']
            for call in calls:
                self.assertTrue('result_name(' in call or 'self.RESULT_PREFIX' in call, f'{name}: {call}')
            if 'RESULT_PREFIX = ' in code:
                self.assertIn("RESULT_PREFIX = result_name('Avaliação', ", code, name)
            for old in OLD_PREFIXES:
                self.assertFalse(any(old.strip("'") in c for c in calls), f'{name}: {old}')
            # Camadas carregadas: o nome (2º argumento) nunca é um texto fixo; vem do arquivo.
            for node in ast.walk(ast.parse(code)):
                if not isinstance(node, ast.Call) or len(node.args) < 2:
                    continue
                func = getattr(node.func, 'id', getattr(node.func, 'attr', ''))
                if func in LOADERS and ast.unparse(node) not in INTERNAL:
                    self.assertFalse(isinstance(node.args[1], ast.Constant), f'{name}: {ast.unparse(node)}')
            self.assertNotIn("name = tr('Monitoria vetorial') if temporary", code, name)

    def test_tabelas_de_operacoes(self):
        rs2 = (ROOT / 'rs2_dialog.py').read_text(encoding='utf-8')
        self.assertIn("'Vetor para GeoTIFF'", rs2)
        voronoi = (ROOT / 'voronoi_dialog.py').read_text(encoding='utf-8')
        self.assertIn("VORONOI_MODES = ('Simples', 'Com Massa', 'Com Atrito', 'Com Massa e Atrito')", voronoi)


if __name__ == '__main__':
    unittest.main()
