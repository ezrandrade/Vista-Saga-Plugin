"""Núcleo independente da Avaliação Espacial vetorial por atributos.

Um registro = uma feição poligonal; não executa operações geométricas.
Zero é uma nota válida. Nulos ou categorias excluídas invalidam o registro,
assim como o NoData na avaliação raster. Sem redistribuição de pesos.
"""
import math
import numbers


def category_key(value):
    """Normaliza categorias numéricas inteiras sem alterar categorias textuais."""
    if value is None:
        return None
    if hasattr(value, 'isNull') and value.isNull():
        return None
    if isinstance(value, str):
        return value if value.strip() else None
    if isinstance(value, numbers.Real):
        if not math.isfinite(float(value)):
            return None
        return format(float(value), '.15g')
    value = str(value)
    return value if value.strip() else None


def category_sort(key):
    try:
        return (0, float(key), str(key))
    except (TypeError, ValueError, OverflowError):
        return (1, str(key).casefold(), str(key))


def validate_criteria(criteria, scale=10, tolerance=.011):
    """Retorna regras normalizadas; sem alteração das regras de origem."""
    if scale not in (10, 100):
        raise ValueError('A escala de notas deve ser 0–10 ou 0–100.')
    if not isinstance(criteria, list) or not criteria:
        raise ValueError('Adicione pelo menos um campo temático.')
    rules = []
    used = set()
    for criterion in criteria:
        if not isinstance(criterion, dict):
            raise ValueError('Critério inválido.')
        field = str(criterion.get('field', '')).strip()
        if not field or field.casefold() in used:
            raise ValueError(f'Campo ausente ou repetido: {field}.')
        used.add(field.casefold())
        try:
            weight = float(criterion.get('weight'))
        except (TypeError, ValueError) as exc:
            raise ValueError(f'{field}: informe um peso válido.') from exc
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError(f'{field}: o peso deve ser maior que zero.')
        categories = set(criterion.get('categories', []))
        notes = criterion.get('notes', {})
        excluded = set(criterion.get('excluded', []))
        if not isinstance(notes, dict) or not categories:
            raise ValueError(f'{field}: classes não identificadas.')
        if None in categories:
            categories.remove(None)  # Nulo não é categoria avaliável.
        if set(notes) & excluded:
            raise ValueError(f'{field}: classe com nota e exclusão simultâneas.')
        covered = set(notes) | excluded
        if categories != covered:
            missing = sorted(categories - covered, key=category_sort)
            unknown = sorted(covered - categories, key=category_sort)
            raise ValueError(f'{field}: classes sem tratamento {missing[:5]}; classes desconhecidas {unknown[:5]}.')
        prepared = {}
        for key, value in notes.items():
            try:
                score = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f'{field}: nota inválida para a classe {key}.') from exc
            if not math.isfinite(score) or not 0 <= score <= scale:
                raise ValueError(f'{field}: nota fora da escala (classe {key}).')
            prepared[key] = score
        rules.append({'field': field, 'weight': weight, 'notes': prepared, 'excluded': excluded})
    total = sum(rule['weight'] for rule in rules)
    if abs(total - 100) > tolerance:
        raise ValueError(f'A soma dos pesos deve ser 100%; valor atual: {total:.2f}%.')
    return rules


def evaluate_record(attributes, rules):
    """Retorna (nota, validade, motivo, notas_por_criterio).

    Registros sem dados/fora da avaliação mantêm sua geometria e obtêm nota
    nula; todos os critérios mantêm o denominador integral.
    """
    weighted = 0.0
    total = 0.0
    notes = []
    reason = None
    for rule in rules:
        field = rule['field']
        key = category_key(attributes.get(field))
        if key is None:
            reason = reason or f'Sem dado: {field}'
            notes.append(None)
            continue
        if key in rule['excluded']:
            reason = reason or f'Excluída: {field} = {key}'
            notes.append(None)
            continue
        if key not in rule['notes']:
            raise ValueError(f'{field}: categoria sem nota ou exclusão: {key}.')
        score = rule['notes'][key]
        notes.append(score)
        total += rule['weight']
        weighted += score * rule['weight']
    if reason:
        return None, 0, reason, notes
    return weighted / total, 1, '', notes
