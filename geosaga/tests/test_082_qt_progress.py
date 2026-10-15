"""Regressao de TypeError de progresso float em QGIS 4.2.2/Qt6.

Pode rodar sem QGIS: extrai o metodo e exercita o seu codigo em um simulador.
"""
import ast
import math
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

class FakeProgressDialog:
    def __init__(self):
        self.values = []
    def setValue(self, progress: int):
        if type(progress) is not int:
            raise TypeError("setValue(self, progress: int): argument 1 has unexpected type 'float'")
        self.values.append(progress)

class ProgressQt6Tests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT/'voronoi_dialog.py').read_text(encoding='utf-8')
        tree = ast.parse(self.source)
        klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'VoronoiDialog')
        method = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == '_on_raster_task_progress')
        method.decorator_list = []
        wrapper = ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[]))
        ns = {'isfinite': math.isfinite}
        exec(compile(wrapper,'voronoi_dialog.py','exec'),ns)
        self.fn = ns['_on_raster_task_progress']
        self.dialog = FakeProgressDialog()
        self.obj = SimpleNamespace(_task=object(),_progress_dialog=self.dialog)

    def test_qgs_task_signal_not_connected_directly_to_integer_slot(self):
        self.assertIn('task.progressChanged.connect(self._on_raster_task_progress)',self.source)
        self.assertNotIn('task.progressChanged.connect(dialog.setValue)',self.source)
        self.assertIn('@pyqtSlot(float)',self.source)

    def test_decimal_is_converted_to_integer(self):
        for value, expected in ((0.0,0), (14.75,15), (32.1,32), (100.0,100), (101.8,100), (-2.5,0)):
            self.fn(self.obj,value)
            self.assertEqual(self.dialog.values[-1],expected)
            self.assertIs(type(self.dialog.values[-1]),int)

    def test_invalid_and_stale_updates_ignored(self):
        for value in (math.nan, math.inf, -math.inf):
            self.fn(self.obj,value)
        self.assertEqual(self.dialog.values,[])
        self.obj._task=None
        self.fn(self.obj,20.6)
        self.assertEqual(self.dialog.values,[])
        self.obj._task=object()
        self.obj._progress_dialog=None
        self.fn(self.obj,20.6)
        self.assertEqual(self.dialog.values,[])

if __name__=='__main__':unittest.main()
