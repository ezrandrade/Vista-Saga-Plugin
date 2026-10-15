"""Integração entre o mapa de transições da Monitoria e vetores poligonizados.

A tabela de transições é gerada pelo próprio módulo de Monitoria; não reinterpreta
códigos de classe como rótulos. Área em hectares somente com unidades válidas.
"""
import csv
import json
import math
from pathlib import Path

from .rs2_format import RS2Error

REQUIRED = frozenset(('ID_TRANS', 'CLASSE_INICIAL', 'CLASSE_FINAL', 'SITUACAO',
                      'LEGENDA', 'DEIXOU_DE_SER', 'TORNOU_SE'))
META_KEY = 'VISTA_SAGA_MONITORIA_TRANSICOES'


def _check_row(raw, origin):
    try:
        code = int(raw['ID_TRANS'])
        if code < 1:
            raise ValueError('ID não positivo')
        initial = float(raw['CLASSE_INICIAL'])
        final = float(raw['CLASSE_FINAL'])
        if not math.isfinite(initial) or not math.isfinite(final):
            raise ValueError('classe não finita')
        situation = str(raw['SITUACAO']).strip()
        if situation not in ('Permanência', 'Mudança'):
            raise ValueError('situação não reconhecida')
        label = str(raw['LEGENDA']).strip()
        if not label:
            raise ValueError('legenda ausente')
        return code, dict(initial=initial, final=final, situacao=situation,
                          legenda=label, deixou=str(raw.get('DEIXOU_DE_SER') or ''),
                          tornou=str(raw.get('TORNOU_SE') or ''))
    except (KeyError, ValueError, TypeError) as exc:
        raise RS2Error(f'Dados de transição inválidos ({origin}): {exc}') from exc


def _parse_rows(rows, origin):
    mapping = {}
    for row in rows:
        code, data = _check_row(row, origin)
        if code in mapping:
            raise RS2Error(f'ID_TRANS duplicado ({code}) em {origin}.')
        mapping[code] = data
    if not mapping:
        raise RS2Error(f'Tabela de transições vazia: {origin}.')
    return mapping


def find_monitoring_transitions(tiff_path, band):
    """Lê o CSV associado, senão metadados internos do GeoTIFF, se presentes.

    Um CSV no mesmo diretório é a fonte preferencial; rótulos embutidos tornam
    os mapas autoexplicativos quando copiados para outro diretório.
    """
    sidecar = Path(tiff_path).with_suffix('')
    csv_path = Path(str(sidecar) + '_transicoes.csv')
    if csv_path.is_file():
        with csv_path.open('r', encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream, delimiter=';')
            if not reader.fieldnames or not REQUIRED.issubset(set(reader.fieldnames)):
                raise RS2Error(f'CSV de transições malformado: {csv_path.name}.')
            return _parse_rows(reader, csv_path.name)
    getter = getattr(band, 'GetMetadataItem', None)
    encoded = getter(META_KEY) if callable(getter) else None
    if encoded:
        try:
            rows = json.loads(encoded)
            if not isinstance(rows, list):
                raise ValueError('lista não encontrada')
        except (ValueError, TypeError) as exc:
            raise RS2Error('Metadados de transição inválidos no GeoTIFF.') from exc
        return _parse_rows(rows, 'GeoTIFF')
    return {}


def serialize_monitoring_rows(rows):
    """Registra informações suficientes para a vetorização autodescritiva."""
    data = []
    for row in rows:
        is_change = row['situacao'] == 'Mudança'
        data.append({
            'ID_TRANS': row['id'], 'CLASSE_INICIAL': row['inicial'],
            'CLASSE_FINAL': row['final'], 'SITUACAO': row['situacao'],
            'LEGENDA': row['legenda'],
            'DEIXOU_DE_SER': row['classe_inicial_nome'] if is_change else '',
            'TORNOU_SE': row['classe_final_nome'] if is_change else '',
        })
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))


def polygon_area_m2(geometry, srs):
    """Área planimétrica convertida a m²; geodésica apenas se suportada por OGR.

    Não interpretar graus quadrados nem unidades desconhecidas como metros.
    """
    if geometry is None or srs is None:
        return None
    if srs.IsProjected():
        units = float(srs.GetLinearUnits())
        if not math.isfinite(units) or units <= 0:
            return None
        area = abs(float(geometry.GetArea())) * units ** 2
    elif srs.IsGeographic() and callable(getattr(geometry, 'GetGeodesicArea', None)):
        try:
            area = abs(float(geometry.GetGeodesicArea()))
        except (RuntimeError, ValueError):
            return None
    else:
        return None
    return area if math.isfinite(area) else None


def monitoring_color(code, change):
    """Paleta próxima à utilizada pela Monitoria raster (sem depender do Qt)."""
    if not change:
        return '#B9C2C7'
    import colorsys
    rgb = colorsys.hsv_to_rgb(((int(code) * 53) % 360) / 360., 160 / 255., 205 / 255.)
    return '#' + ''.join(f'{round(255 * v):02X}' for v in rgb)
