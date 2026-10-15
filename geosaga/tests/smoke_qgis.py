"""Executar no Console Python do QGIS após ativar o Vista Saga Plugin:

    from geosaga.tests.smoke_qgis import check
    check()

Não faz escrita em arquivos nem executa a análise espacial.
"""
from qgis.core import QgsApplication, QgsProject


def check():
    registry = QgsApplication.processingRegistry()
    for name in ('avaliacao', 'monitoria', 'assinatura'):
        algorithm_id = 'geosaga:' + name
        algorithm = registry.algorithmById(algorithm_id)
        if algorithm is None:
            raise RuntimeError(f'Algoritmo ausente no QGIS: {algorithm_id}')
        if not algorithm.parameterDefinitions():
            raise RuntimeError(f'Algoritmo sem parâmetros: {algorithm_id}')
        print(f'OK: {algorithm_id} ({algorithm.displayName()})')
    print(f'OK: projeto QGIS acessível — {QgsProject.instance().fileName() or "sem arquivo"}')
    print('Registro validado. Execução geoespacial e interface ainda exigem testes manuais.')
    return True
