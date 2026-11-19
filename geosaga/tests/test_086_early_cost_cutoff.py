"""Interrupção antecipada das trajetórias (poda exata), no modelo do Vista SAGA desde a 1.4.0."""
import unittest
import numpy as np
from geosaga.voronoi_core import Generator
from geosaga.voronoi_friction import _vista_saga_cost_batch, assign_friction_window
from geosaga.tests.friction_reference import path_cost, reference


class TestFrictionEarlyCutoff086(unittest.TestCase):
    def test_batch_matches_scalar_reference(self):
        rng=np.random.default_rng(391)
        for seed in range(6):
            raster=rng.uniform(0, 19, (14, 17))
            raster[4, 6] = np.nan
            start=(1+seed, 2)
            cols=rng.integers(0, 17, 60)
            rows=rng.integers(0, 14, 60)
            got=_vista_saga_cost_batch(raster,*start,cols,rows,pixel_x=10.,pixel_y=10.)
            expected=[path_cost(raster,*start,int(c),int(r),10.,10.) for c,r in zip(cols,rows)]
            np.testing.assert_allclose(got,expected,rtol=1e-12)
            unlimited=_vista_saga_cost_batch(raster,*start,cols,rows,pixel_x=10.,pixel_y=10.,max_costs=np.inf)
            np.testing.assert_array_equal(unlimited,got)

    def test_cutoff_returns_inf_only_when_full_cost_exceeds_threshold(self):
        raster=np.full((3,15), 4.)
        cols=np.arange(15)
        rows=np.zeros(15,dtype=int)
        full=_vista_saga_cost_batch(raster,0,0,cols,rows)
        limits=np.array([1, 5, 10, 15, 20, 100, 500, 0, 100, 100, 1, 1, 5, 50, 2.],dtype=float)
        stats={}
        got=_vista_saga_cost_batch(raster,0,0,cols,rows,max_costs=limits,stats=stats)
        for old,new,lim in zip(full,got,limits):
            self.assertEqual(np.isfinite(new), old<=lim)
            if old<=lim:
                self.assertEqual(old,new)
        self.assertGreater(stats['early_stops'],0)
        self.assertLess(stats['visited_cells'],sum(range(15)))

    def test_equal_cost_limit_preserved(self):
        raster=np.ones((1,7))
        cost=_vista_saga_cost_batch(raster,0,0,np.array([3]),np.array([0]))[0]
        same=_vista_saga_cost_batch(raster,0,0,np.array([3]),np.array([0]),max_costs=[cost])[0]
        self.assertEqual(cost,6.)  # 1×1 + 2×1 + 3×1
        self.assertEqual(cost,same)

    def test_random_modes_match_exhaustive_reference(self):
        for seed in range(8):
            rng=np.random.default_rng(seed*13+17)
            nrows,ncols=11,15
            geo=(500000.,10.,0.,9000000.,0.,-10.)
            fr=rng.choice([0.,1.,2.,4.,10.,100.,np.nan],size=(nrows,ncols),p=[.18,.21,.2,.14,.13,.08,.06])
            generators=[]
            for i, (col,row) in enumerate(((1,1),(13,2),(2,9),(12,8),(7,5))):
                fr[row,col]=2
                generators.append(Generator(i+1,geo[0]+(col+.5)*10,
                                            geo[3]-(row+.5)*10,float(rng.uniform(.1,25)),str(i)))
            for masses in (False, True):
                stat={}
                actual=assign_friction_window(generators,fr,geo,0,nrows,mass_weighted=masses,stats=stat,batch_size=13)
                expected=reference(generators,fr,geo,weighted=masses)
                np.testing.assert_array_equal(actual,expected)
                self.assertGreaterEqual(stat['traced_paths'],stat.get('early_stops',0))
                self.assertGreater(stat['visited_cells'],0)

    def test_invalid_limits_rejected(self):
        fr=np.zeros((1,2))
        for bad in ([float('nan')],[float('-inf')],[-1]):
            with self.assertRaisesRegex(ValueError,'não negativos'):
                _vista_saga_cost_batch(fr,0,0,np.array([1]),np.array([0]),max_costs=bad)
