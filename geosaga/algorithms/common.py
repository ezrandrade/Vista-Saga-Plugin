"""Funções de leitura/validação GDAL e exportação."""
import csv
import os
import numpy as np
from osgeo import gdal, osr
from qgis.core import QgsProcessingException

from ..core import pixel_area_ha

BLOCK = 256


def dataset_for_layer(layer):
    # gdal.Open aceita arquivos locais e caminhos reconhecidos pelo GDAL.
    # Fontes exclusivamente virtuais/de rede devem ser exportadas antes.
    source = layer.source().split('|', 1)[0]
    ds = gdal.Open(source, gdal.GA_ReadOnly)
    if ds is None:
        raise QgsProcessingException(
            f'Não foi possível abrir o raster "{layer.name()}" via GDAL. '
            'Exporte a camada para GeoTIFF e tente novamente.'
        )
    if ds.RasterCount < 1:
        raise QgsProcessingException('Raster sem bandas.')
    return ds


def assert_same_grid(datasets):
    base = datasets[0]
    for other in datasets[1:]:
        if base.RasterXSize != other.RasterXSize or base.RasterYSize != other.RasterYSize:
            raise QgsProcessingException('Dimensões diferentes. Alinhe as grades antes do processamento.')
        if not np.allclose(base.GetGeoTransform(), other.GetGeoTransform(), atol=1e-8, rtol=0):
            raise QgsProcessingException('Resolução, extensão ou grade diferentes. Alinhe os rasters.')
        if base.GetProjection() != other.GetProjection():
            # Podem ser matematicamente iguais mas serializados de modo distinto.
            sr1, sr2 = osr.SpatialReference(), osr.SpatialReference()
            if sr1.ImportFromWkt(base.GetProjection()) != 0 or sr2.ImportFromWkt(other.GetProjection()) != 0 or not sr1.IsSame(sr2):
                raise QgsProcessingException('Sistemas de referência diferentes. Reprojete os rasters.')


def window_iterator(dataset):
    for y in range(0, dataset.RasterYSize, BLOCK):
        h = min(BLOCK, dataset.RasterYSize - y)
        for x in range(0, dataset.RasterXSize, BLOCK):
            w = min(BLOCK, dataset.RasterXSize - x)
            yield x, y, w, h


def create_output(path, reference, dtype, nodata):
    if not path.lower().endswith(('.tif', '.tiff')):
        raise QgsProcessingException('Saída raster deve ser um arquivo GeoTIFF (.tif).')
    driver = gdal.GetDriverByName('GTiff')
    options = ['TILED=YES', 'COMPRESS=DEFLATE', 'BIGTIFF=IF_SAFER']
    if dtype == gdal.GDT_Float32:
        options += ['PREDICTOR=3']
    else:
        options += ['PREDICTOR=2']
    dst = driver.Create(path, reference.RasterXSize, reference.RasterYSize, 1, dtype, options=options)
    if dst is None:
        raise QgsProcessingException(f'Não foi possível criar o arquivo {path}')
    dst.SetGeoTransform(reference.GetGeoTransform())
    dst.SetProjection(reference.GetProjection())
    band = dst.GetRasterBand(1)
    band.SetNoDataValue(nodata)
    return dst


def assert_output_not_input(output_path, layers):
    destination = os.path.realpath(output_path)
    for layer in layers:
        source = layer.source().split('|', 1)[0]
        if os.path.realpath(source) == destination:
            raise QgsProcessingException('A saída não pode sobrescrever um raster de entrada.')


def area_ha(dataset):
    srs = osr.SpatialReference()
    if not dataset.GetProjection() or srs.ImportFromWkt(dataset.GetProjection()) != 0:
        return None
    projected = bool(srs.IsProjected())
    return pixel_area_ha(dataset.GetGeoTransform(), projected, srs.GetLinearUnits() if projected else 1)


def write_csv(path, header, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as fh:
        writer = csv.writer(fh, delimiter=';')
        writer.writerow(header)
        writer.writerows(rows)


def fmt_code(value):
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)
