"""Apoio comum aos testes estáticos (sem PyQGIS).

Evita duas fragilidades que deixaram 16 testes falhando após a 1.0.4:

- número de versão escrito à mão em cada teste (``version=1.0.3``);
- busca de trechos exatos de código que mudaram com a tradução, como
  ``QPushButton('Fechar')`` → ``QPushButton(tr('Fechar'))``.
"""
import ast
import configparser
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Estável (1.0.4) ou de teste (1.0.4-rc10, 1.0.5-dev3).
VERSION_PATTERN = re.compile(r'^\d+\.\d+\.\d+(?:-(?:rc|dev)\d+)?$')


def source(name):
    return (ROOT / name).read_text(encoding='utf-8')


def metadata():
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(ROOT / 'metadata.txt', encoding='utf-8')
    return cfg['general']


def check_release_metadata(test):
    """Coerência da versão em vez de um número fixo que envelhece a cada lançamento."""
    text = source('metadata.txt')
    test.assertEqual(len(re.findall(r'^version=', text, flags=re.M)), 1,
                     'metadata.txt deve ter exatamente uma linha version=')
    version = metadata()['version'].strip()
    test.assertRegex(version, VERSION_PATTERN)
    test.assertEqual(metadata()['qgisMinimumVersion'], '4.0')
    test.assertTrue(metadata()['changelog'].lstrip().startswith(version + ':'),
                    'O changelog do metadata.txt deve começar pela versão atual.')
    test.assertRegex(source('CHANGELOG.md'), r'(?m)^## ' + re.escape(version) + r'\b',
                     'CHANGELOG.md deve ter uma seção para a versão atual.')
    if '-' not in version:
        # O script de build inclui esta nota no ZIP de uma versão estável.
        notes = ROOT / f"NOTAS_DA_VERSAO_{version.replace('.', '')}.md"
        test.assertTrue(notes.is_file(), f'Nota da versão ausente: {notes.name}')
    return version


def ui_text(text):
    """Expressão regular para um texto de interface, traduzido ou não: 'X' ou tr('X')."""
    literal = re.escape(repr(text))
    return rf"(?:{literal}|tr\({literal}\))"


def menu_modules():
    """Lista ``(título, callback)`` dos módulos do menu, lida da estrutura de ``plugin.py``.

    Na 1.0.4 o menu passou a ser montado por um laço sobre a tupla ``modules``
    em ``initGui``, em vez de uma chamada ``_add_menu_action`` por módulo.
    """
    tree = ast.parse(source('plugin.py'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'VistaSagaPlugin')
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'initGui')
    assignment = next(n for n in ast.walk(init) if isinstance(n, ast.Assign) and
                      any(isinstance(t, ast.Name) and t.id == 'modules' for t in n.targets))
    calls = [n for n in ast.walk(init) if isinstance(n, ast.Call) and
             isinstance(n.func, ast.Attribute) and n.func.attr == '_add_menu_action']
    if len(calls) != 1:
        raise AssertionError('Esperada uma única chamada _add_menu_action no laço de módulos.')
    return [(item.elts[0].value, item.elts[1].attr) for item in assignment.value.elts]
