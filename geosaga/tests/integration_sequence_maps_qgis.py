"""Teste funcional GUI/renderização na instalação real do QGIS 4.x.

Execute no Console Python do QGIS:
    from geosaga.tests.integration_sequence_maps_qgis import run
    run()

Usa somente camadas sintéticas em memória e um raster em pasta temporária;
não adiciona camadas ao projeto do usuário.
"""
from pathlib import Path
import tempfile


def run():
    from osgeo import gdal, osr
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import (QgsFeature, QgsField, QgsGeometry, QgsProject,
                           QgsRasterLayer, QgsRectangle, QgsVectorLayer)
    from geosaga.image_sequence_dialog import ImageSequenceDialog
    from geosaga.sequence_plan import temporal_frames
    from geosaga.gif_codec import encode_gif

    initial_ids = set(QgsProject.instance().mapLayers())
    folder = Path(tempfile.mkdtemp(prefix='vista_saga_map_sequence_'))
    raster_path = folder / 'fundo_2000.tif'
    dataset = gdal.GetDriverByName('GTiff').Create(str(raster_path), 120, 90, 1, gdal.GDT_Byte)
    dataset.SetGeoTransform((500000.0, 10.0, 0.0, 9000000.0, 0.0, -10.0))
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(31985)
    dataset.SetProjection(spatial_ref.ExportToWkt())
    dataset.GetRasterBand(1).Fill(7)
    dataset = None
    raster = QgsRasterLayer(str(raster_path), 'raster_2000', 'gdal')
    vector = QgsVectorLayer('Polygon?crs=EPSG:31985', 'areas_temporais', 'memory')
    vector.dataProvider().addAttributes([QgsField('ano', QVariant.Int)])
    vector.updateFields()
    feats = []
    for i, year in enumerate((1985, 2000, 2024)):
        feature = QgsFeature(vector.fields())
        feature['ano'] = year
        x = 500050.0 + 180.0*i
        feature.setGeometry(QgsGeometry.fromRect(QgsRectangle(x, 8999400.0, x+130, 8999570.0)))
        feats.append(feature)
    vector.dataProvider().addFeatures(feats)
    vector.updateExtents()
    if not raster.isValid() or not vector.isValid():
        raise AssertionError('Falha ao construir camada sintética.')

    panel = ImageSequenceDialog(None)
    try:
        project_crs = raster.crs()
        panel._add(raster)
        panel._add(raster)
        extent_raster = panel._shared_extent(project_crs)
        raster_frame = panel._render(panel.entries[0], project_crs, extent_raster, 240, 150)
        if len(raster_frame) != 240*150*3:
            raise AssertionError('Raster: bytes RGB inesperados.')

        panel.tabs.setCurrentIndex(1)
        panel._add_vector(vector)
        panel._add_vector(vector)
        vector_extent = panel._shared_extent(project_crs)
        vector_frame = panel._render(panel.entries[0], project_crs, vector_extent, 240, 150)
        if len(vector_frame) != 240*150*3:
            raise AssertionError('Vetor: bytes RGB inesperados.')

        panel.tabs.setCurrentIndex(2)
        panel._add_entry([vector, raster], '2000')
        panel._add_entry([vector, raster], '2024')
        mixed_extent = panel._shared_extent(project_crs)
        mixed_frame = panel._render(panel.entries[0], project_crs, mixed_extent, 240, 150)
        if len(mixed_frame) != 240*150*3:
            raise AssertionError('Misto: bytes RGB inesperados.')

        frames = temporal_frames(vector, 'ano', [1985, 2000, 2024], True,
                                 base_layers=[raster])
        panel.entries[:] = frames
        filtered = panel._temporal_layer(frames[0])
        if filtered.featureCount() != 1 or vector.featureCount() != 3:
            raise AssertionError('Filtro temporal alterou a camada ou selecionou feições erradas.')
        if panel._temporal_layer(frames[-1]).featureCount() != 3:
            raise AssertionError('Acumulação temporal inválida.')
        extent = panel._shared_extent(project_crs)
        rgb = [panel._render(e, project_crs, extent, 240, 150) for e in frames]
        gif = encode_gif(folder/'misto.gif', rgb, 240, 150, delay_cs=50)
        if not Path(gif['path']).read_bytes().startswith(b'GIF89a') or gif['frames'] != 3:
            raise AssertionError('GIF misto inválido.')
    finally:
        panel.close()
    if set(QgsProject.instance().mapLayers()) != initial_ids:
        raise AssertionError('O teste modificou as camadas do projeto.')
    print('Vista Saga 0.8.7: integração Raster/Vetorial/Misto e filtro temporal concluída:',
          str(folder/'misto.gif'))
    return {'path': str(folder/'misto.gif'), 'frames': 3}
