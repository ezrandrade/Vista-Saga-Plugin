"""Teste integrado em GeoTIFF reais com adaptador mínimo GDAL (ambiente sem PyQGIS).

OBS: adaptador simulado de osgeo, não substitui testes na instalação QGIS.
"""
from pathlib import Path
import csv
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np
import rasterio
from rasterio.transform import from_origin, Affine
from rasterio.windows import Window
from pyproj import CRS

from geosaga.monitoring_engine import run_monitoring


class ReadBand:
    DataType = 3

    def __init__(self, dataset):
        self.dataset = dataset

    def GetNoDataValue(self):
        return self.dataset.src.nodata

    def ReadAsArray(self, x, y, w, h):
        return self.dataset.src.read(1, window=Window(x, y, w, h))


class ReadDataset:
    RasterCount = 1

    def __init__(self, path):
        self.src = rasterio.open(path)
        self.RasterXSize = self.src.width
        self.RasterYSize = self.src.height

    def GetRasterBand(self, _):
        return ReadBand(self)

    def GetProjection(self):
        return self.src.crs.to_wkt() if self.src.crs else ''

    def GetGeoTransform(self):
        return self.src.transform.to_gdal()


class WriteBand:
    def __init__(self, owner):
        self.owner = owner

    def SetNoDataValue(self, nodata):
        self.owner.nodata = nodata

    def WriteArray(self, values, x, y):
        self.owner._begin()
        h, w = values.shape
        self.owner.output.write(values, 1, window=Window(x, y, w, h))


class WriteDataset:
    def __init__(self, path, width, height):
        self.path, self.width, self.height = path, width, height
        self.transform = None
        self.crs = None
        self.nodata = None
        self.output = None
        self.band = WriteBand(self)

    def SetGeoTransform(self, transform):
        self.transform = Affine.from_gdal(*transform)

    def SetProjection(self, projection):
        self.crs = CRS.from_wkt(projection) if projection else None

    def GetRasterBand(self, _):
        return self.band

    def _begin(self):
        if self.output is None:
            self.output = rasterio.open(
                self.path, 'w', driver='GTiff', width=self.width, height=self.height,
                count=1, dtype='int32', transform=self.transform,
                crs=self.crs, nodata=self.nodata, compress='deflate')

    def FlushCache(self):
        if self.output is not None:
            self.output.close()
            self.output = None


class FakeSRS:
    def __init__(self):
        self.crs = None

    def ImportFromWkt(self, wkt):
        self.crs = CRS.from_wkt(wkt)
        return 0

    def IsProjected(self):
        return self.crs.is_projected

    def GetLinearUnits(self):
        return self.crs.axis_info[0].unit_conversion_factor

    def IsSame(self, other):
        return self.crs == other.crs


def adapter():
    gdal = types.ModuleType('osgeo.gdal')
    gdal.GA_ReadOnly = 0
    gdal.GDT_Int32 = 5
    gdal.GDT_CFloat32 = 10
    gdal.GDT_CFloat64 = 11
    gdal.Open = lambda p, access: ReadDataset(p)
    gdal.GetDriverByName = lambda name: types.SimpleNamespace(
        Create=lambda p, w, h, count, dtype, options: WriteDataset(p, w, h))
    osr = types.ModuleType('osgeo.osr')
    osr.SpatialReference = FakeSRS
    osgeo = types.ModuleType('osgeo')
    osgeo.gdal, osgeo.osr = gdal, osr
    return {'osgeo': osgeo, 'osgeo.gdal': gdal, 'osgeo.osr': osr}


class RealTiffsWithAdapter(unittest.TestCase):
    def _make(self, path, array, shift_x=0):
        with rasterio.open(path, 'w', driver='GTiff', width=array.shape[1],
                           height=array.shape[0], count=1, dtype='int16',
                           transform=from_origin(500000 + shift_x, 9000000, 10, 10),
                           crs='EPSG:31985', nodata=-9999) as output:
            output.write(array, 1)

    def test_full_two_pass_workflow(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p, q, out = d/'a.tif', d/'b.tif', d/'transicoes.tif'
            self._make(p, np.array([[1, 1, 2], [-9999, 0, 3]], dtype=np.int16))
            self._make(q, np.array([[2, 1, 2], [1, 0, 2]], dtype=np.int16))
            with patch.dict(sys.modules, adapter()):
                summary = run_monitoring(p, q, out, before_label='1985', after_label='2024')
            self.assertEqual(summary['validos'], 5)
            self.assertEqual(summary['mudancas'], 2)
            self.assertAlmostEqual(summary['area_valida_ha'], .05)
            with rasterio.open(out) as written:
                self.assertEqual(written.nodata, -9999)
                self.assertEqual(written.crs.to_epsg(), 31985)
                self.assertEqual(written.res, (10, 10))
                ids = summary['ids']
                np.testing.assert_array_equal(written.read(1),
                    [[ids[(1., 2.)], ids[(1., 1.)], ids[(2., 2.)]],
                     [-9999, ids[(0., 0.)], ids[(3., 2.)]]])
            with open(summary['matriz'], encoding='utf-8-sig', newline='') as f:
                rows = list(csv.reader(f, delimiter=';'))
            self.assertEqual(rows[-1][-1], '5')
            self.assertIn('1985', Path(summary['resumo']).read_text(encoding='utf8'))

    def test_reject_misaligned_grids(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p, q, out = d/'a.tif', d/'b.tif', d/'c.tif'
            self._make(p, np.ones((2, 2), dtype=np.int16))
            self._make(q, np.ones((2, 2), dtype=np.int16), shift_x=10)
            with patch.dict(sys.modules, adapter()):
                with self.assertRaisesRegex(ValueError, 'Alinhe'):
                    run_monitoring(p, q, out)
            self.assertFalse(out.exists())

    def test_cancel_before_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p, q, out = d/'a.tif', d/'b.tif', d/'c.tif'
            self._make(p, np.ones((2, 2), dtype=np.int16))
            self._make(q, np.ones((2, 2), dtype=np.int16))
            with patch.dict(sys.modules, adapter()):
                with self.assertRaises(InterruptedError):
                    run_monitoring(p, q, out, cancelled=lambda: True)
            self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
