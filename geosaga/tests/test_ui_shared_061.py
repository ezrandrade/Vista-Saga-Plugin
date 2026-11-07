"""Regressões básicas de saídas temporárias e preservação das rotinas estáveis."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
# ui_shared usa importação relativa (from .i18n import tr): importar pelo pacote.
import sys  # noqa: E402
sys.path.insert(0, str(ROOT.parent))
try:
    from geosaga import ui_shared as ui  # noqa: E402
except ImportError as exc:  # QGIS ausente no Python que executa a suíte
    raise unittest.SkipTest(f'ui_shared requer PyQGIS: {exc}')

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
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import _support
        _support.assert_release_version(self)
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
