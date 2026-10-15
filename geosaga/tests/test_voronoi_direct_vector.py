"""Testes do Voronoi vetorial não discretizado, sem runtime QGIS."""
import math
import unittest
from geosaga.voronoi_core import Generator, assign_window
from geosaga.voronoi_vector import simple_voronoi_polygons


def _polygon_area(ring):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:])))/2


class DirectVectorTests(unittest.TestCase):
    def test_two_centres_rectangle_exact_boundary(self):
        points=[Generator(1,0,5,label='A'),Generator(2,10,5,label='B')]
        polygons=dict((p.identifier,coords) for p,coords in simple_voronoi_polygons(points,(0,0,10,10)))
        self.assertEqual(set(polygons),{1,2})
        self.assertAlmostEqual(_polygon_area(polygons[1]),50)
        self.assertAlmostEqual(_polygon_area(polygons[2]),50)
        self.assertAlmostEqual(sum(_polygon_area(p) for p in polygons.values()),100)
        self.assertAlmostEqual(max(x for x,y in polygons[1]),5)
        self.assertAlmostEqual(min(x for x,y in polygons[2]),5)

    def test_irregular_centres_partition_rectangle(self):
        points=[Generator(1,1,1),Generator(2,8,2),Generator(3,3,7),Generator(4,9,9)]
        results=list(simple_voronoi_polygons(points,(0,0,10,10)))
        self.assertAlmostEqual(sum(_polygon_area(coords) for p,coords in results),100,places=7)
        self.assertTrue(all(coords[0]==coords[-1] for p,coords in results))

    def test_outside_centres_and_tie(self):
        points=[Generator(1,-10,5),Generator(2,20,5)]
        polys=list(simple_voronoi_polygons(points,(0,0,10,10)))
        self.assertAlmostEqual(sum(_polygon_area(poly) for _,poly in polys),100)
        self.assertAlmostEqual(max(x for x,y in polys[0][1]),5)

    def test_single_centre(self):
        poly=list(simple_voronoi_polygons([Generator(1,2,2)],(0,0,10,10)))
        self.assertEqual(len(poly),1)
        self.assertAlmostEqual(_polygon_area(poly[0][1]),100)

    def test_zero_area_rejected(self):
        with self.assertRaisesRegex(ValueError,'área positiva'):
            list(simple_voronoi_polygons([Generator(1,1,1)],(0,0,0,10)))

    def test_invalid_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError,'coincidentes'):
            list(simple_voronoi_polygons([Generator(1,2,2),Generator(2,2,2)],(0,0,10,10)))

    def test_cancel(self):
        with self.assertRaises(InterruptedError):
            list(simple_voronoi_polygons([Generator(1,0,0)],(0,0,10,10),cancelled=lambda:True))

    def test_ui_disables_mass_for_simple_and_has_direct_output(self):
        from pathlib import Path
        content=(Path(__file__).resolve().parents[1]/'voronoi_dialog.py').read_text()
        self.assertIn('if self.mode.currentIndex() in (1,3) else None',content)
        self.assertIn('GeoPackage (vetor direto — Simples)',content)
        self.assertIn('self.mass_field.setVisible(weighted)',content)
        self.assertIn('self.output_type.model().item(1).setEnabled(not (weighted or friction))',content)
        self.assertIn('self.extent_mode.addItem',content)

if __name__=='__main__': unittest.main()

class GridBBoxTests(unittest.TestCase):
    def test_no_margin(self):
        from geosaga.voronoi_engine import grid_from_bbox
        trans,width,height=grid_from_bbox((0,0,100,80),10)
        self.assertEqual((width,height),(10,8))
        self.assertEqual(trans,(0,10.,0.,80.,0.,-10.))

    def test_grid_bbox_limit(self):
        from geosaga.voronoi_engine import grid_from_bbox
        with self.assertRaisesRegex(ValueError,'50 milhões'):
            grid_from_bbox((0,0,100_000,100_000),1)
