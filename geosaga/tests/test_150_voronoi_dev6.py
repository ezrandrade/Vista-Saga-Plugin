"""1.4.0-dev6: recorte pela área de estudo na guia Raster, NoData do atrito atravessável, lascas do
recorte final, tempo de cálculo e partes abaixo da escala no resumo do vetor direto. Requer GDAL."""
import os
import tempfile
import unittest

import numpy as np

from geosaga.voronoi_core import Generator

try:
    from osgeo import gdal, ogr, osr
    HAS_GDAL = True
except ImportError:  # pragma: no cover - depende do ambiente
    HAS_GDAL = False


def _polygon(coords):
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in list(coords) + [coords[0]]:
        ring.AddPoint_2D(x, y)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return poly


def _rect(x0, y0, x1, y1):
    return _polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


class _FakeStudy:
    """Imita o necessário de QgsGeometry para ``save_vector_voronoi`` (sem PyQGIS)."""
    def __init__(self, geometry):
        self.geometry = geometry

    def isNull(self):
        return False

    def isEmpty(self):
        return self.geometry.IsEmpty()

    def isGeosValid(self):
        return self.geometry.IsValid()

    def asWkb(self):
        return self.geometry.ExportToWkb()


def _wkt():
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(31985)
    return srs.ExportToWkt()


def _read(path):
    ds = gdal.Open(path)
    data = ds.ReadAsArray()
    ds = None
    return data


@unittest.skipUnless(HAS_GDAL, 'GDAL/OGR indisponível')
class RasterStudyClipTests(unittest.TestCase):
    """Item 4: com extensão de camada poligonal, a guia Raster recorta pela área (centro da célula)."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.wkt = _wkt()
        self.t = (0., 2., 0., 100., 0., -2.)
        self.points = [Generator(1, 20., 20., 1.), Generator(2, 80., 80., 4.)]
        # Triângulo (cerca de metade da grade), sem centro de célula sobre a borda.
        self.study = _polygon([(0., 0.), (100., 0.), (0., 99.)])

    def _run(self, name, **kw):
        return run_voronoi_call(self.points, os.path.join(self.folder.name, name), self.wkt, self.t, **kw)

    def test_simple_and_mass_clip_by_cell_centre(self):
        cols, rows = np.meshgrid(np.arange(50), np.arange(50))
        x = self.t[0] + (cols + .5) * self.t[1]
        y = self.t[3] + (rows + .5) * self.t[5]
        inside = x / 100. + y / 99. < 1.
        for mode in ('simple', 'mass'):
            with self.subTest(modalidade=mode):
                full = self._run(f'{mode}_cheio.tif', mode=mode)
                clipped = self._run(f'{mode}_recorte.tif', mode=mode, study_wkb=self.study.ExportToWkb())
                a, b = _read(full['output']), _read(clipped['output'])
                self.assertTrue((b[~inside] == 0).all())
                np.testing.assert_array_equal(b[inside], a[inside])
                self.assertEqual(clipped['study_cells'], int(inside.sum()))
                self.assertEqual(clipped['pixels_valid'], int(inside.sum()))
                with open(clipped['txt'], encoding='utf-8') as f:
                    text = f.read()
                self.assertIn('Recorte pela área de estudo', text)
                self.assertIn(f'{int(inside.sum())} pixels dentro', text)

    def test_friction_outside_study_still_passable(self):
        # Atrito vetorial cobrindo a grade toda; o recorte só tira o resultado de fora, sem mudar os custos.
        features = [(bytes(_rect(0, 0, 100, 100).ExportToWkb()), 1.), (bytes(_rect(40, 40, 60, 60).ExportToWkb()), 5.)]
        spec = {'features': features, 'outside': 1.0}
        full = self._run('atrito_cheio.tif', mode='friction', friction_vector=spec)
        clipped = self._run('atrito_recorte.tif', mode='friction', friction_vector=spec,
                            study_wkb=self.study.ExportToWkb())
        a, b = _read(full['output']), _read(clipped['output'])
        inside = b > 0
        np.testing.assert_array_equal(b[inside], a[inside])
        self.assertEqual(int(inside.sum()), clipped['study_cells'])

    def test_empty_study_rejected(self):
        far = _rect(1000., 1000., 1001., 1001.)
        with self.assertRaisesRegex(ValueError, 'área de estudo'):
            self._run('vazio.tif', mode='simple', study_wkb=far.ExportToWkb())


def run_voronoi_call(points, destination, wkt, t, **kw):
    from geosaga.voronoi_engine import run_voronoi
    return run_voronoi(points, destination, wkt, t, 50, 50, **kw)


@unittest.skipUnless(HAS_GDAL, 'GDAL/OGR indisponível')
class RasterNoDataPassageTests(unittest.TestCase):
    """Item 6: NoData do raster de atrito = sem resultado, atravessável com nota 1."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.wkt = _wkt()
        self.t = (0., 2., 0., 100., 0., -2.)
        self.points = [Generator(1, 11., 89., 1.), Generator(2, 89., 11., 1.)]
        friction = np.full((50, 50), 2.0)
        friction[:, 20:30] = -9999.    # faixa vertical sem nota entre os polos
        friction[5:15, 35:45] = 4.
        self.friction = friction

    def _tif(self, name, array, nodata=-9999.):
        path = os.path.join(self.folder.name, name)
        ds = gdal.GetDriverByName('GTiff').Create(path, 50, 50, 1, gdal.GDT_Float64)
        ds.SetGeoTransform(self.t)
        ds.SetProjection(self.wkt)
        band = ds.GetRasterBand(1)
        band.WriteArray(array)
        if nodata is not None:
            band.SetNoDataValue(nodata)
        ds = None
        return path

    def test_nodata_strip_is_crossed_with_rating_one(self):
        from geosaga.voronoi_engine import run_voronoi
        nodata = self.friction == -9999.
        with_nodata = self._tif('atrito_nodata.tif', self.friction)
        reference = self.friction.copy()
        reference[nodata] = 1.0
        ones = self._tif('atrito_um.tif', reference, nodata=None)
        for mode in ('friction', 'mass_friction'):
            with self.subTest(modalidade=mode):
                got = run_voronoi(self.points, os.path.join(self.folder.name, f'{mode}_a.tif'), self.wkt, self.t,
                                  50, 50, mode=mode, friction_path=with_nodata)
                expected = run_voronoi(self.points, os.path.join(self.folder.name, f'{mode}_b.tif'), self.wkt,
                                       self.t, 50, 50, mode=mode, friction_path=ones)
                a, b = _read(got['output']), _read(expected['output'])
                self.assertTrue((a[nodata] == 0).all())               # sem resultado
                np.testing.assert_array_equal(a[~nodata], b[~nodata])  # custos = nota 1 na faixa
                self.assertTrue((a[:, 30:] == 2).any() and (a[:, :20] == 1).any())
                self.assertEqual(got['friction_nodata_cells'], int(nodata.sum()))
                with open(got['txt'], encoding='utf-8') as f:
                    text = f.read()
                self.assertIn(f'NoData da superfície de atrito ({int(nodata.sum())} células)', text)
                self.assertNotIn('barreira', text)

    def test_centre_on_nodata_still_rejected(self):
        from geosaga.voronoi_engine import run_voronoi
        path = self._tif('atrito_nodata2.tif', self.friction)
        points = [Generator(1, 50., 50., 1.), Generator(2, 89., 11., 1.)]
        with self.assertRaisesRegex(ValueError, 'NoData'):
            run_voronoi(points, os.path.join(self.folder.name, 'x.tif'), self.wkt, self.t, 50, 50,
                        mode='friction', friction_path=path)


@unittest.skipUnless(HAS_GDAL, 'GDAL/OGR indisponível')
class ClipSliverTests(unittest.TestCase):
    """Item 1: lascas do recorte final vão para a região vizinha de maior fronteira comum."""

    def test_thin_part_moves_to_neighbour(self):
        from geosaga.voronoi_friction_continuous import absorb_clip_slivers
        a, b = Generator(1, 0., 0., 1.), Generator(2, 1., 1., 1.)
        region_a = ogr.Geometry(ogr.wkbMultiPolygon)
        region_a.AddGeometry(_rect(0., 0., 50., 100.))
        region_a.AddGeometry(_rect(50., 99.98, 100., 100.))   # lasca de 2 cm na borda de B
        region_b = ogr.Geometry(ogr.wkbMultiPolygon)
        region_b.AddGeometry(_rect(50., 0., 100., 99.98))
        regions, moved = absorb_clip_slivers([(a, region_a), (b, region_b)], 0.5)
        self.assertEqual(moved, 1)
        self.assertEqual(regions[0][1].GetGeometryCount(), 1)
        self.assertEqual(regions[1][1].GetGeometryCount(), 1)
        self.assertAlmostEqual(regions[0][1].GetArea(), 5000., places=6)
        self.assertAlmostEqual(regions[1][1].GetArea(), 5000., places=6)

    def test_wide_parts_are_kept(self):
        from geosaga.voronoi_friction_continuous import absorb_clip_slivers
        a, b = Generator(1, 0., 0., 1.), Generator(2, 1., 1., 1.)
        region_a = ogr.Geometry(ogr.wkbMultiPolygon)
        region_a.AddGeometry(_rect(0., 0., 50., 100.))
        region_a.AddGeometry(_rect(50., 98., 100., 100.))     # 2 m: maior que 2 × tolerância
        region_b = ogr.Geometry(ogr.wkbMultiPolygon)
        region_b.AddGeometry(_rect(50., 0., 100., 98.))
        regions, moved = absorb_clip_slivers([(a, region_a), (b, region_b)], 0.5)
        self.assertEqual(moved, 0)
        self.assertEqual(regions[0][1].GetGeometryCount(), 2)


@unittest.skipUnless(HAS_GDAL, 'GDAL/OGR indisponível')
class VectorSummaryTests(unittest.TestCase):
    """Itens 3 e 5a: tempo de cálculo e partes < 25 m² (só informadas) no resumo do vetor direto."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.wkt = _wkt()

    def test_small_parts_listed_by_region(self):
        from geosaga.voronoi_friction_continuous import small_parts
        a = Generator(1, 0., 0., 1., 'A')
        region = ogr.Geometry(ogr.wkbMultiPolygon)
        region.AddGeometry(_rect(0., 0., 10., 10.))     # 100 m²
        region.AddGeometry(_rect(20., 20., 24., 24.))   # 16 m²
        region.AddGeometry(_rect(30., 30., 31., 32.))   # 2 m²
        found = small_parts([(a, region)], 1.0, 25.)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][1], 2)
        self.assertAlmostEqual(found[0][2], 18.)

    def test_mass_summary_has_time_and_small_parts_line(self):
        from geosaga.voronoi_vector import save_vector_voronoi
        points = [Generator(1, 100., 100., 1., 'A'), Generator(2, 400., 400., 4., 'B')]
        target = os.path.join(self.folder.name, 'massa.gpkg')
        result = save_vector_voronoi(points, (0., 0., 500., 500.), target, self.wkt, mode='mass')
        with open(result['txt'], encoding='utf-8') as f:
            text = f.read()
        self.assertRegex(text, r'Tempo de cálculo \(s\): \d+\.\d')
        self.assertIn('Partes com área menor que 25 m²', text)
        self.assertIn('nenhuma', text)

    def test_friction_with_study_runs_and_reports(self):
        from geosaga.voronoi_vector import save_vector_voronoi
        features = [(bytes(_rect(0, 0, 100, 100).ExportToWkb()), 1.), (bytes(_rect(40, 0, 60, 100).ExportToWkb()), 3.)]
        points = [Generator(1, 20., 50., 1., 'A'), Generator(2, 80., 50., 1., 'B')]
        study = _FakeStudy(_polygon([(0., 0.), (100., 0.), (100., 100.), (0., 60.)]))
        target = os.path.join(self.folder.name, 'atrito.gpkg')
        result = save_vector_voronoi(points, (0., 0., 100., 100.), target, self.wkt, mode='friction',
                                     friction_features=features, study_geometry=study,
                                     friction_info={'outside': 1.0, 'layer_name': 'uso', 'rating_field': 'NOTA'})
        self.assertAlmostEqual(sum(r['AREA_M2'] for r in result['rows']), study.geometry.GetArea(), delta=1.)
        with open(result['txt'], encoding='utf-8') as f:
            text = f.read()
        self.assertIn('Tempo de cálculo (s):', text)
        self.assertIn('Partes com área menor que 25 m²', text)


if __name__ == '__main__':
    unittest.main()
