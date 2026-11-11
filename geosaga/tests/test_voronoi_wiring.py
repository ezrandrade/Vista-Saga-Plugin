from pathlib import Path
import configparser
import unittest
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support  # noqa: E402

ROOT=Path(__file__).resolve().parents[1]
class VoronoiWiring(unittest.TestCase):
    def test_registered_in_panel_and_menu(self):
        home=(ROOT/'home_dialog.py').read_text(encoding='utf-8')
        plugin=(ROOT/'plugin.py').read_text(encoding='utf-8')
        self.assertIn("'Análises Voronoi'",home)
        self.assertIn('self.plugin.open_voronoi',home)
        self.assertIn(('Análises Voronoi', 'open_voronoi'), _support.menu_entries())
        self.assertIn('open_voronoi', _support.plugin_methods())
        self.assertIn('voronoi_dialog', _support.module_attributes())
        self.assertIn('dialog.deleteLater()', plugin)  # descarga genérica em _dispose_dialog

    def test_four_modalities_two_available(self):
        dialog=(ROOT/'voronoi_dialog.py').read_text(encoding='utf-8')
        for name in ('Simples','Com Massa','Com Atrito','Com Massa e Atrito'):
            self.assertIn(name,dialog)
        self.assertIn("'Com Massa e Atrito (experimental)'", dialog)
        self.assertIn('Com Atrito (experimental)',dialog)
        self.assertIn('QgsMapLayerComboBox',dialog)
        self.assertIn('temporary_destination',dialog)

    def test_unchanged_algorithms(self):
        import zipfile
        base=Path('/mnt/data/Vista_Saga_Plugin_QGIS4_v0.6.5_ABAS_PADRONIZADAS.zip')
        if not base.exists(): self.skipTest('Base ausente')
        with zipfile.ZipFile(base) as archive:
            for filename in ('core.py','raster_engine.py','monitoring_engine.py','signature_engine.py',
                             'combination_raster.py','combination_vector.py','rs2_converter.py'):
                self.assertEqual((ROOT/filename).read_bytes(), archive.read('geosaga/'+filename))

    def test_metadata(self):
        cfg=configparser.ConfigParser(interpolation=None)
        cfg.read(ROOT/'metadata.txt',encoding='utf-8')
        _support.assert_release_version(self)
        self.assertEqual(cfg['general']['qgisMinimumVersion'],'4.0')

if __name__=='__main__':unittest.main()
