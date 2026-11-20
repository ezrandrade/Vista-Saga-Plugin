"""Dados do tutorial: a cidade fictícia de Vila Serena (todos os dados são sintéticos).

Uso:  python3.12 docs/tutorial/gerar_dados.py <pasta_de_saida> [pt|en|es]

Gera, numa grade de 200 x 200 células de 10 m (2 km x 2 km, SIRGAS 2000 / UTM 25S, EPSG:31985):
  uso_solo_2000.tif, uso_solo_2010.tif, uso_solo_2020.tif  (1 Área urbana, 2 Vegetação nativa,
                                                            3 Agricultura, 4 Pastagem, 5 Água)
  solos.tif        (1 Argissolo, 2 Latossolo, 3 Neossolo flúvico)
  declividade.tif  (1 Plano 0-3%, 2 Suave ondulado 3-8%, 3 Ondulado 8-20%, 4 Forte ondulado > 20%)
  atrito.tif       (nota de atrito para o Voronoi, Float32: urbana 1, pastagem 2, agricultura 2,
                    vegetação 4, água 10)
  bairros.gpkg     (6 bairros: CODIGO, NOME)
  escolas.gpkg     (6 escolas: NOME, MATRICULAS)
A geração é determinística (semente fixa): quem baixar os dados obtém os mesmos números do tutorial.
"""
import os
import sys

import numpy as np
from osgeo import gdal, ogr, osr

N = 200
CELL = 10.0
X0, Y0 = 200000.0, 8932000.0       # canto superior esquerdo (fictício)
EPSG = 31985

USO = {1: ('Área urbana', (215, 48, 39)), 2: ('Vegetação nativa', (26, 120, 60)),
       3: ('Agricultura', (240, 200, 70)), 4: ('Pastagem', (180, 220, 120)), 5: ('Água', (49, 130, 189))}
SOLOS = {1: ('Argissolo', (205, 133, 63)), 2: ('Latossolo', (178, 34, 34)), 3: ('Neossolo flúvico', (160, 160, 200))}
DECL = {1: ('Plano (0-3%)', (237, 248, 233)), 2: ('Suave ondulado (3-8%)', (186, 228, 179)),
        3: ('Ondulado (8-20%)', (116, 196, 118)), 4: ('Forte ondulado (> 20%)', (35, 139, 69))}
# Nomes das classes e dos bairros em cada idioma (os códigos e os nomes dos arquivos não mudam).
NAMES = {
    'pt': {'uso': ['Área urbana', 'Vegetação nativa', 'Agricultura', 'Pastagem', 'Água'],
           'solos': ['Argissolo', 'Latossolo', 'Neossolo flúvico'],
           'decl': ['Plano (0-3%)', 'Suave ondulado (3-8%)', 'Ondulado (8-20%)', 'Forte ondulado (> 20%)'],
           'bairros': ['Beira-Rio', 'Centro', 'Alto da Serra', 'Porto', 'Jardim Novo', 'Vila Verde']},
    'en': {'uso': ['Urban area', 'Native vegetation', 'Farming', 'Pasture', 'Water'],
           'solos': ['Argisol', 'Latosol', 'Fluvic neosol'],
           'decl': ['Flat (0-3%)', 'Gently rolling (3-8%)', 'Rolling (8-20%)', 'Strongly rolling (> 20%)'],
           'bairros': ['Riverside', 'Downtown', 'Hilltop', 'Harbour', 'New Garden', 'Green Village']},
    'es': {'uso': ['Área urbana', 'Vegetación nativa', 'Agricultura', 'Pastizal', 'Agua'],
           'solos': ['Argisol', 'Latosol', 'Neosol flúvico'],
           'decl': ['Plano (0-3%)', 'Suave ondulado (3-8%)', 'Ondulado (8-20%)', 'Fuerte ondulado (> 20%)'],
           'bairros': ['Ribera', 'Centro', 'Alto de la Sierra', 'Puerto', 'Jardín Nuevo', 'Villa Verde']},
}


def _named(legend, names):
    return {code: (name, rgb) for (code, (_old, rgb)), name in zip(legend.items(), names)}
ESCOLAS = [('E. M. Monteiro Lobato', 640, 420, 900), ('E. E. Cecília Meireles', 1380, 560, 600),
           ('E. M. Paulo Freire', 520, 1350, 450), ('E. M. Rachel de Queiroz', 1550, 1450, 300),
           ('E. E. Darcy Ribeiro', 1000, 980, 1200), ('E. M. Cora Coralina', 300, 820, 250)]


def _srs():
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(EPSG)
    return srs


def _smooth_noise(rng, scale, octaves=4):
    out = np.zeros((N, N))
    for k in range(octaves):
        size = max(2, int(N / scale * 2 ** k))
        coarse = rng.random((size + 1, size + 1))
        yi = np.linspace(0, size, N)
        xi = np.linspace(0, size, N)
        y0, x0 = np.floor(yi).astype(int).clip(0, size - 1), np.floor(xi).astype(int).clip(0, size - 1)
        fy, fx = (yi - y0)[:, None], (xi - x0)[None, :]
        c = coarse
        top = c[y0][:, x0] * (1 - fx) + c[y0][:, x0 + 1] * fx
        bot = c[y0 + 1][:, x0] * (1 - fx) + c[y0 + 1][:, x0 + 1] * fx
        out += (top * (1 - fy) + bot * fy) / 2 ** k
    return (out - out.min()) / (out.max() - out.min())


def _write_classes(path, array, legend):
    ds = gdal.GetDriverByName('GTiff').Create(path, N, N, 1, gdal.GDT_Byte, options=['COMPRESS=DEFLATE'])
    ds.SetGeoTransform((X0, CELL, 0, Y0, 0, -CELL))
    ds.SetProjection(_srs().ExportToWkt())
    band = ds.GetRasterBand(1)
    table = gdal.ColorTable()
    names = [''] * (max(legend) + 1)
    names[0] = 'FUNDO'
    for code, (name, rgb) in legend.items():
        table.SetColorEntry(code, (*rgb, 255))
        names[code] = name
    band.SetColorTable(table)
    band.SetCategoryNames(names)
    band.WriteArray(array.astype(np.uint8))
    ds = None


def _write_float(path, array):
    ds = gdal.GetDriverByName('GTiff').Create(path, N, N, 1, gdal.GDT_Float32, options=['COMPRESS=DEFLATE'])
    ds.SetGeoTransform((X0, CELL, 0, Y0, 0, -CELL))
    ds.SetProjection(_srs().ExportToWkt())
    ds.GetRasterBand(1).WriteArray(array.astype(np.float32))
    ds = None


def build(folder, lang='pt'):
    os.makedirs(folder, exist_ok=True)
    rng = np.random.default_rng(2026)
    yy, xx = np.mgrid[0:N, 0:N]
    # Rio meandrando de norte a sul, a oeste do centro.
    river_x = 70 + 18 * np.sin(yy / 23.0) + 6 * np.sin(yy / 7.0)
    dist_river = np.abs(xx - river_x)
    water = dist_river < 3.2
    # Relevo: serra a leste (cresce para leste e para norte), planície junto ao rio.
    relief = 0.55 * (xx / N) + 0.25 * (1 - yy / N) + 0.35 * _smooth_noise(rng, 40)
    t = np.clip((dist_river - 6) / 30.0, 0, 1)
    relief = relief * (0.3 + 0.7 * t * t * (3 - 2 * t))   # várzea plana, transição suave
    # Declividade (%) desenhada: quase nula na várzea, crescendo para a serra a leste.
    floodplain = np.clip((dist_river - 8) / 25.0, 0, 1)
    slope = (1.0 + 26.0 * (xx / N) ** 1.3 * (0.4 + _smooth_noise(rng, 50, octaves=2))
             + 6.0 * _smooth_noise(rng, 20, octaves=2)) * (0.15 + 0.85 * floodplain)
    decl = np.digitize(slope, [3, 8, 20]) + 1
    # Solos: neossolo flúvico na várzea, latossolo nos topos, argissolo nas encostas.
    solos = np.where(dist_river < 14, 3, np.where(relief > 0.62, 2, 1))
    # Núcleo urbano a leste do rio, crescendo de 2000 a 2020.
    cx, cy = 100, 75
    noise = _smooth_noise(rng, 25)
    radial = np.hypot((xx - cx) / 1.25, yy - cy) + 22 * (noise - 0.5)
    veg_noise = _smooth_noise(rng, 30)
    agri_noise = _smooth_noise(rng, 35)

    def land_use(radius, veg_loss):
        uso = np.full((N, N), 4)                                    # pastagem
        uso[agri_noise > 0.55] = 3                                   # agricultura
        uso[(veg_noise > 0.58 + veg_loss) | ((dist_river < 9 + 4 * veg_noise) & (veg_noise > 0.25 + veg_loss))
            | ((relief > 0.78) & (veg_noise > 0.3 + veg_loss))] = 2  # vegetação nativa
        uso[radial < radius] = 1                                     # área urbana
        uso[water] = 5
        return uso

    uso = {2000: land_use(30, 0.0), 2010: land_use(42, 0.06), 2020: land_use(55, 0.12)}
    for year, array in uso.items():
        _write_classes(os.path.join(folder, f'uso_solo_{year}.tif'), array, _named(USO, NAMES[lang]['uso']))
    _write_classes(os.path.join(folder, 'solos.tif'), solos, _named(SOLOS, NAMES[lang]['solos']))
    _write_classes(os.path.join(folder, 'declividade.tif'), decl, _named(DECL, NAMES[lang]['decl']))
    friction = np.choose(uso[2020], [1, 1, 4, 2, 2, 10]).astype(float)
    _write_float(os.path.join(folder, 'atrito.tif'), friction)

    # Bairros: 3 colunas x 2 linhas cobrindo a grade inteira.
    driver = ogr.GetDriverByName('GPKG')
    path = os.path.join(folder, 'bairros.gpkg')
    if os.path.exists(path):
        driver.DeleteDataSource(path)
    ds = driver.CreateDataSource(path)
    layer = ds.CreateLayer('bairros', _srs(), ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn('CODIGO', ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn('NOME', ogr.OFTString))
    xs = [X0, X0 + 700, X0 + 1300, X0 + N * CELL]
    ys = [Y0, Y0 - 1000, Y0 - N * CELL]
    order = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)]
    names = NAMES[lang]['bairros']
    for code, ((col, row), name) in enumerate(zip(order, names), 1):
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for x, y in ((xs[col], ys[row]), (xs[col + 1], ys[row]), (xs[col + 1], ys[row + 1]),
                     (xs[col], ys[row + 1]), (xs[col], ys[row])):
            ring.AddPoint_2D(x, y)
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField('CODIGO', code)
        feature.SetField('NOME', name)
        feature.SetGeometry(poly)
        layer.CreateFeature(feature)
    ds = None

    path = os.path.join(folder, 'escolas.gpkg')
    if os.path.exists(path):
        driver.DeleteDataSource(path)
    ds = driver.CreateDataSource(path)
    layer = ds.CreateLayer('escolas', _srs(), ogr.wkbPoint)
    layer.CreateField(ogr.FieldDefn('NOME', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('MATRICULAS', ogr.OFTInteger))
    for name, dx, dy, mass in ESCOLAS:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint_2D(X0 + dx, Y0 - dy)
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField('NOME', name)
        feature.SetField('MATRICULAS', mass)
        feature.SetGeometry(point)
        layer.CreateFeature(feature)
    ds = None
    return uso, solos, decl


if __name__ == '__main__':
    gdal.UseExceptions()  # só no uso autônomo (importado pelo tutorial, não altera o GDAL do processo)
    uso, solos, decl = build(os.path.abspath(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else 'pt')
    for year, array in uso.items():
        values, counts = np.unique(array, return_counts=True)
        print(year, dict(zip(values.tolist(), (counts / counts.sum() * 100).round(1).tolist())))
    for name, array in (('solos', solos), ('decl', decl)):
        values, counts = np.unique(array, return_counts=True)
        print(name, dict(zip(values.tolist(), (counts / counts.sum() * 100).round(1).tolist())))
