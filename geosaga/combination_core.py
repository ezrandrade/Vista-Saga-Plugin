"""Regras independentes de QGIS para Combinação de Mapas categóricos."""
import csv
import math
from collections import Counter

MAX_COMBINATIONS = 100000


def normalized_code(value):
    """Chave estável: códigos numéricos inteiros ou categorias textuais."""
    if value is None or (hasattr(value, 'isNull') and value.isNull()):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(float(value)):
            return None
        number = float(value)
        if number.is_integer():
            return str(int(number))
        raise ValueError('Combinação requer classes discretas. Reclassifique valores contínuos.')
    string = str(value).strip()
    return string if string else None


def canonical_keys(keys):
    """Ordenação independente da ordem de leitura das feições ou blocos."""
    return sorted(keys, key=lambda tup: tuple((0, int(x)) if x.lstrip('-').isdigit()
                                                else (1, x.casefold()) for x in tup))


def combination_index(counts):
    if not counts:
        raise ValueError('Os mapas não possuem categorias válidas em uma área comum.')
    if len(counts) > MAX_COMBINATIONS:
        raise ValueError('Número excessivo de combinações (> 100.000). Reduza ou agrupe categorias.')
    return {key: idx for idx, key in enumerate(canonical_keys(counts), 1)}


def composition_rows(counts, names, *, pixel_area_m2=None, vector=False):
    """counts: tupla -> contagem de pixels ou superfície em metros quadrados.

    names: lista de dicionários de código (texto) -> legenda.
    """
    if not counts or len(names) != len(next(iter(counts))):
        raise ValueError('Critérios, legendas e combinações são inconsistentes.')
    ids = combination_index(counts)
    total = sum(counts.values())
    if not total or not math.isfinite(total):
        raise ValueError('Não foi encontrada área válida para combinação.')
    rows = []
    for key, idx in ids.items():
        units = counts[key]
        display = [str(legends.get(code) or f'Classe {code}') for legends, code in zip(names, key)]
        if vector:
            area_m2 = float(units)
            pixels = None
        else:
            pixels = int(units)
            area_m2 = None if pixel_area_m2 is None else pixels * pixel_area_m2
        rows.append({'id': idx, 'codes': key, 'labels': display,
                     'legend': ' | '.join(display), 'pixels': pixels,
                     'area_m2': area_m2,
                     'area_ha': None if area_m2 is None else area_m2 / 10000.0,
                     'percent': 100 * units / total})
    return rows


def write_combination_reports(csv_path, txt_path, rows, sources, *, mode, crs, area_method):
    """Arquivos independentes das geometrias, uma linha por combinação observada."""
    columns = ['ID_COMB', 'LEGENDA', 'PIXELS', 'AREA_M2', 'AREA_HA', 'PCT_AREA']
    for i in range(len(sources)):
        columns.extend((f'COD_{i+1:02d}', f'CLASSE_{i+1:02d}'))
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.writer(stream, delimiter=';')
        writer.writerow(columns)
        for row in rows:
            line = [row['id'], row['legend'], '' if row['pixels'] is None else row['pixels'],
                    '' if row['area_m2'] is None else f"{row['area_m2']:.6f}",
                    '' if row['area_ha'] is None else f"{row['area_ha']:.6f}",
                    f"{row['percent']:.6f}"]
            for code, label in zip(row['codes'], row['labels']):
                line.extend((code, label))
            writer.writerow(line)
    with open(txt_path, 'w', encoding='utf-8') as stream:
        stream.write('VISTA SAGA PLUGIN — COMBINAÇÃO DE MAPAS\n' + '='*54 + '\n')
        stream.write(f'Modalidade: {mode}\nSRC: {crs}\nCálculo de área: {area_method}\n')
        for i, source in enumerate(sources, 1):
            stream.write(f'Mapa {i:02d}: {source}\n')
        stream.write(f'Combinações observadas: {len(rows)}\n')
        stream.write(f'Soma percentual: {sum(r["percent"] for r in rows):.6f}%\n\n')
        for row in rows:
            area = 'N/D' if row['area_ha'] is None else f"{row['area_ha']:.6f} ha"
            count = 'N/D' if row['pixels'] is None else str(row['pixels'])
            stream.write(f"{row['id']:>5} | {row['legend']} | pixels={count} | "
                         f"{area} | {row['percent']:.6f}%\n")
        stream.write('\nSomente classes com presença conjunta válida foram consideradas. '
                     'Não foram aplicados pesos ou notas.\n')


def read_combination_legend(csv_path):
    """Reconstitui rótulos combinados do CSV do módulo para vetorização posterior."""
    result = {}
    with open(csv_path, newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream, delimiter=';')
        if not reader.fieldnames or not {'ID_COMB', 'LEGENDA'} <= set(reader.fieldnames):
            raise ValueError('CSV de combinações sem ID_COMB e LEGENDA.')
        for row in reader:
            code = int(row['ID_COMB'])
            if code < 1 or code in result or not row['LEGENDA']:
                raise ValueError('CSV de combinações inconsistente ou duplicado.')
            result[code] = row['LEGENDA']
    return result
