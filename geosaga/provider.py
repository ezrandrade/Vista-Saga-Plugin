"""Provedor de algoritmos de processamento."""
from qgis.core import QgsProcessingProvider

from .algorithms.avaliacao import AvaliacaoAlgorithm
from .algorithms.monitoria import MonitoriaAlgorithm
from .algorithms.assinatura import AssinaturaAlgorithm


class GeoSAGAProvider(QgsProcessingProvider):
    def id(self):
        return 'geosaga'

    def name(self):
        return 'Vista Saga Plugin'

    def longName(self):
        return 'Vista Saga Plugin — análises temáticas'

    def loadAlgorithms(self):
        self.addAlgorithm(AvaliacaoAlgorithm())
        self.addAlgorithm(MonitoriaAlgorithm())
        self.addAlgorithm(AssinaturaAlgorithm())
