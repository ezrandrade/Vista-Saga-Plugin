"""Verificações estáticas de integração nas 3 modalidades sem PyQGIS."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReportingWiringTests(unittest.TestCase):
    def test_raster_has_both_report_options(self):
        src = (ROOT / 'evaluation_dialog.py').read_text()
        self.assertIn('self.txt_check', src)
        self.assertIn('self.csv_check', src)
        self.assertIn("'legendas': [e['labels']", src)
        engine = (ROOT / 'raster_engine.py').read_text()
        self.assertIn('add_raster_combinations(combinations, arrays, valid)', engine)
        self.assertIn('create_reports(report_txt, report', engine)

    def test_vector_modes_write_area_fields_and_reports(self):
        writer = (ROOT / 'vector_evaluation_writer.py').read_text()
        for field in ('AREA_M2', 'AREA_HA', 'PCT_AREA'):
            self.assertIn(field, writer)
        self.assertIn('create_reports(report_t, report_c', writer)
        self.assertIn('_publish_set(pairs, parent)', writer)
        attrs = (ROOT / 'vector_evaluation_dialog.py').read_text()
        overlay = (ROOT / 'vector_overlay_dialog.py').read_text()
        for src in (attrs, overlay):
            self.assertIn('report_csv=self.csv_check.isChecked()', src)
            self.assertIn('report_txt=self.txt_check.isChecked()', src)
        self.assertIn('report_criteria=', (ROOT/'vector_overlay_engine.py').read_text())


if __name__ == '__main__':
    unittest.main()
