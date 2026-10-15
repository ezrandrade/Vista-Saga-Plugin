"""Validação matemática da composição por pesos/notas sem depender de QGIS."""
import unittest
import numpy as np
from geosaga.voronoi_friction_stack import (
    parse_class_notes, apply_class_notes, combine_friction_arrays,
)
from geosaga.voronoi_core import Generator
from geosaga.voronoi_friction import assign_friction_window

class MultiFrictionTests(unittest.TestCase):
    def test_class_notes_and_reweighting(self):
        a = np.array([[1,2],[2,1]], dtype=float)
        b = np.array([[2,6],[2,6]], dtype=float)
        got = combine_friction_arrays([a,b],[2,1],['1=0;2=9',''])
        expected = (np.array([[0,9],[9,0]])*2+b)/3
        np.testing.assert_allclose(got, expected)

    def test_nodata_union_of_barriers(self):
        a=np.array([[0.,2.],[np.nan,5.]])
        b=np.array([[3.,np.nan],[6.,4.]])
        got=combine_friction_arrays([a,b],[1,1])
        self.assertEqual(got[0,0], 1.5)
        self.assertTrue(np.isnan(got[0,1]))
        self.assertTrue(np.isnan(got[1,0]))
        self.assertEqual(got[1,1], 4.5)

    def test_equal_weights_and_no_notes_is_mean(self):
        a=np.full((5,4),2.)
        b=np.full((5,4),6.)
        np.testing.assert_allclose(combine_friction_arrays([a,b],[3,3]),4.)

    def test_missing_class_note_raises(self):
        with self.assertRaisesRegex(ValueError,'sem nota'):
            combine_friction_arrays([np.array([[1,2]])],[1],['1=9'])

    def test_invalid_weights_and_notes(self):
        for weights in ([0,1],[-1,2],[float('nan'),1]):
            with self.assertRaises(ValueError):
                combine_friction_arrays([np.ones((2,2))]*2,weights)
        with self.assertRaises(ValueError):
            parse_class_notes('1=2;1=3')
        with self.assertRaises(ValueError):
            parse_class_notes('1=-5')

    def test_single_map_stack_same_as_original(self):
        a=np.arange(64,dtype=float).reshape(8,8)%5
        t=(0.,10.,0.,80.,0.,-10.)
        p=[Generator(1,5,75,1.,'A'),Generator(2,75,5,3.,'B')]
        np.testing.assert_array_equal(
            assign_friction_window(p,a,t,0,8,mass_weighted=True),
            assign_friction_window(p,combine_friction_arrays([a],[9]),t,0,8,mass_weighted=True)
        )

    def test_multimap_changes_winner(self):
        a=np.zeros((8,8),dtype=float)
        b=np.zeros((8,8),dtype=float)
        b[:,2:4]=50
        t=(0.,1.,0.,8.,0.,-1.)
        p=[Generator(1,.5,3.5,1.,'A'),Generator(2,7.5,3.5,1.,'B')]
        x=assign_friction_window(p, a,t,0,8)
        y=assign_friction_window(p, combine_friction_arrays([a,b],[1,8]),t,0,8)
        self.assertFalse(np.array_equal(x,y))

    def test_operation_counts_diagnostic_no_change_to_result(self):
        a=np.zeros((8,8))
        t=(0.,1.,0.,8.,0.,-1.)
        p=[Generator(1,1.5,6.5,1.,'A'),Generator(2,6.5,1.5,4.,'B')]
        from geosaga.voronoi_friction import assign_friction_window
        metrics={}
        result=assign_friction_window(p,a,t,0,8,mass_weighted=True,stats=metrics)
        baseline=assign_friction_window(p,a,t,0,8,mass_weighted=True)
        np.testing.assert_array_equal(result,baseline)
        self.assertEqual(metrics['candidate_pairs'],128)
        self.assertGreater(metrics['traced_paths'],0)
        self.assertLessEqual(metrics['traced_paths'],metrics['candidate_pairs'])

    def test_reader_streams_layers_without_reprojection(self):
        import tempfile
        from pathlib import Path
        from geosaga.voronoi_friction_stack import read_friction_stack
        class FakeBand:
            def __init__(self, array): self.array = array
            def ReadAsArray(self): return self.array
            def GetNoDataValue(self): return -9999.
            def GetMaskBand(self): return self
        class FakeDataset:
            RasterCount=1
            RasterXSize=2
            RasterYSize=2
            def __init__(self, data, gt): self.data,self.gt=data,gt
            def GetGeoTransform(self): return self.gt
            def GetProjectionRef(self): return 'WKT'
            def GetRasterBand(self, number): return FakeBand(self.data)
        class GDAL:
            GA_ReadOnly=0
            def __init__(self, datasets): self.datasets=datasets
            def Open(self, path, _): return self.datasets[path]
        class SRS:
            def ImportFromWkt(self, value): return 0
            def IsSame(self, other): return True
        class OSR:
            SpatialReference=SRS
        gt=(0.,10.,0.,20.,0.,-10.)
        with tempfile.TemporaryDirectory() as directory:
            paths=[str(Path(directory)/f'{n}.tif') for n in (1,2)]
            for path in paths: Path(path).touch()
            gd=GDAL({paths[0]: FakeDataset(np.array([[1.,2.],[2.,1.]]),gt),
                     paths[1]: FakeDataset(np.array([[2.,3.],[2.,-9999.]]),gt)})
            out=read_friction_stack([
                  {'path':paths[0],'weight':3,'notes':'1=2;2=8'},
                  {'path':paths[1],'weight':1,'notes':'2=4;3=6'}],
                  gd, 'WKT', gt, 2, 2, OSR)
            np.testing.assert_allclose(out[0],[(3*2+4)/4,(3*8+6)/4])
            self.assertTrue(np.isnan(out[1,1]))

    def test_all_invalid_fails_to_have_valid_output(self):
        a=np.full((3,3),np.nan)
        np.testing.assert_array_equal(np.isnan(combine_friction_arrays([a],[1])),np.ones((3,3),bool))

if __name__=='__main__':unittest.main()
