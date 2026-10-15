"""Teste manual do sequenciador no Console Python do QGIS 4.x.

from geosaga.tests.integration_image_sequence_qgis import run
run()
"""
from pathlib import Path
import tempfile


def run():
    from osgeo import gdal, osr
    from qgis.core import QgsProject, QgsRasterLayer
    from geosaga.image_sequence_dialog import ImageSequenceDialog
    from geosaga.gif_codec import encode_gif

    folder = Path(tempfile.mkdtemp(prefix='vistasaga_gif_integration_'))
    raster_paths = []
    for year, value in ((2000, 1), (2020, 2)):
        raster_path = folder / f'uso_{year}.tif'
        ds = gdal.GetDriverByName('GTiff').Create(str(raster_path), 12, 8, 1, gdal.GDT_Byte)
        ds.SetGeoTransform((500000., 10., 0., 9000000., 0., -10.))
        sr = osr.SpatialReference()
        sr.ImportFromEPSG(31985)
        ds.SetProjection(sr.ExportToWkt())
        ds.GetRasterBand(1).Fill(value)
        ds = None
        raster_paths.append(raster_path)
    layers = [QgsRasterLayer(str(path), path.stem, 'gdal') for path in raster_paths]
    if any(not layer.isValid() for layer in layers):
        raise AssertionError('Falha ao carregar rasters sintéticos.')
    panel = ImageSequenceDialog(None)
    for layer in layers:
        panel._add(layer)
    crs = layers[0].crs()
    extent = panel._shared_extent(crs)
    frames = [panel._render(entry, crs, extent, 120, 80) for entry in panel.entries]
    result = encode_gif(folder/'sequencia_teste.gif', frames, 120, 80, delay_cs=50)
    if result['frames'] != 2 or not Path(result['path']).read_bytes().startswith(b'GIF89a'):
        raise AssertionError('Falha na geração do GIF de teste.')
    panel.close()
    print('Vista Saga GIF: teste integrado concluído:', result['path'])
    return result
