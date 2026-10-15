"""Testes de mapeamento exato RGB -> classes RS2 sem importar QGIS/GDAL."""
import unittest
import numpy as np

from geosaga.rs2_format import RS2Error
from geosaga.rs2_rgb import RS2RGBMapper


class RS2RGBTests(unittest.TestCase):
    def setUp(self):
        self.mapper = RS2RGBMapper([(255, 255, 255, 0), (3, 2, 1, 0),
                                    (10, 120, 250, 0), (0, 0, 0, 0)])

    def test_rgbs_recuperam_codigos(self):
        r = np.array([255, 3, 10, 0], dtype=np.uint8)
        g = np.array([255, 2, 120, 0], dtype=np.uint8)
        b = np.array([255, 1, 250, 0], dtype=np.uint8)
        np.testing.assert_array_equal(self.mapper.map_row(r, g, b), [0, 1, 2, 3])

    def test_transparencia_remapeia_para_fundo(self):
        r = np.array([3, 10], dtype=np.uint8)
        g = np.array([2, 120], dtype=np.uint8)
        b = np.array([1, 250], dtype=np.uint8)
        alpha = np.array([255, 0], dtype=np.uint8)
        np.testing.assert_array_equal(self.mapper.map_row(r, g, b, alpha), [1, 0])

    def test_rgba_transparente_com_rgb_ausente_da_paleta(self):
        r = np.array([253, 3], dtype=np.uint8)
        g = np.array([253, 2], dtype=np.uint8)
        b = np.array([253, 1], dtype=np.uint8)
        alpha = np.array([0, 255], dtype=np.uint8)
        np.testing.assert_array_equal(self.mapper.map_row(r, g, b, alpha), [0, 1])

    def test_cor_desconhecida_identifica_local(self):
        with self.assertRaisesRegex(RS2Error, 'linha 8, coluna 1'):
            self.mapper.map_row(np.array([90], dtype=np.uint8),
                                np.array([91], dtype=np.uint8),
                                np.array([92], dtype=np.uint8), y=7)

    def test_paleta_ambigua_recusada(self):
        with self.assertRaisesRegex(RS2Error, 'mesma cor'):
            RS2RGBMapper([(255, 255, 255), (255, 255, 255)])

    def test_semitransparencia_recusada(self):
        with self.assertRaisesRegex(RS2Error, 'semitransparente'):
            self.mapper.map_row(np.array([3], dtype=np.uint8),
                                np.array([2], dtype=np.uint8),
                                np.array([1], dtype=np.uint8),
                                np.array([128], dtype=np.uint8))


if __name__ == '__main__':
    unittest.main()
