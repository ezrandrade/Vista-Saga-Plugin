"""Compara saídas do Voronoi do Vista SAGA original com o plugin, sobre o MESMO RS2 de entrada.

Uso:
    python3.12 scripts/comparar_caso_bacia.py --rs2 ENTRADA.rs2 --pontos PONTOS.txt --epsg CODIGO \
        [--simples S.rs2] [--massa M.rs2] [--atrito A.rs2] [--massa-atrito MA.rs2] [--vetorial] \
        [--saida PASTA]

- ENTRADA.rs2: o mapa de classes aberto no Vista SAGA (com atrito, as notas vêm do [ATRITOS] do arquivo
  de pontos, uma por classe, na ordem da legenda; confirmado em 18/11/2026).
- PONTOS.txt: arquivo de pontos do Vista SAGA (Nome;Massa;coluna:linha, contadas a partir de 1).
- --epsg: SRC projetado da grade, informado pelo usuário (o RS2 não guarda SRC; nunca é deduzido).
- --vetorial: roda também a guia Vetorial (modelo contínuo) sobre o RS2 convertido em polígonos (bordas
  em degrau; a classe FUNDO entra como polígono com a própria nota). Pode levar alguns minutos.

O plugin roda nas mesmas células: guia Raster (run_voronoi) com a grade e os polos do Vista SAGA.
A área de estudo é a das células que não são FUNDO na ENTRADA. Saída: tabela por modalidade e os três
critérios de comparabilidade aceitos pelo autor em 19/11/2026:
  (1) >= 99% das células da área de estudo iguais às do Vista SAGA;
  (2) >= 90% das divergências na fronteira entre regiões do Vista SAGA (vizinhança de 8);
  (3) nenhuma região com diferença de área > 1% da própria área (área do Vista SAGA na área de estudo).

Limitação observada do Vista SAGA original (19/11/2026): com atrito, a saída só saiu correta quando a
grade de entrada tinha cerca de 495 × 1.107 células; com 990 × 2.214 saiu reduzida à metade e vazia, com
247 × 553 saiu dobrada e só um quarto preenchido, sem aviso. O script recorta a saída à grade de entrada,
avisa quando o tamanho difere e conta os códigos fora da legenda (sem resultado).

Os RS2 e pontos do autor NÃO vão para o repositório.
"""
import argparse
import os
import sys
import tempfile
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from geosaga.rs2_format import PAIR, RS2Reader  # noqa: E402

LIMIAR_CELULAS = 99.0
LIMIAR_FRONTEIRA = 90.0
LIMIAR_AREA = 1.0


def ler_rs2(path):
    """Lê o RLE sem exigir que os códigos estejam na legenda (saídas do Vista SAGA podem ter códigos extras).

    Devolve (cabeçalho, matriz, códigos fora da legenda com contagem)."""
    reader = RS2Reader(path)
    h, d = reader.header, reader._data
    pos = h.data_offset
    out = np.empty((h.height, h.width), dtype=np.uint16)
    for y in range(h.height):
        pos += 4
        x = 0
        while x < h.width:
            n, c = PAIR.unpack_from(d, pos)
            pos += 4
            if not 0 < n <= h.width - x:
                raise ValueError(f'{path}: linha {y + 1} com extensão RLE inválida.')
            out[y, x:x + n] = c
            x += n
        pos += 1
    legenda = set(h.legend_codes)
    u, k = np.unique(out, return_counts=True)
    extras = {int(c): int(n) for c, n in zip(u, k) if int(c) not in legenda}
    return h, out, extras


def ler_pontos(path):
    texto = open(path, encoding='cp1252').read()
    partes = texto.split('[ATRITOS]')
    polos = []
    for linha in partes[0].strip().splitlines():
        nome, massa, xy = linha.strip().split(';')
        col, lin = map(int, xy.split(':'))
        polos.append((nome, float(massa), col, lin))
    notas = [float(v.replace(',', '.')) for v in partes[1].split()] if len(partes) > 1 else None
    return polos, notas


def fronteira(rotulos):
    r = rotulos.astype(np.int64)
    borda = np.zeros(r.shape, dtype=bool)
    p = np.pad(r, 1, mode='edge')
    h, w = r.shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                borda |= p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] != r
    return borda


def avaliar(vs, plugin, estudo, n_polos, area_celula_ha):
    """Critérios sobre a área de estudo; células "Ponto" (código 0) do Vista SAGA ficam de fora."""
    valido = estudo & (vs != 0) & (vs <= n_polos)
    iguais = valido & (vs == plugin)
    dif = valido & ~iguais
    c1 = 100 * iguais.sum() / valido.sum()
    c2 = 100 * (dif & fronteira(vs)).sum() / dif.sum() if dif.sum() else 100.0
    regioes = []
    for i in range(1, n_polos + 1):
        a_vs = ((vs == i) & valido).sum() * area_celula_ha
        a_pl = ((plugin == i) & valido).sum() * area_celula_ha
        rel = 100 * abs(a_pl - a_vs) / a_vs if a_vs else float('inf')
        regioes.append((i, a_vs, a_pl, rel))
    c3 = max(r[3] for r in regioes)
    return c1, int(dif.sum()), c2, c3, regioes


def rodar_raster(h, classes, notas, polos, wkt, modo, pasta):
    from osgeo import gdal
    from geosaga.voronoi_core import Generator
    from geosaga.voronoi_engine import run_voronoi
    res = (h.xmax - h.xmin) / h.width
    gt = (h.xmin, res, 0, h.ymax, 0, -res)
    geradores = [Generator(i, h.xmin + (c - .5) * res, h.ymax - (l - .5) * res, m, n)
                 for i, (n, m, c, l) in enumerate(polos, 1)]
    destino = os.path.join(pasta, f'plugin_{modo}.tif')
    kwargs = {}
    if modo in ('friction', 'mass_friction'):
        lut = np.zeros(int(max(h.legend_codes)) + 1)
        for k, codigo in enumerate(h.legend_codes):
            lut[codigo] = notas[k]
        atrito = os.path.join(pasta, 'atrito.tif')
        if not os.path.exists(atrito):
            ds = gdal.GetDriverByName('GTiff').Create(atrito, h.width, h.height, 1, gdal.GDT_Float32)
            ds.SetGeoTransform(gt)
            ds.SetProjection(wkt)
            ds.GetRasterBand(1).WriteArray(lut[classes])
            ds = None
        kwargs['friction_path'] = atrito
    run_voronoi(geradores, destino, wkt, gt, h.width, h.height, mode=modo, **kwargs)
    ds = gdal.Open(destino)
    rotulos = ds.ReadAsArray()
    ds = None
    return rotulos


def rodar_vetorial(h, classes, notas, polos, wkt, massa):
    from osgeo import gdal, ogr, osr
    from geosaga.voronoi_core import Generator
    from geosaga.voronoi_friction_continuous import friction_voronoi_polygons
    res = (h.xmax - h.xmin) / h.width
    gt = (h.xmin, res, 0, h.ymax, 0, -res)
    srs = osr.SpatialReference()
    srs.ImportFromWkt(wkt)
    nota = {codigo: notas[k] for k, codigo in enumerate(h.legend_codes)}
    mem = gdal.GetDriverByName('MEM').Create('', h.width, h.height, 1, gdal.GDT_Int32)
    mem.SetGeoTransform(gt)
    mem.SetProjection(wkt)
    mem.GetRasterBand(1).WriteArray(classes.astype(np.int32))
    vds = ogr.GetDriverByName('Memory').CreateDataSource('v')
    camada = vds.CreateLayer('p', srs, ogr.wkbPolygon)
    camada.CreateField(ogr.FieldDefn('c', ogr.OFTInteger))
    gdal.Polygonize(mem.GetRasterBand(1), None, camada, 0)
    feicoes = [(f.GetGeometryRef().ExportToWkb(), nota[f.GetField('c')]) for f in camada]
    geradores = [Generator(i, h.xmin + (c - .5) * res, h.ymax - (l - .5) * res, m, n)
                 for i, (n, m, c, l) in enumerate(polos, 1)]
    limites = (h.xmin, h.ymax - h.height * res, h.xmin + h.width * res, h.ymax)
    regioes, stats = friction_voronoi_polygons(geradores, feicoes, limites, mass_weighted=massa)
    saida = vds.CreateLayer('r', srs, ogr.wkbMultiPolygon)
    saida.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
    for g, geom in regioes:
        f = ogr.Feature(saida.GetLayerDefn())
        f.SetField('id', g.identifier)
        f.SetGeometry(geom)
        saida.CreateFeature(f)
    grade = gdal.GetDriverByName('MEM').Create('', h.width, h.height, 1, gdal.GDT_Int32)
    grade.SetGeoTransform(gt)
    gdal.RasterizeLayer(grade, [1], saida, options=['ATTRIBUTE=id'])
    return grade.ReadAsArray(), stats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--rs2', required=True)
    ap.add_argument('--pontos', required=True)
    ap.add_argument('--epsg', required=True, type=int)
    ap.add_argument('--simples')
    ap.add_argument('--massa')
    ap.add_argument('--atrito')
    ap.add_argument('--massa-atrito')
    ap.add_argument('--vetorial', action='store_true')
    ap.add_argument('--saida')
    a = ap.parse_args(argv)
    from osgeo import gdal, osr
    gdal.UseExceptions()  # script de linha de comando, fora do QGIS
    srs = osr.SpatialReference()
    if srs.ImportFromEPSG(a.epsg) != 0 or not srs.IsProjected():
        raise SystemExit('Informe um EPSG de SRC projetado.')
    wkt = srs.ExportToWkt()
    h, classes, extras = ler_rs2(a.rs2)
    if extras:
        raise SystemExit(f'O RS2 de entrada tem códigos fora da legenda: {extras}')
    polos, notas = ler_pontos(a.pontos)
    if notas is not None and len(notas) != len(h.legend_codes):
        raise SystemExit(f'[ATRITOS] tem {len(notas)} notas; a legenda tem {len(h.legend_codes)} classes.')
    fundo = h.background_code
    estudo = classes != fundo if fundo is not None else np.ones(classes.shape, dtype=bool)
    res = (h.xmax - h.xmin) / h.width
    area_celula_ha = res * res / 1e4
    pasta = a.saida or tempfile.mkdtemp(prefix='comparar_bacia_')
    os.makedirs(pasta, exist_ok=True)
    print(f'Entrada: {h.width} × {h.height} células de {res:g} m; área de estudo {estudo.sum()} células '
          f'({estudo.sum() * area_celula_ha:.2f} ha); {len(polos)} polos; notas {notas}')
    casos = [('Simples', a.simples, 'simple'), ('Com Massa', a.massa, 'mass'),
             ('Com Atrito', a.atrito, 'friction'), ('Com Massa e Atrito', a.massa_atrito, 'mass_friction')]
    resumo = []
    for rotulo, arquivo, modo in casos:
        if not arquivo:
            continue
        if modo in ('friction', 'mass_friction') and notas is None:
            raise SystemExit('Arquivo de pontos sem [ATRITOS]: necessário para as modalidades com atrito.')
        hv, vs, extras_vs = ler_rs2(arquivo)
        print(f'\n== {rotulo}: {os.path.basename(arquivo)}')
        if (hv.width, hv.height) != (h.width, h.height):
            print(f'   AVISO: saída do Vista SAGA com {hv.width} × {hv.height} células (entrada {h.width} × '
                  f'{h.height}); recortada ao canto superior esquerdo.')
        vs = vs[:h.height, :h.width]
        if vs.shape != classes.shape:
            print('   Saída menor que a entrada: sem comparação possível (rodada inválida).')
            continue
        if extras_vs:
            print(f'   AVISO: códigos fora da legenda na saída (sem resultado): {extras_vs}')
        if not (vs[estudo] <= len(polos)).any():
            print('   Saída sem resultado na área de estudo: rodada inválida.')
            continue
        polos_vs = sorted((int(x) + 1, int(y) + 1) for y, x in zip(*np.where(vs == 0)))
        esperados = sorted((c, l) for _, _, c, l in polos)
        print('   células "Ponto" nas posições do arquivo: ' + ('sim' if polos_vs == esperados else f'NÃO ({polos_vs})'))
        t = time.time()
        guias = [('Raster', rodar_raster(h, classes, notas, polos, wkt, modo, pasta), time.time() - t)]
        if a.vetorial and modo in ('friction', 'mass_friction'):
            t = time.time()
            rot, _ = rodar_vetorial(h, classes, notas, polos, wkt, modo == 'mass_friction')
            guias.append(('Vetorial', rot, time.time() - t))
        for guia, rot, seg in guias:
            c1, ndif, c2, c3, regioes = avaliar(vs, rot, estudo, len(polos), area_celula_ha)
            ok = (c1 >= LIMIAR_CELULAS, c2 >= LIMIAR_FRONTEIRA, c3 <= LIMIAR_AREA)
            print(f'   Guia {guia} ({seg:.0f} s): (1) células {c1:.3f}% ({ndif} dif.) {"passa" if ok[0] else "NÃO passa"}; '
                  f'(2) na fronteira {c2:.1f}% {"passa" if ok[1] else "NÃO passa"}; '
                  f'(3) maior diferença de área {c3:.2f}% {"passa" if ok[2] else "NÃO passa"}')
            for i, a_vs, a_pl, rel in regioes:
                print(f'      {i:3d} {polos[i - 1][0]:24s} Vista SAGA {a_vs:10.2f} ha | plugin {a_pl:10.2f} ha | '
                      f'{a_pl - a_vs:+8.2f} ha ({rel:.2f}%)')
            resumo.append((rotulo, guia, c1, c2, c3, all(ok)))
    if resumo:
        print('\nResumo (critérios de 19/11/2026: células >= 99%, fronteira >= 90%, área <= 1% por região):')
        for rotulo, guia, c1, c2, c3, ok in resumo:
            print(f'   {rotulo:20s} {guia:9s} {c1:7.3f}% {c2:6.1f}% {c3:6.2f}%  {"atende" if ok else "NÃO atende"}')
    print(f'\nArquivos do plugin em {pasta}')


if __name__ == '__main__':
    main()
