"""Agrupamento e relatórios da Monitoria vetorial, sem dependência de QGIS.

Uma transição é uma combinação ordenada (classe em T0, classe em T1).
Áreas são somadas por geometria de interseção; feições nunca equivalem a pixels.
"""
import csv
import math
from collections import defaultdict


def transition_identity(initial_code, final_code, initial_name=None, final_name=None):
    """Igualdade temática por nomes explícitos, ou por códigos sem nomes.

    Com legendas em somente um dos períodos, não se infere equivalência:
    somente os códigos são comparados e o relatório assinala a limitação.
    """
    named = bool(initial_name and str(initial_name).strip() and
                 final_name and str(final_name).strip())
    if named:
        return str(initial_name).strip().casefold() == str(final_name).strip().casefold()
    return str(initial_code).strip() == str(final_code).strip()


def make_transition(initial, final, initial_name='', final_name=''):
    initial = str(initial).strip()
    final = str(final).strip()
    if not initial or not final:
        raise ValueError('A transição precisa ter duas classes válidas.')
    ni = str(initial_name or '').strip() or f'Classe {initial}'
    nf = str(final_name or '').strip() or f'Classe {final}'
    # Somente rótulos explícitos dos DOIS mapas comprovam identidade temática.
    named_i = str(initial_name or '').strip()
    named_f = str(final_name or '').strip()
    unchanged = transition_identity(initial, final, named_i, named_f)
    return {
        'codigo_inicial': initial, 'codigo_final': final,
        'classe_inicial': ni, 'classe_final': nf,
        'situacao': 'Permanência' if unchanged else 'Mudança',
        'legenda': f'Permaneceu: {ni}' if unchanged else f'Deixou de ser: {ni} | Tornou-se: {nf}',
        'deixou_ser': '' if unchanged else ni,
        'tornou_se': '' if unchanged else nf,
        'comparacao': 'NOMES' if named_i and named_f else 'CODIGOS',
    }


def aggregate_transitions(features):
    """Consolida tuplas (id de transição, dicionário da transição, área_m2).

    Calcula percentuais sobre área comum válida dos dois mapas. Sem SRC
    definido não se deve chamar a função com áreas não métricas.
    """
    result = {}
    for _, item, area in features:
        if not math.isfinite(area) or area < 0:
            raise ValueError('Área vetorial negativa ou não finita.')
        key = (item['codigo_inicial'], item['codigo_final'],
               item['classe_inicial'], item['classe_final'])
        if key not in result:
            result[key] = dict(item, feicoes=0, area_m2=0.0)
        result[key]['feicoes'] += 1
        result[key]['area_m2'] += area
    if not result:
        raise ValueError('A interseção não produziu feições válidas para monitoria.')
    area_total = sum(r['area_m2'] for r in result.values())
    if area_total <= 0:
        raise ValueError('Não há área positiva na interseção dos mapas.')
    rows = []
    for number, key in enumerate(sorted(result, key=lambda x: tuple(str(z).casefold() for z in x)), 1):
        r = result[key]
        r['id'] = number
        r['area_ha'] = r['area_m2'] / 10000.0
        r['pct_area'] = 100 * r['area_m2'] / area_total
        rows.append(r)
    stable = sum(row['area_m2'] for row in rows if row['situacao'] == 'Permanência')
    return {'linhas': rows, 'area_total_m2': area_total, 'area_total_ha': area_total / 10000.0,
            'area_permanencia_ha': stable / 10000.0,
            'area_mudanca_ha': (area_total - stable) / 10000.0,
            'pct_permanencia': 100 * stable / area_total,
            'pct_mudanca': 100 * (area_total - stable) / area_total,
            'feicoes': sum(r['feicoes'] for r in rows)}


def write_reports(csv_path, matrix_path, txt_path, summary, *, title='', initial='', final='',
                  crs='', input_sources=(), excluded=()):
    rows = summary['linhas']
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['ID_TRANS', 'COD_INI', 'COD_FIM', 'NOME_INI', 'NOME_FIM',
                         'SITUACAO', 'LEGENDA', 'FEICOES', 'AREA_M2', 'AREA_HA', 'PCT_AREA', 'COMPARACAO'])
        for r in rows:
            writer.writerow([r['id'], r['codigo_inicial'], r['codigo_final'],
                             r['classe_inicial'], r['classe_final'], r['situacao'],
                             r['legenda'], r['feicoes'], f"{r['area_m2']:.6f}",
                             f"{r['area_ha']:.6f}", f"{r['pct_area']:.6f}", r['comparacao']])
    starts = sorted({r['codigo_inicial'] for r in rows})
    ends = sorted({r['codigo_final'] for r in rows})
    lookup = defaultdict(float)
    for r in rows:
        lookup[(r['codigo_inicial'], r['codigo_final'])] += r['area_ha']
    with open(matrix_path, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Inicial \\ Final (ha)'] + ends + ['TOTAL_HA'])
        for a in starts:
            nums = [lookup[(a, b)] for b in ends]
            writer.writerow([a] + [f'{v:.6f}' for v in nums] + [f'{sum(nums):.6f}'])
        writer.writerow(['TOTAL_HA'] + [f'{sum(lookup[(a,b)] for a in starts):.6f}' for b in ends]
                        + [f"{summary['area_total_ha']:.6f}"])
    with open(txt_path, 'w', encoding='utf-8', newline='\n') as file:
        file.write('VISTA SAGA PLUGIN — MONITORIA VETORIAL DIRETA\n' + '=' * 60 + '\n')
        file.write(f'Título: {title or "Monitoria vetorial"}\nPeríodo inicial: {initial}\n'
                   f'Período final: {final}\nSRC: {crs}\n')
        for source in input_sources:
            file.write(f'Camada de entrada: {source}\n')
        file.write(f"Área comum analisada (ha): {summary['area_total_ha']:.6f}\n"
                   f"Área de permanência (ha): {summary['area_permanencia_ha']:.6f} "
                   f"({summary['pct_permanencia']:.4f}%)\n"
                   f"Área de mudança (ha): {summary['area_mudanca_ha']:.6f} "
                   f"({summary['pct_mudanca']:.4f}%)\n\n")
        for row in rows:
            file.write(f"{row['id']} | {row['legenda']} | {row['area_ha']:.6f} ha | "
                       f"{row['pct_area']:.4f}% | {row['feicoes']} polígonos\n")
        file.write('\nNotas metodológicas:\n- Interseção de duas camadas poligonais; '
                   'fora da cobertura comum não se inferem mudanças.\n'
                   '- Percentuais calculados por área, não por quantidade de feições.\n'
                   '- A matriz representa hectares, não contagens de pixels.\n'
                   '- Sem rótulos temáticos nos dois períodos, a permanência usa igualdade '
                   'dos códigos; confira a equivalência das classes.\n'
                   '- O procedimento não executa Mann–Kendall para apenas duas datas.\n'
                   '- Sobreposições internas de feições em uma mesma camada podem duplicar '
                   'áreas; verificar previamente a topologia dos mapas.\n')
        if excluded:
            file.write('- Exclusões: ' + ', '.join(map(str, excluded)) + '\n')
