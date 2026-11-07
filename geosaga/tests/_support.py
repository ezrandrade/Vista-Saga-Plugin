"""Verificações estruturais compartilhadas pelos testes de integração do plugin.

Os testes antigos procuravam trechos literais do código-fonte (por exemplo,
``"self._add_menu_action('Avaliação', self.open_interactive)"``) e versões
fixas (``version=1.0.3``), quebrando a cada versão. Estas funções leem a
estrutura real: a tabela ``MODULES`` do plugin.py, os métodos da classe e a
versão declarada no metadata.txt comparada com o CHANGELOG.md.
"""
import ast
import configparser
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _plugin_tree():
    return ast.parse((ROOT / 'plugin.py').read_text(encoding='utf-8'))


def menu_entries():
    """[(título, método público)] na ordem do menu, a partir de MODULES."""
    for node in _plugin_tree().body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', '') == 'MODULES' for t in node.targets):
            return [(item.elts[3].value, item.elts[4].value) for item in node.value.elts]
    raise AssertionError('MODULES não encontrado em plugin.py')


def module_attributes():
    for node in _plugin_tree().body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', '') == 'MODULES' for t in node.targets):
            return [item.elts[0].value for item in node.value.elts]
    raise AssertionError('MODULES não encontrado em plugin.py')


def plugin_methods():
    cls = next(n for n in _plugin_tree().body if isinstance(n, ast.ClassDef) and n.name == 'VistaSagaPlugin')
    return {n.name for n in cls.body if isinstance(n, ast.FunctionDef)}


def metadata():
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(ROOT / 'metadata.txt', encoding='utf-8')
    return cfg['general']


def assert_release_version(test):
    """Versão única no metadata.txt e igual à primeira entrada do CHANGELOG.md."""
    text = (ROOT / 'metadata.txt').read_text(encoding='utf-8')
    versions = re.findall(r'^version=(.+)$', text, flags=re.M)
    test.assertEqual(len(versions), 1)
    version = versions[0].strip()
    test.assertRegex(version, r'^\d+\.\d+\.\d+$')
    first = re.search(r'^## (\S+)', (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8'), flags=re.M)
    test.assertIsNotNone(first)
    test.assertEqual(first.group(1), version)
    return version
