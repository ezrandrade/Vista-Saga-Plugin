"""Testes unitários da quinta operação sem GDAL/QGIS instalados."""
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest

from geosaga.rs2_format import RS2Error
from geosaga.vector_raster import (split_vector_source, raster_dimensions,
                                  field_mode, normalize_color, convert_vector_to_tif)


class VectorRasterTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.vector = self.folder/'classes.gpkg'
        self.vector.write_bytes(b'stub')

    def test_vector_source_with_name(self):
        p, name, index = split_vector_source(str(self.vector)+'|layername=ambiental')
        self.assertEqual((p, name, index), (self.vector, 'ambiental', None))
        p, name, index = split_vector_source(str(self.vector)+'|layerid=2')
        self.assertEqual((p, name, index), (self.vector, None, 2))

    def test_reject_non_vector_or_missing_file(self):
        tiff = self.folder/'classes.tif'
        tiff.touch()
        with self.assertRaisesRegex(RS2Error, 'vetor local'):
            split_vector_source(tiff)
        with self.assertRaisesRegex(RS2Error, 'não encontrado'):
            split_vector_source(self.folder/'faltante.gpkg')
        with self.assertRaisesRegex(RS2Error, 'Opção não reconhecida'):
            split_vector_source(str(self.vector)+'|subset=abc')

    def test_grid_exact_and_rounded(self):
        cols, rows, gt = raster_dimensions((100, 143, 150, 190), 10)
        self.assertEqual((cols, rows, gt), (5, 4, (100., 10., 0., 190., 0., -10.)))
        self.assertEqual(raster_dimensions((100, 140, 150, 190), 10)[:2], (4, 4))

    def test_single_point_produces_one_pixel(self):
        cols, rows, gt = raster_dimensions((100, 100, 200, 200), 10)
        self.assertEqual((cols, rows, gt), (1, 1, (95., 10., 0., 205., 0., -10.)))

    def test_limits_nonfinite_and_large(self):
        for bb, res in [((0, 10, 0, 10), 0), ((0, 10, 0, 10), -10),
                        ((5, 3, 0, 10), 1), ((0, 10, 0, 10), float('nan')),
                        ((0, 1e7, 0, 1e7), 1)]:
            with self.subTest(bb=bb, res=res), self.assertRaises(RS2Error):
                raster_dimensions(bb, res)

    def test_field_types(self):
        ogr = SimpleNamespace(OFTInteger=0, OFTInteger64=12, OFTReal=2, OFTString=4)
        self.assertEqual(field_mode(0, ogr), 'int')
        self.assertEqual(field_mode(12, ogr), 'int')
        self.assertEqual(field_mode(2, ogr), 'real')
        self.assertEqual(field_mode(4, ogr), 'text')
        with self.assertRaisesRegex(RS2Error, 'campo escolhido'):
            field_mode(9, ogr)

    def test_color_hex_strict(self):
        self.assertEqual(normalize_color(' #a0bF10 '), '#A0BF10')
        for value in ('#abcdef00', '#xz3456', 'orange', '', None):
            self.assertEqual(normalize_color(value), '')

    def test_missing_file_before_osgeo_import(self):
        with self.assertRaisesRegex(RS2Error, 'não encontrado'):
            convert_vector_to_tif(self.folder/'missing.gpkg', self.folder/'out.tif', 'CODIGO', 10)

    def test_ui_unchanged_modes_and_new_mode_present(self):
        src = (Path(__file__).resolve().parents[1] / 'rs2_dialog.py').read_text(encoding='utf-8')
        for label in ('RS2 → GeoTIFF', 'GeoTIFF → RS2', 'RS2 → Vetor',
                      'GeoTIFF → Vetor', 'Vetor → GeoTIFF'):
            self.assertIn(label, src)
        self.assertIn('self.vector_field.currentText()', src)
        self.assertIn('self.pixel_size.value()', src)
        self.assertIn('self.vector_all_touched.isChecked()', src)


if __name__ == '__main__':
    unittest.main()
