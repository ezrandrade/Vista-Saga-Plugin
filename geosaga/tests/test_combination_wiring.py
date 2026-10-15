"""Testes de integração estática: painel, metadados, preservação legada."""
import configparser
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class CombinationWiring(unittest.TestCase):
    def test_panel_and_menu(self):
        panel=(ROOT/'home_dialog.py').read_text(encoding='utf-8')
        plugin=(ROOT/'plugin.py').read_text(encoding='utf-8')
        self.assertIn('Combinação de Mapas',panel)
        self.assertIn('self.plugin.open_combination',panel)
        self.assertIn("self._add_menu_action('Combinação de Mapas', self.open_combination)",plugin)
        self.assertIn('def open_combination(self, checked=False):',plugin)
        self.assertIn('self.combination_dialog.deleteLater()',plugin)
        self.assertIn('def closeEvent(self,event):',(ROOT/'combination_dialog.py').read_text())

    def test_metadata(self):
        cfg=configparser.ConfigParser(interpolation=None)
        cfg.read(ROOT/'metadata.txt',encoding='utf-8')
        self.assertEqual(cfg['general']['version'],'1.0.0')
        self.assertEqual(cfg['general']['qgisMinimumVersion'],'4.0')

    def test_old_modules_not_modified_in_core(self):
        from zipfile import ZipFile
        zip_path=Path('/mnt/data/Vista_Saga_Plugin_QGIS4_v0.5.2_PADRONIZACAO.zip')
        if not zip_path.exists():
            self.skipTest('Arquivo-base não está disponível neste sistema.')
        unchanged=['raster_engine.py','evaluation_task.py','monitoring_engine.py',
                   'signature_engine.py','vector_monitoring_engine.py',
                   'vector_overlay_engine.py','rs2_format.py']
        with ZipFile(zip_path) as z:
            for name in unchanged:
                current = (ROOT/name).read_bytes()
                old = z.read('geosaga/'+name)
                if name == 'evaluation_task.py':
                    # A única alteração permitida é o título público da tarefa.
                    current = current.replace(b'Vista Saga \\xe2\\x80\\x94 Avalia\\xc3\\xa7\\xc3\\xa3o\\x27',
                                              b'Vista Saga \\xe2\\x80\\x94 Avalia\\xc3\\xa7\\xc3\\xa3o Espacial\\x27')
                self.assertEqual(current, old, name)

    def test_legend_bridge_from_combined_raster(self):
        import tempfile
        from geosaga.combination_core import write_combination_reports, composition_rows
        from geosaga.tiff_vector import _legend
        class FakeDS:
            def GetMetadataItem(self, key):
                return 'COMBINACAO_MAPAS' if key=='VISTA_SAGA_MODULE' else None
        class FakeBand:
            def GetDataset(self):return FakeDS()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'cross.tif'
            path.write_bytes(b'placeholder')
            rows=composition_rows({('1','3'):4},[{'1':'Tabuleiro'},{'3':'Pastagem'}],pixel_area_m2=100)
            write_combination_reports(str(Path(directory)/'cross_combinacoes.csv'),
                                      str(Path(directory)/'cross_resumo.txt'),
                                      rows,['geologia','uso'],mode='Raster',
                                      crs='EPSG:31985',area_method='Pixel × 100 m²')
            result=_legend(path,FakeBand())
            self.assertEqual(result[1][0],'Tabuleiro | Pastagem')
            self.assertTrue(result[1][1].startswith('#'))
