"""Testes da sexta operação do conversor: Vetor → RS2.

Os testes de planejamento (grade, códigos, legenda) não dependem de GDAL.
Os testes de conversão real usam GDAL/OGR quando disponíveis e verificam,
célula a célula, o RS2 lido de volta pelo leitor independente ``RS2Reader``.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from geosaga.rs2_format import RS2Error, RS2Header, RS2Reader, write_rs2
from geosaga.vector_rs2 import (RS2Grid, convert_vector_to_rs2, default_color,
                                extent_intersects_grid, grid_from_reference,
                                plan_codes, plan_rs2_grid)

try:
    from osgeo import gdal, ogr, osr
    gdal.UseExceptions()
    HAS_GDAL = True
except ImportError:  # ambiente de desenvolvimento sem bindings GDAL
    HAS_GDAL = False


class GridPlanTests(unittest.TestCase):
    def test_aligned_extent_is_kept(self):
        grid = plan_rs2_grid((100, 140, 200, 220), 10)
        self.assertEqual(grid, RS2Grid(4, 2, 100, 200, 140, 220))
        self.assertEqual(grid.geotransform, (100., 10., 0., 220., 0., -10.))

    def test_fractional_extent_snaps_outwards_to_pixel_multiples(self):
        grid = plan_rs2_grid((103.4, 136.2, 201.9, 218.7), 10)
        self.assertEqual(grid, RS2Grid(4, 2, 100, 200, 140, 220))

    def test_utm_south_coordinates(self):
        grid = plan_rs2_grid((812345.6, 815000.0, 8901234.5, 8903000.0), 30)
        self.assertEqual((grid.xmin, grid.ymin), (812340, 8901210))
        self.assertEqual(grid.xmax - grid.xmin, grid.width * 30)
        self.assertEqual(grid.ymax - grid.ymin, grid.height * 30)

    def test_point_gets_one_cell(self):
        self.assertEqual(plan_rs2_grid((105, 105, 205, 205), 10),
                         RS2Grid(1, 1, 100, 200, 110, 210))

    def test_fractional_pixel_size_is_rejected(self):
        with self.assertRaisesRegex(RS2Error, 'inteiro positivo'):
            plan_rs2_grid((0, 100, 0, 100), 2.5)
        with self.assertRaisesRegex(RS2Error, 'inteiro positivo'):
            plan_rs2_grid((0, 100, 0, 100), 0)

    def test_negative_coordinates_are_rejected(self):
        with self.assertRaisesRegex(RS2Error, 'não negativas'):
            plan_rs2_grid((-50, 100, 0, 100), 10)

    def test_rs2_side_and_cell_limits(self):
        with self.assertRaisesRegex(RS2Error, '65535'):
            plan_rs2_grid((0, 70000, 0, 10), 1)
        with self.assertRaisesRegex(RS2Error, '100 milhões'):
            plan_rs2_grid((0, 20000, 0, 20000), 1)

    def test_reference_grid_and_intersection(self):
        header = RS2Header(6, 4, 90, 190, 150, 230, ['FUNDO'], [(255, 255, 255, 0)])
        grid = grid_from_reference(header)
        self.assertEqual(grid, RS2Grid(6, 4, 90, 190, 150, 230))
        self.assertTrue(extent_intersects_grid((100, 140, 200, 220), grid))
        self.assertFalse(extent_intersects_grid((500, 600, 500, 600), grid))


class CodePlanTests(unittest.TestCase):
    def test_small_positive_codes_are_preserved(self):
        mapping, labels, colors, mode = plan_codes(
            'int', {2: ('Pastagem', '#FFFF00'), 1: ('Caatinga', '#008000')})
        self.assertEqual(mode, 'preserve')
        self.assertEqual(mapping, {1: 1, 2: 2})
        self.assertEqual(labels, ['FUNDO', 'Caatinga', 'Pastagem'])
        self.assertEqual(colors[1], (0, 128, 0, 0))
        self.assertEqual(colors[2], (255, 255, 0, 0))

    def test_gaps_are_filled_with_generic_classes(self):
        _, labels, colors, mode = plan_codes('int', {1: ('', ''), 4: ('Água', '')})
        self.assertEqual(mode, 'preserve')
        self.assertEqual(labels, ['FUNDO', 'Classe 1', 'Classe 2', 'Classe 3', 'Água'])
        self.assertEqual(len(colors), 5)
        self.assertEqual(colors[4], default_color(4))

    def test_sparse_codes_are_renumbered_automatically(self):
        mapping, labels, _, mode = plan_codes('int', {3000: ('', ''), 101: ('Mata', '')})
        self.assertEqual(mode, 'renumber')
        self.assertEqual(mapping, {101: 1, 3000: 2})
        self.assertEqual(labels, ['FUNDO', 'Mata', 'Classe 3000'])

    def test_sparse_small_codes_are_renumbered_automatically(self):
        # Caso real (pluviometria): códigos 125 e 158 geravam 159 classes, 156 vazias.
        mapping, labels, _, mode = plan_codes('int', {125: ('', ''), 158: ('', '')})
        self.assertEqual(mode, 'renumber')
        self.assertEqual(mapping, {125: 1, 158: 2})
        self.assertEqual(labels, ['FUNDO', 'Classe 125', 'Classe 158'])

    def test_dense_codes_with_small_gap_are_preserved(self):
        mapping, labels, _, mode = plan_codes('int', {1: ('', ''), 2: ('', ''), 4: ('', '')})
        self.assertEqual((mode, mapping), ('preserve', {1: 1, 2: 2, 4: 4}))
        self.assertEqual(len(labels), 5)
        _, labels, _, mode = plan_codes('int', {125: ('', ''), 158: ('', '')}, 'preserve')
        self.assertEqual((mode, len(labels)), ('preserve', 159))

    def test_code_zero_is_never_merged_with_background(self):
        mapping, _, _, mode = plan_codes('int', {0: ('Água', ''), 1: ('Mata', '')})
        self.assertEqual(mode, 'renumber')
        self.assertEqual(mapping, {0: 1, 1: 2})
        with self.assertRaisesRegex(RS2Error, 'reservado ao FUNDO'):
            plan_codes('int', {0: ('', ''), 1: ('', '')}, 'preserve')

    def test_preserve_can_be_forced_up_to_rs2_limit(self):
        mapping, labels, _, mode = plan_codes('int', {300: ('', '')}, 'preserve')
        self.assertEqual((mode, mapping, len(labels)), ('preserve', {300: 300}, 301))
        with self.assertRaisesRegex(RS2Error, 'excede o limite'):
            plan_codes('int', {40000: ('', '')}, 'preserve')

    def test_renumber_can_be_forced(self):
        mapping, _, _, mode = plan_codes('int', {2: ('', ''), 7: ('', '')}, 'renumber')
        self.assertEqual((mode, mapping), ('renumber', {2: 1, 7: 2}))

    def test_text_codes_are_alphabetical_and_reproducible(self):
        mapping, labels, _, mode = plan_codes(
            'text', {'Pastagem': ('', ''), 'caatinga': ('', '#00FF00'), 'Água': ('', '')})
        self.assertEqual(mode, 'text')
        self.assertEqual(mapping, {'caatinga': 1, 'Pastagem': 2, 'Água': 3})
        self.assertEqual(labels, ['FUNDO', 'caatinga', 'Pastagem', 'Água'])

    def test_rejections(self):
        with self.assertRaisesRegex(RS2Error, 'negativos'):
            plan_codes('int', {-1: ('', '')})
        with self.assertRaisesRegex(RS2Error, 'decimais'):
            plan_codes('real', {1.5: ('', '')})
        with self.assertRaisesRegex(RS2Error, 'CP1252'):
            plan_codes('text', {'Floresta ☘': ('', '')})
        with self.assertRaisesRegex(RS2Error, 'Nenhuma feição'):
            plan_codes('int', {})
        with self.assertRaisesRegex(RS2Error, 'Modo de códigos'):
            plan_codes('int', {1: ('', '')}, 'outro')


class EarlyValidationTests(unittest.TestCase):
    def test_rejects_before_touching_gdal(self):
        with TemporaryDirectory() as td:
            folder = Path(td)
            vector = folder / 'classes.gpkg'
            vector.write_bytes(b'stub')
            with self.assertRaisesRegex(RS2Error, r'\.rs2'):
                convert_vector_to_rs2(vector, folder / 'saida.tif', 'CODIGO', 10)
            with self.assertRaisesRegex(RS2Error, 'não encontrado'):
                convert_vector_to_rs2(folder / 'faltante.gpkg', folder / 'saida.rs2',
                                      'CODIGO', 10)
            with self.assertRaisesRegex(RS2Error, 'referência não encontrado'):
                convert_vector_to_rs2(vector, folder / 'saida.rs2', 'CODIGO', 10,
                                      reference_rs2=folder / 'ref.rs2')


def _square(x0, y0, x1, y1):
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)):
        ring.AddPoint_2D(x, y)
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    return polygon


def _make_vector(path, features, epsg=31985, code_type=None, driver='GPKG'):
    """Cria um vetor com campos CODIGO, CLASSE e COR_HEX; ``None`` omite o valor."""
    ds = ogr.GetDriverByName(driver).CreateDataSource(str(path))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    layer = ds.CreateLayer('temas', srs=srs, geom_type=ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn('CODIGO', code_type or ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn('CLASSE', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('COR_HEX', ogr.OFTString))
    for code, name, color, box in features:
        feature = ogr.Feature(layer.GetLayerDefn())
        if code is not None:
            feature.SetField('CODIGO', code)
        if name is not None:
            feature.SetField('CLASSE', name)
        if color is not None:
            feature.SetField('COR_HEX', color)
        feature.SetGeometry(_square(*box))
        layer.CreateFeature(feature)
    ds = None
    return path


def _matrix(path):
    reader = RS2Reader(path)
    return reader.header, np.vstack(list(reader.rows()))


@unittest.skipUnless(HAS_GDAL, 'GDAL/OGR não disponível neste ambiente')
class VectorToRS2ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_two_classes_exact_cells_legend_and_sidecar(self):
        vector = _make_vector(self.folder / 'uso.gpkg', [
            (1, 'Caatinga', '#008000', (100, 200, 120, 220)),
            (2, 'Pastagem', '#FFFF00', (120, 200, 140, 220)),
        ])
        output = self.folder / 'uso.rs2'
        result = convert_vector_to_rs2(str(vector) + '|layername=temas', output, 'CODIGO', 10)
        header, cells = _matrix(output)
        self.assertEqual((header.width, header.height), (4, 2))
        self.assertEqual((header.xmin, header.ymin, header.xmax, header.ymax),
                         (100, 200, 140, 220))
        np.testing.assert_array_equal(cells, [[1, 1, 2, 2], [1, 1, 2, 2]])
        self.assertEqual(header.labels, ['FUNDO', 'Caatinga', 'Pastagem'])
        self.assertEqual(header.colors[1][:3], (0, 128, 0))
        self.assertEqual(header.colors[2][:3], (255, 255, 0))
        self.assertEqual(result.summary['overlap_cells'], 0)
        self.assertEqual(result.summary['background_cells'], 0)
        sidecar = json.loads(Path(str(output) + '.rs2.json').read_text(encoding='utf-8'))
        self.assertIn('31985', sidecar['source_wkt'])
        self.assertEqual(sidecar['rasterization']['code_mode'], 'preserve')
        self.assertEqual([m['celulas'] for m in sidecar['rasterization']['code_mapping']], [4, 4])

    def test_unaligned_vector_uses_snapped_grid_and_background(self):
        vector = _make_vector(self.folder / 'mata.gpkg', [
            (5, 'Mata', None, (103, 201, 128, 219)),
        ])
        output = self.folder / 'mata.rs2'
        convert_vector_to_rs2(vector, output, 'CODIGO', 10)
        header, cells = _matrix(output)
        self.assertEqual((header.xmin, header.ymin, header.xmax, header.ymax),
                         (100, 200, 130, 220))
        # Centros das células: x=105,115,125; y=215,205 — todos dentro do polígono.
        np.testing.assert_array_equal(cells, [[1, 1, 1], [1, 1, 1]])
        # Código único 5: renumerado para 1, sem quatro classes vazias de preenchimento.
        self.assertEqual(header.labels, ['FUNDO', 'Mata'])

    def test_reference_grid_is_copied_exactly(self):
        reference = self.folder / 'geom.rs2'
        ref_header = RS2Header(6, 4, 90, 190, 150, 230, ['FUNDO', 'Plano'],
                               [(255, 255, 255, 0), (10, 20, 30, 0)])
        write_rs2(reference, ref_header, [np.ones(6, dtype=np.uint16)] * 4)
        vector = _make_vector(self.folder / 'uso.gpkg', [
            (1, 'Caatinga', '#008000', (100, 200, 120, 220)),
            (2, 'Pastagem', '#FFFF00', (120, 200, 140, 220)),
        ])
        output = self.folder / 'uso_na_grade.rs2'
        convert_vector_to_rs2(vector, output, 'CODIGO', 999, reference_rs2=reference)
        header, cells = _matrix(output)
        self.assertEqual((header.width, header.height, header.xmin, header.ymin,
                          header.xmax, header.ymax), (6, 4, 90, 190, 150, 230))
        np.testing.assert_array_equal(cells, [[0, 0, 0, 0, 0, 0],
                                              [0, 1, 1, 2, 2, 0],
                                              [0, 1, 1, 2, 2, 0],
                                              [0, 0, 0, 0, 0, 0]])

    def test_reference_without_intersection_is_rejected(self):
        reference = self.folder / 'longe.rs2'
        write_rs2(reference, RS2Header(2, 2, 5000, 5000, 5020, 5020, ['FUNDO'],
                                       [(255, 255, 255, 0)]),
                  [np.zeros(2, dtype=np.uint16)] * 2)
        vector = _make_vector(self.folder / 'uso.gpkg', [(1, 'A', None, (100, 200, 120, 220))])
        with self.assertRaisesRegex(RS2Error, 'não intersecta'):
            convert_vector_to_rs2(vector, self.folder / 'x.rs2', 'CODIGO', 10,
                                  reference_rs2=reference)

    def test_sparse_codes_are_renumbered_and_mapped_in_sidecar(self):
        vector = _make_vector(self.folder / 'solo.shp', [
            (3000, 'Argissolo', None, (100, 200, 110, 210)),
            (101, 'Latossolo', None, (110, 200, 120, 210)),
        ], driver='ESRI Shapefile')
        output = self.folder / 'solo.rs2'
        result = convert_vector_to_rs2(vector, output, 'CODIGO', 10)
        header, cells = _matrix(output)
        np.testing.assert_array_equal(cells, [[2, 1]])
        self.assertEqual(header.labels, ['FUNDO', 'Latossolo', 'Argissolo'])
        self.assertEqual(result.summary['code_mode'], 'renumber')
        self.assertEqual(result.summary['filler_classes'], 0)
        sidecar = json.loads(Path(str(output) + '.rs2.json').read_text(encoding='utf-8'))
        pairs = [(m['codigo_rs2'], m['valor_original'])
                 for m in sidecar['rasterization']['code_mapping']]
        self.assertEqual(pairs, [(1, 101), (2, 3000)])

    def test_text_field_and_skipped_features(self):
        vector = _make_vector(self.folder / 'uso.gpkg', [
            (None, 'Pastagem', None, (100, 200, 110, 210)),
            (None, 'Caatinga', None, (110, 200, 120, 210)),
            (None, None, None, (120, 200, 130, 210)),
        ])
        output = self.folder / 'uso.rs2'
        result = convert_vector_to_rs2(vector, output, 'CLASSE', 10)
        header, cells = _matrix(output)
        np.testing.assert_array_equal(cells, [[2, 1, 0]])
        self.assertEqual(header.labels, ['FUNDO', 'Caatinga', 'Pastagem'])
        self.assertEqual(result.summary['skipped_features'], 1)

    def test_overlaps_are_counted_and_last_feature_wins(self):
        vector = _make_vector(self.folder / 'sobreposto.gpkg', [
            (1, 'A', None, (100, 200, 120, 210)),
            (2, 'B', None, (110, 200, 130, 210)),
        ])
        output = self.folder / 'sobreposto.rs2'
        result = convert_vector_to_rs2(vector, output, 'CODIGO', 10)
        _, cells = _matrix(output)
        np.testing.assert_array_equal(cells, [[1, 2, 2]])
        self.assertEqual(result.summary['overlap_cells'], 1)

    def test_pluviometry_case_two_sparse_codes_give_two_classes(self):
        vector = _make_vector(self.folder / 'pluviometria.shp', [
            (125, None, None, (197515, 8929745, 200000, 8940815)),
            (158, None, None, (200000, 8929745, 202465, 8940815)),
        ], driver='ESRI Shapefile')
        output = self.folder / 'pluviometria.rs2'
        result = convert_vector_to_rs2(vector, output, 'CODIGO', 5)
        header = RS2Reader(output).header
        self.assertEqual(header.labels, ['FUNDO', 'Classe 125', 'Classe 158'])
        self.assertEqual((result.summary['code_mode'], result.summary['filler_classes']),
                         ('renumber', 0))
        forced = convert_vector_to_rs2(vector, self.folder / 'forcado.rs2', 'CODIGO', 5,
                                       code_mode='preserve')
        self.assertEqual(forced.summary['filler_classes'], 156)

    def test_methodological_rejections(self):
        geographic = _make_vector(self.folder / 'graus.gpkg',
                                  [(1, 'A', None, (-36.0, -9.6, -35.9, -9.5))], epsg=4674)
        with self.assertRaisesRegex(RS2Error, 'geográfico'):
            convert_vector_to_rs2(geographic, self.folder / 'g.rs2', 'CODIGO', 10)
        real = _make_vector(self.folder / 'real.gpkg',
                            [(1.5, 'A', None, (100, 200, 110, 210))], code_type=ogr.OFTReal)
        with self.assertRaisesRegex(RS2Error, 'decimais'):
            convert_vector_to_rs2(real, self.folder / 'r.rs2', 'CODIGO', 10)

    def test_cancellation_leaves_no_output(self):
        vector = _make_vector(self.folder / 'uso.gpkg', [(1, 'A', None, (100, 200, 140, 240))])
        output = self.folder / 'cancelado.rs2'
        with self.assertRaisesRegex(RS2Error, 'cancelad'):
            convert_vector_to_rs2(vector, output, 'CODIGO', 10,
                                  progress=lambda done, total: done < 500)
        self.assertFalse(output.exists())
        self.assertFalse(Path(str(output) + '.rs2.json').exists())
        self.assertEqual([p.name for p in self.folder.iterdir() if p.name.startswith('.vista')], [])


if __name__ == '__main__':
    unittest.main()
