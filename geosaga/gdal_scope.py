"""Exceções GDAL/OGR/OSR com escopo local.

``gdal.UseExceptions()`` altera um estado GLOBAL compartilhado por todo o QGIS:
outros complementos, o Processing e rotinas deste próprio complemento que
esperam ``None`` como retorno de falha passam a receber exceções. Este módulo
liga as exceções apenas durante a função decorada e restaura o estado anterior,
inclusive quando ocorre erro.
"""
from contextlib import contextmanager
from functools import wraps


@contextmanager
def gdal_exceptions():
    from osgeo import gdal, ogr, osr
    modules = (gdal, ogr, osr)
    previous = [module.GetUseExceptions() for module in modules]
    for module in modules:
        module.UseExceptions()
    try:
        yield
    finally:
        for module, enabled in zip(modules, previous):
            if not enabled:
                module.DontUseExceptions()


def with_gdal_exceptions(function):
    """Decorador: executa ``function`` com exceções GDAL e restaura o estado."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        with gdal_exceptions():
            return function(*args, **kwargs)
    return wrapper
