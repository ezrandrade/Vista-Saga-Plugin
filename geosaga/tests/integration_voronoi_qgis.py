"""Rode no Console Python do QGIS 4.x: from geosaga.tests.integration_voronoi_qgis import run; run()"""
from pathlib import Path
import tempfile


def run():
    from osgeo import gdal, osr
    import numpy as np
    from geosaga.voronoi_core import Generator
    from geosaga.voronoi_engine import run_voronoi

    points=[Generator(1,5,5,1.,'A'), Generator(2,45,5,3.,'B')]
    srs=osr.SpatialReference()
    srs.ImportFromEPSG(3857)
    transform=(0,10,0,10,0,-10)
    with tempfile.TemporaryDirectory(prefix='vistasaga_voronoi_') as directory:
        simple=run_voronoi(points, str(Path(directory)/'simples.tif'),srs.ExportToWkt(),
                           transform,5,1,mode='simple',vectorize=True)
        mass=run_voronoi(points, str(Path(directory)/'massa.tif'),srs.ExportToWkt(),
                         transform,5,1,mode='mass',vectorize=True)
        original=gdal.Open(simple['output'])
        weighted=gdal.Open(mass['output'])
        arr0=original.GetRasterBand(1).ReadAsArray()
        arr1=weighted.GetRasterBand(1).ReadAsArray()
        if list(arr0[0])!=[1,1,1,2,2]:
            raise RuntimeError('Falha no Voronoi simples: '+str(arr0))
        if list(arr1[0])!=[1,1,2,2,2]:
            raise RuntimeError('Falha no Voronoi ponderado pela massa: '+str(arr1))
        if not Path(simple['gpkg']).is_file() or not Path(mass['gpkg']).is_file():
            raise RuntimeError('GeoPackages não foram gravados.')
        if not Path(mass['csv']).is_file() or not Path(mass['txt']).is_file():
            raise RuntimeError('Relatórios não foram gravados.')
        original=weighted=None
    print('Voronoi 0.7.0: simples, massa, GDAL, GeoPackage e relatórios: OK.')
    return True
