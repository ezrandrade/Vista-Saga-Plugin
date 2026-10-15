"""Invariantes matemáticas de Massa + Atrito, independentes do QGIS."""
import unittest
import numpy as np
from geosaga.voronoi_core import Generator
from geosaga.voronoi_friction import assign_friction_window

class MassFrictionTest(unittest.TestCase):
    def setUp(self):
        self.friction = np.ones((1,7),dtype=np.float64)
        self.tr = (0.,1.,0.,1.,0.,-1.)
        self.same = [Generator(1,.5,.5,1), Generator(2,6.5,.5,1)]
    def test_equal_masses_match_friction_only(self):
        a=assign_friction_window(self.same,self.friction,self.tr,0,1)
        b=assign_friction_window(self.same,self.friction,self.tr,0,1,mass_weighted=True)
        np.testing.assert_array_equal(a,b)
    def test_larger_mass_extends_influence(self):
        a=assign_friction_window(self.same,self.friction,self.tr,0,1)
        points=[Generator(1,.5,.5,1),Generator(2,6.5,.5,10)]
        b=assign_friction_window(points,self.friction,self.tr,0,1,mass_weighted=True)
        self.assertGreater(np.count_nonzero(b==2),np.count_nonzero(a==2))
    def test_all_masses_scale_invariant(self):
        p1=[Generator(1,.5,.5,2),Generator(2,6.5,.5,5)]
        p2=[Generator(1,.5,.5,20),Generator(2,6.5,.5,50)]
        np.testing.assert_array_equal(
            assign_friction_window(p1,self.friction,self.tr,0,1,mass_weighted=True),
            assign_friction_window(p2,self.friction,self.tr,0,1,mass_weighted=True))
    def test_invalid_mass(self):
        points=[Generator(1,.5,.5,0),Generator(2,6.5,.5,1)]
        with self.assertRaisesRegex(ValueError,'massas'):
            assign_friction_window(points,self.friction,self.tr,0,1,mass_weighted=True)
    def test_friction_barrier_still_blocks(self):
        f=self.friction.copy()
        f[0,3]=np.nan
        result=assign_friction_window(self.same,f,self.tr,0,1,mass_weighted=True)
        self.assertEqual(result[0,3],0)
        self.assertEqual(result[0,2],1)
        self.assertEqual(result[0,4],2)
