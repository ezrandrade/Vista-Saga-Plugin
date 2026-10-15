"""Integração com GeoTIFF reais e adaptador GDAL para validar a série."""
import csv
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import rasterio
from rasterio.transform import from_origin

from geosaga.monitoring_engine import run_monitoring
from geosaga.tests.test_monitoring_rasterio_integration import adapter


class TrendIntegration(unittest.TestCase):
    def make(self, path, data):
        with rasterio.open(path, 'w', driver='GTiff', width=10, height=10,
                           count=1, dtype='uint8', transform=from_origin(500000, 9000000, 10, 10),
                           crs='EPSG:31985', nodata=0) as dst:
            dst.write(data, 1)

    def test_two_dates_not_tested(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            paths=[d/'a.tif',d/'b.tif']
            self.make(paths[0], np.ones((10,10),dtype='uint8'))
            self.make(paths[1], np.full((10,10),2,dtype='uint8'))
            with patch.dict(sys.modules, adapter()):
                out=run_monitoring(paths[0],paths[1],d/'result.tif',
                                   before_label='1986',after_label='2016')
            self.assertEqual(out['temporal']['status'],'nao_aplicavel')
            with open(out['tendencias'], encoding='utf-8-sig', newline='') as f:
                row=list(csv.DictReader(f,delimiter=';'))[0]
            self.assertEqual(row['MK_P_BILATERAL'],'')
            self.assertEqual(out['mudancas'],100)

    def test_five_dates_class_trend(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            years=[1986,1991,1996,2001,2016]
            paths=[]
            for idx, year in enumerate(years,1):
                arr = np.full((10,10),2,dtype='uint8')
                arr.ravel()[:idx*10]=1
                p=d/f'class_{year}.tif'
                self.make(p,arr)
                paths.append(p)
            with patch.dict(sys.modules, adapter()):
                out=run_monitoring(paths[0],paths[-1],d/'output.tif',
                                   before_label='1986',after_label='2016',
                                   temporal_files=list(zip(years[1:-1],paths[1:-1])))
            self.assertEqual(out['temporal']['status'],'calculado')
            self.assertEqual(out['temporal']['validos'],100)
            self.assertEqual(len(out['temporal']['linhas']),2)
            c1=next(x for x in out['temporal']['linhas'] if x['classe']==1)
            self.assertEqual(c1['pct'],[10,20,30,40,50])
            self.assertAlmostEqual(c1['mk']['p'],2/120)
            with open(out['tendencias'], encoding='utf-8-sig', newline='') as f:
                rows=list(csv.DictReader(f,delimiter=';'))
            self.assertEqual(rows[0]['N_DATAS'],'5')
            self.assertIn('CUIDADO',Path(out['resumo']).read_text('utf8'))

    def test_invalid_third_grid_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            years=[1986,1991,1996,2001,2016]
            paths=[]
            for year in years:
                p=d/f'{year}.tif'
                self.make(p,np.ones((10,10),dtype='uint8'))
                paths.append(p)
            # Altera uma transformação espacial, mantendo mesma matriz
            with rasterio.open(paths[2], 'r+') as dst:
                dst.transform = from_origin(500100,9000000,10,10)
            with patch.dict(sys.modules,adapter()):
                with self.assertRaisesRegex(ValueError,'Alinhe'):
                    run_monitoring(paths[0],paths[-1],d/'output.tif',
                                   before_label='1986',after_label='2016',
                                   temporal_files=list(zip(years[1:-1],paths[1:-1])))
            self.assertFalse((d/'output.tif').exists())

if __name__=='__main__':
    unittest.main()
