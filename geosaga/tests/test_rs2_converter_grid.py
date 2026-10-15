"""Testes das regras de georreferenciamento e autodetecção do conversor."""
import unittest
from types import SimpleNamespace

from geosaga.rs2_format import RS2Error
from geosaga.rs2_converter import _validated_grid, _parse_bounds, convert_tif_to_rs2
from geosaga.rs2_rgb import discover_rgb_palette, RS2RGBMapper
import numpy as np


class FakeRGB:
    RasterXSize = 3
    RasterYSize = 2
    RasterCount = 3
    def ReadAsArray(self, x, y, w, h):
        rgb = np.array([
            [[255, 25, 5], [255, 5, 25]],
            [[255, 15, 2], [255, 2, 15]],
            [[255, 10, 1], [255, 1, 10]]
        ], dtype=np.uint8)
        return rgb[:, y:y+h, x:x+w]


class ConverterGridTests(unittest.TestCase):
    def test_manual_bounds_integer_order(self):
        self.assertEqual(_parse_bounds('178260,8900320,178290,8900340', 3, 2),
                         (178260, 8900320, 178290, 8900340))

    def test_missing_georef_requires_manual_grid(self):
        ds = SimpleNamespace(RasterXSize=3, RasterYSize=2,
                             GetGeoTransform=lambda can_return_null: None)
        with self.assertRaisesRegex(RS2Error, 'Extensão manual'):
            _validated_grid(ds)
        self.assertEqual(_validated_grid(ds, '178260,8900320,178290,8900340'),
                         (178260, 8900320, 178290, 8900340))

    def test_reject_fractional_or_invalid_coordinates(self):
        for invalid in ('1.5,2,30,40', '10,10,5,20', '20,30,40', '-5,10,20,30'):
            with self.subTest(invalid=invalid), self.assertRaises(RS2Error):
                _parse_bounds(invalid, 3, 2)

    def test_rs2_in_tiff_conversion_rejected_before_open(self):
        with self.assertRaisesRegex(RS2Error, 'escolha RS2 → GeoTIFF'):
            convert_tif_to_rs2('USO.rs2', 'saída.rs2')

    def test_rgb_palette_generated_from_input(self):
        labels, colors = discover_rgb_palette(FakeRGB())
        self.assertEqual(labels[0], 'FUNDO (branco/transparente)')
        self.assertEqual(colors[0][:3], (255, 255, 255))
        self.assertEqual(len(labels), 3)
        ds = FakeRGB()
        mapper = RS2RGBMapper(colors)
        data = ds.ReadAsArray(0, 0, 3, 1)
        row = mapper.map_row(data[0, 0], data[1, 0], data[2, 0])
        self.assertEqual(int(row[0]), 0)
        self.assertEqual(len(set(row)), 3)


if __name__ == '__main__':
    unittest.main()
