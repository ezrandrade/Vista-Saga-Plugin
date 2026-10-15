"""Smoke-test da integração de UI e do empacotamento 0.4.3 sem QGIS."""
import unittest
from pathlib import Path


class WiringTests(unittest.TestCase):
    def test_menu_opens_vector_dialog(self):
        root = Path(__file__).resolve().parents[1]
        dialog = (root / 'monitoring_dialog.py').read_text(encoding='utf-8')
        self.assertIn('self.vector_tab = QScrollArea()', dialog)
        self.assertIn('VectorMonitoringDialog', dialog)
        self.assertIn('def _open_vector_monitoring', dialog)

    def test_vector_engine_uses_intersection_and_safe_publish(self):
        root = Path(__file__).resolve().parents[1]
        engine = (root / 'vector_monitoring_engine.py').read_text(encoding='utf-8')
        self.assertIn("processing.run('native:intersection'", engine)
        self.assertIn('_publish_set(pairs, parent)', engine)
        self.assertIn('validate_vector_monitoring', engine)

    def test_metadata_version(self):
        root = Path(__file__).resolve().parents[1]
        meta = (root / 'metadata.txt').read_text(encoding='utf-8')
        self.assertIn('version=1.0.1', meta)


if __name__ == '__main__':
    unittest.main()
