"""Avaliação ambiental multicritério por pesos e notas, sem interpolação."""
import os
from qgis.core import (
    Qgis, QgsProcessingAlgorithm, QgsProcessingException,
    QgsProcessingParameterMultipleLayers, QgsProcessingParameterString,
    QgsProcessingParameterRasterDestination,
)
from osgeo import gdal

from ..core import evaluate_block, parse_config, NODATA_OUT
from .common import dataset_for_layer, assert_same_grid, window_iterator, create_output, assert_output_not_input

EXAMPLE = '{"camadas":[{"peso":60,"notas":{"1":10,"2":7,"3":3}},{"peso":40,"notas":{"1":9,"2":5,"3":1}}]}'


class AvaliacaoAlgorithm(QgsProcessingAlgorithm):
    RASTERS = 'RASTERS'
    REGRAS = 'REGRAS'
    OUTPUT = 'OUTPUT'

    def name(self):
        return 'avaliacao'

    def displayName(self):
        return 'Avaliação ambiental — pesos e notas'

    def group(self):
        return 'Análise ambiental'

    def groupId(self):
        return 'analise'

    def shortHelpString(self):
        return (
            'Calcula a média ponderada das notas das classes de cada raster. '
            'Selecione os rasters categóricos na ordem correspondente às entradas do JSON. '
            'Atribua peso positivo para cada tema e notas entre 0 e 10 a TODAS as classes. '
            'Os pesos são normalizados pela soma; não precisam somar 100. '
            'Áreas com NoData em qualquer raster ficam com NoData no resultado. '
            'Rasters devem possuir mesmo SRC, grade, resolução e extensão. '\
            'Exemplo com dois rasters: ' + EXAMPLE
        )

    def initAlgorithm(self, config=None):
        p = QgsProcessingParameterMultipleLayers(
            self.RASTERS, 'Rasters de classes (ordem correspondente ao JSON)',
            layerType=Qgis.ProcessingSourceType.Raster)
        p.setMinimumNumberInputs(1)
        self.addParameter(p)
        self.addParameter(QgsProcessingParameterString(
            self.REGRAS, 'Pesos e notas por classe (JSON)', multiLine=True, defaultValue=EXAMPLE))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT, 'Carta de avaliação (.tif)'))

    def processAlgorithm(self, parameters, context, feedback):
        layers = self.parameterAsLayerList(parameters, self.RASTERS, context)
        if not layers:
            raise QgsProcessingException('Selecione pelo menos um raster.')
        try:
            rules = parse_config(self.parameterAsString(parameters, self.REGRAS, context), len(layers))
        except ValueError as exc:
            raise QgsProcessingException(str(exc)) from exc
        datasets = [dataset_for_layer(layer) for layer in layers]
        assert_same_grid(datasets)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        assert_output_not_input(output, layers)
        for layer, ds in zip(layers, datasets):
            if not ds.GetRasterBand(1):
                raise QgsProcessingException(f'Raster sem banda: {layer.name()}')
        dest = create_output(output, datasets[0], gdal.GDT_Float32, NODATA_OUT)
        total = datasets[0].RasterYSize
        success = False
        try:
            for x, y, w, h in window_iterator(datasets[0]):
                if feedback.isCanceled():
                    raise QgsProcessingException('Operação cancelada.')
                arrays = [ds.GetRasterBand(1).ReadAsArray(x, y, w, h) for ds in datasets]
                nds = [ds.GetRasterBand(1).GetNoDataValue() for ds in datasets]
                try:
                    output_data = evaluate_block(arrays, nds, rules)
                except ValueError as exc:
                    raise QgsProcessingException(str(exc)) from exc
                dest.GetRasterBand(1).WriteArray(output_data, x, y)
                feedback.setProgress(100 * (y + h) / total)
            dest.FlushCache()
            success = True
        finally:
            dest = None
            if not success and os.path.exists(output):
                os.remove(output)
        return {self.OUTPUT: output}

    def createInstance(self):
        return AvaliacaoAlgorithm()
