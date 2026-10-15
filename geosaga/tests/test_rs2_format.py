"""Testes locais sem dependência do QGIS, com matrizes RS2 sintéticas."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from geosaga.rs2_format import RS2Error, RS2Header, RS2Reader, write_rs2


class RS2FormatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'teste.rs2'
        self.matrix = np.array([
            [0, 0, 1, 1, 0, 2, 2, 2],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [3, 3, 3, 3, 3, 3, 3, 3],
            [0, 1, 0, 2, 0, 3, 0, 1],
            [0, 0, 0, 3, 3, 0, 0, 0],
        ], dtype=np.uint16)
        self.header = RS2Header(8, 5, 178260, 8900320, 178340, 8900370,
                                ['FUNDO', 'VÁRZEA', 'FLORESTA', 'TERRAÇO'],
                                [(255,255,255,0), (1,2,3,0), (22,33,44,0),
                                 (200,210,220,0)])

    def tearDown(self):
        self.temp.cleanup()

    def test_roundtrip_preserves_matrix_and_legend(self):
        write_rs2(self.path, self.header, iter(self.matrix))
        r = RS2Reader(self.path)
        self.assertTrue(np.array_equal(np.stack(list(r.rows())), self.matrix))
        self.assertEqual(r.header.labels[1], 'VÁRZEA')
        self.assertEqual(r.header.colors[3], (200,210,220,0))
        self.assertEqual((r.header.pixel_x, r.header.pixel_y), (10,10))
        self.assertEqual(sum(r.validate().values()), 8*5)

    def test_rewrite_is_byte_identical(self):
        write_rs2(self.path, self.header, iter(self.matrix))
        origin = self.path.read_bytes()
        rdr = RS2Reader(self.path)
        rebuilt = self.path.with_name('copia.rs2')
        write_rs2(rebuilt, rdr.header, rdr.rows())
        self.assertEqual(rebuilt.read_bytes(), origin)

    def test_reject_noninteger_or_unknown_category(self):
        bad = self.matrix.copy()
        bad[0,0] = 4
        with self.assertRaises(RS2Error):
            write_rs2(self.path, self.header, iter(bad))
        self.assertFalse(self.path.exists())

    def test_reject_corrupt_row(self):
        write_rs2(self.path, self.header, iter(self.matrix))
        b = bytearray(self.path.read_bytes())
        data_offset = RS2Reader(self.path).header.data_offset
        b[data_offset] = 7  # primeiro índice de linha deveria ser 1
        self.path.write_bytes(b)
        with self.assertRaises(RS2Error):
            list(RS2Reader(self.path).rows())

    def test_read_reject_malformed_header(self):
        self.path.write_bytes(b'\0' * 512)
        with self.assertRaises(RS2Error):
            RS2Reader(self.path)


if __name__ == '__main__':
    unittest.main()
