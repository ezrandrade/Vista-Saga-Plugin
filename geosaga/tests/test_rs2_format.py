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


class SparseLegendTests(unittest.TestCase):
    """Correção 1.0.5: legenda com códigos não consecutivos, como o Vista SAGA grava.

    Estrutura reproduzida de um RS2 regravado pelo próprio Vista SAGA (pluviometria):
    n = 3, códigos 0, 125 e 158, pares RLE com esses códigos, paleta indexada pelo
    código logo após a matriz e 1.920 bytes residuais no fim do arquivo.
    """

    def setUp(self):
        import tempfile
        from pathlib import Path
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'esparso.rs2'
        self.header = RS2Header(4, 2, 100, 200, 140, 220,
                                ['FUNDO', 'Classe 125', 'Classe 158'],
                                [(255, 255, 255, 0), (167, 235, 106, 0), (106, 119, 235, 0)],
                                codes=[0, 125, 158])
        self.rows = [np.array([125, 125, 158, 0], dtype=np.uint16),
                     np.array([0, 158, 158, 158], dtype=np.uint16)]
        write_rs2(self.path, self.header, self.rows)

    def test_round_trip_keeps_sparse_codes_and_palette_by_code(self):
        reader = RS2Reader(self.path)
        h = reader.header
        self.assertEqual(h.num_classes, 3)
        self.assertEqual(h.legend_codes, [0, 125, 158])
        self.assertEqual(h.colors[1][:3], (167, 235, 106))
        self.assertEqual(h.colors[2][:3], (106, 119, 235))
        self.assertEqual(h.raw_palette[125 * 4:125 * 4 + 3], bytes((167, 235, 106)))
        np.testing.assert_array_equal(np.vstack(list(reader.rows())), np.vstack(self.rows))
        self.assertEqual(reader.validate(), {0: 2, 125: 2, 158: 4})

    def test_trailing_bytes_after_palette_are_tolerated(self):
        data = self.path.read_bytes()
        self.path.write_bytes(data + bytes(1920))
        reader = RS2Reader(self.path)
        self.assertEqual(reader.header.trailing_bytes, 1920)
        self.assertEqual(reader.header.legend_codes, [0, 125, 158])
        self.assertEqual(reader.validate(), {0: 2, 125: 2, 158: 4})
        # Regravação produz o arquivo canônico, sem o resíduo.
        copy = self.path.with_name('copia.rs2')
        write_rs2(copy, reader.header, RS2Reader(self.path).rows())
        self.assertEqual(copy.read_bytes(), data)

    def test_undeclared_code_is_rejected(self):
        with self.assertRaisesRegex(RS2Error, 'não previstos'):
            write_rs2(self.path.with_name('x.rs2'), self.header,
                      [np.array([1, 0, 0, 0], dtype=np.uint16)] * 2)

    def test_invalid_legend_codes_are_rejected(self):
        for codes in ([0, 125, 125], [0, 125, 40000]):
            header = RS2Header(4, 2, 100, 200, 140, 220, ['FUNDO', 'A', 'B'],
                               [(0, 0, 0, 0)] * 3, codes=codes)
            with self.subTest(codes=codes), self.assertRaises(RS2Error):
                write_rs2(self.path.with_name('y.rs2'), header, self.rows)


class EvaluationLegendTests(unittest.TestCase):
    """Correção 1.0.6: estrutura de um RS2 gerado pelo módulo de avaliação do Vista SAGA.

    n = 11 em 2 bytes, seguido do código de CADA classe, inclusive a primeira:
    Nota 1..10 com códigos 1..10 e FUNDO com código 11, por último; sem código 0.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'avaliacao.rs2'
        labels = [f'Nota {i}' for i in range(1, 11)] + ['FUNDO']
        colors = [(i * 20, 0, 0, 0) for i in range(1, 12)]
        self.header = RS2Header(3, 2, 100, 200, 130, 220, labels, colors,
                                codes=list(range(1, 12)))
        self.rows = [np.array([11, 1, 10], dtype=np.uint16),
                     np.array([5, 11, 11], dtype=np.uint16)]
        write_rs2(self.path, self.header, self.rows)

    def test_count_and_first_code_are_two_uint16(self):
        data = self.path.read_bytes()
        # Após 11 bytes de prefixo e 20 de bordas e dimensões: n = 11, código 1, "Nota 1".
        self.assertEqual(data[31:35], bytes.fromhex('0b 00 01 00'))
        self.assertEqual(data[35:42], b'Nota 1\0')

    def test_read_without_code_zero_and_background_last(self):
        reader = RS2Reader(self.path)
        h = reader.header
        self.assertEqual(h.legend_codes, list(range(1, 12)))
        self.assertEqual(h.labels[-1], 'FUNDO')
        self.assertEqual(h.background_code, 11)
        np.testing.assert_array_equal(np.vstack(list(reader.rows())), np.vstack(self.rows))
        self.assertEqual(reader.validate()[11], 3)

    def test_rewrite_is_byte_identical(self):
        copy = self.path.with_name('copia.rs2')
        write_rs2(copy, RS2Reader(self.path).header, RS2Reader(self.path).rows())
        self.assertEqual(copy.read_bytes(), self.path.read_bytes())

    def test_background_code_rules(self):
        self.assertEqual(RS2Header(1, 1, 0, 0, 1, 1, ['FUNDO', 'A'], [(0, 0, 0, 0)] * 2)
                         .background_code, 0)
        self.assertIsNone(RS2Header(1, 1, 0, 0, 1, 1, ['A', 'B'], [(0, 0, 0, 0)] * 2,
                                    codes=[3, 4]).background_code)


class SidecarCodesTests(unittest.TestCase):
    def test_legacy_sidecar_uses_position_as_code(self):
        from geosaga.rs2_format import sidecar_codes
        self.assertEqual(sidecar_codes({'labels': ['FUNDO', 'A', 'B']}), [0, 1, 2])

    def test_sparse_sidecar_codes(self):
        from geosaga.rs2_format import sidecar_codes
        info = {'labels': ['FUNDO', 'Classe 125', 'Classe 158'], 'codes': [0, 125, 158]}
        self.assertEqual(sidecar_codes(info), [0, 125, 158])
        with self.assertRaises(RS2Error):
            sidecar_codes({'labels': ['FUNDO'], 'codes': [0, 125]})
