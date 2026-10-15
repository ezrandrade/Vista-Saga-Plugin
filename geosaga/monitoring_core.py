"""Núcleo independente da GUI para monitoria categórica em dois períodos.

Os relatórios registram pares (classe inicial, classe final) e respectivas áreas.
Com nomes em ambos os períodos, a permanência usa identidade temática;
sem legenda comparável, usa igualdade de códigos numéricos.
"""
from collections import Counter
import csv
import math

from .core import transition_counts


def combine_block(counts, a, b, nodata_a=None, nodata_b=None):
    """Acumula pares válidos, mantendo códigos 0 legítimos."""
    new, valid = transition_counts(a, b, nodata_a, nodata_b)
    counts.update(new)
    return int(valid.sum())


def transitions_summary(counts, total_pixels, hectare_pixel=None, before_names=None, after_names=None):
    """Gera estatísticas sem arredondar contagens ou alterar categorias."""
    if not counts:
        raise ValueError('Não existem transições em pixels válidos comuns.')
    valid = sum(counts.values())
    ids = {pair: ix for ix, pair in enumerate(sorted(counts), 1)}
    rows = []
    before_names = before_names or {}
    after_names = after_names or {}
    for (a, b), n in sorted(counts.items()):
        name_a = before_names.get(float(a), f'Classe {csv_code(a)}')
        name_b = after_names.get(float(b), f'Classe {csv_code(b)}')
        both_named = float(a) in before_names and float(b) in after_names
        is_stable = (name_a.strip().casefold() == name_b.strip().casefold()
                     if both_named else a == b)
        label = (f'Permaneceu: {name_a}' if is_stable else
                 f'Deixou de ser: {name_a} | Tornou-se: {name_b}')
        rows.append({
            'id': ids[(a, b)], 'inicial': a, 'final': b,
            'situacao': 'Permanência' if is_stable else 'Mudança',
            'legenda': label, 'classe_inicial_nome': name_a, 'classe_final_nome': name_b,
            'pixels': n, 'percentual': 100.0 * n / valid,
            'area_ha': None if hectare_pixel is None else n * hectare_pixel,
        })
    stable = sum(row['pixels'] for row in rows if row['situacao'] == 'Permanência')
    changed = valid - stable
    return {'validos': valid, 'invalidos': total_pixels - valid,
            'total': total_pixels, 'permanencias': stable, 'mudancas': changed,
            'pct_permanencia': 100.0 * stable / valid,
            'pct_mudanca': 100.0 * changed / valid,
            'area_valida_ha': None if hectare_pixel is None else valid * hectare_pixel,
            'ids': ids, 'linhas': rows}


def csv_code(value):
    v = float(value)
    return str(int(v)) if v.is_integer() else format(v, '.15g')


def write_monitoring_reports(transitions_path, matrix_path, text_path, summary, *,
                             title='', before_label='Inicial', after_label='Final',
                             crs='', resolution='', series=None, use_descriptive=True):
    """Relatório detalhado, matriz de contingência e síntese textual em UTF-8."""
    rows = summary['linhas']
    with open(transitions_path, 'w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream, delimiter=';')
        writer.writerow(['ID_TRANS', 'CLASSE_INICIAL', 'CLASSE_FINAL', 'SITUACAO',
                         'PIXELS', 'PCT_VALIDOS', 'AREA_HA',
                         'LEGENDA', 'DEIXOU_DE_SER', 'TORNOU_SE'])
        for row in rows:
            writer.writerow([row['id'], csv_code(row['inicial']), csv_code(row['final']),
                             row['situacao'], row['pixels'], f"{row['percentual']:.6f}",
                             '' if row['area_ha'] is None else f"{row['area_ha']:.6f}",
                             row['legenda'],
                             '' if row['situacao'] == 'Permanência' else row['classe_inicial_nome'],
                             '' if row['situacao'] == 'Permanência' else row['classe_final_nome']])
    # A matriz usa pixels como unidade. Linhas iniciais x colunas finais.
    initials = sorted({r['inicial'] for r in rows})
    finals = sorted({r['final'] for r in rows})
    values = {(r['inicial'], r['final']): r['pixels'] for r in rows}
    with open(matrix_path, 'w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream, delimiter=';')
        writer.writerow(['Inicial \\ Final'] + [csv_code(n) for n in finals] + ['TOTAL'])
        for a in initials:
            ns = [values.get((a, b), 0) for b in finals]
            writer.writerow([csv_code(a)] + ns + [sum(ns)])
        writer.writerow(['TOTAL'] + [sum(values.get((a, b), 0) for a in initials)
                                     for b in finals] + [summary['validos']])
    hectares = ('Indisponível (SRC não projetado ou sem unidades lineares válidas)'
                if summary['area_valida_ha'] is None else f"{summary['area_valida_ha']:.6f}")
    with open(text_path, 'w', encoding='utf-8', newline='\n') as stream:
        stream.write('VISTA SAGA PLUGIN — MONITORIA ESPACIAL\n')
        stream.write('=' * 65 + '\n')
        stream.write(f'Título: {title or "Monitoria de mudanças"}\n')
        stream.write(f'Período inicial: {before_label}\nPeríodo final: {after_label}\n')
        stream.write(f'SRC: {crs or "Não definido"}\nResolução: {resolution}\n\n')
        stream.write(f'Pixels totais: {summary["total"]}\n')
        stream.write(f'Pixels comuns válidos: {summary["validos"]}\n')
        stream.write(f'Pixels fora da análise (NoData): {summary["invalidos"]}\n')
        stream.write(f'Permanências (pixels): {summary["permanencias"]} '
                     f'({summary["pct_permanencia"]:.6f}% dos válidos)\n')
        stream.write(f'Mudanças (pixels): {summary["mudancas"]} '
                     f'({summary["pct_mudanca"]:.6f}% dos válidos)\n')
        stream.write(f'Área válida (ha): {hectares}\n\n')
        stream.write('TRANSIÇÕES — IDENTIFICADOR | INICIAL -> FINAL | PIXELS | % VÁLIDOS | HA\n')
        for row in rows:
            area = 'N/D' if row['area_ha'] is None else f"{row['area_ha']:.6f}"
            stream.write(f"{row['id']} | {csv_code(row['inicial'])} -> "
                         f"{csv_code(row['final'])} | {row['pixels']} | "
                         f"{row['percentual']:.6f} | {area} | {row['legenda'] if use_descriptive else str(csv_code(row['inicial'])) + ' -> ' + str(csv_code(row['final']))}\n")
        stream.write('\nNotas: as áreas derivam da área do pixel do raster inicial. '
                     'Não foi feita reprojeção nem reamostragem. Percentuais sobre pixels '
                     'válidos em ambos os períodos.\n')


def write_mk_csv(path, series):
    """CSV independente do mapa de transições; não cria valores p para duas datas."""
    with open(path, 'w', encoding='utf-8-sig', newline='') as stream:
        w = csv.writer(stream, delimiter=';')
        w.writerow(['STATUS', 'CLASSE', 'N_DATAS', 'ANOS', 'SERIE_PERCENTUAL',
                    'PIXELS_COMUNS', 'MK_S', 'MK_TAU', 'MK_Z', 'MK_P_BILATERAL',
                    'SEN_PONTOS_PERCENTUAIS_ANO', 'METODO', 'INTERPRETACAO',
                    'MK_Q_FDR_BH', 'SIGNIFICATIVO_FDR_5PCT'])
        if not series or series.get('status') != 'calculado':
            message = (series or {}).get('mensagem',
                'Não aplicável: são necessários pelo menos 5 mapas datados para Mann–Kendall.')
            w.writerow(['NAO_APLICAVEL', '', (series or {}).get('n', 2), '', '',
                        '', '', '', '', '', '', '', message, '', ''])
            return
        for row in series['linhas']:
            result = row['mk']
            w.writerow(['CALCULADO', csv_code(row['classe']), result['n'],
                        ','.join(map(str, row['anos'])),
                        ','.join(f'{v:.6f}' for v in row['pct']),
                        series['validos'], result['s'], f"{result['tau']:.8f}",
                        f"{result['z']:.8f}", f"{result['p']:.8f}",
                        f"{result['sen']:.8f}", result['metodo'], result['direcao'],
                        f"{result['q_fdr_bh']:.8f}",
                        'SIM' if result['significativo_fdr_5pct'] else 'NAO'])


def append_mk_txt(path, series):
    with open(path, 'a', encoding='utf-8') as out:
        out.write('\n\nANÁLISE TEMPORAL — MANN–KENDALL (bilateral)\n')
        if not series or series.get('status') != 'calculado':
            out.write((series or {}).get('mensagem',
                'Não aplicável: a comparação de dois mapas não permite Mann–Kendall.') + '\n')
            return
        out.write('Percentual de cada classe na máscara comum a todas as datas.\n')
        out.write(f"Anos: {', '.join(map(str, series['anos']))}. "
                  f"Pixels válidos em todas as datas: {series['validos']}.\n")
        for row in series['linhas']:
            mk = row['mk']
            out.write(f"Classe {csv_code(row['classe'])}: S={mk['s']}, "
                      f"tau={mk['tau']:.5f}, p={mk['p']:.6f}, "
                      f"Sen={mk['sen']:.6f} pontos percentuais/ano; "
                      f"q(FDR-BH)={mk['q_fdr_bh']:.6f}; "
                      f"{mk['direcao']}; "
                      f"significativo_FDR_5pct={'SIM' if mk['significativo_fdr_5pct'] else 'NÃO'}.\n")
        out.write('CUIDADO: Mann–Kendall testa tendência monotônica da proporção temporal de '
                  'cada classe, não valida a causalidade das transições. Autocorrelação temporal, '
                  'incerteza de classificação e múltiplos testes podem afetar a significância.\n')
