"""Testes integrados de vetorização real com GDAL/OGR, rodar no Console Python do QGIS.

    from geosaga.tests.integration_rs2_vector_qgis import run
    run()

Não altera mapas do usuário: usa RS2 sintético e pasta temporária.
"""
from pathlib import Path
import tempfile

import numpy as np


def run():
    from osgeo import ogr
    from qgis.core import QgsVectorLayer
    from geosaga.rs2_format import RS2Header, write_rs2
    from geosaga.rs2_vector import convert_rs2_to_vector

    rows = np.array([[0, 1, 1, 2],
                     [0, 1, 2, 2],
                     [1, 1, 0, 2]], dtype=np.uint16)
    header = RS2Header(4, 3, 100, 200, 140, 230,
                       ['FUNDO', 'Floresta', 'Pastagem'],
                       [(255,255,255,0), (5,128,200,0), (30,200,20,0)])
    with tempfile.TemporaryDirectory(prefix='vista_saga_vetores_') as tmp:
        root = Path(tmp)
        source = root / 'caso.rs2'
        write_rs2(source, header, iter(rows))
        for ext in ('.gpkg', '.shp', '.geojson', '.fgb'):
            target = root / ('caso' + ext)
            produced = convert_rs2_to_vector(source, target, ignore_background=True)
            if not produced.is_file():
                raise RuntimeError(f'Saída não criada: {ext}')
            ds = ogr.Open(str(produced), 0)
            if ds is None:
                raise RuntimeError(f'OGR não abriu {ext}')
            layer = ds.GetLayer(0)
            fields = [field.name for field in layer.schema]
            if not all(key in fields for key in ('CODIGO', 'CLASSE', 'COR_HEX')):
                raise RuntimeError(f'Campos incompletos {ext}: {fields}')
            records = [(int(f.GetField('CODIGO')), f.GetField('CLASSE'),
                        f.GetField('COR_HEX')) for f in layer]
            if sorted(records) != [(1, 'Floresta', '#0580C8'),
                                    (2, 'Pastagem', '#1EC814')]:
                raise RuntimeError(f'Valores inesperados em {ext}: {records}')
            ds = None
            qlayer = QgsVectorLayer(str(target), 'teste', 'ogr')
            if not qlayer.isValid():
                raise RuntimeError(f'QGIS não abriu a camada {ext}')
        with_background = root / 'fundo.gpkg'
        convert_rs2_to_vector(source, with_background, ignore_background=False)
        ds = ogr.Open(str(with_background))
        n = ds.GetLayer(0).GetFeatureCount()
        ds = None
        if n != 4:
            raise RuntimeError(f'Esperados 4 polígonos incluindo fundo, obtidos {n}')
        print('Vista Saga 0.3.5: 4 formatos, atributos, polígonos e opção FUNDO aprovados.')
    return True
