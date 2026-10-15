"""Testes sem QGIS/GDAL real; integração completa via integration_tiff_vector_qgis.py."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from geosaga.rs2_format import RS2Error
from geosaga.tiff_vector import _legend, _validate_tiff, convert_tif_to_vector
from geosaga.rs2_batch import prepare_batch, Grid


class FakeColorTable:
    def GetCount(self):
        return 3

    def GetColorEntry(self, i):
        return [(255, 255, 255, 255), (8, 140, 22, 255), (33, 44, 211, 255)][i]


class FakeBand:
    def GetCategoryNames(self):
        return ['FUNDO', 'Floresta', 'Pastagem']

    def GetRasterColorTable(self):
        return FakeColorTable()


class GeoTiffVectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.a = self.base / 'a.tif'
        self.b = self.base / 'b.tiff'
        self.a.write_bytes(b'x')
        self.b.write_bytes(b'x')

    def test_legend_from_palette(self):
        legend = _legend(self.a, FakeBand())
        self.assertEqual(legend[0], ('FUNDO', '#FFFFFF'))
        self.assertEqual(legend[1], ('Floresta', '#088C16'))
        self.assertEqual(legend[2], ('Pastagem', '#212CD3'))

    def test_legend_from_rs2_json(self):
        data = {'format': 'Vista SAGA RS2', 'labels': ['FUNDO', 'Caatinga'],
                'colors': [[255, 255, 255], [12, 120, 40]]}
        Path(str(self.a) + '.rs2.json').write_text(json.dumps(data), encoding='utf-8')
        self.assertEqual(_legend(self.a, FakeBand())[1], ('Caatinga', '#0C7828'))

    def test_malformed_sidecar_is_rejected(self):
        Path(str(self.a) + '.rs2.json').write_text('{broken', encoding='utf-8')
        with self.assertRaisesRegex(RS2Error, 'Metadados'):
            _legend(self.a, FakeBand())

    def test_validate_raster_types(self):
        for typ in ('Byte', 'UInt16', 'Int16', 'UInt32', 'Int32', 'Int64', 'Float32', 'Float64'):
            _validate_tiff(self.a, 1, typ)
        _validate_tiff(self.a, 3, 'Byte')
        _validate_tiff(self.a, 4, 'Byte')
        for bands, dtype in ((1, 'CFloat32'), (3, 'UInt16'), (2, 'Byte')):
            with self.assertRaises(RS2Error):
                _validate_tiff(self.a, bands, dtype)

    def test_bad_input_before_gdal(self):
        with self.assertRaisesRegex(RS2Error, 'existente'):
            convert_tif_to_vector(self.base/'nonexistent.tif', self.base/'x.gpkg')
        with self.assertRaisesRegex(RS2Error, 'GeoTIFF'):
            convert_tif_to_vector(self.base/'nonexistent.rs2', self.base/'x.gpkg')

    def test_batch_new_mode_and_preserve_old_mode(self):
        dims = Grid(100, 100, 10., 10., (10, 10, 1010, 1010))
        with patch('geosaga.rs2_batch.inspect_grid', return_value=dims):
            op, plans, got = prepare_batch([self.a, self.b], self.base,
                                           operation=3, vector_extension='.shp')
            self.assertEqual(op, 3)
            self.assertEqual(plans[0][1], self.base/'a_poligonos.shp')
            self.assertEqual(plans[1][1], self.base/'b_poligonos.shp')
            self.assertEqual(got, dims)
            op, plans, _ = prepare_batch([self.a], self.base, operation=1)
            self.assertEqual(op, 1)
            self.assertEqual(plans[0][1], self.base/'a_convertido.rs2')
            with self.assertRaisesRegex(RS2Error, 'não corresponde'):
                prepare_batch([self.a], self.base, operation=2)
            with self.assertRaisesRegex(RS2Error, 'não suportado'):
                prepare_batch([self.a], self.base, operation=3, vector_extension='.exe')


if __name__ == '__main__':
    unittest.main()
