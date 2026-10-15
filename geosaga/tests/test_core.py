"""Testes executáveis com Python, NumPy e biblioteca unittest (sem QGIS)."""
import unittest

import numpy as np

from geosaga.core import (
    NODATA_OUT, evaluate_block, parse_config, pixel_area_ha,
    transition_counts, valid_mask,
)


class TestConfiguration(unittest.TestCase):
    def test_weights_and_scale(self):
        rules = parse_config({'escala': 10, 'camadas': [
            {'peso': 60, 'notas': {'1': 10, '2': 5}},
            {'peso': 40, 'notas': {'1': 6}, 'bloqueadas': ['2']},
        ]}, 2)
        self.assertEqual(rules[0][0], 60)
        self.assertEqual(rules[1][2], {2.0})

    def test_legacy_json(self):
        rules = parse_config('{"camadas":[{"peso":1,"notas":{"1":8}}]}', 1)
        self.assertEqual(rules[0][1][1.0], 8)

    def test_wrong_layer_count(self):
        with self.assertRaisesRegex(ValueError, 'rasters'):
            parse_config({'camadas': []}, 1)

    def test_negative_weight(self):
        with self.assertRaisesRegex(ValueError, 'positivo'):
            parse_config({'camadas': [{'peso': -3, 'notas': {'1': 2}}]}, 1)

    def test_score_above_scale(self):
        with self.assertRaisesRegex(ValueError, 'notas entre'):
            parse_config({'camadas': [{'peso': 100, 'notas': {'1': 11}}]}, 1)

    def test_note_and_block_conflict(self):
        with self.assertRaisesRegex(ValueError, 'bloqueada'):
            parse_config({'camadas': [{
                'peso': 100, 'notas': {'1': 4}, 'bloqueadas': ['1'],
            }]}, 1)

    def test_non_finite_weight(self):
        with self.assertRaisesRegex(ValueError, 'finito'):
            parse_config({'camadas': [{'peso': 'nan', 'notas': {'1': 2}}]}, 1)


class TestEvaluation(unittest.TestCase):
    def test_weighted_average(self):
        arrays = [np.array([[1, 2]], dtype=np.int16), np.array([[1, 2]], dtype=np.int16)]
        rules = [(60, {1: 10, 2: 4}, set()), (40, {1: 5, 2: 6}, set())]
        out = evaluate_block(arrays, [None, None], rules)
        np.testing.assert_array_almost_equal(out, [[8., 4.8]])
        self.assertEqual(out.dtype, np.float32)

    def test_zero_is_a_valid_grade(self):
        out = evaluate_block([np.array([[1, 2]])], [None], [(1, {1: 0, 2: 10}, set())])
        np.testing.assert_array_equal(out, [[0, 10]])

    def test_blocked_classes_become_nodata(self):
        a = np.array([[1, 2, 1]])
        b = np.array([[1, 1, 9]])
        rules = [(50, {1: 10}, {2}), (50, {1: 2, 9: 2}, set())]
        out = evaluate_block([a, b], [None, None], rules)
        np.testing.assert_array_equal(out, [[6, NODATA_OUT, 6]])

    def test_nodata_is_not_graduated(self):
        a = np.array([[1, -9999]])
        out = evaluate_block([a], [-9999], [(1, {1: 7}, set())])
        np.testing.assert_array_equal(out, [[7, NODATA_OUT]])

    def test_unknown_class_fails(self):
        with self.assertRaisesRegex(ValueError, 'sem notas'):
            evaluate_block([np.array([[1, 2]])], [None], [(1, {1: 5}, set())])

    def test_mismatched_shapes_fail(self):
        with self.assertRaisesRegex(ValueError, 'dimensões'):
            evaluate_block([np.ones((2, 2)), np.ones((1, 2))],
                           [None, None], [(1, {1: 5}), (1, {1: 5})])

    def test_nan_nodata(self):
        result = valid_mask(np.array([1., np.nan]), np.nan)
        np.testing.assert_array_equal(result, [True, False])


class TestMonitoringAndSignatureGeometry(unittest.TestCase):
    def test_transition_count_and_missing_pixels(self):
        a = np.array([[1, 1, 2, -1]])
        b = np.array([[2, 2, 2, 1]])
        counted, valid = transition_counts(a, b, -1, -1)
        self.assertEqual(counted, {(1., 2.): 2, (2., 2.): 1})
        self.assertEqual(int(valid.sum()), 3)

    def test_projected_area(self):
        self.assertAlmostEqual(pixel_area_ha((0, 30, 0, 0, 0, -30), True), 0.09)

    def test_geographic_area_not_assumed(self):
        self.assertIsNone(pixel_area_ha((0, .01, 0, 0, 0, -.01), False))

    def test_rotated_affine_area(self):
        self.assertAlmostEqual(pixel_area_ha((0, 30, 3, 0, 0, -30), True), 0.09)


if __name__ == '__main__':
    unittest.main()
