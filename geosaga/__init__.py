"""Vista Saga Plugin: implementação independente de fluxos de análise ambiental."""


def classFactory(iface):
    from .plugin import VistaSagaPlugin
    return VistaSagaPlugin(iface)
