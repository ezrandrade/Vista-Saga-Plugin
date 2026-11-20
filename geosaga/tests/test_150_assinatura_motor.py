"""Motor da Assinatura 1.5.0 (raster e vetorial), com dados sintéticos.

A estrutura reproduz o caso de referência do autor (Vista SAGA, 20/11/2026): classe com uma célula
ligada só pela diagonal, classe da legenda sem células, FUNDO e NoData contando como classe. Os dados
reais ficam fora do repositório; a comparação com eles é feita por
``scripts/comparar_assinatura_vista_saga.py``.
"""
import csv
import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

try:
    from osgeo import gdal, ogr, osr
except ImportError:  # pragma: no cover - ambiente sem GDAL
    gdal = None

if gdal is not None:
    from geosaga.rs2_format import RS2Header, write_rs2
    from geosaga.signature_model import CONFLICT_KEY, NO_CLASS_KEY, NODATA_KEY
    from geosaga.signature_raster import open_raster_map, run_raster_signature, scan_reference_classes
    from geosaga.signature_reports import CSV_FIELDS, write_csv, write_txt
    from geosaga.signature_vector import VectorMap, run_vector_signature

# Referência: 0 FUNDO, 1 A, 2 B, 3 C (na legenda, sem células). A célula (3, 3) da classe B só toca
# o resto da classe pela diagonal: o balde do Vista SAGA a deixaria de fora; o plugin a inclui.
REF = np.array([
    [0, 1, 1, 0, 0, 0],
    [0, 1, 1, 0, 2, 2],
    [0, 0, 0, 0, 2, 2],
    [0, 0, 0, 2, 0, 0],
    [0, 0, 0, 0, 0, 0],
], dtype=np.uint16)
USO = np.array([
    [1, 1, 2, 2, 1, 1],
    [1, 1, 2, 2, 1, 1],
    [1, 2, 2, 2, 255, 1],
    [1, 1, 1, 1, 1, 1],
    [255, 1, 1, 1, 1, 1],
], dtype=np.uint8)
X0, Y1, CELL = 197510, 8940820, 10


def _srs(epsg):
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    return srs.ExportToWkt()


@unittest.skipIf(gdal is None, 'GDAL indisponível')
class RasterSignatureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = self.temp.name
        self.ref = os.path.join(self.dir, 'Bairros.rs2')
        header = RS2Header(6, 5, X0, Y1 - 5 * CELL, X0 + 6 * CELL, Y1, ['FUNDO', 'A', 'B', 'C'],
                           [(255, 255, 255, 0), (1, 2, 3, 0), (4, 5, 6, 0), (7, 8, 9, 0)])
        write_rs2(self.ref, header, iter(REF))
        self.uso = self.tif('Uso.tif', USO, nodata=255, names=['', 'Edificada', 'Vegetação'])

    def tearDown(self):
        self.temp.cleanup()

    def tif(self, name, array, *, nodata=None, names=None, epsg=31985, origin=(X0, Y1), dtype=gdal.GDT_Byte):
        path = os.path.join(self.dir, name)
        ds = gdal.GetDriverByName('GTiff').Create(path, array.shape[1], array.shape[0], 1, dtype)
        ds.SetGeoTransform((origin[0], CELL, 0, origin[1], 0, -CELL))
        ds.SetProjection(_srs(epsg))
        band = ds.GetRasterBand(1)
        band.WriteArray(array)
        if nodata is not None:
            band.SetNoDataValue(nodata)
        if names:
            band.SetCategoryNames(names)
        ds = None
        return path

    def maps(self, *paths):
        return [open_raster_map(p, crs='EPSG:31985') for p in (self.ref,) + paths]

    def row(self, msig, key):
        return next(r for r in msig.rows if r.key == key)

    def test_union_counts_whole_class_including_diagonal_cell(self):
        result = run_raster_signature(self.maps(self.uso), [2])
        ref, uso = result.union.maps
        self.assertEqual(ref.asn_cells, 5)  # 4 + a célula diagonal
        self.assertEqual(self.row(ref, 2).pct_category, 100.0)
        self.assertEqual(self.row(ref, 3).total_cells, 0)  # classe da legenda sem células aparece
        self.assertEqual(self.row(uso, 1).asn_cells, 4)
        self.assertEqual(self.row(uso, NODATA_KEY).asn_cells, 1)  # NoData conta como classe
        self.assertAlmostEqual(self.row(uso, 1).pct_area, 80.0)
        self.assertAlmostEqual(self.row(uso, NODATA_KEY).pct_area, 20.0)
        self.assertAlmostEqual(self.row(uso, 1).pct_category, 100.0 * 4 / 21)
        self.assertAlmostEqual(uso.asn_ha, 0.05)
        self.assertEqual(uso.total_cells, 30)
        self.assertAlmostEqual(sum(r.pct_area for r in uso.rows), 100.0)

    def test_per_feature_is_one_cut_per_selected_class(self):
        result = run_raster_signature(self.maps(self.uso), [1, 2])
        self.assertEqual(result.union.maps[0].asn_cells, 9)
        self.assertEqual([f.key for f in result.features], [1, 2])
        uso_a = result.features[0].maps[1]
        self.assertEqual(self.row(uso_a, 1).asn_cells, 2)
        self.assertEqual(self.row(uso_a, 2).asn_cells, 2)
        self.assertEqual(result.selection, ['1 - A', '2 - B'])

    def test_whole_map_includes_background_like_vista_saga(self):
        keys = [k for k, _n, _c in scan_reference_classes(self.maps()[0])]
        self.assertEqual(keys, [0, 1, 2, 3])
        result = run_raster_signature(self.maps(self.uso), keys, per_feature=False)
        ref, uso = result.union.maps
        self.assertEqual(ref.asn_cells, 30)
        self.assertAlmostEqual(self.row(ref, 0).pct_area, 100.0 * 21 / 30)
        self.assertEqual(self.row(uso, NODATA_KEY).asn_cells, 2)
        self.assertEqual(result.features, [])

    def test_nodata_of_reference_can_be_selected(self):
        result = run_raster_signature([open_raster_map(self.uso), open_raster_map(self.ref, crs='EPSG:31985')],
                                      [NODATA_KEY])
        self.assertEqual(result.union.maps[0].asn_cells, 2)
        self.assertEqual(result.selection, ['NoData'])

    def test_nodata_named_in_legend_counts_as_that_class(self):
        path = self.tif('Fundo.tif', REF.astype(np.uint8), nodata=0, names=['FUNDO', 'A', 'B', 'C'])
        ref, _ = run_raster_signature(self.maps(path), [0], per_feature=False).union.maps
        fundo = self.maps(path)[1]
        self.assertIsNone(fundo.nodata)
        self.assertEqual(self.row(ref, 0).asn_cells, 21)

    def test_names_saved_only_in_aux_xml_are_read(self):
        # O GeoTIFF guarda os nomes das classes no .aux.xml; o GDAL 3.8 só o carrega após outra consulta.
        path = self.tif('Nomes.tif', USO, names=['', 'Edificada', 'Vegetação'])
        self.assertTrue(os.path.isfile(path + '.aux.xml'))
        self.assertEqual(open_raster_map(path).legend, {1: 'Edificada', 2: 'Vegetação'})

    def test_style_labels_from_qgis_prevail(self):
        legend = open_raster_map(self.uso, labels={1: 'Casas', 2: '2', 9: 'Nova'}).legend
        self.assertEqual(legend, {1: 'Casas', 2: 'Vegetação', 9: 'Nova'})  # rótulo "2" = código, ignorado
        rs2 = open_raster_map(self.ref, crs='EPSG:31985', labels={1: 'Antares'}).legend
        self.assertEqual(rs2[1], 'Antares')
        self.assertEqual(rs2[0], 'FUNDO')

    def test_selection_without_cells_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'nenhuma célula'):
            run_raster_signature(self.maps(self.uso), [3])
        with self.assertRaisesRegex(ValueError, 'pelo menos uma classe'):
            run_raster_signature(self.maps(self.uso), [])

    def test_class_without_cells_in_per_feature_gives_warning(self):
        result = run_raster_signature(self.maps(self.uso), [2, 3])
        self.assertTrue(any('C' in w for w in result.warnings))

    def test_grid_mismatch_is_refused(self):
        shifted = self.tif('Desloc.tif', USO, origin=(X0 + 5, Y1))
        with self.assertRaisesRegex(ValueError, 'mesma grade'):
            run_raster_signature(self.maps(shifted), [1])
        smaller = self.tif('Menor.tif', USO[:4])
        with self.assertRaisesRegex(ValueError, 'mesma grade'):
            run_raster_signature(self.maps(smaller), [1])

    def test_crs_rules(self):
        other = self.tif('Outro.tif', USO, epsg=31984)
        with self.assertRaisesRegex(ValueError, 'outro SRC'):
            run_raster_signature(self.maps(other), [1])
        geographic = self.tif('Graus.tif', USO, epsg=4674)
        with self.assertRaisesRegex(ValueError, 'projetado'):
            run_raster_signature([open_raster_map(geographic)], [1])
        feet = self.tif('Pes.tif', USO, epsg=2227)
        with self.assertRaisesRegex(ValueError, 'metros'):
            run_raster_signature([open_raster_map(feet)], [1])

    def test_rs2_without_crs_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'não registra SRC'):
            open_raster_map(self.ref)

    def test_fractional_values_are_refused(self):
        values = USO.astype(np.float32) + 0.5
        path = self.tif('Frac.tif', values, dtype=gdal.GDT_Float32)
        with self.assertRaisesRegex(ValueError, 'fracionários'):
            run_raster_signature(self.maps(path), [1])

    def test_multi_band_is_refused(self):
        path = os.path.join(self.dir, 'Duas.tif')
        ds = gdal.GetDriverByName('GTiff').Create(path, 6, 5, 2, gdal.GDT_Byte)
        ds.SetGeoTransform((X0, CELL, 0, Y1, 0, -CELL))
        ds.SetProjection(_srs(31985))
        ds = None
        with self.assertRaisesRegex(ValueError, 'única banda'):
            open_raster_map(path)

    def test_cancel(self):
        with self.assertRaises(InterruptedError):
            run_raster_signature(self.maps(self.uso), [1], cancelled=lambda: True)

    def test_reports(self):
        result = run_raster_signature(self.maps(self.uso), [1, 2], per_feature=True)
        csv_path, txt_path = os.path.join(self.dir, 'a.csv'), os.path.join(self.dir, 'a.txt')
        write_csv(csv_path, result)
        write_txt(txt_path, result, title='Teste')
        with open(csv_path, encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream, delimiter=';'))
        self.assertEqual(list(rows[0]), CSV_FIELDS)
        per_cut = len(result.union.maps[0].rows) + len(result.union.maps[1].rows)
        self.assertEqual(len(rows), 3 * per_cut)  # união + 2 classes
        self.assertEqual({r['RECORTE'] for r in rows}, {'UNIAO', 'FEICAO'})
        text = Path(txt_path).read_text(encoding='utf-8')
        for piece in ('UNIÃO DA SELEÇÃO', 'CLASSE: A', 'CLASSE: B', 'Resultado da assinatura do mapa Uso.tif',
                      '% Categoria', 'NoData'):
            self.assertIn(piece, text)
        self.assertNotIn('—', text)


def _square(x0, y0, x1, y1):
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)):
        ring.AddPoint_2D(X0 + x, Y1 + y)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return bytes(poly.ExportToWkb())


@unittest.skipIf(gdal is None, 'GDAL indisponível')
class VectorSignatureTests(unittest.TestCase):
    def setUp(self):
        self.wkt = _srs(31985)
        self.ref = VectorMap('Bairros', self.wkt, [(1, _square(0, 0, 10, 10), 'A', 'Bairro A'),
                                                   (2, _square(10, 0, 20, 10), 'B', 'Bairro B'),
                                                   (3, _square(20, 0, 30, 10), 'C', 'Bairro C')])
        # Classes 1 e 2 se sobrepõem em 12-15 (30 m²); a classe 1 tem dois polígonos sobrepostos.
        self.uso = VectorMap('Uso', self.wkt, [(1, _square(0, 0, 15, 10), 1, 'Edificada'),
                                               (2, _square(5, 0, 8, 10), 1, 'Edificada'),
                                               (3, _square(12, 0, 25, 10), 2, 'Vegetação')])
        self.selected = [(1, 'Bairro A', _square(0, 0, 10, 10)), (2, 'Bairro B', _square(10, 0, 20, 10))]

    def row(self, msig, key):
        return next(r for r in msig.rows if r.key == key)

    def test_union_with_overlap_excluded(self):
        result = run_vector_signature([self.ref, self.uso], self.selected)
        ref, uso = result.union.maps
        self.assertAlmostEqual(ref.asn_ha, 0.02)
        self.assertAlmostEqual(self.row(ref, 'C').asn_ha, 0.0)
        self.assertAlmostEqual(self.row(uso, 1).asn_ha, 0.012)  # 0-12, mesma classe dissolvida
        self.assertAlmostEqual(self.row(uso, 2).asn_ha, 0.005)  # 15-20
        self.assertAlmostEqual(self.row(uso, CONFLICT_KEY).asn_ha, 0.003)
        self.assertFalse(any(r.key == NO_CLASS_KEY for r in uso.rows))
        self.assertAlmostEqual(sum(r.pct_area for r in uso.rows), 100.0)
        self.assertAlmostEqual(self.row(uso, 2).pct_category, 50.0)  # 50 de 100 m² resolvidos
        self.assertIsNone(self.row(uso, 1).total_cells)
        self.assertTrue(any('sobreposição' in w for w in result.warnings))

    def test_per_feature(self):
        result = run_vector_signature([self.ref, self.uso], self.selected)
        self.assertEqual([f.name for f in result.features], ['Bairro A', 'Bairro B'])
        uso_a = result.features[0].maps[1]
        self.assertAlmostEqual(self.row(uso_a, 1).pct_area, 100.0)
        none = run_vector_signature([self.ref, self.uso], self.selected, per_feature=False)
        self.assertEqual(none.features, [])

    def test_strict_overlap_stops(self):
        with self.assertRaisesRegex(ValueError, 'se sobrepõem'):
            run_vector_signature([self.ref, self.uso], self.selected, overlap='strict')

    def test_gap_becomes_no_class_with_warning(self):
        partial = VectorMap('Parcial', self.wkt, [(1, _square(0, 0, 5, 10), 'x', 'X')])
        result = run_vector_signature([self.ref, partial], self.selected)
        gap = self.row(result.union.maps[1], NO_CLASS_KEY)
        self.assertAlmostEqual(gap.asn_ha, 0.015)
        self.assertAlmostEqual(gap.pct_area, 75.0)
        self.assertIsNone(gap.pct_category)
        self.assertTrue(any('Sem classe' in w for w in result.warnings))

    def test_crs_rules(self):
        other = VectorMap('Outro', _srs(31984), self.uso.features)
        with self.assertRaisesRegex(ValueError, 'outro SRC'):
            run_vector_signature([self.ref, other], self.selected)
        geo = VectorMap('Graus', _srs(4674), self.ref.features)
        with self.assertRaisesRegex(ValueError, 'projetado'):
            run_vector_signature([geo], self.selected)

    def test_invalid_geometry_is_refused(self):
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for x, y in ((0, 0), (10, 10), (10, 0), (0, 10), (0, 0)):
            ring.AddPoint_2D(X0 + x, Y1 + y)
        bowtie = ogr.Geometry(ogr.wkbPolygon)
        bowtie.AddGeometry(ring)
        bad = VectorMap('Ruim', self.wkt, [(7, bytes(bowtie.ExportToWkb()), 1, 'X')])
        with self.assertRaisesRegex(ValueError, 'Geometria inválida na feição 7'):
            run_vector_signature([self.ref, bad], self.selected)

    def test_selection_required_and_labels_consistent(self):
        with self.assertRaisesRegex(ValueError, 'pelo menos uma feição'):
            run_vector_signature([self.ref], [])
        mixed = VectorMap('Misto', self.wkt, [(1, _square(0, 0, 5, 5), 1, 'X'), (2, _square(5, 5, 9, 9), 1, 'Y')])
        with self.assertRaisesRegex(ValueError, 'legendas diferentes'):
            run_vector_signature([self.ref, mixed], self.selected)

    def test_reports(self):
        result = run_vector_signature([self.ref, self.uso], self.selected)
        with tempfile.TemporaryDirectory() as folder:
            csv_path, txt_path = os.path.join(folder, 'v.csv'), os.path.join(folder, 'v.txt')
            write_csv(csv_path, result)
            write_txt(txt_path, result, overlap='excluir a região ambígua')
            with open(csv_path, encoding='utf-8-sig', newline='') as stream:
                rows = list(csv.DictReader(stream, delimiter=';'))
            text = Path(txt_path).read_text(encoding='utf-8')
        self.assertTrue(all(r['TOTAL_PIXELS'] == '' for r in rows))
        self.assertIn('FEIÇÃO: Bairro A (ID 1)', text)
        self.assertIn('Sobreposição excluída', text)


if __name__ == '__main__':
    unittest.main()
