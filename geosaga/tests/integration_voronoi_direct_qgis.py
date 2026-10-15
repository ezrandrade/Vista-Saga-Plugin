"""Teste manual no Console Python do QGIS 4.x: from geosaga.tests.integration_voronoi_direct_qgis import run; run()."""
import tempfile
from pathlib import Path


def run():
    from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry, QgsPointXY, QgsVectorLayer
    from osgeo import ogr
    from geosaga.voronoi_core import Generator
    from geosaga.voronoi_vector import save_simple_voronoi

    crs=QgsCoordinateReferenceSystem('EPSG:31985')
    if not crs.isValid():
        raise RuntimeError('Não foi possível inicializar EPSG:31985.')
    generators=[Generator(1,0.,5.,label='A'),Generator(2,10.,5.,label='B')]
    with tempfile.TemporaryDirectory(prefix='vista_voronoi_qgis_') as directory:
        dest=str(Path(directory)/'voronoi.gpkg')
        result=save_simple_voronoi(generators,(0,0,10,10),dest,crs.toWkt())
        if result['gpkg']!=dest:
            raise AssertionError('Caminho de saída GPKG incorreto.')
        layer=QgsVectorLayer(dest+'|layername=voronoi_espacial','Teste Voronoi','ogr')
        if not layer.isValid() or layer.featureCount()!=2:
            raise AssertionError('GeoPackage direto inválido ou contagem de feições incorreta.')
        areas=sorted([feat['AREA_M2'] for feat in layer.getFeatures()])
        if any(abs(area-50.)>1e-6 for area in areas):
            raise AssertionError(f'Área inesperada: {areas}')
        if not Path(result['csv']).exists() or not Path(result['txt']).exists():
            raise AssertionError('Relatórios ausentes.')
        # Caso de corte ao polígono de estudo, 10x5 unidades.
        clip=QgsGeometry.fromPolygonXY([[QgsPointXY(0,0),QgsPointXY(10,0),
                                        QgsPointXY(10,5),QgsPointXY(0,5),QgsPointXY(0,0)]])
        clipped=save_simple_voronoi(generators,(0,0,10,10),dest,crs.toWkt(),study_geometry=clip)
        cut=QgsVectorLayer(dest+'|layername=voronoi_espacial','Teste Voronoi recortado','ogr')
        if not cut.isValid():
            raise AssertionError('GeoPackage recortado inválido.')
        total=sum(feat['AREA_M2'] for feat in cut.getFeatures())
        if abs(total-50.)>1e-6:
            raise AssertionError(f'Área recortada incorreta: {total}')
    print('Voronoi vetorial direto: duas feições, áreas, relatórios e recorte aprovados.')
    return True
