"""1.4.0: superfície de atrito vetorial (polígonos → grade de notas)."""
import unittest

import numpy as np

from geosaga.voronoi_friction_vector import BARRIER, check_rating, describe, ratings_from_column

try:
    from osgeo import ogr, osr
    HAS_GDAL = True
except ImportError:  # pragma: no cover - depende do ambiente
    HAS_GDAL = False


class RatingTests(unittest.TestCase):
    def test_column_values(self):
        self.assertEqual(ratings_from_column([1, 0.1, None, '2.5']), [1.0, 0.1, None, 2.5])
        for bad in (0, -1, float('nan'), 'abc'):
            with self.assertRaises(ValueError):
                ratings_from_column([bad])

    def test_check_rating(self):
        self.assertEqual(check_rating(BARRIER, 'x'), BARRIER)
        self.assertEqual(check_rating('0.1', 'x'), 0.1)
        for bad in ('0', -0.1):
            with self.assertRaisesRegex(ValueError, 'maior que 0'):
                check_rating(bad, 'x')

    def test_describe_lists_choices(self):
        spec = {'layer_name': 'uso', 'rating_field': 'ATRITO', 'skipped': 2}
        text = describe(spec, {'features': 4, 'uncovered_cells': 10, 'barrier_cells': 3}, 10)
        for piece in ('Superfície de atrito vetorial', 'coluna ATRITO', 'atravessáveis com nota 1',
                      'centro da célula', 'coluna vazia: 2'):
            self.assertIn(piece, text)


def _square(x0, y0, x1, y1):
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)):
        ring.AddPoint_2D(x, y)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return bytes(poly.ExportToWkb())


@unittest.skipUnless(HAS_GDAL, 'GDAL/OGR indisponível')
class RasterizeTests(unittest.TestCase):
    def setUp(self):
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(31985)
        self.wkt = srs.ExportToWkt()
        self.t = (500000., 10., 0., 8900600., 0., -10.)

    def test_cell_centre_rule_outside_and_barrier(self):
        from geosaga.voronoi_friction_vector import rasterize_friction
        features = [(_square(500000, 8900000, 500400, 8900600), 1.0),     # metade oeste
                    (_square(500406, 8900000, 500600, 8900600), 3.0),     # não cobre o centro da coluna 40
                    (_square(500300, 8900300, 500350, 8900350), BARRIER),
                    (_square(500000, 8900000, 500800, 8900600), None)]    # campo vazio: ignorada
        grid, stats, no_result = rasterize_friction(features, 7.0, self.t, 80, 60, self.wkt)
        self.assertEqual(grid[0, 0], 1.0)
        self.assertEqual(grid[0, 40], 7.0)   # centro em 500405, fora do polígono que começa em 500406
        self.assertEqual(grid[0, 41], 3.0)
        self.assertEqual(grid[0, 79], 7.0)
        self.assertTrue(np.isnan(grid[27, 32]))
        self.assertEqual(stats['features'], 3)
        self.assertEqual(stats['barrier_cells'], 25)
        self.assertEqual(stats['uncovered_cells'], 60 * 21)  # coluna 40 e colunas 60-79
        # 1.4.0-dev5: a área sem polígono é atravessável (nota 7 aqui) mas fica sem resultado.
        self.assertTrue(no_result[0, 40] and no_result[0, 79] and not no_result[0, 0])
        self.assertEqual(int(no_result.sum()), 60 * 21)

    def test_uncovered_cells_need_a_choice(self):
        from geosaga.voronoi_friction_vector import rasterize_friction
        features = [(_square(500000, 8900000, 500400, 8900600), 2.0)]
        with self.assertRaisesRegex(ValueError, 'não são cobertas'):
            rasterize_friction(features, None, self.t, 80, 60, self.wkt)
        grid, _, no_result = rasterize_friction(features, BARRIER, self.t, 80, 60, self.wkt)
        self.assertIsNone(no_result)
        self.assertTrue(np.isnan(grid[:, 40:]).all())
        self.assertTrue((grid[:, :40] == 2.0).all())

    def test_full_cover_needs_no_outside_rating(self):
        from geosaga.voronoi_friction_vector import rasterize_friction
        grid, stats, _ = rasterize_friction([(_square(499990, 8899990, 500810, 8900610), 4.0)], None,
                                            self.t, 80, 60, self.wkt)
        self.assertTrue((grid == 4.0).all())
        self.assertEqual(stats['uncovered_cells'], 0)

    def test_vector_case_reproduces_raster_case(self):
        # O caso validado, desenhado em polígonos, dá a mesma grade de notas que o raster.
        from geosaga.voronoi_friction_vector import rasterize_friction
        from geosaga.tests.test_140_voronoi_vista_saga_case import caso
        notas, _ = caso()
        X, Y = 500000, 8900600

        def cells(c0, l0, c1, l1):  # colunas c0..c1-1, linhas l0..l1-1
            return _square(X + c0 * 10, Y - l1 * 10, X + c1 * 10, Y - l0 * 10)
        features = [(cells(0, 0, 40, 60), 1.0), (cells(40, 0, 80, 60), 3.0), (cells(30, 0, 40, 60), 5.0),
                    (cells(30, 25, 40, 35), 1.0), (cells(55, 5, 70, 20), 5.0)]
        grid, _, _ = rasterize_friction(features, None, self.t, 80, 60, self.wkt)
        np.testing.assert_array_equal(grid, notas)

    def test_outside_passable_without_result_in_raster_engine(self):
        # Área de estudo côncava (em L): a reta que sai pelo canto vazio passa com nota 1, e o canto
        # vazio fica sem resultado. Com barreira, o polo não alcançaria o braço de cima.
        import tempfile, os
        from osgeo import osr as _osr
        from geosaga.voronoi_core import Generator
        from geosaga.voronoi_engine import run_voronoi
        features = [(_square(0, 0, 100, 50), 2.0), (_square(0, 50, 50, 100), 2.0)]
        t = (0., 2., 0., 100., 0., -2.)
        srs = _osr.SpatialReference(); srs.ImportFromEPSG(31985)
        points = [Generator(1, 95., 5., 1.), Generator(2, 5., 95., 1.)]
        with tempfile.TemporaryDirectory() as folder:
            out = run_voronoi(points, os.path.join(folder, 'l.tif'), srs.ExportToWkt(), t, 50, 50,
                              mode='friction', friction_vector={'features': features, 'outside': 1.0})
            from osgeo import gdal
            ds = gdal.Open(out['output']); labels = ds.ReadAsArray(); ds = None
        self.assertTrue((labels[:25, 25:] == 0).all())          # canto vazio: sem resultado
        self.assertGreater(int((labels == 1).sum()), 0)
        self.assertGreater(int((labels == 2).sum()), 0)
        self.assertEqual(int((labels > 0).sum()), 50 * 50 - 25 * 25)  # todo o L tem resultado


if __name__ == '__main__':
    unittest.main()
