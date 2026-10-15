"""Monitoria: classificação de transições entre mapas categóricos."""
from collections import Counter
import os
import numpy as np
from osgeo import gdal
from qgis.core import (
    QgsProcessingAlgorithm, QgsProcessingException, QgsProcessingParameterRasterLayer,
    QgsProcessingParameterRasterDestination, QgsProcessingParameterFileDestination,
)

from ..core import transition_counts, NODATA_OUT
from .common import (
    dataset_for_layer, assert_same_grid, window_iterator, create_output,
    area_ha, write_csv, fmt_code, assert_output_not_input,
)


class MonitoriaAlgorithm(QgsProcessingAlgorithm):
    ANTES = 'ANTES'
    DEPOIS = 'DEPOIS'
    OUTPUT = 'OUTPUT'
    TABELA = 'TABELA'

    def name(self):
        return 'monitoria'

    def displayName(self):
        return 'Monitoria espacial — matriz de transição'

    def group(self):
        return 'Análise ambiental'

    def groupId(self):
        return 'analise'

    def shortHelpString(self):
        return (
            'Identifica as transições de classe entre dois rasters categóricos. '
            'O mapa final guarda identificadores inteiros consecutivos; a tabela CSV '
            'relaciona cada identificador às classes de origem e destino, quantidade '
            'de pixels, porcentagem e área (ha quando o SRC é projetado). '
            'NoData em qualquer data exclui o pixel. Exige grades alinhadas.'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.ANTES, 'Raster no período inicial'))
        self.addParameter(QgsProcessingParameterRasterLayer(self.DEPOIS, 'Raster no período final'))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT, 'Mapa de transições (.tif)'))
        self.addParameter(QgsProcessingParameterFileDestination(self.TABELA, 'Matriz de transições (.csv)', 'CSV (*.csv)'))

    def processAlgorithm(self, parameters, context, feedback):
        layer_a = self.parameterAsRasterLayer(parameters, self.ANTES, context)
        layer_b = self.parameterAsRasterLayer(parameters, self.DEPOIS, context)
        before = dataset_for_layer(layer_a)
        after = dataset_for_layer(layer_b)
        assert_same_grid([before, after])
        counts = Counter()
        band_a = before.GetRasterBand(1)
        band_b = after.GetRasterBand(1)
        nd_a, nd_b = band_a.GetNoDataValue(), band_b.GetNoDataValue()
        total = before.RasterYSize
        # 1ª passagem: conta os pares únicos, sem ler todos os pixels na RAM.
        for x, y, w, h in window_iterator(before):
            if feedback.isCanceled():
                raise QgsProcessingException('Operação cancelada.')
            a, b = band_a.ReadAsArray(x, y, w, h), band_b.ReadAsArray(x, y, w, h)
            block_counts, _ = transition_counts(a, b, nd_a, nd_b)
            counts.update(block_counts)
            feedback.setProgress(50 * (y + h) / total)
        if not counts:
            raise QgsProcessingException('Não há pixels válidos comuns nos dois períodos.')
        if len(counts) > 2_000_000:
            raise QgsProcessingException('Número de transições ultrapassa o limite de IDs inteiros.')
        transitions = sorted(counts)
        ids = {pair: i for i, pair in enumerate(transitions, 1)}
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        assert_output_not_input(output, [layer_a, layer_b])
        table = self.parameterAsFileOutput(parameters, self.TABELA, context)
        dest = create_output(output, before, gdal.GDT_Int32, int(NODATA_OUT))
        success = False
        try:
            # 2ª passagem: codifica cada par com ID da tabela.
            for x, y, w, h in window_iterator(before):
                if feedback.isCanceled():
                    raise QgsProcessingException('Operação cancelada.')
                a, b = band_a.ReadAsArray(x, y, w, h), band_b.ReadAsArray(x, y, w, h)
                _, valid = transition_counts(a, b, nd_a, nd_b)
                encoded = np.full((h, w), int(NODATA_OUT), dtype=np.int32)
                if valid.any():
                    pairs, inverse = np.unique(
                        np.column_stack((a[valid], b[valid])), axis=0, return_inverse=True)
                    block_ids = np.array([ids[(float(p[0]), float(p[1]))] for p in pairs], dtype=np.int32)
                    encoded[valid] = block_ids[inverse]
                dest.GetRasterBand(1).WriteArray(encoded, x, y)
                feedback.setProgress(50 + 50 * (y + h) / total)
            dest.FlushCache()
            success = True
        finally:
            dest = None
            if not success and os.path.exists(output):
                os.remove(output)
        total_valid = sum(counts.values())
        ha_per_pixel = area_ha(before)
        rows = [
            [ids[p], fmt_code(p[0]), fmt_code(p[1]), counts[p],
             round(100 * counts[p] / total_valid, 6),
             '' if ha_per_pixel is None else round(counts[p] * ha_per_pixel, 6)]
            for p in transitions
        ]
        write_csv(table, ['id', 'classe_inicial', 'classe_final', 'pixels', 'percentual_validos', 'area_ha'], rows)
        if ha_per_pixel is None:
            feedback.pushWarning('SRC não projetado: não foi calculada área em hectares.')
        return {self.OUTPUT: output, self.TABELA: table}

    def createInstance(self):
        return MonitoriaAlgorithm()
