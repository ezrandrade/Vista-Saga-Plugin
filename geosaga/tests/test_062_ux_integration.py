"""Teste de regressão estrutural: execução Qt/PyQGIS deve ser homologada no QGIS."""
from pathlib import Path
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]

def source(name):
    return (ROOT / name).read_text(encoding='utf-8')

class TabsUX062(unittest.TestCase):
    def test_five_cards_share_identical_factory(self):
        panel = source('home_dialog.py')
        for module in ('Avaliação Espacial', 'Monitoria Espacial', 'Assinatura Espacial',
                       'Combinação de Mapas', 'Conversão de Formatos'):
            self.assertIn(module, panel)
        self.assertIn('self._add_card(cards, index // 3, index % 3', panel)
        self.assertEqual(panel.count('self._add_card('), 1)
        self.assertIn('Escolha um módulo para começar.', panel)
        self.assertIn('Uma nova janela será aberta para cada módulo.', panel)
        self.assertNotIn('A Avaliação Espacial possui', panel)
        self.assertNotIn('Ferramentas complementares:', panel)
        self.assertIn('Não contém código do programa original', panel)
        self.assertIn('Esdras Andrade', panel)
        self.assertIn('IGDEMA', panel)
        self.assertIn('UFAL', panel)
        self.assertIn('description_label = QLabel(description)', panel)

    def test_evaluation_contains_embedded_modalities(self):
        code = source('evaluation_dialog.py')
        self.assertIn("'Vetorial — atributos'", code)
        self.assertIn("'Vetorial — sobreposição'", code)
        self.assertIn('self.attributes_scroll.setWidgetResizable(True)', code)
        self.assertIn('self.overlay_scroll.setWidgetResizable(True)', code)
        self.assertIn('scroll.setWidget(dialog)', code)
        self.assertIn('dialog_type(self.iface, parent=self, embedded=True)', code)
        self.assertNotIn('dialog.setWindowFlags(Qt.WindowType.Widget)', code)
        self.assertIn('QgsMessageLog.logMessage', code)
        self.assertIn('class VectorEvaluationDialog(QWidget)', source('vector_evaluation_dialog.py'))
        self.assertIn('self._close_form', source('vector_evaluation_dialog.py'))
        self.assertIn('def _on_analysis_tab_changed', code)
        self.assertIn('host.open_vector_overlay()', source('vector_evaluation_dialog.py'))

    def test_monitoring_contains_embedded_vector_and_shared_results(self):
        code = source('monitoring_dialog.py')
        self.assertIn('self.vector_tab.setWidget(dialog)', code)
        self.assertIn("self.results_tab.addTab(results_page, 'Vetorial')", code)
        self.assertIn('dialog.tabs.removeTab(1)', code)
        self.assertIn('self.tabs.currentChanged.connect(self._on_mode_changed)', code)
        self.assertIn('control.setVisible(is_raster)', code)
        self.assertIn('self.results_tab.setCurrentIndex(0)', code)
        self.assertIn('dialog._embedded_results_host', code)
        self.assertIn('class VectorMonitoringDialog(QWidget)', source('vector_monitoring_dialog.py'))
        self.assertIn('QgsMessageLog.logMessage', code)
        vector = source('vector_monitoring_dialog.py')
        self.assertIn('result_tabs.setCurrentIndex(1)', vector)
        self.assertIn('main_tabs.setCurrentIndex(2)', vector)

    def test_previous_engines_unchanged(self):
        baseline = Path('/mnt/data/Vista_Saga_Plugin_QGIS4_v0.6.1_INTERFACE_TEMPORARIOS.zip')
        if not baseline.exists():
            self.skipTest('Base de referência ausente')
        engines = ('raster_engine.py', 'monitoring_engine.py', 'vector_overlay_engine.py',
                   'vector_monitoring_engine.py', 'signature_engine.py',
                   'combination_raster.py', 'combination_vector.py', 'rs2_format.py')
        with ZipFile(baseline) as z:
            for filename in engines:
                self.assertEqual((ROOT / filename).read_bytes(), z.read('geosaga/' + filename), filename)

if __name__ == '__main__':
    unittest.main()
