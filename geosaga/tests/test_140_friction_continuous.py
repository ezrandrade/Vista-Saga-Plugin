"""1.4.0: Voronoi com atrito em vetor direto (modelo contínuo). Requer GDAL/OGR."""
import math
import random
import unittest

import numpy as np

from geosaga.voronoi_core import Generator

try:
    from osgeo import ogr
    HAS_GDAL = True
except ImportError:  # pragma: no cover - depende do ambiente
    HAS_GDAL = False

X0, Y1 = 500000., 8900600.


def _rect(x0, y0, x1, y1):
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)):
        ring.AddPoint_2D(x, y)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return bytes(poly.ExportToWkb())


def _cells(c0, l0, c1, l1):
    return _rect(X0 + c0 * 10, Y1 - l1 * 10, X0 + c1 * 10, Y1 - l0 * 10)


def _case_features():
    """O caso validado contra o Vista SAGA, desenhado em polígonos (a ordem importa)."""
    return [(_cells(0, 0, 40, 60), 1.), (_cells(40, 0, 80, 60), 3.), (_cells(30, 0, 40, 60), 5.),
            (_cells(30, 25, 40, 35), 1.), (_cells(55, 5, 70, 20), 5.)]


def _numeric_cost(features_grid, gx, gy, x, y, n=20000):
    t = (np.arange(n) + .5) / n
    f = features_grid(gx + t * (x - gx), gy + t * (y - gy))
    return ((x - gx) ** 2 + (y - gy) ** 2) * float(np.mean(t * f))


@unittest.skipUnless(HAS_GDAL, 'GDAL/OGR indisponível')
class ContinuousCostTests(unittest.TestCase):
    def setUp(self):
        ogr.DontUseExceptions()
        from geosaga.tests.test_140_voronoi_vista_saga_case import caso
        self.notas, self.pontos = caso()

    def test_exact_cost_matches_numeric_integral(self):
        from geosaga.voronoi_friction_continuous import FrictionSurface
        surface = FrictionSurface(_case_features())
        notas = self.notas

        def grid(px, py):
            c = np.clip(((px - X0) / 10).astype(int), 0, 79)
            r = np.clip(((Y1 - py) / 10).astype(int), 0, 59)
            return notas[r, c]
        rng = np.random.default_rng(4)
        g = self.pontos[1]
        inside = np.arange(len(surface.ratings)) == surface.locate([g.x + 1.1e-6], [g.y + 0.7e-6])[0]
        x = rng.uniform(X0, X0 + 800, 60)
        y = rng.uniform(Y1 - 600, Y1, 60)
        got = surface.costs(g.x, g.y, inside, x, y)
        expected = np.array([_numeric_cost(grid, g.x, g.y, a, b) for a, b in zip(x, y)])
        np.testing.assert_allclose(got, expected, rtol=1e-3)

    def test_uniform_rating_is_half_rating_times_squared_distance(self):
        from geosaga.voronoi_friction_continuous import FrictionSurface
        surface = FrictionSurface([(_rect(0, 0, 100, 100), 3.)])
        x = np.array([10., 90., 50.])
        y = np.array([20., 80., 50.])
        got = surface.costs(40., 40., np.array([True]), x, y)
        np.testing.assert_allclose(got, 3. * ((x - 40) ** 2 + (y - 40) ** 2) / 2)

    def test_barrier_and_uncovered_area_block(self):
        from geosaga.voronoi_friction_continuous import FrictionSurface
        # Dois quadrados separados por uma faixa sem polígono; o quadrado do meio não tem nota.
        surface = FrictionSurface([(_rect(0, 0, 10, 10), 1.), (_rect(10, 0, 20, 10), None),
                                   (_rect(20, 0, 30, 10), 1.)])
        got = surface.costs(5., 5., np.array([True, False]), np.array([8., 25., 15.]), np.array([5., 5., 5.]))
        self.assertTrue(np.isfinite(got[0]))
        self.assertTrue(np.isinf(got[1]))   # atravessa a barreira
        self.assertTrue(np.isinf(got[2]))   # dentro da barreira

    def test_vertex_passage_is_robust(self):
        # Segmentos que passam exatamente pelo canto do bloco (polo no centro de célula).
        from geosaga.voronoi_friction_continuous import ContinuousModel, FrictionSurface
        model = ContinuousModel(self.pontos, FrictionSurface(_case_features()), mass_weighted=True)
        xs = np.arange(500680, 500712, 1.0) + .25
        ys = np.arange(8900361, 8900350, -1.0) - .25
        xx, yy = np.meshgrid(xs, ys)
        self.assertTrue((model.labels(xx, yy) == 2).all())

    def test_case_agrees_with_vista_saga_counts_at_cell_centres(self):
        # Contagens do modelo contínuo no centro das células (Vista SAGA: 2843/1505/449 com massa).
        from geosaga.voronoi_friction_continuous import ContinuousModel, FrictionSurface
        surface = FrictionSurface(_case_features())
        cx = X0 + (np.arange(80) + .5) * 10
        cy = Y1 - (np.arange(60) + .5) * 10
        xx, yy = np.meshgrid(cx, cy)
        labels = ContinuousModel(self.pontos, surface, mass_weighted=True).labels(xx, yy)
        counts = [int((labels == i).sum()) for i in (1, 2, 3)]
        self.assertEqual(sum(counts), 4800)
        for got, vista_saga in zip(counts, (2843 + 1, 1505 + 1, 449 + 1)):
            self.assertLess(abs(got - vista_saga), 20)

    def test_pole_outside_polygons_rejected(self):
        from geosaga.voronoi_friction_continuous import ContinuousModel, FrictionSurface
        surface = FrictionSurface([(_rect(0, 0, 10, 10), 1.)])
        with self.assertRaisesRegex(ValueError, 'fora dos polígonos'):
            ContinuousModel([Generator(1, 50., 50.)], surface, mass_weighted=False)


@unittest.skipUnless(HAS_GDAL, 'GDAL/OGR indisponível')
class ContinuousPolygonsTests(unittest.TestCase):
    def setUp(self):
        ogr.DontUseExceptions()

    def _check_partition(self, results, area):
        total = sum(geom.GetArea() for _, geom in results)
        union = None
        for _, geom in results:
            union = geom.Clone() if union is None else union.Union(geom)
        self.assertAlmostEqual(total, area, delta=1e-6 * area)
        self.assertLess(total - union.GetArea(), 1e-6 * area, 'regiões vizinhas não podem se sobrepor')

    def test_case_partition_and_vista_saga_agreement(self):
        from geosaga.tests.test_140_voronoi_vista_saga_case import caso
        from geosaga.voronoi_friction_continuous import friction_voronoi_polygons
        _, pontos = caso()
        results, stats = friction_voronoi_polygons(pontos, _case_features(), (X0, Y1 - 600, X0 + 800, Y1),
                                                   spacing=10, tolerance=0.01, mass_weighted=True)
        self.assertEqual(sorted(g.identifier for g, _ in results), [1, 2, 3])
        self._check_partition(results, 480000.)
        # Sem fragmentos: as tiras entre o traçado e a borda da cobertura ficam com a região certa.
        self.assertEqual([geom.GetGeometryCount() for _, geom in results], [1, 1, 1])
        areas = {g.identifier: geom.GetArea() for g, geom in results}
        # Vista SAGA: 2843, 1505 e 449 células de 100 m² (+ a célula do polo).
        for ident, cells in ((1, 2844), (2, 1506), (3, 450)):
            self.assertLess(abs(areas[ident] / 100. - cells) / cells, 0.02)

    def test_uniform_friction_reproduces_apollonius_mass_voronoi(self):
        # Nota uniforme: A = f d²/2, logo A/M dá a lei M/d² do Com Massa (vetor exato da 1.3).
        from geosaga.voronoi_friction_continuous import friction_voronoi_polygons
        from geosaga.voronoi_vector import mass_voronoi_polygons
        rnd = random.Random(8)
        points = [Generator(i + 1, rnd.uniform(50, 950), rnd.uniform(50, 750), rnd.choice([1., 2., 5.]))
                  for i in range(7)]
        bounds = (0., 0., 1000., 800.)
        traced, _ = friction_voronoi_polygons(points, [(_rect(*bounds), 2.)], bounds, spacing=20,
                                              tolerance=0.01, mass_weighted=True)
        exact = {g.identifier: geom for g, geom in mass_voronoi_polygons(points, bounds, tolerance=0.01)}
        self._check_partition(traced, 800000.)
        for g, geom in traced:
            difference = geom.SymDifference(exact[g.identifier]).GetArea()
            perimeter = exact[g.identifier].Boundary().Length()
            # Diferença compatível com fronteiras a ~1 cm uma da outra.
            self.assertLess(difference, 0.03 * perimeter, g.identifier)

    def test_random_polygons_partition_and_labels(self):
        from geosaga.voronoi_friction_continuous import ContinuousModel, FrictionSurface, friction_voronoi_polygons
        rnd = random.Random(21)
        features = [(_rect(0, 0, 1000, 800), 1.)]
        for _ in range(12):
            x, y = rnd.uniform(0, 900), rnd.uniform(0, 700)
            features.append((_rect(x, y, x + rnd.uniform(30, 200), y + rnd.uniform(30, 200)),
                             rnd.choice([0.5, 2., 4., 8.])))
        points = [Generator(i + 1, rnd.uniform(20, 980), rnd.uniform(20, 780), rnd.uniform(1, 6)) for i in range(9)]
        bounds = (0., 0., 1000., 800.)
        for weighted in (False, True):
            results, stats = friction_voronoi_polygons(points, features, bounds, spacing=15, tolerance=0.01,
                                                       mass_weighted=weighted)
            self._check_partition(results, 800000.)
            model = ContinuousModel(points, FrictionSurface(features), mass_weighted=weighted)
            by_id = {g.identifier: geom for g, geom in results}
            boundary = None
            for geom in by_id.values():
                boundary = geom.Boundary() if boundary is None else boundary.Union(geom.Boundary())
            checked = 0
            for _ in range(400):
                px, py = rnd.uniform(0, 1000), rnd.uniform(0, 800)
                label = int(model.labels([px], [py])[0])
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint_2D(px, py)
                if boundary.Distance(point) < 0.5:
                    continue  # perto da fronteira: dentro do que a malha pode não resolver
                self.assertTrue(by_id[label].Contains(point), (px, py, label, weighted))
                checked += 1
            self.assertGreater(checked, 350)

    def test_invalid_parameters(self):
        from geosaga.voronoi_friction_continuous import friction_voronoi_polygons
        feats = [(_rect(0, 0, 10, 10), 1.)]
        with self.assertRaisesRegex(ValueError, 'Espaçamento'):
            friction_voronoi_polygons([Generator(1, 5, 5)], feats, (0, 0, 10, 10), spacing=1, tolerance=2)
        with self.assertRaisesRegex(ValueError, 'Nenhum polígono'):
            friction_voronoi_polygons([Generator(1, 5, 5)], [(_rect(0, 0, 10, 10), None)], (0, 0, 10, 10),
                                      spacing=1, tolerance=.01)


if __name__ == '__main__':
    unittest.main()
