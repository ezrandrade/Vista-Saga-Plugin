"""Mann–Kendall, Voronoi, atrito composto, combinação, sequência e GIF — sem QGIS."""
import math
import struct
from itertools import product

import numpy as np
import pytest

from geosaga.monitoring_trends import mk_test
from geosaga.voronoi_core import Generator, assign_window, validate_generators
from geosaga.voronoi_friction_stack import parse_class_notes, combine_friction_arrays
from geosaga.combination_core import normalized_code, canonical_keys, combination_index
from geosaga.sequence_plan import extract_year, temporal_key
from geosaga.continuous_vector import class_edges, classify_array
from geosaga.gif_codec import encode_gif


# ------------------------------------------------------------ Mann–Kendall
def test_mk_exact_p_for_monotonic_series_n5():
    # Só 2 das 5! permutações atingem |S| = 10: p bilateral exato = 2/120.
    r = mk_test([2000, 2001, 2002, 2003, 2004], [1, 2, 3, 4, 5])
    assert r['s'] == 10 and r['metodo'] == 'exato_bilateral'
    assert r['p'] == pytest.approx(2 / 120)
    assert r['tau'] == pytest.approx(1.0) and r['direcao'] == 'crescimento'


def test_mk_normal_approximation_n8_and_sen_slope():
    years = list(range(2000, 2008))
    r = mk_test(years, [2 * y + 1 for y in range(8)])
    variance = 8 * 7 * 21 / 18
    z = 27 / math.sqrt(variance)
    assert r['metodo'] == 'normal_aproximado_bilateral'
    assert r['z'] == pytest.approx(z)
    assert r['p'] == pytest.approx(math.erfc(z / math.sqrt(2)))
    assert r['sen'] == pytest.approx(2.0)


def test_mk_constant_and_invalid():
    assert mk_test(range(2000, 2005), [3] * 5)['p'] == 1.0
    with pytest.raises(ValueError):
        mk_test([2000, 2001, 2002, 2003], [1, 2, 3, 4])
    with pytest.raises(ValueError):
        mk_test([2000, 2000, 2002, 2003, 2004], [1, 2, 3, 4, 5])


# ----------------------------------------------------------------- Voronoi
GT = (0.0, 1.0, 0.0, 10.0, 0.0, -1.0)


def brute_force(generators, mode):
    out = np.zeros((10, 10), dtype=np.int32)
    for row, col in product(range(10), range(10)):
        x, y = col + .5, 10 - (row + .5)
        best = None
        for g in generators:
            d2 = (x - g.x) ** 2 + (y - g.y) ** 2
            score = d2 / g.mass ** 2 if mode == 'mass' else d2
            if best is None or score < best[0]:
                best = (score, g.identifier)
        out[row, col] = best[1]
    return out


@pytest.mark.parametrize('mode', ['simple', 'mass'])
def test_voronoi_assignment_matches_brute_force(mode):
    gens = [Generator(1, 2.0, 2.0, 1.0), Generator(2, 8.0, 7.0, 3.0), Generator(3, 5.0, 9.5, 0.5)]
    labels = assign_window(gens, GT, 10, 0, 10, mode=mode)
    assert (labels == brute_force(gens, mode)).all()


def test_voronoi_window_offset_is_consistent():
    gens = [Generator(1, 2.0, 2.0), Generator(2, 8.0, 7.0)]
    full = assign_window(gens, GT, 10, 0, 10)
    assert (assign_window(gens, GT, 10, 4, 3) == full[4:7]).all()


def test_voronoi_rejects_duplicates_and_bad_mass():
    with pytest.raises(ValueError):
        validate_generators([Generator(1, 0, 0), Generator(1, 1, 1)])
    with pytest.raises(ValueError):
        validate_generators([Generator(1, 0, 0, 0.0)], weighted=True)


# ------------------------------------------------------- atrito composto
def test_parse_class_notes():
    assert parse_class_notes('1=2; 2=8') == {1.0: 2.0, 2.0: 8.0}
    assert parse_class_notes('') == {}
    for bad in ('1:2', '1=x', '1=-1', '1=2;1=3'):
        with pytest.raises(ValueError):
            parse_class_notes(bad)


def test_combine_friction_weighted_mean_and_nodata_barrier():
    a = np.array([[1.0, 2.0], [np.nan, 4.0]])
    b = np.array([[1, 2], [1, 2]], dtype=np.uint8)
    out = combine_friction_arrays([a, b], [3, 1], ['', '1=10;2=20'])
    assert out[0, 0] == pytest.approx((3 * 1 + 10) / 4)
    assert out[0, 1] == pytest.approx((3 * 2 + 20) / 4)
    assert math.isnan(out[1, 0])
    with pytest.raises(ValueError):
        combine_friction_arrays([a], [0])
    with pytest.raises(ValueError):
        combine_friction_arrays([np.array([[-1.0]])], [1])


# ---------------------------------------------------- combinação/sequência
def test_combination_codes_and_canonical_order():
    assert normalized_code(3.0) == '3' and normalized_code(' Mata ') == 'Mata'
    assert normalized_code(None) is None and normalized_code(float('nan')) is None
    with pytest.raises(ValueError):
        normalized_code(2.5)
    keys = [('10', 'b'), ('2', 'B'), ('2', 'a')]
    assert canonical_keys(keys) == [('2', 'a'), ('2', 'B'), ('10', 'b')]
    assert combination_index({k: 1 for k in keys})[('2', 'a')] == 1


def test_sequence_year_and_order():
    assert extract_year('uso_2015_final.tif') == '2015'
    assert extract_year('id12345') == ''
    assert sorted(['2010', 'b', '1999', 'A'], key=temporal_key) == ['1999', '2010', 'A', 'b']


def test_continuous_classes_include_maximum():
    edges = class_edges(0.0, 10.0, 5)
    codes = classify_array(np.array([0.0, 1.99, 2.0, 10.0, -1.0]), edges, nodata=-1.0)
    assert codes.tolist() == [1, 1, 2, 5, 0]


# --------------------------------------------------------------------- GIF
def test_gif_structure(tmp_path):
    w, h = 7, 5
    frames = [bytes([i * 60, 255 - i * 60, 30]) * (w * h) for i in range(3)]
    path = tmp_path / 'a.gif'
    encode_gif(path, frames, w, h, delay_cs=50)
    data = path.read_bytes()
    assert data[:6] == b'GIF89a' and data[-1:] == b';'
    assert struct.unpack('<HH', data[6:10]) == (w, h)
    assert data.count(b'NETSCAPE2.0') == 1
    assert data.count(b'\x21\xf9\x04') == 3          # um controle gráfico por quadro
    assert not (tmp_path / 'a.gif.part').exists()
    with pytest.raises(ValueError):
        encode_gif(path, frames, w + 1, h)
