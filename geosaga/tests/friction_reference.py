"""Referência escalar (Python puro) do atrito do Vista SAGA, para conferir o motor vetorizado.

Mesma reta de Bresenham e mesma soma da validação de 17/11/2026 (scripts/comparar_caso_atrito.py).
"""
import math
import numpy as np


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


def path_cost(raster, c0, l0, c1, l1, px=1.0, py=1.0):
    """Σ d(polo, célula) × nota × passo; infinito se a reta cruza NoData."""
    pts = bresenham(c0, l0, c1, l1)
    total = 0.0
    for (pa, pb), (a, b) in zip(pts, pts[1:]):
        value = raster[b, a]
        if not np.isfinite(value):
            return math.inf
        step = math.hypot(px, py) if (a != pa and b != pb) else (px if a != pa else py)
        total += math.hypot((a - c0) * px, (b - l0) * py) * value * step
    return total


def reference(generators, raster, t, *, weighted=False):
    """Compara todos os polos em todas as células, sem poda (primeiro polo vence empates)."""
    height, width = raster.shape
    px, py = abs(t[1]), abs(t[5])
    poles = [(math.floor((p.x - t[0]) / t[1]), math.floor((p.y - t[3]) / t[5])) for p in generators]
    out = np.zeros((height, width), dtype=np.int32)
    for row in range(height):
        for col in range(width):
            if not np.isfinite(raster[row, col]):
                continue
            best, choice = math.inf, 0
            for p, (c0, l0) in zip(generators, poles):
                score = path_cost(raster, c0, l0, col, row, px, py) / (p.mass if weighted else 1.0)
                if score < best:
                    best, choice = score, p.identifier
            out[row, col] = choice
    for p, (c0, l0) in reversed(list(zip(generators, poles))):
        out[l0, c0] = p.identifier
    return out
