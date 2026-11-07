"""Catálogos e mecanismo de tradução (i18n.py) — sem QGIS."""
import ast
import json
import re

import pytest

from conftest import PLUGIN_DIR
from geosaga.i18n import translate_for_locale as t, normalize_language

PH = re.compile(r'(?<!\{)\{([A-Za-z0-9_]*)\}(?!\})')


def load(lang):
    return json.loads((PLUGIN_DIR / 'i18n' / f'{lang}.json').read_text(encoding='utf-8'))


def test_language_normalization():
    assert normalize_language('pt_BR') == 'pt'
    assert normalize_language('en-US') == 'en'
    assert normalize_language('') == 'en'


def test_portuguese_is_identity_and_unknown_text_unchanged():
    assert t('Operação cancelada.', 'pt_BR') == 'Operação cancelada.'
    assert t('texto que não existe no catálogo', 'en_US') == 'texto que não existe no catálogo'
    assert t(None, 'en') is None


def test_exact_and_template_translation():
    assert t('Operação cancelada.', 'en_US') == 'Operation cancelled.'
    assert t('Camada 3: peso numérico obrigatório.', 'en') == 'Layer 3: a numeric weight is required.'
    assert t('Foram selecionados 2 rasters, mas há 3 regras.', 'en') == '2 rasters were selected, but there are 3 rules.'


def test_nested_message_translation():
    inner = 'Não foi possível abrir o TIFF.'
    outer = f'Falha na interseção do mapa 2: {inner}'
    assert t(outer, 'en') == 'Intersection of map 2 failed: Could not open the TIFF.'


def test_unsupported_language_falls_back_to_english():
    assert t('Operação cancelada.', 'de_DE') == 'Operation cancelled.'
    assert t('Camada 3: peso numérico obrigatório.', 'fr') == 'Layer 3: a numeric weight is required.'


@pytest.mark.parametrize('lang', ['en', 'es'])
def test_catalog_placeholders_and_newlines_match(lang):
    bad = [k for k, v in load(lang).items()
           if sorted(PH.findall(k)) != sorted(PH.findall(v)) or k.count('\n') != v.count('\n')]
    assert bad == []


def _template(js):
    parts, n = [], 0
    for v in js.values:
        if isinstance(v, ast.Constant):
            parts.append(v.value.replace('{', '{{').replace('}', '}}'))
        else:
            parts.append('{%d}' % n)
            n += 1
    return ''.join(parts)


def test_every_user_message_in_code_has_english_translation():
    """tr('...'), mensagens de exceção e avisos do Processing devem estar no catálogo."""
    en = load('en')
    missing = set()
    for path in PLUGIN_DIR.rglob('*.py'):
        if 'tests' in path.relative_to(PLUGIN_DIR).parts:
            continue  # suíte histórica: mensagens de assert não são texto de usuário
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            name = getattr(node.func, 'id', None) or getattr(node.func, 'attr', None) or ''
            if not (name == 'tr' or name.endswith(('Error', 'Exception'))
                    or name in ('pushWarning', 'pushInfo', 'reportError')):
                continue
            arg = node.args[0]
            key = (arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                   else _template(arg) if isinstance(arg, ast.JoinedStr) else None)
            if key and any(c.isalpha() for c in key) and key not in en:
                missing.add((path.name, key[:80]))
    assert sorted(missing) == []
