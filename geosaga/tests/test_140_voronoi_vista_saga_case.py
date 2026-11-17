"""1.4.0: regressão com o caso sintético validado contra o Vista SAGA original (17/11/2026).

O mapa e os pontos são recriados aqui (scripts/gerar_caso_atrito.py), sem arquivos do Vista SAGA.
Contagens por polo no Vista SAGA (a célula do polo sai como "Ponto", por isso o plugin tem +1):
Simples 2010/1708/1079; Com Massa 2693/1592/512; Com Atrito 2291/1485/1021;
Com Massa e Atrito 2843/1505/449. Simples e Com Massa coincidem célula a célula; os modos com
atrito coincidem em 99,7% (diferenças só na fronteira entre regiões), e as contagens do plugin
ficam fixadas abaixo para detectar qualquer mudança involuntária do modelo.
"""
import unittest

import numpy as np

from geosaga.voronoi_core import Generator, assign_window
from geosaga.voronoi_friction import assign_friction_window

T = (500000., 10., 0., 8900600., 0., -10.)
# Arquivo de pontos do Vista SAGA: 12:15, 60:50 e 72:10 (coluna:linha contadas a partir de 1).
POLOS = [('Polo A', 9., 11, 14), ('Polo B', 4., 59, 49), ('Polo C', 1., 71, 9)]


def caso():
    classes = np.full((60, 80), 1)
    classes[:, 40:] = 2
    classes[:, 30:40] = 3
    classes[25:35, 30:40] = 1
    classes[5:20, 55:70] = 3
    notas = np.array([1., 1., 3., 5.])[classes]
    pontos = [Generator(i + 1, T[0] + c * 10 + 5, T[3] - l * 10 - 5, m, n)
              for i, (n, m, c, l) in enumerate(POLOS)]
    return notas, pontos


def contagens(labels):
    return [int((labels == i).sum()) for i in (1, 2, 3)]


class VistaSagaCase140Tests(unittest.TestCase):
    def setUp(self):
        self.notas, self.pontos = caso()

    def test_simple_matches_vista_saga(self):
        self.assertEqual(contagens(assign_window(self.pontos, T, 80, 0, 60)), [2011, 1709, 1080])

    def test_mass_is_m_over_d_squared_like_vista_saga(self):
        labels = assign_window(self.pontos, T, 80, 0, 60, mode='mass')
        self.assertEqual(contagens(labels), [2694, 1593, 513])
        # O modelo antigo (M/d) dava ao Polo C (M = 1) só uma fração dessa área.
        yy, xx = np.mgrid[0:60, 0:80]
        d = np.stack([np.hypot(xx - c, yy - l) for _, _, c, l in POLOS])
        old = (d / np.array([9., 4., 1.])[:, None, None]).argmin(0) + 1
        self.assertLess(int((old == 3).sum()), 200)

    def test_friction_counts_fixed(self):
        labels = assign_friction_window(self.pontos, self.notas, T, 0, 60)
        self.assertEqual(contagens(labels), [2297, 1485, 1018])

    def test_mass_friction_counts_fixed(self):
        labels = assign_friction_window(self.pontos, self.notas, T, 0, 60, mass_weighted=True)
        self.assertEqual(contagens(labels), [2849, 1506, 445])

    def test_uniform_rating_one_reproduces_mass_law_closely(self):
        # Com nota 1 em toda parte, o atrito com massa aproxima M/d² (A ≈ d²/2).
        uniform = np.ones_like(self.notas)
        friction = assign_friction_window(self.pontos, uniform, T, 0, 60, mass_weighted=True)
        mass = assign_window(self.pontos, T, 80, 0, 60, mode='mass')
        self.assertGreater(float((friction == mass).mean()), 0.99)


if __name__ == '__main__':
    unittest.main()
