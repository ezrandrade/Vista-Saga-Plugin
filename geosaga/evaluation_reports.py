"""Relatórios auditáveis da Avaliação Espacial; independente de QGIS/GDAL.

Replica a lógica de 'Relatório de Combinações' do Vista SAGA, preservando
as notas contínuas do raster. A nota *inteira* serve apenas para agrupar as
combinações no relatório (arredondamento decimal convencional, half-up).
"""
import csv
import math
import os
from collections import Counter, defaultdict
from pathlib import Path

MAX_COMBINATIONS = 100_000


def final_note(score):
    if not math.isfinite(float(score)) or score < 0:
        raise ValueError('Nota final inválida para o relatório.')
    return int(math.floor(float(score) + .5))


def add_raster_combinations(counter, arrays, valid_mask, limit=MAX_COMBINATIONS):
    """Conta todas as combinações válidas em um bloco; sem ler novamente o raster."""
    import numpy as np
    if not np.any(valid_mask):
        return
    unique, counts = np.unique(np.stack([a[valid_mask] for a in arrays], axis=1),
                               axis=0, return_counts=True)
    for combo, count in zip(unique, counts):
        # Os critérios raster são códigos numéricos, não classes texto.
        key = tuple(format(float(value), '.15g') for value in combo)
        counter[key] += int(count)
    if len(counter) > limit:
        raise ValueError(f'O relatório ultrapassou {limit:,} combinações de classes. '
                         'Desative o relatório ou simplifique os mapas temáticos.')


def _score_combo(key, criteria):
    parts = []
    total, weights = 0.0, 0.0
    for code, criterion in zip(key, criteria):
        note = float(criterion['notes'][code])
        weight = float(criterion['weight'])
        product = note * weight / 100
        total += note * weight
        weights += weight
        parts.append((note, weight, product))
    return total / weights, parts


def _rows(combinations, criteria, unit_area_ha, unit_label, total_units, total_area_ha):
    # Valor: número de pixels/feições, soma da área em hectares (vetor).
    grouped = defaultdict(list)
    totals = Counter()
    totals_area = defaultdict(float)
    for key, pair in combinations.items():
        count, area = pair
        score, products = _score_combo(key, criteria)
        note = final_note(score)
        if unit_label == 'Pixels':
            area = None if unit_area_ha is None else count * unit_area_ha
        grouped[note].append((key, count, area, score, products))
        totals[note] += count
        if area is not None:
            totals_area[note] += area
    for note in sorted(grouped):
        for number, (key, count, area, score, products) in enumerate(
                sorted(grouped[note], key=lambda item: (-item[1], item[0])), start=1):
            pct_note = (100 * area / totals_area[note] if totals_area[note] else None) \
                if unit_label == 'Feições' else (100 * count / totals[note] if totals[note] else None)
            pct_map = (100 * area / total_area_ha if total_area_ha else None) if area is not None else (
                100 * count / total_units if total_units else None)
            for i, (code, (grade, weight, product)) in enumerate(zip(key, products)):
                labels = criteria[i].get('labels') or {}
                yield dict(nota_final=note, combinacao=number, criterio=criteria[i]['name'],
                           codigo=code, legenda=labels.get(code, code), nota=grade,
                           peso=weight, produto=product, nota_ponderada=score,
                           unidades=count, area_ha=area, pct_nota=pct_note,
                           pct_mapa=pct_map, last=(i == len(key) - 1))


def create_reports(txt_path, csv_path, *, combinations, criteria,
                   total_units, valid_units, area_per_unit_ha=None,
                   total_area_ha=None, title='', author='', crs='',
                   unit_label='Pixels', invalid_area_ha=None):
    """Grava versões TXT e/ou CSV com a mesma informação, sem arredondar o cálculo.

    combinations: {tupla_de_codigos: (quantidade, area_ha_ou_None)}
    totais de área para raster derivam da grade; para vetor são somas geométricas.
    """
    if not txt_path and not csv_path:
        return
    if total_area_ha is None and area_per_unit_ha is not None:
        total_area_ha = total_units * area_per_unit_ha
    rows = list(_rows(combinations, criteria, area_per_unit_ha,
                      unit_label, total_units, total_area_ha))
    totals = Counter()
    area_by_note = defaultdict(float)
    for row in rows:
        if row['last']:
            totals[row['nota_final']] += row['unidades']
            if row['area_ha'] is not None:
                area_by_note[row['nota_final']] += row['area_ha']
    if sum(totals.values()) != valid_units:
        raise ValueError('Inconsistência entre o mapa e o relatório de combinações.')
    meta = [
        ('Título', title), ('Autor', author), ('SRC', crs),
        ('Unidade contada', unit_label), ('Total de unidades', total_units),
        ('Unidades avaliadas', valid_units), ('Unidades sem avaliação', total_units-valid_units),
        ('Área total (ha)', total_area_ha),
        ('Área sem avaliação (ha)', invalid_area_ha),
        ('Área (ha)', 'Não calculada: SRC sem unidades lineares métricas'
         if total_area_ha is None else 'Calculada a partir da referência espacial'),
        ('Agrupamento de notas', 'Arredondamento half-up apenas no relatório; resultados espaciais mantêm valores originais'),
        ('Denominador de % Nota', 'Área por nota final, no modo vetorial; pixels por nota final, no modo raster'),
        ('Denominador de % área do mapa', 'Área total da saída, inclusive regiões sem nota quando presentes'),
    ]
    for i, criterion in enumerate(criteria, 1):
        meta.append((f'Critério {i} (nome)', criterion['name']))
        meta.append((f'Critério {i} (origem)', criterion.get('source', '')))
    header = ['NOTA_FINAL', 'COMBINACAO', 'CRITERIO', 'CODIGO', 'LEGENDA', 'NOTA',
              'PESO_PCT', 'PRODUTO', 'NOTA_PONDERADA', 'QUANTIDADE', 'AREA_HA',
              'PCT_NOTA', 'PCT_AREA_MAPA']
    def fmt(v):
        return '' if v is None else (format(v, '.12g') if isinstance(v, float) else str(v))
    created = []
    try:
        if csv_path:
            Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
            temp = str(csv_path) + '.vistasaga_tmp'
            with open(temp, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['VISTA SAGA PLUGIN — RELATÓRIO DE COMBINAÇÕES'])
                for key, value in meta:
                    writer.writerow([key, fmt(value)])
                writer.writerow([])
                writer.writerow(header)
                for row in rows:
                    writer.writerow([fmt(row[name]) for name in
                        ('nota_final','combinacao','criterio','codigo','legenda','nota',
                         'peso','produto','nota_ponderada','unidades','area_ha',
                         'pct_nota','pct_mapa')])
                writer.writerow([])
                writer.writerow(['CRITERIOS E REGRAS DE AVALIACAO'])
                writer.writerow(['CRITERIO', 'PESO_PCT', 'CODIGO', 'LEGENDA', 'NOTA', 'EXCLUIDA'])
                for criterion in criteria:
                    codes = set(criterion['notes']) | set(criterion.get('excluded', ()))
                    for code in sorted(codes):
                        writer.writerow([criterion['name'], fmt(criterion['weight']), code,
                                         (criterion.get('labels') or {}).get(code, code),
                                         fmt(criterion['notes'].get(code)),
                                         'SIM' if code in criterion.get('excluded', ()) else 'NÃO'])
                writer.writerow([])
                writer.writerow(['NOTA_FINAL', 'QUANTIDADE', 'AREA_HA', 'PCT_UNIDADES'])
                for note in sorted(totals):
                    writer.writerow([note, totals[note],
                                     fmt(area_by_note[note]) if total_area_ha is not None else '',
                                     fmt(100 * totals[note] / valid_units) if valid_units else ''])
            os.replace(temp, csv_path)
            created.append(csv_path)
        if txt_path:
            Path(txt_path).parent.mkdir(parents=True, exist_ok=True)
            temp = str(txt_path) + '.vistasaga_tmp'
            with open(temp, 'w', encoding='utf-8-sig', newline='\n') as f:
                f.write('Relatório de Combinações — Vista Saga Plugin\n\n')
                for key, value in meta:
                    f.write(f'{key}: {fmt(value)}\n')
                f.write('\n')
                active_note = None
                for row in rows:
                    if row['nota_final'] != active_note:
                        active_note = row['nota_final']
                        f.write(f'\nCombinações que originaram a nota final: {active_note:03d}\n')
                        f.write('Comb.\tCritério\tCódigo\tLegenda\tNota\tPeso (%)\tProduto\tNota ponderada\t'
                                f'{unit_label}\tÁrea (ha)\t% Nota\t% área do mapa final\n')
                    f.write('\t'.join(fmt(x) for x in (
                        row['combinacao'], row['criterio'], row['codigo'], row['legenda'],
                        row['nota'], row['peso'], row['produto'],
                        row['nota_ponderada'] if row['last'] else None,
                        row['unidades'] if row['last'] else None,
                        row['area_ha'] if row['last'] else None,
                        row['pct_nota'] if row['last'] else None,
                        row['pct_mapa'] if row['last'] else None)) + '\n')
                f.write('\nCRITERIOS E REGRAS DE AVALIACAO\n')
                f.write('Critério\tPeso (%)\tCódigo\tLegenda\tNota\tExcluída\n')
                for criterion in criteria:
                    codes = set(criterion['notes']) | set(criterion.get('excluded', ()))
                    for code in sorted(codes):
                        f.write('\t'.join(fmt(x) for x in (
                            criterion['name'], criterion['weight'], code,
                            (criterion.get('labels') or {}).get(code, code),
                            criterion['notes'].get(code),
                            'SIM' if code in criterion.get('excluded', ()) else 'NÃO')) + '\n')
                f.write('\nRESUMO POR NOTA FINAL\nNota\tQuantidade\tÁrea (ha)\t% das unidades avaliadas\n')
                for note in sorted(totals):
                    f.write(f'{note}\t{totals[note]}\t'
                            f'{fmt(area_by_note[note]) if total_area_ha is not None else ""}\t'
                            f'{fmt(100 * totals[note] / valid_units) if valid_units else ""}\n')
            os.replace(temp, txt_path)
            created.append(txt_path)
    finally:
        for path in (txt_path, csv_path):
            if path:
                try:
                    os.remove(str(path) + '.vistasaga_tmp')
                except FileNotFoundError:
                    pass
    return created
