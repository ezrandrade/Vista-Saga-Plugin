"""Lotes alinhados e substituição segura de GeoTIFF e auxiliares."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from geosaga.rs2_format import RS2Error, RS2Header, write_rs2
from geosaga.rs2_batch import (Grid, compatible_grids, inspect_grid,
                                prepare_batch, source_mode, alignment_warnings)
from geosaga.rs2_outputs import (output_conflicts, output_family,
                                 publish_geotiff, write_worldfile)


class BatchOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.out = self.root / 'output'
        self.out.mkdir()
        self.h = RS2Header(4, 3, 100, 200, 140, 230,
                           ['FUNDO', 'ALVO'], [(255,255,255,0), (0,0,0,0)])
        self.input_a = self.root / 'a.rs2'
        self.input_b = self.root / 'b.rs2'
        for f in (self.input_a, self.input_b):
            write_rs2(f, self.h, iter(np.ones((3, 4), dtype=np.uint16)))

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_rs2_batch(self):
        mode, plans, grid = prepare_batch([self.input_a, self.input_b], self.out)
        self.assertEqual(mode, 0)
        self.assertEqual(grid, Grid(4, 3, 10, 10, (100, 200, 140, 230)))
        self.assertEqual(plans[1][1], self.out / 'b_categorias.tif')

    def test_different_extents_warn_but_convert_if_resolution_matches(self):
        h = RS2Header(4, 3, 110, 200, 150, 230, self.h.labels, self.h.colors)
        write_rs2(self.input_b, h, iter(np.zeros((3, 4), dtype=np.uint16)))
        self.assertEqual(len(prepare_batch([self.input_a, self.input_b], self.out)[1]), 2)
        self.assertEqual(len(alignment_warnings([self.input_a, self.input_b])), 1)

    def test_different_resolution_rejected(self):
        h = RS2Header(4, 3, 100, 200, 180, 230, self.h.labels, self.h.colors)
        write_rs2(self.input_b, h, iter(np.zeros((3, 4), dtype=np.uint16)))
        with self.assertRaisesRegex(RS2Error, 'resolução'):
            prepare_batch([self.input_a, self.input_b], self.out)

    def test_mixed_extensions_rejected_before_open(self):
        tiff = self.root / 'c.tif'
        tiff.write_bytes(b'not a tiff')
        with self.assertRaisesRegex(RS2Error, 'Não misture'):
            prepare_batch([self.input_a, tiff], self.out)

    def test_deduplicate_sources(self):
        with self.assertRaisesRegex(RS2Error, 'repetidos'):
            prepare_batch([self.input_a, self.input_a], self.out)

    def test_publish_removes_stale_sidecars_and_preserves_unrelated_xml(self):
        target = self.out / 'foo.tif'
        stage = self.out / 'foo.tif.part.tif'
        target.write_bytes(b'old')
        Path(str(target) + '.aux.xml').write_text('old aux')
        Path(str(target) + '.xml').write_text('old xml')
        Path(str(target) + '.rs2.json').write_text('old json')
        Path(str(target) + 'w').write_text('old tifw')
        target.with_suffix('.tfw').write_text('old tfw')
        unrelated = target.with_suffix('.xml')
        unrelated.write_text('external metadata')
        stage.write_bytes(b'new tiff')
        Path(str(stage) + '.rs2.json').write_text('new json')
        stage.with_suffix('.tfw').write_text('new world file')
        self.assertEqual(len(output_conflicts(target)), 6)
        publish_geotiff(stage, target)
        self.assertEqual(target.read_bytes(), b'new tiff')
        self.assertEqual(Path(str(target) + '.rs2.json').read_text(), 'new json')
        self.assertEqual(target.with_suffix('.tfw').read_text(), 'new world file')
        self.assertFalse(Path(str(target) + '.aux.xml').exists())
        self.assertFalse(Path(str(target) + '.xml').exists())
        self.assertFalse(Path(str(target) + 'w').exists())
        self.assertEqual(unrelated.read_text(), 'external metadata')

    def test_publish_rolls_back_if_replace_fails(self):
        target = self.out / 'foo.tif'
        stage = self.out / 'foo.tif.part.tif'
        target.write_bytes(b'original')
        Path(str(target) + '.rs2.json').write_text('old')
        stage.write_bytes(b'new')
        Path(str(stage) + '.rs2.json').write_text('new')
        import geosaga.rs2_outputs as module
        original_replace = module.os.replace

        def failing_replace(a, b):
            if Path(a) == Path(str(stage) + '.rs2.json'):
                raise PermissionError('simulated write lock')
            return original_replace(a, b)
        with patch.object(module.os, 'replace', side_effect=failing_replace):
            with self.assertRaisesRegex(RS2Error, 'simulated write lock'):
                publish_geotiff(stage, target)
        self.assertEqual(target.read_bytes(), b'original')
        self.assertEqual(Path(str(target) + '.rs2.json').read_text(), 'old')

    def test_worldfile_centers_pixels(self):
        name = self.out / 'abc.part.tif'
        result = write_worldfile(name, 100, 230, 10, 10)
        self.assertEqual(result.suffix, '.tfw')
        self.assertEqual([float(x) for x in result.read_text().splitlines()],
                         [10, 0, 0, -10, 105, 225])

    def test_grid_dimension_check(self):
        good, why = compatible_grids(Grid(4, 3, 10, 10, (100,200,140,230)),
                                     Grid(4, 4, 10, 10, (100,200,140,240)))
        self.assertFalse(good)
        self.assertIn('dimensões', why)


if __name__ == '__main__':
    unittest.main()
