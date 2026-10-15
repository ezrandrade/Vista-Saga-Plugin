"""Estatísticas e relatórios da Assinatura Espacial (independentes de PyQGIS).

Percentuais referem-se à área/pixels tematicamente cobertos em cada polígono;
áreas não cobertas e NoData não entram no denominador da distribuição.
"""
import csv
import math
from collections import defaultdict


def category_code(value):
    """Codifica números sem perder o zero e conserva categorias textuais."""
    if value is None or (hasattr(value, 'isNull') and value.isNull()):
        return None
    if isinstance(value, str):
        return value.strip() or None
    try:
        n = float(value)
    except (ValueError, TypeError):
        return str(value)
    if not math.isfinite(n):
        return None
    return str(int(n)) if n.is_integer() else format(n, '.15g')


def summarize_area(area_id, area_name, values, *, kind, pixel_ha=None,
                   thematic_names=None, area_aoi_ha=None):
    """values: {code: count (raster) ou área_ha (vetorial)}.

    Raster sem SRC métrico: pixels e percentuais disponíveis, ha = None.
    Vetor: unidades em ha calculadas geometricamente pelo mecanismo de área.
    """
    if kind not in ('raster', 'vector'):
        raise ValueError('Tipo de assinatura não reconhecido.')
    counts = defaultdict(float)
    for k, v in values.items():
        code = category_code(k)
        if code is None or not math.isfinite(float(v)) or float(v) < 0:
            raise ValueError('Categoria ou contagem inválida.')
        counts[code] += float(v)
    counts = {k: v for k, v in counts.items() if v > 0}
    total = sum(counts.values())
    if total <= 0:
        return [], dict(id=str(area_id), name=str(area_name), classes=0, dominant='',
                        aoi_ha=area_aoi_ha, analyzed_ha=0.0 if kind == 'vector' or pixel_ha is not None else None,
                        coverage_pct=0.0 if area_aoi_ha and (kind == 'vector' or pixel_ha is not None) else None)
    rows = []
    for key in sorted(counts, key=lambda x: (0, float(x)) if _numeric(x) else (1, x)):
        value = counts[key]
        units = int(value) if kind == 'raster' else None
        area = (value * pixel_ha if pixel_ha is not None else None) if kind == 'raster' else value
        rows.append(dict(area_id=str(area_id), area_name=str(area_name), code=key,
                         label=str((thematic_names or {}).get(key, key)),
                         pixels=units, area_ha=area,
                         percentage=100.0 * value / total))
    dominant = max(rows, key=lambda r: (r['percentage'], r['code']))['label']
    analyzed_ha = total * pixel_ha if kind == 'raster' and pixel_ha is not None else (total if kind == 'vector' else None)
    coverage = 100.0 * analyzed_ha / area_aoi_ha if area_aoi_ha and analyzed_ha is not None else None
    return rows, dict(id=str(area_id), name=str(area_name), classes=len(rows),
                      dominant=dominant, aoi_ha=area_aoi_ha,
                      analyzed_ha=analyzed_ha, coverage_pct=coverage)


def _numeric(value):
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def _decimal(value, places=6):
    return '' if value is None else f'{float(value):.{places}f}'


def write_signature_reports(csv_path, txt_path, summaries, rows, *, title='',
                            theme='', mode='', crs='', area_source=''):
    """CSV UTF-8 BOM com separador ;, TXT com parâmetros e distribuição por área."""
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        cols = ['ID_AREA', 'NOME_AREA', 'CODIGO', 'CLASSE', 'PIXELS',
                'AREA_HA', 'PCT_CLASSE', 'AREA_AOI_HA', 'AREA_ANALISADA_HA', 'COBERTURA_PCT']
        if mode == 'vector':
            cols.extend(['AREA_CONFLITO_HA', 'PCT_CONFLITO_AOI'])
        writer.writerow(cols)
        byid = {s['id']: s for s in summaries}
        for r in rows:
            info = byid[r['area_id']]
            record = [r['area_id'], r['area_name'], r['code'], r['label'],
                      r['pixels'] if r['pixels'] is not None else '', _decimal(r['area_ha']),
                      _decimal(r['percentage']), _decimal(info['aoi_ha']),
                      _decimal(info['analyzed_ha']), _decimal(info['coverage_pct'])]
            if mode == 'vector':
                record.extend([_decimal(info.get('conflict_ha')),
                               _decimal(info.get('conflict_pct'))])
            writer.writerow(record)
        if mode == 'vector':
            # Se todas as classes estão em conflito, registrar área ambígua
            # mesmo sem nenhuma classe válida para a unidade analisada.
            reported = {r['area_id'] for r in rows}
            for info in summaries:
                if info['id'] not in reported:
                    writer.writerow([info['id'], info['name'], '', 'SEM CLASSE VÁLIDA',
                                     '', '', '', _decimal(info.get('aoi_ha')),
                                     _decimal(info.get('analyzed_ha')),
                                     _decimal(info.get('coverage_pct')),
                                     _decimal(info.get('conflict_ha')),
                                     _decimal(info.get('conflict_pct'))])
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('VISTA SAGA PLUGIN — RELATÓRIO DE ASSINATURA ESPACIAL\n')
        f.write(f'Título: {title}\nModalidade: {mode}\nMapa temático: {theme}\n')
        f.write(f'Áreas de análise: {area_source}\nSRC: {crs}\n')
        f.write('Método: distribuição de classes por área; pixels por centro (raster), '
                'interseção geométrica (vetor).\n')
        f.write('Percentuais das classes: denominador = total tematicamente válido na respectiva área.\n')
        f.write('Áreas em ha: conforme SRC e método geodésico/planimétrico; vazias quando indisponíveis.\n')
        if mode == 'vector':
            f.write('Na modalidade vetorial, polígonos da mesma classe são dissolvidos; '
                    'interseções entre classes diferentes são excluídas se esta opção for escolhida, '
                    'e suas áreas são informadas separadamente.\n')
        f.write('Polígonos de análise distintos são resumidos separadamente; se se sobrepõem, '
                'seus totais não devem ser somados como área única.\n')
        by_id = defaultdict(list)
        for r in rows:
            by_id[r['area_id']].append(r)
        for s in summaries:
            f.write('\n' + '-' * 65 + '\n')
            f.write(f"Área: {s['name']} (ID: {s['id']})\n")
            f.write(f"Área do polígono (ha): {_decimal(s['aoi_ha']) or 'Indisponível'}\n")
            f.write(f"Área temática válida (ha): {_decimal(s['analyzed_ha']) or 'Indisponível'}\n")
            f.write(f"Cobertura (%): {_decimal(s['coverage_pct']) or 'Indisponível'}\n")
            if s.get('conflict_ha') is not None:
                f.write(f"Área ambígua por conflito de classes (ha): {_decimal(s['conflict_ha'])}\n")
                f.write(f"Conflito relativo à área de análise (%): {_decimal(s.get('conflict_pct'))}\n")
            f.write(f"Classes identificadas: {s['classes']}\nPredominante: {s['dominant'] or 'Sem cobertura válida'}\n")
            f.write('Código; Classe; Pixels; Área (ha); % da área temática válida\n')
            for r in by_id[s['id']]:
                f.write(f"{r['code']}; {r['label']}; "
                        f"{r['pixels'] if r['pixels'] is not None else ''}; "
                        f"{_decimal(r['area_ha'])}; {_decimal(r['percentage'])}\n")
