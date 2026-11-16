"""1.3.0: Voronoi Com Massa em vetor direto (círculos de Apolônio, sem grade).

Região de cada centro = onde M/d é máximo. Testes com GDAL/OGR real; pulados sem ``osgeo``.
"""
import csv
import math
from pathlib import Path
import random
import tempfile
import unittest

from geosaga.voronoi_core import Generator

try:
    from osgeo import ogr, osr
    HAS_GDAL = True
except ImportError:  # pragma: no cover - depende do ambiente
    HAS_GDAL = False


def _polygon_area(ring):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(ring, ring[1:]))) / 2


class MassDirectWiringTests(unittest.TestCase):
    def test_dialog_enables_direct_vector_for_mass(self):
        content = (Path(__file__).resolve().parents[1] / 'voronoi_dialog.py').read_text(encoding='utf-8')
        self.assertIn("direct=kind=='vector' and self.mode.currentIndex() in (0,1)", content)
        self.assertIn("mode='mass' if self.mode.currentIndex()==1 else 'simple'", content)


@unittest.skipUnless(HAS_GDAL, 'GDAL/OGR indisponível')
class MassVoronoiPolygonsTests(unittest.TestCase):
    def setUp(self):
        ogr.DontUseExceptions()

    def _polygons(self, points, bounds, tolerance=0.01):
        from geosaga.voronoi_vector import mass_voronoi_polygons
        return {g.identifier: geom for g, geom in
                mass_voronoi_polygons(points, bounds, tolerance=tolerance)}

    def test_two_centres_match_apollonius_circle(self):
        # A (M=1) vence onde d_A/d_B < 1/2: disco de centro (-10/3, 0) e raio 20/3.
        result = self._polygons([Generator(1, 0, 0, 1.), Generator(2, 10, 0, 2.)], (-50, -50, 50, 50))
        radius = 0.5 * 10 / 0.75
        self.assertAlmostEqual(result[1].GetArea(), math.pi * radius**2, delta=0.005)
        self.assertAlmostEqual(result[1].GetArea() + result[2].GetArea(), 10000., places=4)
        cx, cy = -10 / 3, 0.
        ring = result[1].GetGeometryRef(0).GetGeometryRef(0)
        for i in range(ring.GetPointCount()):
            x, y = ring.GetX(i), ring.GetY(i)
            self.assertLess(abs(math.hypot(x - cx, y - cy) - radius), 0.01)

    def test_equal_masses_reproduce_simple_voronoi(self):
        from geosaga.voronoi_vector import simple_voronoi_polygons
        rnd = random.Random(5)
        points = [Generator(i + 1, rnd.uniform(0, 5000), rnd.uniform(0, 4000), 2.5) for i in range(30)]
        bounds = (0, 0, 5000, 4000)
        mass = {k: round(g.GetArea(), 3) for k, g in self._polygons(points, bounds).items()}
        simple = {g.identifier: round(_polygon_area(r), 3) for g, r in simple_voronoi_polygons(points, bounds)}
        self.assertEqual(mass, simple)

    def test_random_centres_follow_highest_mass_over_distance(self):
        rnd = random.Random(11)
        bounds = (0, 0, 10000, 8000)
        points = [Generator(i + 1, rnd.uniform(0, 10000), rnd.uniform(0, 8000),
                            rnd.choice([1, 2, 3, 5, 8]) * rnd.uniform(.8, 1.2)) for i in range(80)]
        result = self._polygons(points, bounds)
        total = sum(g.GetArea() for g in result.values())
        self.assertAlmostEqual(total, 8.e7, delta=0.01)
        union = None
        for geometry in result.values():
            union = geometry.Clone() if union is None else union.Union(geometry)
        self.assertLess(total - union.GetArea(), 1.e-3, 'regiões vizinhas não podem se sobrepor')
        checked = 0
        for _ in range(2000):
            x, y = rnd.uniform(0, 10000), rnd.uniform(0, 8000)
            scores = sorted((math.hypot(x - p.x, y - p.y) / p.mass, p.identifier) for p in points)
            if scores[1][0] - scores[0][0] < 1.e-4 * scores[0][0]:
                continue  # perto da fronteira: dentro da tolerância dos arcos
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint_2D(x, y)
            self.assertTrue(result[scores[0][1]].Contains(point), (x, y))
            checked += 1
        self.assertGreater(checked, 1900)

    def test_extreme_mass_ratios(self):
        bounds = (0, 0, 50000, 40000)
        for points in ([Generator(1, 1000, 1000, 1.), Generator(2, 1010, 1000, 1. + 1e-9),
                        Generator(3, 30000, 20000, 1.)],
                       [Generator(1, 25000, 20000, 1e6), Generator(2, 25010, 20000, 1.),
                        Generator(3, 100, 100, 5.)]):
            result = self._polygons(points, bounds)
            self.assertEqual(sorted(result), [1, 2, 3])
            self.assertAlmostEqual(sum(g.GetArea() for g in result.values()), 2.e9, delta=0.05)

    def test_invalid_inputs(self):
        from geosaga.voronoi_vector import mass_voronoi_polygons
        with self.assertRaisesRegex(ValueError, 'maiores que zero'):
            mass_voronoi_polygons([Generator(1, 0, 0, 0.)], (0, 0, 10, 10), tolerance=.01)
        with self.assertRaisesRegex(ValueError, 'Tolerância'):
            mass_voronoi_polygons([Generator(1, 0, 0, 1.)], (0, 0, 10, 10), tolerance=0.)


@unittest.skipUnless(HAS_GDAL, 'GDAL/OGR indisponível')
class SaveMassVectorTests(unittest.TestCase):
    def setUp(self):
        ogr.DontUseExceptions()
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(31983)
        self.wkt = srs.ExportToWkt()
        self.points = [Generator(1, 500200., 7500300., 1., 'Escola São José'),
                       Generator(2, 500700., 7500400., 4., 'Hospital Ação'),
                       Generator(3, 500400., 7500800., 2., 'Posto C')]
        self.bounds = (500000., 7500000., 501000., 7501000.)
        self.folder = tempfile.TemporaryDirectory(prefix='vistasaga_130m_')
        self.addCleanup(self.folder.cleanup)

    def test_mass_direct_in_geopackage_and_shapefile(self):
        from geosaga.voronoi_vector import save_vector_voronoi
        for extension in ('.gpkg', '.shp'):
            with self.subTest(formato=extension):
                target = Path(self.folder.name) / f'massa_direta{extension}'
                result = save_vector_voronoi(self.points, self.bounds, str(target), self.wkt, mode='mass')
                self.assertTrue(result['vector_direct'])
                self.assertEqual(result['vector'], str(target))
                ds = ogr.Open(str(target))
                layer = ds.GetLayer(0)
                rows = {f.GetField('CENTRO_ID'): (f.GetField('CENTRO'), f.GetField('MASSA'),
                                                   f.GetField('AREA_HA'), f.GetGeometryRef().Clone())
                        for f in layer}
                ds = None
                self.assertEqual(sorted(rows), [1, 2, 3])
                self.assertEqual(rows[1][0], 'Escola São José')
                self.assertAlmostEqual(sum(r[2] for r in rows.values()), 100., places=5)  # 1 km² = 100 ha
                # O centro mais pesado (M=4) domina mais área que o mais leve (M=1).
                self.assertGreater(rows[2][2], rows[1][2])
                with open(result['csv'], encoding='utf-8-sig', newline='') as handle:
                    table = list(csv.DictReader(handle, delimiter=';'))
                self.assertAlmostEqual(sum(float(r['PCT_AREA']) for r in table), 100., places=6)
                report = Path(result['txt']).read_text(encoding='utf-8')
                self.assertIn('Com Massa (maior M/d); saída vetorial direta', report)
                self.assertIn('círculos de Apolônio', report)

    def test_friction_mode_rejected(self):
        from geosaga.voronoi_vector import save_vector_voronoi
        with self.assertRaisesRegex(ValueError, 'Simples e Com Massa'):
            save_vector_voronoi(self.points, self.bounds, str(Path(self.folder.name) / 'x.gpkg'),
                                self.wkt, mode='friction')


if __name__ == '__main__':
    unittest.main()
