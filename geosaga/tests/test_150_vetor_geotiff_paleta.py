"""Conversor Vetor -> GeoTIFF (correção na 1.5.0): paleta sempre gravada, para o QGIS mostrar os nomes.

Até a 1.4.2 a paleta só era gravada quando o vetor tinha o campo COR_HEX; sem ela, o QGIS abria o mapa
em tons de cinza e os nomes das classes (no .aux.xml) não apareciam (observação do autor, 20/11/2026).
"""
import os
import tempfile
import unittest

try:
    from osgeo import gdal, ogr, osr
except ImportError:  # pragma: no cover
    gdal = None


@unittest.skipIf(gdal is None, 'GDAL indisponível')
class VetorGeoTiffPaleta150(unittest.TestCase):
    def convert(self, with_color):
        from geosaga.vector_raster import convert_vector_to_tif
        folder = self.enterContext(tempfile.TemporaryDirectory())
        source = os.path.join(folder, 'bairros.gpkg')
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(31985)
        ds = ogr.GetDriverByName('GPKG').CreateDataSource(source)
        layer = ds.CreateLayer('bairros', srs, ogr.wkbPolygon)
        layer.CreateField(ogr.FieldDefn('NOME', ogr.OFTString))
        if with_color:
            layer.CreateField(ogr.FieldDefn('COR_HEX', ogr.OFTString))
        for i, name in enumerate(['Centro', 'Farol']):
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField('NOME', name)
            if with_color:
                feature.SetField('COR_HEX', '#ff0000')
            x = 200000 + 100 * i
            feature.SetGeometry(ogr.CreateGeometryFromWkt(
                f'POLYGON(({x} 9000000,{x + 100} 9000000,{x + 100} 9000100,{x} 9000100,{x} 9000000))'))
            layer.CreateFeature(feature)
        ds = None
        out = os.path.join(folder, 'saida', 'bairros.tif')
        convert_vector_to_tif(source + '|layername=bairros', out, 'NOME', 10)
        dataset = gdal.Open(out)
        band = dataset.GetRasterBand(1)
        dataset.GetFileList()  # carrega o .aux.xml (GDAL 3.8)
        return dataset, band, out

    def test_paleta_sem_cor_hex(self):
        dataset, band, out = self.convert(with_color=False)
        table = band.GetRasterColorTable()
        self.assertIsNotNone(table)
        self.assertEqual(band.GetRasterColorInterpretation(), gdal.GCI_PaletteIndex)
        self.assertNotEqual(table.GetColorEntry(1)[:3], table.GetColorEntry(2)[:3])
        self.assertEqual(band.GetCategoryNames()[1:3], ['Centro', 'Farol'])
        self.assertTrue(os.path.isfile(out + '.aux.xml'))
        style = open(os.path.splitext(out)[0] + '.qml', encoding='utf-8').read()
        self.assertIn('type="paletted"', style)
        self.assertEqual(style.count('<paletteEntry'), 2)  # só as classes reais, não as 256 cores
        self.assertIn('label="Centro"', style)
        dataset = None

    def test_rs2_para_geotiff_tambem_grava_estilo(self):
        import numpy as np
        from geosaga.rs2_converter import convert_rs2_to_tif
        from geosaga.rs2_format import RS2Header, write_rs2
        folder = self.enterContext(tempfile.TemporaryDirectory())
        rs2 = os.path.join(folder, 'mapa.rs2')
        header = RS2Header(3, 2, 200000, 9000000, 200030, 9000020, ['FUNDO', 'A & B', 'C'],
                           [(255, 255, 255, 0), (10, 20, 30, 0), (40, 50, 60, 0)])
        write_rs2(rs2, header, iter(np.array([[0, 1, 2], [1, 1, 2]], dtype=np.uint16)))
        out = os.path.join(folder, 'mapa.tif')
        convert_rs2_to_tif(rs2, out, 'EPSG:31985')
        style = open(os.path.join(folder, 'mapa.qml'), encoding='utf-8').read()
        self.assertEqual(style.count('<paletteEntry'), 2)  # FUNDO é NoData
        self.assertIn('label="A &amp; B"', style)
        self.assertIn('color="#0a141e"', style)

    def test_cor_hex_continua_valendo(self):
        dataset, band, _out = self.convert(with_color=True)
        self.assertEqual(band.GetRasterColorTable().GetColorEntry(1)[:3], (255, 0, 0))
        dataset = None


if __name__ == '__main__':
    unittest.main()
