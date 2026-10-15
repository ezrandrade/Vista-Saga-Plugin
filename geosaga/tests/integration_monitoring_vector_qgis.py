"""Teste de integração executável no Console Python de QGIS 4.x.

Uso: from geosaga.tests.integration_monitoring_vector_qgis import run; run()
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from geosaga.monitoring_engine import run_monitoring
from geosaga.tiff_vector import convert_tif_to_vector


def run():
    from osgeo import gdal, ogr, osr
    with TemporaryDirectory(prefix='vistasaga_042_') as tmp:
        folder = Path(tmp)
        a, b = folder/'1986.tif', folder/'2016.tif'
        result, vector = folder/'mudancas.tif', folder/'mudancas.gpkg'
        srs = osr.SpatialReference()
        if srs.ImportFromEPSG(31985) != 0:
            raise RuntimeError('Não foi possível criar o SRC EPSG:31985.')
        values = [np.array([[1, 1, 2], [2, 2, 1]], dtype='uint8'),
                  np.array([[1, 2, 2], [1, 2, 2]], dtype='uint8')]
        for path, data in zip((a,b),values):
            ds = gdal.GetDriverByName('GTiff').Create(str(path),3,2,1,gdal.GDT_Byte)
            if ds is None:
                raise RuntimeError('Falha na criação do raster sintético.')
            ds.SetGeoTransform((500000,10,0,9000000,0,-10))
            ds.SetProjection(srs.ExportToWkt())
            band=ds.GetRasterBand(1)
            band.SetNoDataValue(0)
            band.WriteArray(data)
            band.FlushCache()
            ds=None
        summary=run_monitoring(a,b,result,before_label='1986',after_label='2016')
        assert summary['validos']==6
        convert_tif_to_vector(result,vector)
        ds=ogr.Open(str(vector),0)
        if ds is None:
            raise RuntimeError('Não foi possível abrir o vetor exportado.')
        layer=ds.GetLayer(0)
        names=set(field.name for field in layer.schema)
        expected={'CODIGO','CLASSE','SITUACAO','DEIXOU_SER','TORNOU_SE',
                  'COD_INI','COD_FIM','ID_TRANS','AREA_M2','AREA_HA','PCT_AREA'}
        if not expected.issubset(names):
            raise AssertionError(f'Faltam campos: {sorted(expected-names)}')
        rows=list(layer)
        area_sum=sum(float(feat.GetField('AREA_M2')) for feat in rows)
        pct_sum=sum(float(feat.GetField('PCT_AREA')) for feat in rows)
        if abs(area_sum-600.0)>1e-5 or abs(pct_sum-100.)>1e-4:
            raise AssertionError(f'Áreas inválidas: {area_sum} m²; {pct_sum}%.')
        if not any(str(f.GetField('CLASSE')).startswith('Permaneceu') for f in rows):
            raise AssertionError('Falta legenda das permanências.')
        if not any(str(f.GetField('CLASSE')).startswith('Deixou de ser') for f in rows):
            raise AssertionError('Falta legenda das mudanças.')
        ds=None
        return {'status':'OK','poligonos':len(rows),'area_m2':area_sum,
                'pct_area':pct_sum,'transicoes':len(summary['linhas'])}
