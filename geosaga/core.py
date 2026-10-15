"""Núcleo matemático desacoplado do QGIS, testável com NumPy."""
import json
import math
import numpy as np

NODATA_OUT = -9999.0


def valid_mask(data, nodata):
    valid = np.isfinite(data)
    if nodata is not None:
        if math.isnan(float(nodata)):
            valid &= ~np.isnan(data)
        else:
            valid &= data != nodata
    return valid


def parse_config(json_text, layer_count):
    """Configuração v0.1 e v0.2: notas discretas, pesos e classes bloqueadas."""
    try:
        obj = json.loads(json_text) if isinstance(json_text, str) else json_text
    except (ValueError, TypeError) as exc:
        raise ValueError('Configuração inválida: informe JSON válido.') from exc
    if not isinstance(obj, dict) or not isinstance(obj.get('camadas'), list):
        raise ValueError('É necessária uma lista "camadas".')
    rules = obj['camadas']
    if len(rules) != layer_count:
        raise ValueError(f'Foram selecionados {layer_count} rasters, mas há {len(rules)} regras.')
    scale = obj.get('escala', 10)
    if scale not in (10, 100):
        raise ValueError('A escala de notas deve ser 10 ou 100.')
    parsed = []
    for i, item in enumerate(rules, 1):
        if not isinstance(item, dict):
            raise ValueError(f'Camada {i}: regra inválida.')
        try:
            weight = float(item['peso'])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'Camada {i}: peso numérico obrigatório.') from exc
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError(f'Camada {i}: peso deve ser positivo e finito.')
        scores = item.get('notas')
        blocked = item.get('bloqueadas', [])
        if not isinstance(scores, dict) or not isinstance(blocked, list):
            raise ValueError(f'Camada {i}: notas/bloqueadas inválidas.')
        clean = {}
        for raw_class, raw_score in scores.items():
            try:
                k, v = float(raw_class), float(raw_score)
            except (ValueError, TypeError) as exc:
                raise ValueError(f'Camada {i}: código/nota não numérico.') from exc
            if not math.isfinite(k) or not math.isfinite(v) or not 0 <= v <= scale:
                raise ValueError(f'Camada {i}: códigos finitos e notas entre 0 e {scale}.')
            if k in clean:
                raise ValueError(f'Camada {i}: classe duplicada ({k}).')
            clean[k] = v
        blocked_clean = set()
        for raw_code in blocked:
            try:
                v = float(raw_code)
            except (ValueError, TypeError) as exc:
                raise ValueError(f'Camada {i}: classe bloqueada não numérica.') from exc
            if not math.isfinite(v):
                raise ValueError(f'Camada {i}: classe bloqueada não finita.')
            blocked_clean.add(v)
        if not clean and not blocked_clean:
            raise ValueError(f'Camada {i}: atribua notas ou bloqueie as classes.')
        if any(code in blocked_clean for code in clean):
            raise ValueError(f'Camada {i}: uma classe não pode ter nota e estar bloqueada.')
        parsed.append((weight, clean, blocked_clean))
    return parsed


def evaluate_block(arrays, nodatas, rules):
    """Média ponderada: NoData e classes bloqueadas propagam NoData.

    Compatível também com tuplas legadas (peso, notas) da versão 0.1.
    """
    if len(arrays) != len(nodatas) or len(arrays) != len(rules):
        raise ValueError('Rasters, nodata e regras devem ter mesmo comprimento.')
    if not arrays or any(a.shape != arrays[0].shape for a in arrays):
        raise ValueError('As dimensões dos blocos devem ser iguais.')
    combined = np.zeros(arrays[0].shape, dtype=np.float64)
    good = np.ones(arrays[0].shape, dtype=bool)
    weight_total = sum(rule[0] for rule in rules)
    if weight_total <= 0:
        raise ValueError('A soma dos pesos deve ser maior que zero.')
    for i, (arr, nd, rule) in enumerate(zip(arrays, nodatas, rules), 1):
        weight, notes = rule[:2]
        blocked = rule[2] if len(rule) > 2 else set()
        valid = valid_mask(arr, nd)
        graded = np.zeros(arr.shape, dtype=np.float64)
        assigned = np.zeros(arr.shape, dtype=bool)
        blocked_mask = np.zeros(arr.shape, dtype=bool)
        for code in blocked:
            blocked_mask |= valid & (arr == code)
        for code, score in notes.items():
            hit = valid & (arr == code)
            graded[hit] = score
            assigned |= hit
        unknown = valid & ~assigned & ~blocked_mask
        if unknown.any():
            found = np.unique(arr[unknown])[:8].tolist()
            raise ValueError(f'Raster {i}: existem classes sem notas ou bloqueio: {found}.')
        combined += weight * graded
        good &= valid & ~blocked_mask
    out = np.full(arrays[0].shape, NODATA_OUT, dtype=np.float32)
    out[good] = (combined[good] / weight_total).astype(np.float32)
    return out


def transition_counts(a, b, nodata_a, nodata_b):
    """Pares de classes e contagens em pixels válidos de ambos os mapas."""
    valid = valid_mask(a, nodata_a) & valid_mask(b, nodata_b)
    if not valid.any():
        return {}, valid
    pairs, counts = np.unique(np.column_stack((a[valid], b[valid])), axis=0, return_counts=True)
    return {(float(pair[0]), float(pair[1])): int(count) for pair, count in zip(pairs, counts)}, valid


def pixel_area_ha(geotransform, projected, metres_per_unit=1.0):
    """Área constante para SRC projetado; não calcula área planar em graus."""
    if not projected:
        return None
    g = geotransform
    area_native = abs(g[1] * g[5] - g[2] * g[4])
    if area_native <= 0 or metres_per_unit <= 0:
        raise ValueError('Transformação afim ou unidade linear inválida.')
    return area_native * metres_per_unit ** 2 / 10000.0
