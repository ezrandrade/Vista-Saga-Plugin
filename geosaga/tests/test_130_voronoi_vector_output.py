"""1.3.0: saída vetorial do Voronoi em qualquer modalidade e nos formatos padrão do plugin.

Os testes com GDAL real são pulados quando ``osgeo`` não está disponível.
"""
from pathlib import Path
import tempfile
import unittest

from geosaga.voronoi_output import layer_uri, vector_extension

try:
    from osgeo import gdal, ogr, osr  # noqa: F401
    HAS_GDAL = True
except ImportError:  # pragma: no cover - depende do ambiente
    HAS_GDAL = False

FORMATS = ('.gpkg', '.shp', '.geojson', '.fgb')


class VectorOutputHelpersTests(unittest.TestCase):
    def test_extension_from_path_or_suffix(self):
        self.assertEqual(vector_extension('C:/dados/saida.SHP'), '.shp')
        self.assertEqual(vector_extension('.fgb'), '.fgb')
        with self.assertRaisesRegex(ValueError, 'não suportado'):
            vector_extension('saida.kml')

    def test_layer_uri(self):
        self.assertEqual(layer_uri('/x/a.gpkg'), '/x/a.gpkg|layername=voronoi_espacial')
        self.assertEqual(layer_uri('/x/a.shp'), '/x/a.shp')

    def test_dialog_offers_vector_output_for_every_mode(self):
        content = (Path(__file__).resolve().parents[1] / 'voronoi_dialog.py').read_text(encoding='utf-8')
        # Guia Vetorial para todas as modalidades; formatos pelo filtro do "Salvar como…".
        self.assertIn("for title in ('Raster', 'Vetorial'):", content)
        self.assertIn("filters = [f'{label} (*{extension})' for extension, (_, label) in VECTOR_FORMATS.items()]", content)
        self.assertIn("keep_raster=kind=='raster'", content)
        self.assertIn("vectorize=kind=='vector',", content)
        # Padrão do plugin: sem caixas de temporário/carregar; vetor temporário em memória.
        self.assertNotIn('temp_output', content)
        self.assertNotIn('load_project', content)
        self.assertNotIn('poligonização)', content)
        # 1.5.0: a camada carregada recebe o nome do arquivo (temporário = "Análises Voronoi - modalidade").
        self.assertIn("materialize_in_memory(layer_uri(vector_path), layer_name(vector_path))", content)
        self.assertIn("'[Camada temporária em memória]'", content)


@unittest.skipUnless(HAS_GDAL, 'GDAL/OGR indisponível')
class VoronoiVectorFormatsGdalTests(unittest.TestCase):
    def setUp(self):
        from geosaga.voronoi_core import Generator
        self.points = [Generator(1, 500055., 7499945., 1., 'Escola São José'),
                       Generator(2, 500245., 7499855., 3., 'Posto Ação'),
                       Generator(3, 500105., 7499755., 2., 'C')]
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(31983)
        self.srs = srs
        self.wkt = srs.ExportToWkt()
        self.transform = (500000., 10., 0., 7500000., 0., -10.)
        self.folder = tempfile.TemporaryDirectory(prefix='vistasaga_130_')
        self.addCleanup(self.folder.cleanup)
        self.dir = Path(self.folder.name)

    def _run(self, name, **kw):
        from geosaga.voronoi_engine import run_voronoi
        return run_voronoi(self.points, str(self.dir / name), self.wkt, self.transform,
                           30, 25, vectorize=True, **kw)

    def _read(self, path):
        ds = ogr.Open(str(path))
        self.assertIsNotNone(ds, path)
        layer = ds.GetLayer(0)
        fields = [layer.GetLayerDefn().GetFieldDefn(i).GetName()
                  for i in range(layer.GetLayerDefn().GetFieldCount())]
        features = [(f.GetField('CENTRO_ID'), f.GetField('CENTRO'), f.GetField('MASSA'),
                     f.GetField('AREA_HA')) for f in layer]
        srs = layer.GetSpatialRef()
        ds = None
        return fields, features, srs

    def test_mass_vector_only_in_every_format(self):
        expected = None
        for extension in FORMATS:
            with self.subTest(formato=extension):
                result = self._run(f'massa{extension[1:]}.tif', mode='mass',
                                   vector_format=extension, keep_raster=False)
                vector = Path(result['vector'])
                self.assertEqual(vector.suffix, extension)
                self.assertTrue(vector.is_file())
                self.assertIsNone(result['output'])
                self.assertFalse(vector.with_suffix('.tif').exists(), 'GeoTIFF deveria ser descartado')
                self.assertEqual(result['gpkg'], str(vector) if extension == '.gpkg' else None)
                self.assertTrue(Path(result['csv']).is_file() and Path(result['txt']).is_file())
                self.assertEqual(list(self.dir.glob('*_trabalho.gpkg')), [])
                self.assertEqual(list(self.dir.glob('.vista_voronoi_*')), [])
                fields, features, srs = self._read(vector)
                for name in ('CENTRO_ID', 'CENTRO', 'MASSA', 'AREA_HA'):
                    self.assertIn(name, fields)
                names = {row[0]: row[1] for row in features}
                self.assertEqual(names[1], 'Escola São José')
                self.assertEqual(names[2], 'Posto Ação')
                # Área dos polígonos = área dos pixels de cada centro (CSV/TXT).
                by_center = {}
                for center, _, mass, area in features:
                    by_center[center] = by_center.get(center, 0.) + area
                for row in result['rows']:
                    self.assertAlmostEqual(by_center.get(row['ID'], 0.), row['AREA_HA'], places=6)
                if extension != '.geojson':  # GeoJSON grava o SRC de forma simplificada
                    self.assertTrue(srs is not None and srs.IsSame(self.srs), extension)
                summary = sorted((c, round(a, 6)) for c, a in by_center.items())
                if expected is None:
                    expected = summary
                self.assertEqual(summary, expected, 'formatos devem trazer as mesmas regiões')
                report = Path(result['txt']).read_text(encoding='utf-8')
                self.assertIn('poligonização da grade raster', report)
                self.assertIn('GeoTIFF intermediário foi descartado', report)

    def test_shapefile_companions_and_stale_files(self):
        target = self.dir / 'saida.shp'
        stale = self.dir / 'saida.qix'
        stale.write_bytes(b'indice antigo')
        result = self._run('saida.tif', mode='mass', vector_format='.shp', keep_raster=False)
        self.assertEqual(result['vector'], str(target))
        for extension in ('.shp', '.shx', '.dbf', '.prj', '.cpg'):
            self.assertTrue(target.with_suffix(extension).is_file(), extension)
        self.assertFalse(stale.exists(), 'arquivo antigo da família não deve sobrar')
        # Regravar no mesmo destino substitui o conjunto inteiro.
        again = self._run('saida.tif', mode='simple', vector_format='.shp', keep_raster=False)
        self.assertTrue(Path(again['vector']).is_file())

    def test_geotiff_plus_vector_keeps_both(self):
        result = self._run('ambos.tif', mode='mass', vector_format='.fgb')
        self.assertTrue(Path(result['output']).is_file())
        self.assertEqual(Path(result['vector']).name, 'ambos.fgb')
        self.assertTrue(Path(result['vector']).is_file())

    def test_default_stays_geopackage(self):
        result = self._run('padrao.tif', mode='simple')
        self.assertEqual(Path(result['gpkg']).name, 'padrao.gpkg')
        self.assertEqual(result['vector'], result['gpkg'])
        self.assertTrue(Path(result['output']).is_file())

    def test_friction_vector_only_uses_friction_grid(self):
        """Guia Vetorial com atrito: cálculo na grade do atrito, só a camada vetorial fica."""
        import numpy as np
        friction = self.dir / 'atrito.tif'
        ds = gdal.GetDriverByName('GTiff').Create(str(friction), 30, 25, 1, gdal.GDT_Float32)
        ds.SetGeoTransform(self.transform)
        ds.SetProjection(self.wkt)
        surface = np.ones((25, 30), dtype=np.float32)  # 1.4.0: nota 0 é recusada
        surface[:, 14:16] = 50.  # faixa de alto atrito entre os centros
        ds.GetRasterBand(1).WriteArray(surface)
        ds = None
        for mode in ('friction', 'mass_friction'):
            with self.subTest(modalidade=mode):
                result = self._run(f'{mode}.tif', mode=mode, friction_path=str(friction),
                                   vector_format='.shp', keep_raster=False)
                vector = Path(result['vector'])
                self.assertTrue(vector.is_file())
                self.assertIsNone(result['output'])
                self.assertFalse(vector.with_suffix('.tif').exists())
                _, features, _ = self._read(vector)
                total = sum(area for _, _, _, area in features)
                self.assertAlmostEqual(total, sum(row['AREA_HA'] for row in result['rows']), places=6)
                self.assertIn('célula de 10 × 10', Path(result['txt']).read_text(encoding='utf-8'))

    def test_vector_only_requires_vectorize(self):
        from geosaga.voronoi_engine import run_voronoi
        with self.assertRaisesRegex(ValueError, 'precisa ser vetorial'):
            run_voronoi(self.points, str(self.dir / 'x.tif'), self.wkt, self.transform,
                        30, 25, mode='mass', vectorize=False, keep_raster=False)


if __name__ == '__main__':
    unittest.main()
