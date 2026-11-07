"""Núcleo numérico da Avaliação/Monitoria (core.py) — sem QGIS."""
import json
import math

import numpy as np
import pytest

from geosaga import core


def test_valid_mask_handles_nan_and_float32_nodata():
    data = np.array([np.nan, -9999.9, 1, 2], dtype=np.float32)
    assert core.valid_mask(data, -9999.9).tolist() == [False, False, True, True]
    assert core.valid_mask(data, float('nan')).tolist() == [False, True, True, True]
    assert core.valid_mask(np.array([0, 1, 255], dtype=np.uint8), 255).tolist() == [True, True, False]
    assert core.valid_mask(np.array([0, 1]), None).tolist() == [True, True]


def test_parse_config_accepts_text_and_dict():
    cfg = {'camadas': [{'peso': 2, 'notas': {'1': 10, '2': 0}, 'bloqueadas': [3]}]}
    for value in (cfg, json.dumps(cfg)):
        (weight, notes, blocked), = core.parse_config(value, 1)
        assert weight == 2 and notes == {1.0: 10.0, 2.0: 0.0} and blocked == {3.0}


@pytest.mark.parametrize('cfg, count, fragment', [
    ('não é json', 1, 'JSON'),
    ({'x': 1}, 1, 'camadas'),
    ({'camadas': [{'peso': 1, 'notas': {'1': 5}}]}, 2, 'regras'),
    ({'camadas': [{'peso': 0, 'notas': {'1': 5}}]}, 1, 'positivo'),
    ({'camadas': [{'peso': float('inf'), 'notas': {'1': 5}}]}, 1, 'positivo'),
    ({'camadas': [{'peso': 1, 'notas': {'1': 11}}]}, 1, 'notas entre 0 e 10'),
    ({'camadas': [{'peso': 1, 'notas': {'1': 5}, 'bloqueadas': [1]}]}, 1, 'bloqueada'),
    ({'camadas': [{'peso': 1, 'notas': {'1': 5}}], 'escala': 7}, 1, 'escala'),
])
def test_parse_config_rejects_invalid(cfg, count, fragment):
    with pytest.raises(ValueError, match=fragment):
        core.parse_config(cfg, count)


def test_evaluate_block_weighted_mean_and_nodata():
    a = np.array([[1, 2], [3, 0]], dtype=np.uint8)
    b = np.array([[1, 1], [2, 2]], dtype=np.uint8)
    rules = core.parse_config({'camadas': [
        {'peso': 60, 'notas': {'1': 10, '2': 5}, 'bloqueadas': [3]},
        {'peso': 40, 'notas': {'1': 0, '2': 10}}]}, 2)
    out = core.evaluate_block([a, b], [0, None], rules)
    assert out.dtype == np.float32
    assert out[0, 0] == pytest.approx(6.0)          # 0.6*10 + 0.4*0
    assert out[0, 1] == pytest.approx(3.0)          # 0.6*5 + 0.4*0
    assert out[1, 0] == core.NODATA_OUT              # classe bloqueada
    assert out[1, 1] == core.NODATA_OUT              # NoData de entrada


def test_evaluate_block_rejects_class_without_score():
    rules = core.parse_config({'camadas': [{'peso': 1, 'notas': {'1': 10}}]}, 1)
    with pytest.raises(ValueError, match='sem notas'):
        core.evaluate_block([np.array([[1, 7]])], [None], rules)


def test_transition_counts_excludes_nodata_of_either_date():
    a = np.array([[1, 1, 2, 0]])
    b = np.array([[1, 2, 2, 2]])
    counts, valid = core.transition_counts(a, b, 0, None)
    assert counts == {(1.0, 1.0): 1, (1.0, 2.0): 1, (2.0, 2.0): 1}
    assert valid.tolist() == [[True, True, True, False]]


def test_pixel_area_ha_projected_rotated_and_geographic():
    assert core.pixel_area_ha((0, 30, 0, 0, 0, -30), True) == pytest.approx(0.09)
    # grade rotacionada: área é |det| da transformação afim
    gt = (0, 30 * math.cos(0.3), -30 * math.sin(0.3), 0, 30 * math.sin(0.3), 30 * math.cos(0.3))
    assert core.pixel_area_ha(gt, True) == pytest.approx(0.09)
    assert core.pixel_area_ha((0, 1, 0, 0, 0, -1), True, metres_per_unit=0.3048) == pytest.approx(0.3048 ** 2 / 1e4)
    assert core.pixel_area_ha((0, 0.001, 0, 0, 0, -0.001), False) is None
