"""Regression: final labels/order in the public menu and the seven panel cards."""
import ast
from pathlib import Path
import unittest

from geosaga.tests._support import menu_modules

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["Assinatura", "Monitoria", "Avaliação", "Análises Voronoi",
         "Combinação de Mapas", "Conversão de Formatos", "Sequenciador de Mapas"]
CALLBACKS = ["open_signature", "open_monitoring", "open_interactive", "open_voronoi",
             "open_combination", "open_rs2_converter", "open_sequence"]

class PublicModuleOrderTests(unittest.TestCase):
    def test_menu_labels_and_callbacks_order(self):
        # 1.0.4: o painel intermediário deu lugar ao menu suspenso com os sete módulos.
        self.assertEqual(menu_modules(), list(zip(NAMES, CALLBACKS)))

    def test_panel_labels_and_callbacks_order(self):
        tree=ast.parse((ROOT/'home_dialog.py').read_text(encoding='utf-8'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='HomeDialog')
        meth=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_build_ui')
        assignment=next(n for n in meth.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='modules' for t in n.targets))
        actual=[(x.elts[1].value,x.elts[4].attr,int(x.elts[0].value)) for x in assignment.value.elts]
        self.assertEqual(actual,[(t,c,i) for i,(t,c) in enumerate(zip(NAMES,CALLBACKS),1)])

    def test_ui_module_titles_no_spatial_suffix(self):
        for file in ['plugin.py','home_dialog.py','signature_dialog.py','monitoring_dialog.py',
                     'evaluation_dialog.py','vector_evaluation_dialog.py','vector_overlay_dialog.py']:
            txt=(ROOT/file).read_text(encoding='utf-8')
            for old in ('Assinatura Espacial','Monitoria Espacial','Avaliação Espacial'):
                self.assertNotIn(old,txt, file)

    def test_ids_preserved(self):
        self.assertIn("return 'geosaga'",(ROOT/'provider.py').read_text(encoding='utf-8'))
        for mod,name in [('assinatura','assinatura'),('monitoria','monitoria'),('avaliacao','avaliacao')]:
            self.assertIn(f"return '{name}'",(ROOT/'algorithms'/f'{mod}.py').read_text(encoding='utf-8'))
