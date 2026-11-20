"""Executa o tutorial de Vila Serena com os motores do plugin e registra os números esperados.

Uso, na raiz do repositório:
    python3.12 docs/tutorial/executar_tutorial.py <pasta_de_trabalho> [pt|en|es]

Gera <trabalho>/dados (gerar_dados.py), roda os sete módulos com as mesmas funções que as janelas usam,
grava os resultados em <trabalho>/resultados e um resumo numérico em <trabalho>/numeros.json, que o texto
do tutorial cita. Mudou um motor? Rode de novo e confira os números do tutorial.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import gerar_dados  # noqa: E402

# Decisões didáticas do exemplo (não são recomendação de método).
EVALUATION = {
    'titulo': 'Aptidão à expansão urbana - Vila Serena',
    'escala': 10,
    'criterios': [
        ('declividade.tif', 'Declividade', 40, {'1': 10, '2': 8, '3': 4, '4': 1}, []),
        ('solos.tif', 'Solos', 25, {'1': 7, '2': 9, '3': 2}, []),
        ('uso_solo_2020.tif', 'Uso do solo 2020', 35, {'1': 8, '2': 1, '3': 6, '4': 9}, ['5']),
    ],
}
CRITERIA = {'pt': ['Declividade', 'Solos', 'Uso do solo 2020'], 'en': ['Slope', 'Soils', 'Land use 2020'],
            'es': ['Pendiente', 'Suelos', 'Uso del suelo 2020']}
TITLES = {'pt': {'avaliacao': 'Aptidão à expansão urbana - Vila Serena', 'assinatura': 'Centro e Beira-Rio',
                 'monitoria': 'Uso do solo 2000 - 2020'},
          'en': {'avaliacao': 'Suitability for urban growth - Vila Serena', 'assinatura': 'Downtown and Riverside',
                 'monitoria': 'Land use 2000 - 2020'},
          'es': {'avaliacao': 'Aptitud para la expansión urbana - Vila Serena', 'assinatura': 'Centro y Ribera',
                 'monitoria': 'Uso del suelo 2000 - 2020'}}


def _legend(path):
    from osgeo import gdal
    ds = gdal.Open(path)
    names = ds.GetRasterBand(1).GetCategoryNames() or []
    ds = None
    return {str(i): name for i, name in enumerate(names) if name and i}


def run(work, lang='pt'):
    from osgeo import ogr
    data = os.path.join(work, 'dados')
    out = os.path.join(work, 'resultados')
    for folder in (data, out):
        if os.path.isdir(folder):
            shutil.rmtree(folder)
    gerar_dados.build(data, lang)
    names = CRITERIA[lang]
    os.makedirs(out)
    numbers = {}

    # Projeto da Avaliação pronto para "Abrir projeto..." (vai junto com os dados).
    project = {'formato': 'geosaga-avaliacao', 'versao': 1, 'escala': EVALUATION['escala'],
               'camadas': [{'arquivo': f, 'nome': n, 'peso': w, 'notas': notes, 'bloqueadas': blocked}
                           for (f, _n, w, notes, blocked), n in zip(EVALUATION['criterios'], names)]}
    with open(os.path.join(data, 'aptidao_expansao.geosaga.json'), 'w', encoding='utf-8') as stream:
        json.dump(project, stream, ensure_ascii=False, indent=2)

    # 1. Conversor: bairros (vetor) -> GeoTIFF; uso 2020 -> RS2 -> GeoTIFF.
    from geosaga.vector_raster import convert_vector_to_tif
    from geosaga.rs2_converter import convert_rs2_to_tif, convert_tif_to_rs2
    convert_vector_to_tif(os.path.join(data, 'bairros.gpkg'), os.path.join(out, 'bairros.tif'), 'CODIGO', 10.0)
    convert_tif_to_rs2(os.path.join(data, 'uso_solo_2020.tif'), os.path.join(out, 'uso_solo_2020.rs2'))
    convert_rs2_to_tif(os.path.join(out, 'uso_solo_2020.rs2'), os.path.join(out, 'uso_solo_2020_de_volta.tif'),
                       epsg='EPSG:31985')
    from osgeo import gdal
    import numpy as np
    a = gdal.Open(os.path.join(data, 'uso_solo_2020.tif')).ReadAsArray()
    b = gdal.Open(os.path.join(out, 'uso_solo_2020_de_volta.tif')).ReadAsArray()
    bt = gdal.Open(os.path.join(out, 'bairros.tif'))
    numbers['conversor'] = {'ida_e_volta_identico': bool((a == b).all()),
                            'bairros_tif': [bt.RasterXSize, bt.RasterYSize, bt.GetGeoTransform()[1]],
                            'rs2_bytes': os.path.getsize(os.path.join(out, 'uso_solo_2020.rs2'))}
    bt = None

    # 2. Assinatura: bairros.tif (referência) + uso 2020 + solos + declividade; Centro e Beira-Rio.
    from geosaga.signature_raster import open_raster_map, run_raster_signature
    from geosaga.signature_reports import write_csv, write_txt
    maps = [open_raster_map(os.path.join(out, 'bairros.tif'), labels={str(k): v for k, v in enumerate(gerar_dados.NAMES[lang]['bairros'], 1)})]
    maps += [open_raster_map(os.path.join(data, f)) for f in ('uso_solo_2020.tif', 'solos.tif', 'declividade.tif')]
    result = run_raster_signature(maps, [2, 1], per_feature=True)
    write_txt(os.path.join(out, 'assinatura.txt'), result, title=TITLES[lang]['assinatura'])
    write_csv(os.path.join(out, 'assinatura.csv'), result)
    sig = {}  # recorte ('uniao' ou código do bairro) -> mapa -> código da classe -> [ha, % área asn., % categoria]
    for cut in [result.union] + result.features:
        sig['uniao' if cut is result.union else str(cut.key)] = {m.name: {r.code_text: [round(r.asn_ha, 2), round(r.pct_area, 2),
                                              None if r.pct_category is None else round(r.pct_category, 2)]
                                  for r in m.rows} for m in cut.maps}
    numbers['assinatura'] = sig

    # 3. Monitoria 2000 -> 2020.
    from geosaga.monitoring_engine import run_monitoring
    mon = run_monitoring(os.path.join(data, 'uso_solo_2000.tif'), os.path.join(data, 'uso_solo_2020.tif'),
                         os.path.join(out, 'transicoes_2000_2020.tif'), before_label='2000', after_label='2020',
                         title=TITLES[lang]['monitoria'])
    numbers['monitoria'] = {k: v for k, v in mon.items() if isinstance(v, (int, float, str))}

    # 4. Combinação: uso 2020 x solos.
    from geosaga.combination_raster import run_raster_combination
    comb = run_raster_combination([os.path.join(data, 'uso_solo_2020.tif'), os.path.join(data, 'solos.tif')],
                                  os.path.join(out, 'uso2020_x_solos.tif'))
    numbers['combinacao'] = {'combinacoes': comb['combinations'], 'area_ha': comb['area_ha']}

    # 5. Avaliação.
    from geosaga.raster_engine import run_evaluation
    config = {'escala': EVALUATION['escala'],
              'camadas': [{'peso': w, 'notas': notes, 'bloqueadas': blocked}
                          for _, _, w, notes, blocked in EVALUATION['criterios']],
              'nomes': names,
              'legendas': [_legend(os.path.join(data, f)) for f, *_ in EVALUATION['criterios']]}
    ev = run_evaluation([os.path.join(data, f) for f, *_ in EVALUATION['criterios']], config,
                        os.path.join(out, 'aptidao_expansao.tif'), os.path.join(out, 'aptidao_expansao_relatorio.csv'),
                        TITLES[lang]['avaliacao'], report_txt=os.path.join(out, 'aptidao_expansao_relatorio.txt'))
    # Área por nota final como no relatório (agrupamento do relatório: arredondamento half-up).
    with open(os.path.join(out, 'aptidao_expansao_relatorio.txt'), encoding='utf-8-sig') as stream:
        lines = stream.read().split('RESUMO POR NOTA FINAL')[1].strip().splitlines()[1:]
    per_note = {line.split('\t')[0]: float(line.split('\t')[2]) for line in lines if line.strip()}
    numbers['avaliacao'] = {**{k: v for k, v in ev.items() if v is not None}, 'area_por_nota_ha': per_note}

    # 6. Voronoi: escolas, Com massa (MATRICULAS) e Com atrito (atrito.tif), na grade do atrito.
    from geosaga.voronoi_core import Generator
    from geosaga.voronoi_engine import run_voronoi
    ds = ogr.Open(os.path.join(data, 'escolas.gpkg'))
    layer = ds.GetLayer(0)
    points = [Generator(f.GetFID(), f.GetGeometryRef().GetX(), f.GetGeometryRef().GetY(),
                        float(f.GetField('MATRICULAS')), f.GetField('NOME')) for f in layer]
    ds = None
    ref = gdal.Open(os.path.join(data, 'atrito.tif'))
    gt, w, h, wkt = ref.GetGeoTransform(), ref.RasterXSize, ref.RasterYSize, ref.GetProjection()
    ref = None
    vor = {}
    for mode, name in (('simple', 'simples'), ('mass', 'com_massa'), ('friction', 'com_atrito')):
        res = run_voronoi(points, os.path.join(out, f'voronoi_{name}.tif'), wkt, gt, w, h, mode=mode,
                          friction_path=os.path.join(data, 'atrito.tif') if mode == 'friction' else None)
        vor[name] = {row['CENTRO']: {k: row[k] for k in row if k not in ('ID', 'CENTRO')} for row in res['rows']}
    numbers['voronoi'] = vor
    with open(os.path.join(work, 'numeros.json'), 'w', encoding='utf-8') as stream:
        json.dump(numbers, stream, ensure_ascii=False, indent=1, default=str)
    return numbers


if __name__ == '__main__':
    lang = sys.argv[2] if len(sys.argv) > 2 else 'pt'
    print(json.dumps(run(os.path.abspath(sys.argv[1]), lang), ensure_ascii=False, indent=1, default=str)[:3000])
