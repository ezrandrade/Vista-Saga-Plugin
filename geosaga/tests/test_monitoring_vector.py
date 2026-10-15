"""Testes das informações de transições transferidas à vetorização."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from geosaga.monitoring_vector import (
    META_KEY, find_monitoring_transitions, serialize_monitoring_rows,
    polygon_area_m2, monitoring_color,
)
from geosaga.rs2_format import RS2Error


class Band:
    def __init__(self, payload=None):
        self.payload = payload

    def GetMetadataItem(self, name):
        return self.payload if name == META_KEY else None


class CRS:
    def __init__(self, projected=True, unit=1):
        self.projected, self.unit = projected, unit

    def IsProjected(self):
        return self.projected

    def IsGeographic(self):
        return not self.projected

    def GetLinearUnits(self):
        return self.unit


class Polygon:
    def GetArea(self):
        return 100

    def GetGeodesicArea(self):
        return 127.5


class Tests(unittest.TestCase):
    def setUp(self):
        self.context = tempfile.TemporaryDirectory()
        self.addCleanup(self.context.cleanup)
        self.root = Path(self.context.name)
        self.tif = self.root/'monitoria.tif'
        self.rows = [
            {'ID_TRANS':'1', 'CLASSE_INICIAL':'2', 'CLASSE_FINAL':'2',
             'SITUACAO':'Permanência','LEGENDA':'Permaneceu: Pastagem',
             'DEIXOU_DE_SER':'','TORNOU_SE':''},
            {'ID_TRANS':'2','CLASSE_INICIAL':'2','CLASSE_FINAL':'3',
             'SITUACAO':'Mudança','LEGENDA':'Deixou de ser: Pastagem | Tornou-se: Agricultura',
             'DEIXOU_DE_SER':'Pastagem','TORNOU_SE':'Agricultura'},
        ]

    def _write(self):
        with (self.root/'monitoria_transicoes.csv').open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.rows[0], delimiter=';')
            writer.writeheader()
            writer.writerows(self.rows)

    def test_companion_csv(self):
        self._write()
        results = find_monitoring_transitions(self.tif, Band())
        self.assertEqual(results[2]['deixou'], 'Pastagem')
        self.assertEqual(results[2]['tornou'], 'Agricultura')
        self.assertEqual(results[1]['situacao'], 'Permanência')

    def test_embedded_metadata_without_csv(self):
        encoded = json.dumps(self.rows, ensure_ascii=False)
        found = find_monitoring_transitions(self.tif, Band(encoded))
        self.assertEqual(found[1]['legenda'], 'Permaneceu: Pastagem')

    def test_companion_csv_precedence_over_metadata(self):
        self._write()
        found = find_monitoring_transitions(self.tif, Band('not json'))
        self.assertEqual(found[2]['final'], 3)

    def test_no_companion_means_generic_tiff(self):
        self.assertEqual(find_monitoring_transitions(self.tif, Band()), {})

    def test_invalid_csv(self):
        (self.root/'monitoria_transicoes.csv').write_text('X;Y\n1;2\n',encoding='utf-8')
        with self.assertRaisesRegex(RS2Error, 'malformado'):
            find_monitoring_transitions(self.tif, Band())

    def test_duplicate_csv_id(self):
        self.rows[1]['ID_TRANS'] = '1'
        self._write()
        with self.assertRaisesRegex(RS2Error, 'duplicado'):
            find_monitoring_transitions(self.tif, Band())

    def test_invalid_internal_metadata(self):
        with self.assertRaisesRegex(RS2Error, 'Metadados'):
            find_monitoring_transitions(self.tif, Band('{broken'))

    def test_serialize_monitoria_from_core_rows(self):
        values = [{'id': 2, 'inicial':2., 'final':3., 'situacao':'Mudança',
                   'legenda':'Deixou de ser: A | Tornou-se: B',
                   'classe_inicial_nome':'A','classe_final_nome':'B'}]
        decoded = find_monitoring_transitions(self.tif, Band(serialize_monitoring_rows(values)))
        self.assertEqual(decoded[2]['deixou'],'A')

    def test_area_projected_meters(self):
        self.assertEqual(polygon_area_m2(Polygon(), CRS()),100)
        self.assertEqual(polygon_area_m2(Polygon(), CRS(unit=0.3048)),100*0.3048**2)

    def test_area_geographic_geodesic(self):
        self.assertEqual(polygon_area_m2(Polygon(), CRS(projected=False)),127.5)
        self.assertIsNone(polygon_area_m2(Polygon(), None))

    def test_status_colors(self):
        self.assertEqual(monitoring_color(1,False),'#B9C2C7')
        self.assertTrue(monitoring_color(2,True).startswith('#'))
        self.assertNotEqual(monitoring_color(2,True),monitoring_color(3,True))


if __name__=='__main__':
    unittest.main()
