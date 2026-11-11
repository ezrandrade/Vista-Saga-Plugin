"""Homologação real da operação Vetor → RS2; executar no Console Python do QGIS 4.x:

    from geosaga.tests.integration_vector_rs2_qgis import run
    run()

Usa apenas dados sintéticos em pasta temporária. Verifica:
1. o núcleo GDAL/OGR do QGIS (células, legenda, cores e grade do RS2 gravado);
2. a interface Qt6: sexta operação, campos visíveis e caminho de saída sugerido.
A abertura do RS2 no Vista SAGA original continua sendo um teste manual separado.
"""
from pathlib import Path
import tempfile

import numpy as np


def _vector(path):
    from osgeo import ogr, osr
    ds = ogr.GetDriverByName('GPKG').CreateDataSource(str(path))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(31985)
    layer = ds.CreateLayer('temas', srs=srs, geom_type=ogr.wkbPolygon)
    for name, kind in (('CODIGO', ogr.OFTInteger), ('CLASSE', ogr.OFTString),
                       ('COR_HEX', ogr.OFTString)):
        layer.CreateField(ogr.FieldDefn(name, kind))
    for code, name, color, (x0, y0, x1, y1) in (
        (1, 'Caatinga', '#008000', (812300, 8901200, 812500, 8901400)),
        (2, 'Pastagem', '#FFFF00', (812500, 8901200, 812700, 8901300)),
    ):
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)):
            ring.AddPoint_2D(x, y)
        polygon = ogr.Geometry(ogr.wkbPolygon)
        polygon.AddGeometry(ring)
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField('CODIGO', code)
        feature.SetField('CLASSE', name)
        feature.SetField('COR_HEX', color)
        feature.SetGeometry(polygon)
        if layer.CreateFeature(feature) != 0:
            raise RuntimeError('Erro ao construir o vetor de teste.')
    ds = None
    return path


def _check_core(root):
    from geosaga.rs2_format import RS2Reader
    from geosaga.vector_rs2 import convert_vector_to_rs2
    gpkg = _vector(root / 'uso.gpkg')
    output = root / 'uso.rs2'
    result = convert_vector_to_rs2(str(gpkg) + '|layername=temas', output, 'CODIGO', 10)
    reader = RS2Reader(output)
    h = reader.header
    if (h.width, h.height, h.xmin, h.ymin, h.xmax, h.ymax) != (
            40, 20, 812300, 8901200, 812700, 8901400):
        raise RuntimeError(f'Grade RS2 incorreta: {h}')
    cells = np.vstack(list(reader.rows()))
    counts = {int(k): int(v) for k, v in zip(*np.unique(cells, return_counts=True))}
    if counts != {0: 200, 1: 400, 2: 200}:
        raise RuntimeError(f'Contagem de células incorreta: {counts}')
    if h.labels != ['FUNDO', 'Caatinga', 'Pastagem']:
        raise RuntimeError(f'Legenda incorreta: {h.labels}')
    if h.colors[1][:3] != (0, 128, 0) or h.colors[2][:3] != (255, 255, 0):
        raise RuntimeError('Cores COR_HEX não foram gravadas na paleta RS2.')
    if not Path(str(output) + '.rs2.json').is_file():
        raise RuntimeError('Arquivo lateral .rs2.json ausente.')
    if result.summary['overlap_cells'] != 0:
        raise RuntimeError('Sobreposição inexistente foi relatada.')
    return gpkg


def _check_ui(gpkg):
    from qgis.utils import iface
    from geosaga.rs2_dialog import RS2ConverterDialog
    widget = RS2ConverterDialog(iface, iface.mainWindow())
    try:
        if widget.mode.count() != 6:
            raise RuntimeError(f'Esperadas 6 operações, encontradas {widget.mode.count()}.')
        widget.mode.setCurrentIndex(5)
        widget._set_source(str(gpkg) + '|layername=temas')
        if widget.mode.currentIndex() != 5:
            raise RuntimeError('A seleção de um vetor desviou a operação Vetor → RS2.')
        if not widget.destination.text().endswith('_vetor.rs2'):
            raise RuntimeError('Saída sugerida não é .rs2: ' + widget.destination.text())
        if widget.vector_field.currentText() != 'CODIGO':
            raise RuntimeError('O campo CODIGO não foi selecionado automaticamente.')
        if widget.temporary_check.isEnabled() or widget.temporary_check.isChecked():
            raise RuntimeError('RS2 não deve ser oferecido como resultado temporário.')
        if widget.batch.isEnabled():
            raise RuntimeError('O lote não está disponível para Vetor → RS2.')
        for name in ('vector_field', 'pixel_size', 'rs2_code_mode', 'reference_row'):
            if getattr(widget, name).isHidden():
                raise RuntimeError(f'Controle oculto indevidamente: {name}.')
        if not widget.crs_widget.isHidden():
            raise RuntimeError('Vetor → RS2 não deve oferecer atribuição de SRC.')
        widget.mode.setCurrentIndex(4)
        if not widget.rs2_code_mode.isHidden():
            raise RuntimeError('Modo de códigos RS2 visível em Vetor → GeoTIFF.')
    finally:
        widget.close()
        widget.deleteLater()


def run():
    with tempfile.TemporaryDirectory(prefix='vistasaga_vetor_rs2_') as td:
        gpkg = _check_core(Path(td))
        _check_ui(gpkg)
    print('Vista Saga — Vetor → RS2: núcleo GDAL e interface Qt6 aprovados.')
    return True
