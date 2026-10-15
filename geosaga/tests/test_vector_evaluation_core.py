"""Testes independentes de QGIS da avaliação espacial vetorial."""
import math
import unittest

from geosaga.vector_evaluation_core import (
    category_key, category_sort, validate_criteria, evaluate_record)


def criteria():
    return [
        {'field': 'USO', 'weight': 60, 'categories': {'1', '2', '3'},
         'notes': {'1': 8, '2': 2}, 'excluded': {'3'}},
        {'field': 'SOLO', 'weight': 40, 'categories': {'argiloso', 'arenoso'},
         'notes': {'argiloso': 4, 'arenoso': 10}, 'excluded': set()},
    ]


class TestVectorEvaluation(unittest.TestCase):
    def test_weighted_average(self):
        rules = validate_criteria(criteria())
        note, valid, reason, parts = evaluate_record({'USO': 1, 'SOLO': 'arenoso'}, rules)
        self.assertAlmostEqual(note, 8.8)
        self.assertEqual((valid, reason, parts), (1, '', [8., 10.]))

    def test_zero_score_is_valid(self):
        cfg = criteria()
        cfg[0]['notes']['1'] = 0
        rules = validate_criteria(cfg)
        note, valid, _, _ = evaluate_record({'USO': 1, 'SOLO': 'argiloso'}, rules)
        self.assertEqual(valid, 1)
        self.assertAlmostEqual(note, 1.6)

    def test_excluded_keeps_invalid_unit(self):
        rules = validate_criteria(criteria())
        result = evaluate_record({'USO': 3, 'SOLO': 'arenoso'}, rules)
        self.assertEqual(result[0:2], (None, 0))
        self.assertIn('Excluída', result[2])

    def test_missing_is_invalid_not_weight_redistribution(self):
        rules = validate_criteria(criteria())
        result = evaluate_record({'USO': 2, 'SOLO': None}, rules)
        self.assertEqual(result[0:2], (None, 0))
        self.assertIn('Sem dado', result[2])

    def test_unknown_raises(self):
        rules = validate_criteria(criteria())
        with self.assertRaisesRegex(ValueError, 'categoria sem nota'):
            evaluate_record({'USO': '99', 'SOLO': 'arenoso'}, rules)

    def test_total_weight_validation(self):
        cfg = criteria()
        cfg[1]['weight'] = 35
        with self.assertRaisesRegex(ValueError, '100%'):
            validate_criteria(cfg)

    def test_duplicate_field(self):
        cfg = criteria()
        cfg[1]['field'] = 'uso'
        with self.assertRaisesRegex(ValueError, 'repetido'):
            validate_criteria(cfg)

    def test_missing_score(self):
        cfg = criteria()
        cfg[0]['notes'].pop('2')
        with self.assertRaisesRegex(ValueError, 'sem tratamento'):
            validate_criteria(cfg)

    def test_score_bounds(self):
        cfg = criteria()
        cfg[0]['notes']['1'] = -1
        with self.assertRaisesRegex(ValueError, 'fora da escala'):
            validate_criteria(cfg)

    def test_nan(self):
        self.assertIsNone(category_key(float('nan')))
        self.assertIsNone(category_key(float('inf')))
        self.assertIsNone(category_key(None))
        self.assertEqual(category_key(1.), '1')
        self.assertEqual(category_key('1'), '1')

    def test_string_categories_keep_meaning(self):
        self.assertEqual(category_key('Areia fina'), 'Areia fina')
        self.assertEqual(category_key('00'), '00')
        self.assertEqual(category_key(' '), None)
        self.assertEqual(sorted(['10', '1', '2'], key=category_sort), ['1', '2', '10'])

    def test_scale_100(self):
        cfg = criteria()
        cfg[0]['notes']['1'] = 80
        rules = validate_criteria(cfg, scale=100)
        self.assertEqual(evaluate_record({'USO': 1, 'SOLO': 'arenoso'}, rules)[0], 52.)
        with self.assertRaisesRegex(ValueError, 'fora da escala'):
            validate_criteria(cfg, scale=10)

    def test_all_excluded_succeeds(self):
        rules = validate_criteria([{'field':'CRIT','weight':100, 'categories': {'a'},
                                  'notes': {}, 'excluded': {'a'}}])
        self.assertEqual(evaluate_record({'CRIT': 'a'}, rules)[1], 0)


if __name__ == '__main__':
    unittest.main()
