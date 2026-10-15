"""Assinatura de classes de um raster dentro da união de polígonos."""
from collections import Counter
import numpy as np
from osgeo import gdal, ogr, osr
from qgis.core import (
    Qgis, QgsProcessingAlgorithm, QgsProcessingException,
    QgsProcessingParameterRasterLayer, QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFileDestination, QgsCoordinateTransform,
    QgsCoordinateReferenceSystem, QgsProject, QgsGeometry,
)

from ..core import valid_mask
from .common import dataset_for_layer, window_iterator, area_ha, write_csv, fmt_code


class AssinaturaAlgorithm(QgsProcessingAlgorithm):
    RASTER = 'RASTER'
    POLIGONOS = 'POLIGONOS'
    TABELA = 'TABELA'

    def name(self):
        return 'assinatura'

    def displayName(self):
        return 'Assinatura espacial — classes em polígonos'

    def group(self):
        return 'Análise ambiental'

    def groupId(self):
        return 'analise'

    def shortHelpString(self):
        return (
            'Calcula a assinatura temática da área definida pela UNIÃO de todos '
            'os polígonos de entrada: classes de um raster categórico, pixels, '
            'porcentagem e área (ha em SRC projetado). Polígonos sobrepostos '
            'não duplicam a contagem. A seleção de pixels é por centro de célula '
            '(ALL_TOUCHED=FALSE). Não faz relatório individual por feição nesta versão. '
            'O vetor é reprojetado para o SRC do raster, se necessário.'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.RASTER, 'Raster de classes'))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.POLIGONOS, 'Área de análise (polígonos)', types=[Qgis.ProcessingSourceType.VectorPolygon]))
        self.addParameter(QgsProcessingParameterFileDestination(
            self.TABELA, 'Assinatura temática (.csv)', 'CSV (*.csv)'))

    def processAlgorithm(self, parameters, context, feedback):
        raster = dataset_for_layer(self.parameterAsRasterLayer(parameters, self.RASTER, context))
        source = self.parameterAsSource(parameters, self.POLIGONOS, context)
        if source is None:
            raise QgsProcessingException('Camada poligonal inválida.')
        raster_crs = QgsCoordinateReferenceSystem.fromWkt(raster.GetProjection())
        if not raster_crs.isValid():
            raise QgsProcessingException('Raster sem SRC válido.')
        src_crs = source.sourceCrs()
        if not src_crs.isValid():
            raise QgsProcessingException('Polígonos sem SRC válido.')
        transform = None
        if src_crs != raster_crs:
            transform = QgsCoordinateTransform(src_crs, raster_crs, QgsProject.instance())
        mem_driver = ogr.GetDriverByName('Memory')
        vector_mem = mem_driver.CreateDataSource('')
        srs = osr.SpatialReference()
        srs.ImportFromWkt(raster.GetProjection())
        polygon_layer = vector_mem.CreateLayer('areas', srs=srs, geom_type=ogr.wkbUnknown)
        nfeat = 0
        for feature in source.getFeatures():
            if feedback.isCanceled():
                raise QgsProcessingException('Operação cancelada.')
            geom = QgsGeometry(feature.geometry())
            if geom.isEmpty():
                continue
            if transform is not None:
                geom.transform(transform)
            ogr_geom = ogr.CreateGeometryFromWkb(bytes(geom.asWkb()))
            ogr_feature = ogr.Feature(polygon_layer.GetLayerDefn())
            ogr_feature.SetGeometry(ogr_geom)
            if polygon_layer.CreateFeature(ogr_feature) != 0:
                raise QgsProcessingException('Erro ao converter polígonos para análise.')
            ogr_feature = None
            nfeat += 1
        if nfeat == 0:
            raise QgsProcessingException('Não há polígonos válidos de entrada.')
        counts = Counter()
        data_band = raster.GetRasterBand(1)
        nd = data_band.GetNoDataValue()
        gt = raster.GetGeoTransform()
        mem_raster_driver = gdal.GetDriverByName('MEM')
        total = raster.RasterYSize
        for x, y, w, h in window_iterator(raster):
            if feedback.isCanceled():
                raise QgsProcessingException('Operação cancelada.')
            mask_ds = mem_raster_driver.Create('', w, h, 1, gdal.GDT_Byte)
            window_gt = (
                gt[0] + x * gt[1] + y * gt[2], gt[1], gt[2],
                gt[3] + x * gt[4] + y * gt[5], gt[4], gt[5],
            )
            mask_ds.SetGeoTransform(window_gt)
            mask_ds.SetProjection(raster.GetProjection())
            mask_band = mask_ds.GetRasterBand(1)
            mask_band.Fill(0)
            # Filtra as geometrias que atravessam a janela para poupar trabalho.
            corners = [
                (window_gt[0] + dx * gt[1] + dy * gt[2],
                 window_gt[3] + dx * gt[4] + dy * gt[5])
                for dx, dy in ((0, 0), (w, 0), (0, h), (w, h))
            ]
            xs, ys = zip(*corners)
            polygon_layer.SetSpatialFilterRect(min(xs), min(ys), max(xs), max(ys))
            err = gdal.RasterizeLayer(mask_ds, [1], polygon_layer, burn_values=[1])
            if err != 0:
                raise QgsProcessingException('Falha na rasterização dos polígonos.')
            mask = mask_band.ReadAsArray() != 0
            data = data_band.ReadAsArray(x, y, w, h)
            valid = mask & valid_mask(data, nd)
            if valid.any():
                values, how_many = np.unique(data[valid], return_counts=True)
                counts.update({float(v): int(n) for v, n in zip(values, how_many)})
            mask_ds = None
            feedback.setProgress(100 * (y + h) / total)
        polygon_layer.SetSpatialFilter(None)
        if not counts:
            raise QgsProcessingException('Não há pixels válidos na área definida.')
        total_valid = sum(counts.values())
        ha = area_ha(raster)
        rows = [
            [fmt_code(code), n, round(100 * n / total_valid, 6),
             '' if ha is None else round(n * ha, 6)]
            for code, n in sorted(counts.items())
        ]
        table = self.parameterAsFileOutput(parameters, self.TABELA, context)
        write_csv(table, ['classe', 'pixels', 'percentual_validos', 'area_ha'], rows)
        if ha is None:
            feedback.pushWarning('SRC não projetado: não foi calculada área em hectares.')
        return {self.TABELA: table}

    def createInstance(self):
        return AssinaturaAlgorithm()
