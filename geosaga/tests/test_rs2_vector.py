"""Regressões do núcleo de exportação de vetores sem dependência QGIS."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

from geosaga.rs2_format import RS2Error, RS2Header, write_rs2, RS2Reader
from geosaga.rs2_vector import (
    VECTOR_FORMATS, class_attributes, vector_format, vector_family,
    vector_conflicts, _publish_vector, convert_rs2_to_vector,
)
from geosaga.rs2_batch import prepare_batch


class VectorExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.h = RS2Header(4, 3, 100, 200, 140, 230,
                           ['FUNDO', 'Floresta', 'Pastagem'],
                           [(255,255,255,0), (5,128,200,0), (30,200,20,0)])
        self.input = self.folder / 'geologia.rs2'
        write_rs2(self.input, self.h, iter(np.array([
            [0, 1, 1, 2], [0, 1, 2, 2], [1, 1, 0, 2]], dtype=np.uint16)))
        self.out = self.folder / 'out'
        self.out.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_codes_and_hex_preserved(self):
        self.assertEqual(class_attributes(RS2Reader(self.input).header), [
            (0, 'FUNDO', '#FFFFFF'),
            (1, 'Floresta', '#0580C8'),
            (2, 'Pastagem', '#1EC814'),
        ])

    def test_supported_extensions(self):
        self.assertEqual(vector_format('.GPKG')[0], 'GPKG')
        self.assertIn('.fgb', VECTOR_FORMATS)
        with self.assertRaises(RS2Error):
            vector_format('.txt')

    def test_vector_batch(self):
        other = self.folder / 'outro.rs2'
        write_rs2(other, self.h, iter(np.zeros((3, 4), dtype=np.uint16)))
        mode, plans, grid = prepare_batch([self.input, other], self.out,
                                           operation=2, vector_extension='.gpkg')
        self.assertEqual(mode, 2)
        self.assertEqual(plans[0][1], self.out / 'geologia_poligonos.gpkg')
        self.assertEqual(grid.columns, 4)

    def test_invalid_batch_and_extensions(self):
        with self.assertRaises(RS2Error):
            prepare_batch([self.input], self.out, operation=1)
        with self.assertRaises(RS2Error):
            prepare_batch([self.input], self.out, operation=2,
                          vector_extension='.exe')

    def test_vector_family_shp(self):
        self.assertEqual([p.suffix for p in vector_family(self.out / 'a.shp')],
                         ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.qix', '.sbn', '.sbx'])

    def test_shapefile_replacement_and_cleanup(self):
        target = self.out / 'map.shp'
        stage_folder = self.folder / 'stage'
        stage_folder.mkdir()
        stage = stage_folder / 'map.shp'
        for ext in ('.shp', '.dbf', '.shx', '.prj'):
            target.with_suffix(ext).write_text('old')
        for ext in ('.shp', '.dbf', '.shx', '.cpg'):
            stage.with_suffix(ext).write_text('new')
        self.assertEqual(len(vector_conflicts(target)), 4)
        _publish_vector(stage, target)
        for ext in ('.shp', '.dbf', '.shx', '.cpg'):
            self.assertEqual(target.with_suffix(ext).read_text(), 'new')
        self.assertFalse(target.with_suffix('.prj').exists())

    def test_shapefile_missing_companion_refused(self):
        stage = self.folder / 'incomplete.shp'
        stage.write_text('shp only')
        with self.assertRaisesRegex(RS2Error, 'obrigatório'):
            _publish_vector(stage, self.out / 'incomplete.shp')

    def test_rollback_on_failure(self):
        target = self.out / 'x.gpkg'
        stage = self.out / 'y.gpkg'
        target.write_text('original')
        stage.write_text('new')
        import geosaga.rs2_vector as mod
        orig_replace = mod.os.replace
        def fail(a, b):
            if Path(a) == stage:
                raise PermissionError('simulated lock')
            return orig_replace(a, b)
        with patch.object(mod.os, 'replace', side_effect=fail):
            with self.assertRaisesRegex(RS2Error, 'simulated lock'):
                _publish_vector(stage, target)
        self.assertEqual(target.read_text(), 'original')

    def test_missing_source_rejected_without_gdal(self):
        with self.assertRaisesRegex(RS2Error, 'Selecione um arquivo RS2'):
            convert_rs2_to_vector(self.folder / 'missing.rs2', self.out / 'a.gpkg')


if __name__ == '__main__':
    unittest.main()
