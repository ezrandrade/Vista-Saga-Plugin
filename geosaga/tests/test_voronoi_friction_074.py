"""Testes da modalidade atrito, independentes do QGIS/GDAL."""
import unittest
import numpy as np
from geosaga.voronoi_core import Generator, assign_window
from geosaga.voronoi_friction import (
    assign_friction_window, validate_friction, _straight_cost_batch,
    estimated_visits,
)


class FrictionVoronoiTests(unittest.TestCase):
    def setUp(self):
        self.t = (0., 1., 0., 1., 0., -1.)
        self.points = [Generator(1, 0.5, 0.5, 1., 'A'),
                       Generator(2, 4.5, 0.5, 1., 'B')]

    def test_uniform_one_dimensional(self):
        raster = np.ones((1, 5), dtype=float)
        validate_friction(raster, self.t, self.points)
        got = assign_friction_window(self.points, raster, self.t, 0, 1)
        simple = assign_window(self.points, self.t, 5, 0, 1)
        np.testing.assert_array_equal(got, simple)

    def test_high_friction_reduces_a_generators_reach(self):
        raster = np.ones((1, 5), dtype=float)
        ordinary = assign_friction_window(self.points, raster, self.t, 0, 1)
        raster[0, 1] = 100
        friction = assign_friction_window(self.points, raster, self.t, 0, 1)
        self.assertEqual(ordinary[0, 2], 1)
        self.assertEqual(friction[0, 2], 2)

    def test_zero_allowed_with_baseline(self):
        raster = np.zeros((1, 5), dtype=float)
        validate_friction(raster, self.t, self.points)
        self.assertEqual(assign_friction_window(self.points,raster,self.t,0,1).tolist(),
                         [[1, 1, 1, 2, 2]])
        costs = _straight_cost_batch(raster, .5,.5,np.array([2.5]), np.array([.5]))
        self.assertEqual(costs.tolist(), [3.0])

    def test_nodata_in_path_blocks_a_center(self):
        raster = np.ones((1,5))
        raster[0,1] = np.nan
        got = assign_friction_window(self.points,raster,self.t,0,1)
        self.assertEqual(got.tolist(), [[1,0,2,2,2]])

    def test_all_paths_blocked_excluded(self):
        raster = np.array([[1.,np.nan,1.,np.nan,1.]])
        out = assign_friction_window(self.points,raster,self.t,0,1)
        self.assertEqual(out[0,2],0)

    def test_2d_diagonal_corner(self):
        t = (0,1,0,3,0,-1)
        raster=np.ones((3,3))
        # from top-left to lower-right through pixel corners, diagonal cells only
        cost=_straight_cost_batch(raster,.5,.5,np.array([2.5]),np.array([2.5]))
        self.assertEqual(float(cost[0]),6.)

    def test_middle_window_matches_full(self):
        raster=np.ones((9,8))
        t=(0,1,0,9,0,-1)
        points=[Generator(1,1.5,7.5),Generator(2,6.5,1.5)]
        a=assign_friction_window(points,raster,t,0,9)
        b=np.vstack([assign_friction_window(points,raster,t,0,4),
                     assign_friction_window(points,raster,t,4,5)])
        np.testing.assert_array_equal(a,b)

    def test_cancel(self):
        with self.assertRaises(InterruptedError):
            assign_friction_window(self.points,np.ones((1,5)),self.t,0,1,
                                   cancelled=lambda: True)

    def test_invalid_negative_and_outside_generator(self):
        r=np.ones((1,5))
        r[0,1]=-1
        with self.assertRaisesRegex(ValueError,'negativos'):
            validate_friction(r,self.t,self.points)
        r[0,1]=1
        with self.assertRaisesRegex(ValueError,'fora da extensão'):
            validate_friction(r,self.t,[Generator(3,20,20)])

    def test_generator_on_nodata_and_grid_rotated(self):
        r=np.ones((1,5)); r[0,0]=np.nan
        with self.assertRaisesRegex(ValueError,'NoData'):
            validate_friction(r,self.t,self.points)
        with self.assertRaisesRegex(ValueError,'sem rotação'):
            validate_friction(np.ones((1,5)),(0,1,.01,1,0,-1),self.points)

    def test_invalid_baseline(self):
        with self.assertRaisesRegex(ValueError,'basal'):
            assign_friction_window(self.points,np.ones((1,5)),self.t,0,1,baseline=0)

    def test_complexity_estimate_is_finite(self):
        self.assertEqual(estimated_visits(10,10,2),1000)
        self.assertGreater(estimated_visits(2000,2000,20),100_000_000)

    def test_friction_path_wired_into_task(self):
        from pathlib import Path
        folder=Path(__file__).resolve().parents[1]
        dialog=(folder/'voronoi_dialog.py').read_text(encoding='utf-8')
        engine=(folder/'voronoi_engine.py').read_text(encoding='utf-8')
        self.assertIn('friction_path=self.friction_path',dialog)
        self.assertIn('friction_path=friction_path if friction_mode else None',dialog)
        self.assertIn("mode in ('friction','mass_friction')",engine)
        self.assertIn('assign_friction_window(',engine)
        self.assertNotIn('QApplication.processEvents()',engine)

if __name__ == '__main__':
    unittest.main()
