"""Compara os resultados do Vista SAGA original no caso de teste do atrito com modelos candidatos.

Uso: python scripts/comparar_caso_atrito.py PASTA

PASTA contém teste_atrito.rs2 (gerado por scripts/gerar_caso_atrito.py) e as saídas do Vista SAGA:
voronoi_saga_simples.rs2, voronoi_saga_massa.rs2, voronoi_saga_atrito.rs2 e
voronoi_saga_massa_atrito.rs2. Os RS2 de saída não vão para o repositório (dados do autor).

Validação caixa-preta: mesma entrada, comparação célula a célula. A classe 0 ("Ponto") das saídas
marca as células dos polos e fica fora da contagem.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from geosaga.rs2_format import RS2Reader  # noqa: E402

# Arquivo de pontos: X:Y = coluna:linha CONTADAS A PARTIR DE 1 (confirmado em 17/11/2026: os polos
# do arquivo 12:15, 60:50 e 72:10 aparecem nas células 11:14, 59:49 e 71:9 contadas a partir de 0).
POLOS = [(11, 14, 9), (59, 49, 4), (71, 9, 1)]   # coluna, linha (a partir de 0), massa
NOTAS = [1, 1, 3, 5]                              # [ATRITOS], uma por classe, a partir da classe 0


def ler(pasta, nome):
    return np.array(list(RS2Reader(os.path.join(pasta, nome + '.rs2')).rows()))


def bresenham(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    e, x, y = dx + dy, x0, y0
    while True:
        pts.append((x, y))
        if x == x1 and y == y1:
            return pts
        e2 = 2 * e
        if e2 >= dy:
            e += dy
            x += sx
        if e2 <= dx:
            e += dx
            y += sy


def custo_vista_saga(nota, c0, l0, x1, y1):
    """Σ distância(polo, célula) × nota × passo (√2 na diagonal), ao longo da reta polo → célula."""
    pts = bresenham(c0, l0, x1, y1)
    s = 0.0
    for (pa, pb), (a, b) in zip(pts, pts[1:]):
        passo = math.sqrt(2) if (a != pa and b != pb) else 1.0
        s += math.hypot(a - c0, b - l0) * nota[b, a] * passo
    return s


def custo_legado_13(nota, c0, l0, x1, y1):
    """Plugin 1.3 (aproximação célula a célula): D × Σ(1 + C)."""
    pts = bresenham(c0, l0, x1, y1)
    return math.hypot(x1 - c0, y1 - l0) * sum(1 + nota[b, a] for a, b in pts)


def grade(fn, nota, h, w):
    return np.stack([[[fn(nota, c, l, x, y) for x in range(w)] for y in range(h)]
                     for c, l, _ in POLOS])


def acerto(pred, ref):
    m = ref != 0
    return 100 * (pred[m] == ref[m]).mean(), int((pred[m] != ref[m]).sum())


def main(pasta):
    atrito = ler(pasta, 'teste_atrito')
    h, w = atrito.shape
    nota = np.array(NOTAS, dtype=float)[atrito]
    um = np.ones_like(nota)
    ref = {k: ler(pasta, 'voronoi_saga_' + k) for k in ('simples', 'massa', 'atrito', 'massa_atrito')}
    for k, a in ref.items():
        polos = sorted((int(x), int(y)) for y, x in zip(*np.where(a == 0)))
        assert polos == sorted((c, l) for c, l, _ in POLOS), (k, polos)

    yy, xx = np.mgrid[0:h, 0:w]
    d = np.stack([np.hypot(xx - c, yy - l) for c, l, _ in POLOS])
    m = np.array([p[2] for p in POLOS], dtype=float)[:, None, None]
    vs = grade(custo_vista_saga, nota, h, w)
    vs1 = grade(custo_vista_saga, um, h, w)
    leg = grade(custo_legado_13, nota, h, w)
    linhas = [
        ('simples', 'min d', d),
        ('massa', 'min d/M (plugin 1.3)', d / m),
        ('massa', 'min d/√M = max M/d²', d / np.sqrt(m)),
        ('massa', 'Vista SAGA com notas 1, /M', vs1 / m),
        ('atrito', 'legado 1.3: D×Σ(1+C)', leg),
        ('atrito', 'Vista SAGA: Σ dist×nota×passo', vs),
        ('massa_atrito', 'legado 1.3: D×Σ(1+C)/M', leg / m),
        ('massa_atrito', 'Vista SAGA: Σ dist×nota×passo/M', vs / m),
        ('massa_atrito', 'Vista SAGA /√M (controle)', vs / np.sqrt(m)),
    ]
    print(f'{"saída":14s}{"modelo":36s}{"acerto":>9s}{"diverg.":>9s}')
    for k, nome, custo in linhas:
        p, n = acerto(custo.argmin(0) + 1, ref[k])
        print(f'{k:14s}{nome:36s}{p:8.2f}%{n:9d}')


if __name__ == '__main__':
    main(sys.argv[1])
