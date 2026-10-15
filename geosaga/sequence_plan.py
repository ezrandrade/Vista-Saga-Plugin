"""Regras independentes de QGIS/Qt para o sequenciamento cartográfico.

As funções não alteram as feições ou camadas fornecidas. O SRC/extensão comum
são geridos pelo renderizador QGIS na interface.
"""
import re


def extract_year(name):
    match = re.search(r'(?<!\d)((?:18|19|20|21)\d{2})(?!\d)', str(name))
    return match.group(1) if match else ''


def temporal_key(value):
    """Ordena anos numéricos antes de datas/textos (que usam ISO/alfanumérico)."""
    if hasattr(value, 'toPyDateTime'):
        value = value.toPyDateTime()
    elif hasattr(value, 'toPyDate'):
        value = value.toPyDate()
    if hasattr(value, 'isoformat'):
        return (1, value.isoformat())
    text = str(value).strip()
    if re.fullmatch(r'[+-]?\d+(?:\.0+)?', text):
        return (0, int(float(text)))
    return (1, text.casefold())


def temporal_frames(layer, field, values, cumulative=False, base_layers=(), max_frames=120):
    """Cria especificações de quadros, sem depender de objetos concretos QGIS.

    `base_layers` contém mapas estáticos para cada quadro; `layer` é o vetor
    temporal. A renderização calcula as feições por expressão em cópia temporária.
    """
    unique = {}
    for value in values:
        if value is None:
            continue
        if hasattr(value, 'isNull') and value.isNull():
            continue
        if not str(value).strip() or str(value).strip().upper() == 'NULL':
            continue
        key = (type(value).__name__, str(value))
        unique.setdefault(key, value)
        if len(unique) > max_frames:
            raise ValueError(f'O campo temporal possui mais de {max_frames} períodos distintos.')
    ordered = sorted(unique.values(), key=temporal_key)
    if len(ordered) < 2:
        raise ValueError('O campo temporal deve conter pelo menos dois períodos distintos.')
    frames = []
    for index, value in enumerate(ordered):
        frames.append({
            'layer': layer, 'layers': [layer] + list(base_layers), 'date': str(value),
            'temporal': {'source': layer, 'field': field,
                         'values': tuple(ordered[:index + 1] if cumulative else (value,))},
        })
    return frames


def safe_png_name(index, date):
    """Nome previsível, preservando a ordem e impedindo travessia de diretórios."""
    suffix = re.sub(r'[^\w.-]+', '_', str(date), flags=re.UNICODE).strip('._')[:48]
    return f'quadro_{index:03d}' + (f'_{suffix}' if suffix else '') + '.png'
