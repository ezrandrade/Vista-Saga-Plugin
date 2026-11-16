"""Cópia das tabelas de resultado para planilhas (1.2.0)."""
import unittest
from pathlib import Path

from geosaga.ui_shared import spreadsheet_cell, table_to_tsv

ROOT = Path(__file__).resolve().parents[1]


class TableCopyTests(unittest.TestCase):
    def test_decimal_point_follows_language(self):
        self.assertEqual(spreadsheet_cell('3.940', ','), '3,940')
        self.assertEqual(spreadsheet_cell('0.143%', ','), '0,143%')
        self.assertEqual(spreadsheet_cell('3.940', '.'), '3.940')
        self.assertEqual(spreadsheet_cell('1234', ','), '1234')

    def test_text_is_not_touched(self):
        self.assertEqual(spreadsheet_cell('1.0 → 2.0', ','), '1.0 → 2.0')
        self.assertEqual(spreadsheet_cell('Permaneceu: CANAVIAL', ','), 'Permaneceu: CANAVIAL')
        self.assertEqual(spreadsheet_cell('a\tb\nc'), 'a b c')

    def test_tsv_has_header_and_rows(self):
        text = table_to_tsv(['Transição', 'Área (ha)'], [['Permaneceu: CANAVIAL', '548.808']], ',')
        self.assertEqual(text, 'Transição\tÁrea (ha)\nPermaneceu: CANAVIAL\t548,808\n')

    def test_monitoring_tables_wired(self):
        for name in ('monitoring_dialog.py', 'vector_monitoring_dialog.py'):
            self.assertIn('enable_table_copy(self.table)', (ROOT / name).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
