"""Teste manual no Console Python do QGIS 4.x:

    from geosaga.tests.integration_voronoi_stack_qgis import run
    run()

Arquivos sintéticos; não modifica projetos ou fontes do usuário.
"""
import tempfile
from pathlib import Path

import numpy as np


def run():
    from osgeo import gdal, osr
    from geosaga.voronoi_core import Generator
    from geosaga.voronoi_engine import run_voronoi

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(31985)
    wkt = srs.ExportToWkt()
    gt = (200000., 10., 0., 9000000., 0., -10.)
    points = [Generator(1, 200015., 8999985., 2., 'A'),
              Generator(2, 200135., 8999895., 7., 'B')]
    with tempfile.TemporaryDirectory(prefix='vistasagaplugin_voronoi_') as folder:
        root = Path(folder)
        nrows, ncols = 12, 16
        a = np.ones((nrows,ncols),dtype=np.float32)
        b = np.full((nrows,ncols),2,dtype=np.float32)
        b[:,5:8] = 10
        sources=[]
        for i, grid in enumerate((a,b), 1):
            filename = root / f'atrito_{i}.tif'
            ds=gdal.GetDriverByName('GTiff').Create(str(filename),ncols,nrows,1,gdal.GDT_Float32)
            ds.SetProjection(wkt)
            ds.SetGeoTransform(gt)
            ds.GetRasterBand(1).WriteArray(grid)
            ds=None
            sources.append(str(filename))
        result = run_voronoi(points,str(root/'voronoi.tif'),wkt,gt,ncols,nrows,
                             mode='mass_friction',friction_components=[
                               {'path':sources[0], 'weight':2, 'notes':''},
                               {'path':sources[1], 'weight':3, 'notes':'2=2;10=8'}])
        ds=gdal.Open(result['output'])
        assert ds is not None, 'GeoTIFF não criado.'
        data=ds.GetRasterBand(1).ReadAsArray()
        assert data.shape == (12,16) and np.any(data==1) and np.any(data==2)
        assert ds.GetMetadataItem('VISTASAGA_FRICTION_STACK_LAYERS') == '2'
        ds=None
        report=Path(result['txt']).read_text(encoding='utf-8')
        assert 'Pares descartados:' in report
        assert 'Superfícies de atrito integradas' in report
    print('OK: Análises Voronoi com atrito integrado, GeoTIFF, notas, pesos e relatório.')
    return True
