"""Voronoi 0.7.0: testes sem dependência do QGIS."""
import unittest
import numpy as np
from geosaga.voronoi_core import (Generator,assign_window,
                                 validate_generators,pixel_area_m2,counts_as_rows)
from geosaga.voronoi_engine import grid_from_extent

class VoronoiCoreTests(unittest.TestCase):
    def setUp(self):
        self.points = [Generator(1,.5,.5,1.,'A'), Generator(2,4.5,.5,1.,'B')]
        self.grid = (0.,1.,0.,1.,0.,-1.)

    def test_nearest_centres(self):
        labels = assign_window(self.points,self.grid,5,0,1)
        self.assertEqual(labels.tolist(),[[1,1,1,2,2]])

    def test_weight_equal_simple(self):
        simple = assign_window(self.points,self.grid,5,0,1,mode='simple')
        weighted = assign_window(self.points,self.grid,5,0,1,mode='mass')
        np.testing.assert_array_equal(simple,weighted)

    def test_mass_changes_boundary(self):
        generators = [Generator(1,.5,.5,1.,'A'), Generator(2,4.5,.5,3.,'B')]
        simple = assign_window(generators,self.grid,5,0,1,mode='simple')
        weighted = assign_window(generators,self.grid,5,0,1,mode='mass')
        self.assertEqual(simple[0,1],1)
        self.assertEqual(weighted[0,2],2)
        self.assertEqual(weighted[0,0],1)

    def test_tie_first_centre(self):
        result=assign_window([Generator(7,.5,.5),Generator(8,2.5,.5)],
                            self.grid,3,0,1)
        self.assertEqual(result.tolist(),[[7,7,8]])

    def test_scan_in_separate_windows(self):
        t = (0,1,0,3,0,-1)
        full = assign_window(self.points,t,5,0,3)
        joint = np.vstack([assign_window(self.points,t,5,0,1),
                           assign_window(self.points,t,5,1,2)])
        np.testing.assert_array_equal(full,joint)

    def test_rotated_grid(self):
        t=(0,1,.5,0,.25,-1)
        result=assign_window(self.points,t,5,0,2)
        self.assertEqual(result.shape,(2,5))
        self.assertTrue(set(np.unique(result)).issubset({1,2}))

    def test_mask_zeros(self):
        mask=np.array([[True,False,True,True,False]])
        self.assertEqual(assign_window(self.points,self.grid,5,0,1,mask=mask).tolist(),
                         [[1,0,1,2,0]])

    def test_invalid_mass(self):
        with self.assertRaisesRegex(ValueError,'maiores que zero'):
            validate_generators([Generator(1,1,1,0)],weighted=True)
        with self.assertRaisesRegex(ValueError,'finitos'):
            validate_generators([Generator(1,1,1,float('nan'))],weighted=False)

    def test_duplicate_position(self):
        with self.assertRaisesRegex(ValueError,'coincidentes'):
            validate_generators([Generator(1,0,0),Generator(2,0,0)])

    def test_invalid_mode(self):
        with self.assertRaisesRegex(ValueError,'não foi implementada'):
            assign_window(self.points,self.grid,5,0,1,mode='friction')

    def test_pixel_area_and_report(self):
        t=(0,10,0,0,0,-10)
        self.assertEqual(pixel_area_m2(t),100)
        rows=counts_as_rows(self.points,{1:3,2:1},t)
        self.assertEqual(rows[0]['AREA_HA'],.03)
        self.assertEqual(rows[0]['PCT_AREA'],75)
        self.assertEqual(sum(row['PCT_AREA'] for row in rows),100)

    def test_grid_limits(self):
        t,w,h=grid_from_extent((10,10,12,12),1)
        self.assertGreater(w,2)
        self.assertGreater(h,2)
        with self.assertRaisesRegex(ValueError,'50 milhões'):
            grid_from_extent((0,0,100000,100000),1)

    def test_valid_nonprojected_rejected_by_ui_spec(self):
        self.assertGreaterEqual(grid_from_extent((0,0,100,100),10)[1],10)

if __name__=='__main__':unittest.main()
