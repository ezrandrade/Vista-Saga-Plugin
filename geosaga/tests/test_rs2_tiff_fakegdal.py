"""Exercita o escritor RS2->TIFF com GDAL simulado, sem dependência QGIS."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np

from geosaga.rs2_format import RS2Header, write_rs2
from geosaga.rs2_converter import convert_rs2_to_tif


class FakeBand:
    def __init__(self):
        self.rows = []
    def SetNoDataValue(self, x): self.nodata = x
    def SetCategoryNames(self, names): self.names = names
    def SetRasterColorTable(self, table): self.table = table
    def SetRasterColorInterpretation(self, kind): self.kind = kind
    def SetMetadataItem(self, a, b): pass
    def WriteArray(self, arr, xoff=0, yoff=0): self.rows.append(arr.copy())
    def FlushCache(self): pass


class FakeDataset:
    def __init__(self, filename):
        self.name = Path(filename)
        self.name.write_bytes(b'initial TIFF')
        self.band = FakeBand()
    def SetGeoTransform(self, transform): self.transform = transform
    def SetProjection(self, projection): self.projection = projection
    def GetRasterBand(self, number): return self.band
    def FlushCache(self):
        self.name.write_bytes(b'converted TIFF')
        Path(str(self.name) + '.aux.xml').write_text('<PAMDataset/>')


class FakeDriver:
    def Create(self, name, width, height, bands, datatype, options):
        return FakeDataset(name)


class FakeColorTable:
    def SetColorEntry(self, i, entry): pass


class FakeGdal:
    GDT_Byte = 1
    GDT_UInt16 = 2
    GCI_PaletteIndex = 3
    ColorTable = FakeColorTable
    def GetDriverByName(self, driver):
        return FakeDriver() if driver == 'GTiff' else None


class TestFakeGdal(unittest.TestCase):
    def test_tiff_is_replaced_with_its_auxiliaries(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            h = RS2Header(4, 2, 100, 200, 140, 220,
                          ['FUNDO', 'BOSQUE'], [(255,255,255,0), (10,20,30,0)])
            source = p / 'source.rs2'
            write_rs2(source, h, iter(np.ones((2, 4), dtype=np.uint16)))
            dest = p / 'result.tif'
            dest.write_bytes(b'old')
            Path(str(dest) + '.rs2.json').write_text('old json')
            Path(str(dest) + 'w').write_text('old tifw')
            with patch('geosaga.rs2_converter._gdal', return_value=(FakeGdal(), None)):
                result = convert_rs2_to_tif(source, dest)
            self.assertEqual(result, dest)
            self.assertEqual(dest.read_bytes(), b'converted TIFF')
            self.assertEqual(Path(str(dest) + '.aux.xml').read_text(), '<PAMDataset/>')
            self.assertTrue(dest.with_suffix('.tfw').exists())
            self.assertFalse(Path(str(dest) + 'w').exists())
            meta = json.loads(Path(str(dest) + '.rs2.json').read_text())
            self.assertEqual(meta['labels'], ['FUNDO', 'BOSQUE'])
            self.assertEqual(meta['width'], 4)
            self.assertFalse(Path(str(dest) + '.part.tif').exists())


if __name__ == '__main__':
    unittest.main()
