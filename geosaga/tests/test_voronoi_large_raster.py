"""Regressões da correção de volume raster 0.7.2."""
from pathlib import Path
import unittest
import numpy as np
from geosaga.voronoi_core import Generator, assign_window, assign_window_nearest, build_nearest_index


class VoronoiLargeRasterTests(unittest.TestCase):
    def setUp(self):
        self.points = [Generator(10,2,2),Generator(20,6,2),Generator(30,4,6)]
        self.t = (0., .8, 0., 8., 0., -.8)

    def test_indexed_matches_brute_force(self):
        index = build_nearest_index(self.points)
        actual=assign_window_nearest(self.points,self.t,10,0,10,index=index)
        expected=assign_window(self.points,self.t,10,0,10)
        np.testing.assert_array_equal(actual,expected)

    def test_tie_first_generator(self):
        pts=[Generator(7,0,0),Generator(9,2,0),Generator(11,1,1)]
        trans=(0,1,0,1,0,-1)
        actual=assign_window_nearest(pts,trans,2,0,1,index=build_nearest_index(pts))
        expected=assign_window(pts,trans,2,0,1)
        np.testing.assert_array_equal(actual,expected)

    def test_rotated_grid_and_mask(self):
        trans=(0,1,.3,0,.2,-1)
        mask=np.array([[True,False,True],[True,True,False]],dtype=bool)
        index=build_nearest_index(self.points)
        got=assign_window_nearest(self.points,trans,3,0,2,index=index,mask=mask)
        exp=assign_window(self.points,trans,3,0,2,mask=mask)
        np.testing.assert_array_equal(got,exp)

    def test_no_index_uses_numpy(self):
        got=assign_window_nearest(self.points,self.t,10,0,10,index=None)
        exp=assign_window(self.points,self.t,10,0,10)
        np.testing.assert_array_equal(got,exp)

    def test_mass_keeps_existing_method(self):
        weighted=[Generator(1,0,0,1),Generator(2,8,0,3)]
        t=(0,1,0,1,0,-1)
        self.assertEqual(assign_window(weighted,t,10,0,1,mode='mass').shape,(1,10))

    def test_prevent_regression_to_fixed_workload_limit(self):
        engine=(Path(__file__).resolve().parents[1]/'voronoi_engine.py').read_text(encoding='utf-8')
        self.assertNotIn('300_000_000',engine)
        self.assertIn('target_pixels_per_window',engine)
        self.assertIn('rows_per_window',engine)
        self.assertIn('nearest_index',engine)
        self.assertIn('MAX_CELLS',engine)

if __name__=='__main__': unittest.main()
