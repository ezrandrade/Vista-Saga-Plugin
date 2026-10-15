"""Testes sem QGIS do planejamento do empilhamento vetorial."""
import unittest

from geosaga.vector_overlay_engine import validate_overlay_plan


def criterion(index, layer_id=None, source_field='classe'):
    return {'layer_id': layer_id or f'layer_{index}',
            'source_field': source_field, 'field': f'C{index:02d}'}


class OverlayPlanTests(unittest.TestCase):
    def test_two_distinct_layers(self):
        self.assertEqual(validate_overlay_plan([criterion(1), criterion(2)]),
                         ['layer_1', 'layer_2'])

    def test_five_layers_preserve_order(self):
        items = [criterion(i) for i in range(1, 6)]
        self.assertEqual(validate_overlay_plan(items), [f'layer_{i}' for i in range(1, 6)])

    def test_one_layer_is_not_overlay(self):
        with self.assertRaisesRegex(ValueError, 'duas camadas'):
            validate_overlay_plan([criterion(1)])

    def test_no_layers(self):
        with self.assertRaises(ValueError):
            validate_overlay_plan([])

    def test_same_layer_twice(self):
        with self.assertRaisesRegex(ValueError, 'uma vez'):
            validate_overlay_plan([criterion(1), criterion(2, layer_id='layer_1')])

    def test_duplicate_internal_code(self):
        with self.assertRaisesRegex(ValueError, 'repetidos'):
            validate_overlay_plan([criterion(1), {'layer_id': 'other', 'field': 'C01', 'source_field': 'x'}])

    def test_absent_field(self):
        with self.assertRaisesRegex(ValueError, 'campo'):
            validate_overlay_plan([criterion(1), criterion(2, source_field='')])

    def test_absent_layer(self):
        with self.assertRaisesRegex(ValueError, 'uma vez'):
            validate_overlay_plan([criterion(1), {'layer_id': '', 'field': 'C02', 'source_field': 'x'}])

    def test_overridden_requirement(self):
        self.assertEqual(validate_overlay_plan([criterion(1)], min_layers=1), ['layer_1'])


if __name__ == '__main__':
    unittest.main()
