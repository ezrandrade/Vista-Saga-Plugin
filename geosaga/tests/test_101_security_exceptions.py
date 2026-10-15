"""Regression test for two Bandit B110 findings in RS2/GeoTIFF vector styling."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'rs2_dialog.py'

class SecurityExceptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding='utf-8')
        tree = ast.parse(cls.source)
        dialog = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                      and n.name == 'RS2ConverterDialog')
        cls.methods = {n.name: n for n in dialog.body
                       if isinstance(n, ast.FunctionDef)}

    def test_no_silent_exceptions_in_vector_styling(self):
        for method in ('_style_vector', '_style_tiff_vector'):
            with self.subTest(method=method):
                exceptions = [n for n in ast.walk(self.methods[method])
                              if isinstance(n, ast.ExceptHandler)]
                self.assertEqual(len(exceptions), 1)
                catch = exceptions[0]
                self.assertIsNotNone(catch.name)
                self.assertFalse(any(isinstance(n, ast.Pass)
                                     for n in ast.walk(catch)))

    def test_caught_exception_is_logged_as_warning(self):
        for method in ('_style_vector', '_style_tiff_vector'):
            with self.subTest(method=method):
                catch = next(n for n in ast.walk(self.methods[method])
                             if isinstance(n, ast.ExceptHandler))
                calls = [n for n in ast.walk(catch) if isinstance(n, ast.Call)]
                self.assertTrue(any(isinstance(n.func, ast.Attribute)
                                    and n.func.attr == 'logMessage'
                                    and isinstance(n.func.value, ast.Name)
                                    and n.func.value.id == 'QgsMessageLog'
                                    for n in calls))
                self.assertIn('Qgis.MessageLevel.Warning',
                              ast.get_source_segment(self.source, catch))

    def test_no_broad_silent_handlers_in_release_file(self):
        tree = ast.parse(self.source)
        for catch in (n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)):
            is_broad = catch.type is None or (
                isinstance(catch.type, ast.Name) and catch.type.id in ('Exception', 'BaseException'))
            if is_broad:
                self.assertFalse(len(catch.body) == 1 and isinstance(catch.body[0], ast.Pass))
