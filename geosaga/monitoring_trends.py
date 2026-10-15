"""Séries temporais categóricas: Mann–Kendall, inclinação de Sen e ressalvas.

Duas datas descrevem mudança, mas NÃO fornecem um teste Mann–Kendall válido.
O teste é aplicado à porcentagem de área de cada classe numa máscara espacial
comum a TODAS as datas informadas (pelo menos cinco observações).
"""
from collections import Counter
from itertools import permutations
from math import erfc, sqrt, isfinite
from statistics import median

MIN_DATES = 5


def mk_test(years, values):
    """MK bilateral: p exato por permutação (n<=7) ou aproximação com correção de empates."""
    if len(years) != len(values) or len(years) < MIN_DATES:
        raise ValueError('Mann–Kendall requer pelo menos 5 datas com valores.')
    years = [int(y) for y in years]
    values = [float(v) for v in values]
    n = len(years)
    if any(not isfinite(v) for v in values) or any(a >= b for a, b in zip(years, years[1:])):
        raise ValueError('Os anos devem ser crescentes e os valores finitos.')

    def calc_s(items):
        return sum((items[j] > items[i]) - (items[j] < items[i])
                   for i in range(n) for j in range(i + 1, n))

    s = calc_s(values)
    ties = Counter(values)
    n0 = n*(n-1)//2
    t0 = sum(v*(v-1)//2 for v in ties.values())
    tau = s / sqrt(n0*(n0-t0)) if n0 > t0 else 0.0
    slopes = [(values[j] - values[i]) / (years[j] - years[i])
              for i in range(n) for j in range(i + 1, n)]
    sen = float(median(slopes))
    variance = (n*(n-1)*(2*n+5) -
                sum(v*(v-1)*(2*v+5) for v in ties.values())) / 18.0
    if variance <= 0:
        p, z, method = 1.0, 0.0, 'constante'
    elif n <= 7:
        # A permutação dos índices, inclusive os empatados, mantém o p exato
        # sob hipótese nula de intercambialidade temporal.
        total, extreme = 0, 0
        for perm in permutations(values):
            total += 1
            if abs(calc_s(perm)) >= abs(s):
                extreme += 1
        p = extreme / total
        z = ((s-1) / sqrt(variance) if s > 0 else
             (s+1) / sqrt(variance) if s < 0 else 0.0)
        method = 'exato_bilateral'
    else:
        z = ((s-1) / sqrt(variance) if s > 0 else
             (s+1) / sqrt(variance) if s < 0 else 0.0)
        p = erfc(abs(z) / sqrt(2.0))
        method = 'normal_aproximado_bilateral'
    return {'n': n, 's': int(s), 'tau': float(tau), 'z': float(z),
            'p': float(p), 'sen': sen, 'metodo': method,
            'direcao': 'crescimento' if s > 0 else 'redução' if s < 0 else 'sem tendência monotônica'}


def temporal_rows(years, class_counts, valid_total):
    """class_counts: lista de Counters, na ordem dos anos, na mesma área válida comum."""
    if not valid_total:
        raise ValueError('Não existem pixels válidos em todas as datas da série.')
    if len(years) != len(class_counts):
        raise ValueError('Anos e contagens não correspondem.')
    classes = sorted({cl for c in class_counts for cl in c})
    rows = []
    for cl in classes:
        values = [100.0 * item.get(cl, 0) / valid_total for item in class_counts]
        mk = mk_test(years, values) if len(years) >= MIN_DATES else None
        rows.append({'classe': float(cl), 'anos': list(years), 'pct': values, 'mk': mk})
    if rows and rows[0]['mk'] is not None:
        order = sorted(range(len(rows)), key=lambda i: rows[i]['mk']['p'])
        qvalues = [1.0] * len(rows)
        bound = 1.0
        for rank in range(len(order), 0, -1):
            i = order[rank-1]
            bound = min(bound, rows[i]['mk']['p'] * len(rows) / rank)
            qvalues[i] = bound
        for i, row in enumerate(rows):
            row['mk']['q_fdr_bh'] = qvalues[i]
            row['mk']['significativo_fdr_5pct'] = qvalues[i] < 0.05
    return rows
