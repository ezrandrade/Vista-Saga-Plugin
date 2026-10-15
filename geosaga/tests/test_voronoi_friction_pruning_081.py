"""Prova por comparação: poda por limite inferior mantém os resultados do traçado integral."""
import unittest
import numpy as np
from geosaga.voronoi_core import Generator
from geosaga.voronoi_friction import assign_friction_window, _straight_cost_batch


def reference(generators, raster, t, *, weighted=False, baseline=1.):
    """Algoritmo integral pré-0.8.1, compara todos os pontos para cada célula."""
    height, width = raster.shape
    out = np.zeros((height,width), dtype=np.int32)
    for row in range(height):
        cols=np.flatnonzero(np.isfinite(raster[row]))
        xs = cols.astype(float)+.5
        ys=np.full(xs.shape,row+.5)
        wx=t[0]+t[1]*xs
        wy=t[3]+t[5]*ys
        best=np.full(xs.shape,np.inf)
        choice=np.zeros(xs.shape,dtype=np.int32)
        for p in generators:
            sx=(p.x-t[0])/t[1]; sy=(p.y-t[3])/t[5]
            costs=_straight_cost_batch(raster,sx,sy,xs,ys,baseline=baseline)
            scores=np.hypot(wx-p.x,wy-p.y)*costs/(p.mass if weighted else 1.)
            better=scores<best
            best[better]=scores[better]
            choice[better]=p.identifier
        out[row,cols]=choice
    return out


class FrictionPruning081Tests(unittest.TestCase):
    def test_random_rectangular_grids_match_original(self):
        for seed in range(8):
            rng=np.random.default_rng(seed)
            ny,nx=12,14
            t=(320000.,10.,0.,9000000.,0.,-10.)
            a=rng.uniform(0.,15.,(ny,nx))
            a[rng.random((ny,nx))<.025]=np.nan
            coords=[(1,1),(nx-2,ny-2),(3,ny-3),(nx-3,2),(7,5)]
            generators=[]
            for i,(ix,iy) in enumerate(coords):
                a[iy,ix]=rng.uniform(0,15)
                generators.append(Generator(i+1,t[0]+(ix+rng.uniform(.05,.95))*t[1],
                                           t[3]+(iy+rng.uniform(.05,.95))*t[5],
                                           rng.uniform(.2,10.),str(i)))
            for weighted in (False,True):
                full=reference(generators,a,t,weighted=weighted)
                pruned=assign_friction_window(generators,a,t,0,ny,batch_size=19,
                                              mass_weighted=weighted)
                np.testing.assert_array_equal(pruned,full,err_msg=f'seed={seed}, mass={weighted}')

    def test_shuffled_generator_order_and_ties(self):
        a=np.ones((9,9),dtype=float)
        t=(0.,1.,0.,9.,0.,-1.)
        points=[Generator(2,2.5,4.5,1,'first'),Generator(1,6.5,4.5,1,'second'),
                Generator(3,8.5,.5,1,'third')]
        np.testing.assert_array_equal(assign_friction_window(points,a,t,0,9),reference(points,a,t))

    def test_barriers_and_weighted_influence(self):
        a=np.ones((8,16),dtype=float)
        a[3:7,9]=np.nan
        a[0,2]=1000
        p=[Generator(1,1.5,7.5,3,'A'),Generator(2,14.5,1.5,11,'B'),Generator(3,5.5,3.5,1,'C')]
        t=(0.,1.,0.,8.,0.,-1.)
        for mass in (False,True):
            np.testing.assert_array_equal(assign_friction_window(p,a,t,0,8,mass_weighted=mass),reference(p,a,t,weighted=mass))

    def test_legacy_fixed_workload_guard_removed(self):
        from pathlib import Path
        txt=(Path(__file__).resolve().parents[1]/'voronoi_engine.py').read_text(encoding='utf-8')
        self.assertNotIn('MAX_ESTIMATED_CELL_VISITS',txt)
        self.assertIn('assign_friction_window(',txt)

if __name__ == '__main__':
    unittest.main()
