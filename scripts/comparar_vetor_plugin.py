"""Compara o Voronoi vetorial do plugin com o raster do Vista SAGA no caso de teste do atrito.

Uso: python3.12 scripts/comparar_vetor_plugin.py PASTA_VISTA_SAGA PASTA_PLUGIN

PASTA_VISTA_SAGA: voronoi_saga_simples.rs2 e voronoi_saga_massa.rs2.
PASTA_PLUGIN: Voronoi_Plugin_Simples.gpkg e Voronoi_Plugin_Massa.gpkg (campo CENTRO_ID).
Os vetores são rasterizados pelo centro das células da grade do caso (80 × 60, 10 m).
Requer GDAL (osgeo). Os arquivos de dados não vão para o repositório.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from geosaga.gdal_scope import with_gdal_exceptions  # noqa: E402
from geosaga.rs2_format import RS2Reader  # noqa: E402

W, H, CEL, XMIN, YMIN = 80, 60, 10, 500000, 8900000
MASSAS = np.array([9, 4, 1], dtype=float)[:, None, None]
POS_VISTA_SAGA = [(11, 14), (59, 49), (71, 9)]   # onde o Vista SAGA pôs os polos (a partir de 0)
POS_UTM_TXT = [(12, 15), (60, 50), (72, 10)]     # centros do pontos_utm.txt (deslocados 1 célula)


@with_gdal_exceptions
def rasterizar(gpkg):
    from osgeo import gdal
    ds = gdal.Rasterize('/vsimem/voronoi.tif', gpkg, attribute='CENTRO_ID', outputType=gdal.GDT_Int16,
                        outputBounds=(XMIN, YMIN, XMIN + W * CEL, YMIN + H * CEL),
                        xRes=CEL, yRes=CEL, initValues=0)
    a = ds.ReadAsArray()
    ds = None
    gdal.Unlink('/vsimem/voronoi.tif')
    return a


def modelo(pos, expoente):
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.stack([np.hypot(xx - c, yy - l) for c, l in pos])
    return (d / MASSAS ** expoente).argmin(0) + 1


def acerto(a, b, mascara):
    return f'{100 * (a[mascara] == b[mascara]).mean():6.2f}% ({int((a[mascara] != b[mascara]).sum())} células)'


def main(pasta_vs, pasta_plugin):
    tudo = np.ones((H, W), bool)
    for nome, exp_plugin in (('simples', 0), ('massa', 1)):
        vs = np.array(list(RS2Reader(os.path.join(pasta_vs, f'voronoi_saga_{nome}.rs2')).rows()))
        pl = rasterizar(os.path.join(pasta_plugin, f'Voronoi_Plugin_{nome.capitalize()}.gpkg'))
        print(f'\n{nome}')
        print('  plugin × Vista SAGA (bruto)               ', acerto(pl, vs, vs != 0))
        print('  plugin × modelo do plugin, pontos usados  ', acerto(pl, modelo(POS_UTM_TXT, exp_plugin), tudo))
        print('  plugin × modelo Vista SAGA, pontos usados ', acerto(pl, modelo(POS_UTM_TXT, exp_plugin / 2), tudo))
        print('  Vista SAGA × modelo do plugin, pontos VS  ', acerto(modelo(POS_VISTA_SAGA, exp_plugin), vs, vs != 0))
        for i, polo in enumerate('ABC', 1):
            print(f'    Polo {polo}: Vista SAGA {int((vs == i).sum()):5d} células; plugin {int((pl == i).sum()):5d}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
