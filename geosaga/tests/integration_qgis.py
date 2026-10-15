"""Teste geoespacial com raster sintético — executar dentro do QGIS 4.x.

    from geosaga.tests.integration_qgis import run
    run()

Não requer downloads nem altera o projeto QGIS atual.
Os arquivos são criados em uma pasta temporária e removidos após o teste.
"""
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from osgeo import gdal, osr
from qgis.core import (
    QgsApplication, QgsFeature, QgsGeometry, QgsRasterLayer, QgsVectorLayer,
)

from geosaga.raster_engine import run_evaluation


def _write_raster(path, matrix):
    driver = gdal.GetDriverByName('GTiff')
    ds = driver.Create(str(path), 2, 2, 1, gdal.GDT_Int16)
    if ds is None:
        raise RuntimeError('Falha ao criar raster de teste.')
    ds.SetGeoTransform((0, 10, 0, 0, 0, -10))
    srs = osr.SpatialReference()
    if srs.ImportFromEPSG(3857) != 0:
        raise RuntimeError('Não foi possível definir EPSG:3857.')
    ds.SetProjection(srs.ExportToWkt())
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(-9999)
    band.WriteArray(matrix)
    band.FlushCache()
    ds = None


def _csv_rows(path):
    with open(path, encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle, delimiter=';'))


def run():
    import processing

    ids = ('geosaga:avaliacao', 'geosaga:monitoria', 'geosaga:assinatura')
    for algorithm_id in ids:
        if QgsApplication.processingRegistry().algorithmById(algorithm_id) is None:
            raise RuntimeError(f'Ative o plugin antes de testar: {algorithm_id}')

    with TemporaryDirectory(prefix='vistasaga_test_') as tmp:
        root = Path(tmp)
        a = root / 'antes.tif'
        b = root / 'depois.tif'
        _write_raster(a, np.array([[1, 1], [2, 2]], dtype=np.int16))
        _write_raster(b, np.array([[1, 2], [2, 1]], dtype=np.int16))

        # Exercita a Avaliação com o motor empregado pela interface visual.
        config = {'escala': 10, 'camadas': [
            {'peso': 60, 'notas': {'1': 10, '2': 0}, 'bloqueadas': []},
            {'peso': 40, 'notas': {'1': 8, '2': 4}, 'bloqueadas': []},
        ]}
        result = root / 'avaliacao.tif'
        info = run_evaluation([str(a), str(b)], config, str(result))
        output = gdal.Open(str(result))
        if output is None:
            raise RuntimeError('Avaliação não gerou raster de saída.')
        actual = output.GetRasterBand(1).ReadAsArray()
        output = None
        np.testing.assert_allclose(actual, [[9.2, 7.6], [1.6, 3.2]], atol=1e-5)
        if info['pixels_validos'] != 4:
            raise RuntimeError('Contagem de pixels válidos divergente na Avaliação.')
        print('OK — Avaliação Ambiental: média ponderada dos quatro pixels.')

        layer_a = QgsRasterLayer(str(a), 'anterior')
        layer_b = QgsRasterLayer(str(b), 'posterior')
        if not layer_a.isValid() or not layer_b.isValid():
            raise RuntimeError('QGIS não conseguiu ler os rasters sintéticos.')
        transition_csv = root / 'monitoria.csv'
        processing.run('geosaga:monitoria', {
            'ANTES': layer_a, 'DEPOIS': layer_b,
            'OUTPUT': str(root / 'monitoria.tif'), 'TABELA': str(transition_csv),
        })
        transitions = _csv_rows(transition_csv)
        if len(transitions) != 4 or sum(int(row['pixels']) for row in transitions) != 4:
            raise RuntimeError('Matriz de transições divergente.')
        print('OK — Monitoria Ambiental: quatro transições, quatro pixels.')

        region = QgsVectorLayer('Polygon?crs=EPSG:3857', 'área sintética', 'memory')
        if not region.isValid():
            raise RuntimeError('Camada de polígonos de teste inválida.')
        feat = QgsFeature(region.fields())
        feat.setGeometry(QgsGeometry.fromWkt(
            'POLYGON ((0 0, 20 0, 20 -20, 0 -20, 0 0))'))
        ok, _ = region.dataProvider().addFeatures([feat])
        if not ok:
            raise RuntimeError('Não foi possível adicionar polígono sintético.')
        region.updateExtents()
        signature_csv = root / 'assinatura.csv'
        processing.run('geosaga:assinatura', {
            'RASTER': layer_a, 'POLIGONOS': region, 'TABELA': str(signature_csv),
        })
        signature = _csv_rows(signature_csv)
        if len(signature) != 2 or sum(int(row['pixels']) for row in signature) != 4:
            raise RuntimeError('Assinatura: contagens incorretas.')
        print('OK — Assinatura Ambiental: duas classes, quatro pixels.')

    print('TESTE INTEGRADO CONCLUÍDO. Execute novamente no Windows e Linux/Flatpak.')
    return True
