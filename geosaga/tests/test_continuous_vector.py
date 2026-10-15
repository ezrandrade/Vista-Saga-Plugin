"""Testes de discriminação de Float32/Float64 independente da instalação QGIS."""
import unittest
from unittest.mock import Mock
import numpy as np

from geosaga.continuous_vector import (
    class_edges, class_intervals, classify_array, discretize_tiff,
    valid_values, _scan_range,
)
from geosaga.rs2_format import RS2Error


class FloatVectorTests(unittest.TestCase):
    def test_float32_fractional_with_nodata_and_zero_legitimate(self):
        values = np.array([[-9999, 0.0, 0.99, 1.0, 1.99, 2.0, 5.0,
                            np.nan, np.inf]], dtype=np.float32)
        edges = class_edges(0.0, 5.0, 5)
        actual = classify_array(values, edges, -9999.0)
        np.testing.assert_array_equal(actual, [[0, 1, 1, 2, 2, 3, 5, 0, 0]])

    def test_float64_fractions(self):
        values = np.array([[0.25, 0.5, 0.7499, 0.75, 1.0]], dtype=np.float64)
        codes = classify_array(values, class_edges(0.0, 1.0, 4))
        np.testing.assert_array_equal(codes, [[2, 3, 3, 4, 4]])

    def test_mask_nodata_nan_and_finite_zero(self):
        data = np.array([0., -9999., np.nan, -np.inf, np.inf, 3.])
        np.testing.assert_array_equal(valid_values(data, -9999.),
                                      [True, False, False, False, False, True])
        np.testing.assert_array_equal(valid_values(data, None),
                                      [True, True, False, False, False, True])

    def test_constant_float_single_valid_class(self):
        edges = class_edges(4.25, 4.25, 5)
        self.assertEqual(len(edges), 2)
        np.testing.assert_array_equal(classify_array(np.array([4.25, 4.25]), edges), [1, 1])
        self.assertEqual(class_intervals(edges)[1][0], 'Valor 4.25')

    def test_intervals_are_left_closed_and_last_closed(self):
        labels = class_intervals(class_edges(-1., 1., 2))
        self.assertEqual(labels[1], ('[-1; 0)', -1.0, 0.0))
        self.assertEqual(labels[2], ('[0; 1]', 0.0, 1.0))

    def test_invalid_bins_and_invalid_range(self):
        for count in (0, 1, 21, 200, 3.2):
            with self.assertRaises(RS2Error):
                class_edges(1, 9, count)
        for min_, max_ in ((float('nan'), 4), (2, 1), (4, float('inf'))):
            with self.assertRaises(RS2Error):
                class_edges(min_, max_, 5)

    def test_no_valid_pixels_rejected(self):
        band = Mock()
        band.GetNoDataValue.return_value = -9999.
        band.ReadAsArray.return_value = np.array([[-9999., np.nan]])
        with self.assertRaisesRegex(RS2Error, 'não contém pixels válidos'):
            _scan_range(band, 2, 1, lambda _: None)

    def test_range_ignores_nodata_values(self):
        band = Mock()
        band.GetNoDataValue.return_value = -9999.
        band.ReadAsArray.return_value = np.array([[-9999., 0.0, 8.0, np.inf]])
        self.assertEqual(_scan_range(band, 4, 1, lambda _: None), (0.0, 8.0))

    def test_discretizer_gdal_fake_correct_output_and_metadata(self):
        data = np.array([[-9999., 0., 1.], [2., 3., 4.], [np.nan, 5., 0.]],
                        dtype=np.float32)
        class FakeBand:
            def __init__(self, raw): self.raw = raw; self.nodata = None
            def GetNoDataValue(self): return -9999.0 if self.nodata is None else self.nodata
            def ReadAsArray(self, x, y, w, n): return self.raw[y:y+n, x:x+w]
            def WriteArray(self, rows, x, y): self.raw[y:y+rows.shape[0], x:x+rows.shape[1]] = rows
            def SetNoDataValue(self, val): self.nodata = val
            def FlushCache(self): pass
        class FakeDs:
            RasterXSize, RasterYSize = 3, 3
            def __init__(self, array): self.band = FakeBand(array); self.geotransform = None; self.projection = None
            def GetRasterBand(self, n): return self.band
            def GetGeoTransform(self, can_return_null=False): return (100, 10, 0, 200, 0, -10)
            def GetProjectionRef(self): return 'WKT'
            def SetGeoTransform(self, gt): self.geotransform = gt
            def SetProjection(self, wkt): self.projection = wkt
            def FlushCache(self): pass
        src = FakeDs(data)
        dest = FakeDs(np.zeros_like(data, dtype=np.uint8))
        class FakeDriver:
            def Create(self, *args, **kwargs): return dest
        class FakeGDAL:
            GDT_Byte = 1
            @staticmethod
            def GetDriverByName(key): return FakeDriver()
        mapping = discretize_tiff(FakeGDAL(), src, '/tmp/mock.tif', 5, lambda _: None)
        self.assertEqual(dest.geotransform, src.GetGeoTransform())
        self.assertEqual(dest.projection, 'WKT')
        self.assertEqual(dest.band.nodata, 0)
        np.testing.assert_array_equal(dest.band.raw,
                         [[0, 1, 2], [3, 4, 5], [0, 5, 1]])
        self.assertEqual(len(mapping), 5)
        self.assertEqual(mapping[1][1], 0.0)
        self.assertEqual(mapping[5][2], 5.0)


if __name__ == '__main__':
    unittest.main()
