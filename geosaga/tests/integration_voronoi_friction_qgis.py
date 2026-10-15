"""Teste funcional com GDAL dentro do console Python do QGIS 4.x.

Uso:
    from geosaga.tests.integration_voronoi_friction_qgis import run
    run()
Não modifica projeto QGIS ou arquivos do usuário.
"""
import os
import tempfile
import numpy as np
from osgeo import gdal, osr

from geosaga.voronoi_core import Generator
from geosaga.voronoi_engine import run_voronoi


def run():
    srs = osr.SpatialReference()
    if srs.ImportFromEPSG(31985) != 0:
        raise RuntimeError('EPSG:31985 indisponível.')
    wkt = srs.ExportToWkt()
    t = (0.,10.,0.,10.,0.,-10.)
    with tempfile.TemporaryDirectory(prefix='vistasaga_friction_test_') as temp:
        source=os.path.join(temp,'atrito.tif')
        ds=gdal.GetDriverByName('GTiff').Create(source,5,1,1,gdal.GDT_Float32)
        ds.SetGeoTransform(t); ds.SetProjection(wkt)
        band=ds.GetRasterBand(1)
        band.WriteArray(np.array([[0.,100.,0.,0.,0.]],dtype=np.float32))
        ds.FlushCache(); band=None; ds=None
        generators=[Generator(1,5.,5.,1.,'A'),Generator(2,45.,5.,1.,'B')]
        target=os.path.join(temp,'voronoi_atrito.tif')
        result=run_voronoi(generators,target,wkt,t,5,1,mode='friction',friction_path=source)
        out=gdal.Open(result['output']); arr=out.ReadAsArray(); out=None
        if arr.tolist() != [[1,1,2,2,2]]:
            raise AssertionError(f'Resultado inesperado: {arr.tolist()}')
        for key in ('output','csv','txt'):
            if not os.path.exists(result[key]):
                raise AssertionError(f'Arquivo ausente: {key}')
        print('Voronoi com Atrito — teste GDAL concluído:',arr.tolist())
        return True
