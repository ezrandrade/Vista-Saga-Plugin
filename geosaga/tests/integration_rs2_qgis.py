"""Teste real GDAL/QGIS da exportação de RGB para RS2 e ida/volta categórica.

Executar no console Python do QGIS, após habilitar o Vista Saga Plugin:

    from geosaga.tests.integration_rs2_qgis import run
    run()

Utiliza somente diretório temporário; não altera o projeto.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from osgeo import gdal

from geosaga.rs2_format import RS2Header, RS2Reader, write_rs2
from geosaga.rs2_converter import convert_tif_to_rs2, convert_rs2_to_tif


def run():
    h = RS2Header(
        4, 3, 178260, 8900320, 178300, 8900350,
        ['FUNDO', 'VÁRZEA', 'FLORESTA', 'TERRAÇO'],
        [(255, 255, 255, 0), (1, 2, 3, 0),
         (22, 33, 44, 0), (200, 210, 220, 0)],
    )
    codes = np.array([
        [0, 1, 2, 3],
        [3, 2, 1, 0],
        [1, 1, 2, 0],
    ], dtype=np.uint8)

    with TemporaryDirectory(prefix='vistasaga_rgb_') as tmp:
        root = Path(tmp)
        source = root / 'referencia.rs2'
        rgb = root / 'sem_georreferenciamento_rgb.tif'
        reverse = root / 'reconstruido.rs2'
        categorical = root / 'categorico.tif'
        normal_reverse = root / 'reconstruido_por_codigos.rs2'
        write_rs2(source, h, iter(codes))
        ds = gdal.GetDriverByName('GTiff').Create(
            str(rgb), h.width, h.height, 3, gdal.GDT_Byte,
            options=['INTERLEAVE=PIXEL'])
        if ds is None:
            raise RuntimeError('GDAL não criou GeoTIFF de ensaio.')
        for channel in range(3):
            palette = np.array([color[channel] for color in h.colors], dtype=np.uint8)
            ds.GetRasterBand(channel + 1).WriteArray(palette[codes])
        ds = None

        convert_tif_to_rs2(rgb, reverse, reference_rs2=source)
        if source.read_bytes() != reverse.read_bytes():
            raise RuntimeError('Conversão RGB → RS2 não preservou todos os bytes.')

        convert_rs2_to_tif(source, categorical)
        ds = gdal.Open(str(categorical), gdal.GA_ReadOnly)
        if ds is None or ds.RasterCount != 1:
            raise RuntimeError('RS2 → GeoTIFF não produziu uma banda categórica.')
        observed = ds.GetRasterBand(1).ReadAsArray()
        ds = None
        np.testing.assert_array_equal(observed, codes)
        convert_tif_to_rs2(categorical, normal_reverse)
        if source.read_bytes() != normal_reverse.read_bytes():
            raise RuntimeError('Conversão categórica GeoTIFF → RS2 divergiu.')

    print('OK: GeoTIFF RGB sem georreferenciamento → RS2 preservado byte a byte.')
    print('OK: RS2 → GeoTIFF categórico → RS2 preservado byte a byte.')
    return True
