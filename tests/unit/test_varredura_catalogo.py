"""Padrões que o verificador de segurança do catálogo do QGIS (Bandit) bloqueia (1.6.1).

Qualquer achado do Bandit bloqueia a versão no plugins.qgis.org, mesmo de severidade baixa. A 1.6.0 foi
bloqueada por ``try/except/pass`` (B110) e pela importação de ``xml.sax`` (B406). Este teste falha antes do
envio, sem precisar do Bandit instalado.
"""
import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / 'geosaga'
EXCLUDED = {'tests', '__pycache__'}
BLOCKED_IMPORTS = ('xml.sax', 'xml.etree', 'xml.dom', 'xml.dom.minidom', 'pickle', 'telnetlib', 'ftplib')


def _sources():
    for path in sorted(PACKAGE.rglob('*.py')):
        if not EXCLUDED & set(path.relative_to(PACKAGE).parts) and path.name != 'home_dialog.py':
            yield path, ast.parse(path.read_text(encoding='utf-8'), filename=str(path))


def test_sem_try_except_pass():
    found = []
    for path, tree in _sources():
        for node in ast.walk(tree):
            generic = isinstance(node, ast.ExceptHandler) and (
                node.type is None or (isinstance(node.type, ast.Name) and node.type.id in ('Exception', 'BaseException')))
            if generic and all(isinstance(item, ast.Pass) for item in node.body):  # regra B110 do Bandit
                found.append(f'{path.name}:{node.lineno}')
    assert not found, f'use contextlib.suppress no lugar de try/except/pass: {found}'


def test_sem_importacoes_bloqueadas():
    found = []
    for path, tree in _sources():
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module or ''] if isinstance(node, ast.ImportFrom) else []
            found += [f'{path.name}:{node.lineno} {n}' for n in names
                      if any(n == b or n.startswith(b + '.') for b in BLOCKED_IMPORTS)]
    assert not found, f'importações recusadas pelo Bandit: {found}'
