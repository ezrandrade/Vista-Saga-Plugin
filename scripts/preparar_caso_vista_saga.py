"""Prepara um caso real do Voronoi com atrito para rodar no Vista SAGA original (validação cruzada).

Uso:
    python3.12 scripts/preparar_caso_vista_saga.py --uso USO.gpkg --campo-atrito NOTA \
        --bacia BACIA.gpkg --pontos PONTOS.gpkg --campo-massa MASSA [--campo-nome NOME] \
        [--campo-classe CLASSE] [--resolucao 5] [--escala-massa 1] [--decimal virgula|ponto] \
        --saida PASTA

Camadas no formato ARQUIVO ou ARQUIVO|NOME_DA_CAMADA. As três precisam estar no MESMO SRC projetado
(sem reprojeção implícita; regra do CLAUDE.md).

Grava em PASTA:
- caso.rs2: mapa de classes de atrito na grade da análise (retângulo da bacia, alinhado a múltiplos
  inteiros da resolução, porque as bordas do RS2 são inteiros). Classe 0 = FUNDO (sem polígono de uso
  do solo, nota 1, como no plugin); classes 1..n = notas distintas (ou classes do --campo-classe).
  Rasterização pelo centro da célula, última feição vence (a mesma do plugin).
- pontos_vista_saga.txt: Nome;Massa;coluna:linha (contadas a partir de 1, confirmado no caso de teste
  de 17/11/2026), [ATRITOS] com a nota de cada classe a partir da classe 0; CP1252 e CRLF.
- pontos_centros.csv: os mesmos polos no centro das células usadas pelo Vista SAGA, para rodar o plugin
  com posições idênticas.
- atrito_grade.tif: notas na mesma grade (guia Raster do plugin com atrito raster: comparação célula a
  célula; também serve de "Grade de raster de referência" no Simples e Com Massa).
- caso.json: grade, SRC, classes, notas, polos e avisos (para o script de comparação).
- previa.png (se houver Pillow).

Massa: o Vista SAGA lê a massa como inteiro. Massas não inteiras exigem --escala-massa (todas
multiplicadas pela mesma constante e arredondadas): a escala não muda o resultado (M/d² compara
razões), o arredondamento muda; o erro relativo máximo sai no resumo.
Notas não inteiras exigem --decimal: o separador decimal do [ATRITOS] não foi verificado no Vista SAGA.
Os dados do autor NÃO vão para o repositório.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

MAX_CELLS_WARNING = 2_000_000
COLORS = [(255, 255, 255, 0), (200, 230, 170, 0), (250, 210, 120, 0), (190, 80, 60, 0), (150, 190, 230, 0),
          (230, 160, 200, 0), (170, 170, 120, 0), (120, 200, 190, 0), (240, 240, 140, 0), (160, 130, 200, 0)]


def _open_layer(spec):
    from osgeo import ogr
    path, _, name = str(spec).partition('|')
    ds = ogr.Open(path)
    if ds is None:
        raise SystemExit(f'Não foi possível abrir {path}.')
    layer = ds.GetLayerByName(name) if name else ds.GetLayer(0)
    if layer is None:
        raise SystemExit(f'Camada {name!r} ausente em {path}.')
    return ds, layer


def _same_crs(layers):
    refs = [layer.GetSpatialRef() for _, layer in layers]
    if any(r is None for r in refs):
        raise SystemExit('Todas as camadas precisam ter SRC definido.')
    if not refs[0].IsProjected():
        raise SystemExit('O SRC precisa ser projetado (metros).')
    for r in refs[1:]:
        if not r.IsSame(refs[0]):
            raise SystemExit('As camadas estão em SRC diferentes; reprojete antes (sem reprojeção implícita).')
    return refs[0]


def _number(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise SystemExit(f'Valor não numérico em {label}: {value!r}.') from None
    if not math.isfinite(number):
        raise SystemExit(f'Valor inválido em {label}: {value!r}.')
    return number


def preparar(uso, campo_atrito, bacia, pontos, campo_massa, saida, *, campo_nome=None, campo_classe=None,
             resolucao=5.0, escala_massa=None, decimal=None):
    from osgeo import gdal, ogr
    from geosaga.rs2_format import RS2Header, RS2Reader, write_rs2
    from geosaga.voronoi_friction_vector import rasterize_friction, check_rating

    os.makedirs(saida, exist_ok=True)
    avisos = []
    layers = [_open_layer(uso), _open_layer(bacia), _open_layer(pontos)]
    srs = _same_crs(layers)
    wkt = srs.ExportToWkt()
    (_, uso_layer), (_, bacia_layer), (_, pontos_layer) = layers
    resolucao = float(resolucao)
    if resolucao <= 0 or resolucao != int(resolucao):
        raise SystemExit('Use resolução inteira e positiva (as bordas do RS2 são inteiros).')
    res = int(resolucao)

    # Bacia: união das feições; grade alinhada a múltiplos inteiros da resolução.
    union = None
    for feature in bacia_layer:
        geometry = feature.GetGeometryRef()
        if geometry is not None and not geometry.IsEmpty():
            union = geometry.Clone() if union is None else union.Union(geometry)
    if union is None:
        raise SystemExit('A camada da bacia não tem polígonos.')
    bx0, bx1, by0, by1 = union.GetEnvelope()
    xmin = int(math.floor(bx0 / res) * res)
    ymin = int(math.floor(by0 / res) * res)
    xmax = int(math.ceil(bx1 / res) * res)
    ymax = int(math.ceil(by1 / res) * res)
    width, height = (xmax - xmin) // res, (ymax - ymin) // res
    if width > 65535 or height > 65535:
        raise SystemExit('Grade maior que o limite do RS2 (65.535 colunas ou linhas); aumente a resolução.')
    if width * height > MAX_CELLS_WARNING:
        avisos.append(f'Grade grande ({width} × {height} = {width * height:,} células): o desempenho do Vista '
                      'SAGA com esse tamanho não foi testado; se ficar lento, repita com resolução maior.')
    gt = (float(xmin), float(res), 0., float(ymax), 0., -float(res))

    # Uso do solo: nota por feição (coluna vazia = sem polígono, como no plugin).
    features, labels_by_rating, vazias = [], {}, 0
    for feature in uso_layer:
        geometry = feature.GetGeometryRef()
        value = feature.GetField(campo_atrito)
        if geometry is None or geometry.IsEmpty():
            continue
        if value is None:
            vazias += 1
            continue
        rating = check_rating(_number(value, f'{campo_atrito}, feição {feature.GetFID()}'),
                              f'feição {feature.GetFID()}')
        features.append((bytes(geometry.ExportToWkb()), rating))
        if campo_classe:
            label = str(feature.GetField(campo_classe) or '').strip() or f'Nota {rating:g}'
            previous = labels_by_rating.setdefault(rating, label)
            if previous != label:
                raise SystemExit(f'A nota {rating:g} aparece nas classes {previous!r} e {label!r}: com '
                                 '--campo-classe, cada classe precisa de uma nota só e vice-versa.')
    if vazias:
        avisos.append(f'{vazias} feição(ões) com a coluna de atrito vazia: tratadas como sem polígono (FUNDO, nota 1).')
    if not features:
        raise SystemExit('Nenhum polígono de uso do solo com nota.')
    grid, stats, no_poly = rasterize_friction(features, 1.0, gt, width, height, wkt)
    ratings = sorted({r for _, r in features})
    if len(ratings) + 1 > 32768:
        raise SystemExit('Notas distintas demais para o RS2.')
    if len(set(labels_by_rating.values())) != len(labels_by_rating):
        raise SystemExit('Duas notas diferentes com o mesmo nome de classe.')
    codes = np.zeros((height, width), dtype=np.uint16)
    covered = ~no_poly if no_poly is not None else np.ones_like(codes, dtype=bool)
    for code, rating in enumerate(ratings, 1):
        codes[covered & (grid == rating)] = code
    nomes = ['FUNDO'] + [labels_by_rating.get(r, f'Nota {r:g}') for r in ratings]
    notas = [1.0] + ratings

    # Notas no [ATRITOS].
    if all(n == int(n) for n in notas):
        notas_txt = [str(int(n)) for n in notas]
    elif decimal in ('virgula', 'ponto'):
        sep = ',' if decimal == 'virgula' else '.'
        notas_txt = [f'{n:g}'.replace('.', sep) for n in notas]
        avisos.append(f'Notas não inteiras gravadas com {"vírgula" if sep == "," else "ponto"}: confira no Vista '
                      'SAGA se as notas exibidas são as esperadas (separador não verificado).')
    else:
        raise SystemExit('Há notas não inteiras: informe --decimal virgula ou --decimal ponto (o separador '
                         'decimal do [ATRITOS] não foi verificado no Vista SAGA).')

    # Polos: célula que contém o ponto; massa inteira.
    polos, ocupadas = [], {}
    names = [f.GetName() for f in pontos_layer.schema]
    if campo_massa not in names or (campo_nome and campo_nome not in names):
        raise SystemExit(f'Campos disponíveis na camada de pontos: {", ".join(names)}.')
    for feature in pontos_layer:
        geometry = feature.GetGeometryRef()
        if geometry is None or geometry.IsEmpty():
            continue
        x, y = geometry.GetX(), geometry.GetY()
        col, row = int((x - xmin) // res), int((ymax - y) // res)
        nome = str(feature.GetField(campo_nome) if campo_nome else f'Polo {feature.GetFID()}').strip()
        nome = nome.replace(';', ',').replace(':', '-')
        if not (0 <= col < width and 0 <= row < height):
            raise SystemExit(f'O polo {nome!r} está fora da grade da bacia.')
        if (col, row) in ocupadas:
            raise SystemExit(f'Os polos {ocupadas[(col, row)]!r} e {nome!r} caem na mesma célula; use resolução menor.')
        ocupadas[(col, row)] = nome
        if codes[row, col] == 0:
            avisos.append(f'O polo {nome!r} cai numa célula sem polígono de uso do solo (FUNDO); o plugin recusa '
                          'centro fora dos polígonos de atrito.')
        massa = _number(feature.GetField(campo_massa), f'massa de {nome}')
        if massa <= 0:
            raise SystemExit(f'Massa não positiva em {nome!r}.')
        polos.append({'nome': nome, 'massa_original': massa, 'coluna': col, 'linha': row,
                      'x_centro': xmin + (col + .5) * res, 'y_centro': ymax - (row + .5) * res,
                      'deslocamento_m': math.hypot(x - (xmin + (col + .5) * res), y - (ymax - (row + .5) * res))})
    if len(polos) < 2:
        raise SystemExit('São necessários pelo menos 2 polos.')
    if len(polos) > 500:
        raise SystemExit('O Voronoi com atrito do plugin aceita até 500 centros.')
    nao_inteiras = any(p['massa_original'] != int(p['massa_original']) for p in polos)
    if nao_inteiras and not escala_massa:
        raise SystemExit('Há massas não inteiras e o Vista SAGA lê a massa como inteiro: informe --escala-massa '
                         '(ex.: 100), que multiplica todas as massas antes do arredondamento.')
    escala = float(escala_massa or 1)
    erro = 0.0
    for p in polos:
        p['massa'] = int(round(p['massa_original'] * escala))
        if p['massa'] < 1:
            raise SystemExit(f'Massa de {p["nome"]!r} vira 0 com a escala {escala:g}; aumente a escala.')
        erro = max(erro, abs(p['massa'] - p['massa_original'] * escala) / (p['massa_original'] * escala))
    if erro:
        avisos.append(f'Arredondamento das massas (escala {escala:g}): erro relativo máximo {100 * erro:.3f}%.')

    # Gravação.
    header = RS2Header(width=width, height=height, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax,
                       labels=nomes, colors=[COLORS[k % len(COLORS)] for k in range(len(nomes))])
    rs2 = os.path.join(saida, 'caso.rs2')
    write_rs2(rs2, header, list(codes))
    back = RS2Reader(rs2)
    lido = np.array(list(back.rows()) if hasattr(back, 'rows') else back.read_array())
    if not (lido == codes).all():
        raise SystemExit('Releitura do RS2 divergente.')
    linhas = [f'{p["nome"]};{p["massa"]};{p["coluna"] + 1}:{p["linha"] + 1}' for p in polos]
    linhas += ['[ATRITOS]'] + notas_txt
    with open(os.path.join(saida, 'pontos_vista_saga.txt'), 'w', encoding='cp1252', newline='\r\n') as f:
        for line in linhas:
            f.write(line + '\n')
    with open(os.path.join(saida, 'pontos_centros.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        f.write('NOME;MASSA;X;Y\n')
        for p in polos:
            f.write(f'{p["nome"]};{p["massa"]};{p["x_centro"]:.3f};{p["y_centro"]:.3f}\n')
    tif = os.path.join(saida, 'atrito_grade.tif')
    ds = gdal.GetDriverByName('GTiff').Create(tif, width, height, 1, gdal.GDT_Float32, options=['COMPRESS=LZW'])
    ds.SetGeoTransform(gt)
    ds.SetProjection(wkt)
    band = ds.GetRasterBand(1)
    band.WriteArray(np.where(covered, grid, 1.0).astype(np.float32))
    ds = None
    # Máscara da bacia (centro da célula), para o resumo e a comparação.
    from geosaga.voronoi_engine import _study_mask
    dentro = _study_mask(bytes(union.ExportToWkb()), gt, width, height, wkt)
    info = {'grade': {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax, 'resolucao': res,
                      'colunas': width, 'linhas': height, 'geotransform': gt},
            'src_wkt': wkt, 'classes': [{'codigo': k, 'nome': n, 'nota': v} for k, (n, v) in enumerate(zip(nomes, notas))],
            'celulas_por_classe': {nomes[k]: int((codes == k).sum()) for k in range(len(nomes))},
            'celulas_na_bacia': int(dentro.sum()),
            'fundo_na_bacia': int((dentro & (codes == 0)).sum()),
            'escala_massa': escala, 'polos': polos, 'avisos': avisos,
            'contagem_coordenadas': 'coluna:linha a partir de 1'}
    if info['fundo_na_bacia']:
        avisos.append(f'{info["fundo_na_bacia"]} células da bacia sem polígono de uso do solo (FUNDO): o plugin não dá '
                      'resultado a elas; no Vista SAGA, o comportamento da classe FUNDO dentro da área não foi testado.')
    with open(os.path.join(saida, 'caso.json'), 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    try:
        from PIL import Image, ImageDraw
        scale = max(1, min(4, 1600 // max(width, height)))
        rgb = np.array([c[:3] for c in header.colors], dtype=np.uint8)[codes]
        img = Image.fromarray(rgb).resize((width * scale, height * scale), Image.NEAREST)
        draw = ImageDraw.Draw(img)
        for p in polos:
            cx, cy = (p['coluna'] + .5) * scale, (p['linha'] + .5) * scale
            draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(0, 0, 0))
            draw.text((cx + 6, cy - 6), f'{p["nome"]} (M={p["massa"]})', fill=(0, 0, 0))
        img.save(os.path.join(saida, 'previa.png'))
    except ImportError:
        pass
    return info


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--uso', required=True)
    parser.add_argument('--campo-atrito', required=True)
    parser.add_argument('--campo-classe')
    parser.add_argument('--bacia', required=True)
    parser.add_argument('--pontos', required=True)
    parser.add_argument('--campo-massa', required=True)
    parser.add_argument('--campo-nome')
    parser.add_argument('--resolucao', type=float, default=5.0)
    parser.add_argument('--escala-massa', type=float)
    parser.add_argument('--decimal', choices=('virgula', 'ponto'))
    parser.add_argument('--saida', required=True)
    a = parser.parse_args(argv)
    info = preparar(a.uso, a.campo_atrito, a.bacia, a.pontos, a.campo_massa, a.saida, campo_nome=a.campo_nome,
                    campo_classe=a.campo_classe, resolucao=a.resolucao, escala_massa=a.escala_massa,
                    decimal=a.decimal)
    g = info['grade']
    print(f"Grade: {g['colunas']} × {g['linhas']} células de {g['resolucao']} m; {info['celulas_na_bacia']:,} na bacia.")
    for c in info['classes']:
        print(f"  classe {c['codigo']}: {c['nome']} (nota {c['nota']:g}), {info['celulas_por_classe'][c['nome']]:,} células")
    for p in info['polos']:
        print(f"  {p['nome']}: massa {p['massa']}, coluna:linha {p['coluna'] + 1}:{p['linha'] + 1}, "
              f"deslocado {p['deslocamento_m']:.2f} m para o centro da célula")
    for aviso in info['avisos']:
        print('AVISO:', aviso)


if __name__ == '__main__':
    main()
