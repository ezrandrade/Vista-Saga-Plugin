"""Regressão estática de menus, botões e identificadores estáveis (sem PyQGIS)."""
import unittest
from pathlib import Path
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def source(name):
    return (ROOT / name).read_text(encoding='utf-8')


class UiConsistencyTests(unittest.TestCase):
    def test_module_names_on_panel_and_menu(self):
        for title in ('Avaliação', 'Monitoria', 'Assinatura'):
            self.assertIn(title, source('home_dialog.py'))
            self.assertIn(title, source('plugin.py'))

    def test_raster_evaluation_can_close_after_task(self):
        text = source('evaluation_dialog.py')
        self.assertIn("self.close_button = button('Fechar', self.close)", text)
        self.assertIn('self.close_button.setEnabled(False)', text)
        self.assertIn('self.close_button.setEnabled(True)', text)

    def test_monitoring_can_close_after_task(self):
        text = source('monitoring_dialog.py')
        self.assertIn("self.close_button = QPushButton(tr('Fechar'))", text)
        self.assertIn('self.close_button.clicked.connect(self.close)', text)
        self.assertIn('self.close_button.setEnabled(False)', text)
        self.assertIn('self.close_button.setEnabled(True)', text)

    def test_vector_evaluations_can_close(self):
        self.assertIn("self.close_button = button('Fechar', self._close_form)", source('vector_evaluation_dialog.py'))
        for name in ('vector_evaluation_dialog.py', 'vector_overlay_dialog.py'):
            text = source(name)
            self.assertIn('self.close_button.setEnabled(False)', text)
            self.assertIn('self.close_button.setEnabled(True)', text)

    def test_legacy_ids_still_unchanged(self):
        for name, alg in [('monitoria.py', 'monitoria'), ('assinatura.py', 'assinatura')]:
            self.assertIn(f"return '{alg}'", source('algorithms/' + name))
        self.assertIn("'formato': 'geosaga-avaliacao'", source('evaluation_dialog.py'))

    def test_version(self):
        _support.assert_release_version(self)
