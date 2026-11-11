"""Regressões básicas de saídas temporárias e preservação das rotinas estáveis."""
from pathlib import Path
import tempfile
import unittest

from geosaga import ui_shared as ui
from geosaga.tests._support import check_release_metadata

# Desde a 1.0.4, ui_shared importa a tradução (from .i18n import tr): o módulo
# precisa ser importado pelo pacote geosaga, e não carregado como arquivo solto.
ROOT = Path(__file__).resolve().parents[1]

class TemporaryOutputTests(unittest.TestCase):
    def test_generates_distinct_real_directories(self):
        p1 = Path(ui.temporary_destination('avaliacao', '.tif'))
        p2 = Path(ui.temporary_destination('avaliacao', '.tif'))
        self.assertTrue(p1.parent.is_dir())
        self.assertTrue(p2.parent.is_dir())
        self.assertNotEqual(p1, p2)
        self.assertEqual(p1.suffix, '.tif')
        self.assertFalse(p1.exists())

    def test_output_preference(self):
        p = ui.output_destination(False, 'saida.tif', 'x', '.tif')
        self.assertEqual(p, 'saida.tif')
        temp = ui.output_destination(True, '', 'x', '.tif')
        self.assertEqual(Path(temp).suffix, '.tif')

    def test_engines_unchanged_by_gui_update(self):
        check_release_metadata(self)
        from zipfile import ZipFile
        archive = Path('/mnt/data/Vista_Saga_Plugin_QGIS4_v0.6.0_COMBINACAO_MAPAS.zip')
        if not archive.exists():
            self.skipTest('Arquivo de versão anterior ausente')
        with ZipFile(archive) as z:
            for name in ('combination_core.py','combination_raster.py',
                         'combination_vector.py','signature_engine.py',
                         'monitoring_engine.py','raster_engine.py'):
                self.assertEqual((ROOT / name).read_bytes(), z.read('geosaga/' + name))

if __name__ == '__main__':
    unittest.main()
