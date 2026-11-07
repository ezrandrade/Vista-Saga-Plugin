"""Configuração dos testes unitários: importa o pacote geosaga sem iniciar o QGIS.

Defina VSP_PLUGIN_PARENT com a pasta que contém o diretório ``geosaga``;
por padrão usa a raiz do repositório (testa o código-fonte da árvore atual).
"""
import os
import sys
from pathlib import Path

PARENT = Path(os.environ.get('VSP_PLUGIN_PARENT',
                             Path(__file__).resolve().parents[2])).resolve()
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
PLUGIN_DIR = PARENT / 'geosaga'
