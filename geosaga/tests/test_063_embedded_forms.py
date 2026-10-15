"""Test the structural contract of reusable QWidget forms without a QGIS runtime."""
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]

def read(name):
    return (ROOT / name).read_text(encoding='utf-8')

class EmbeddedFormsRegression(unittest.TestCase):
    def test_vector_evaluation_is_widget_with_both_modes(self):
        text = read('vector_evaluation_dialog.py')
        tree = ast.parse(text)
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'VectorEvaluationDialog')
        self.assertEqual([n.id for n in cls.bases], ['QWidget'])
        self.assertIn('embedded=False', text)
        self.assertIn('self._embedding_host = parent if embedded else None', text)
        self.assertNotIn('self.setModal(False)', text)
        self.assertIn('host.close()', text)
        self.assertIn('self.close()', text)

    def test_overlay_inherits_embeddable_base(self):
        text = read('vector_overlay_dialog.py')
        self.assertIn('class VectorOverlayEvaluationDialog(VectorEvaluationDialog)', text)
        self.assertIn('super()._build()', text)
        self.assertIn('Empilhar mapas vetoriais', text)

    def test_embedded_pages_handle_errors_and_protect_running_work(self):
        text = read('evaluation_dialog.py')
        self.assertIn('self.overlay_scroll.setWidgetResizable(True)', text)
        self.assertIn('dialog_type(self.iface, parent=self, embedded=True)', text)
        self.assertIn('scroll.setWidget(dialog)', text)
        self.assertNotIn('dialog.close_button.clicked.disconnect()', text)
        self.assertIn('QgsMessageLog.logMessage(details', text)
        self.assertIn("getattr(self, name, None), 'running', False", text)

    def test_monitoring_same_reusable_widget_design(self):
        text = read('vector_monitoring_dialog.py')
        self.assertIn('class VectorMonitoringDialog(QWidget)', text)
        self.assertNotIn('self.setModal(False)', text)
        text = read('monitoring_dialog.py')
        self.assertIn('parent=self, embedded=True', text)
        self.assertIn('self.vector_tab.setWidget(dialog)', text)

    def test_panel_credits_and_cards(self):
        text = read('home_dialog.py')
        self.assertEqual(text.count("'Abrir "), 7)
        for key in ('Avaliação Espacial', 'Monitoria Espacial', 'Assinatura Espacial',
                    'Combinação de Mapas', 'Conversão de Formatos',
                    'Não contém código do programa original', 'Esdras Andrade', 'IGDEMA', 'UFAL'):
            self.assertIn(key, text)
        self.assertIn('description_label = QLabel(description)', text)
