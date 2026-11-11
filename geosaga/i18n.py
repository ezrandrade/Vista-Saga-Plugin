"""Localização do Vista Saga Plugin baseada no idioma efetivo da interface QGIS.

Textos de origem: português brasileiro. Idiomas sem catálogo usam inglês.
Os nomes internos dos algoritmos, campos e parâmetros não são traduzidos.

Além de chaves exatas, o catálogo aceita MODELOS com marcadores numéricos,
por exemplo ``"Camada {0}: peso numérico obrigatório."``. Isso permite traduzir
mensagens montadas em tempo de execução (f-strings de exceções) sem alterar o
código que as gera: ``tr(str(exc))`` reconhece o modelo, traduz o texto fixo e
também tenta traduzir cada trecho variável (mensagens aninhadas).
"""
import json
import re
from functools import lru_cache
from pathlib import Path

_PLACEHOLDER = re.compile(r'\{(\d+)\}')
_MIN_LITERAL = 6      # modelos com pouco texto fixo casariam com qualquer frase
_MAX_DEPTH = 2        # profundidade de tradução de trechos aninhados


def normalize_language(locale_name):
    """Normaliza pt_BR, en_US, es_ES etc. sem confundir região e idioma."""
    return str(locale_name or "en").strip().replace("-", "_").split("_")[0].lower() or "en"


def qgis_language():
    """Lê a configuração vigente do QGIS, inclusive substituição de idioma.

    QgsApplication.locale() é preferível ao idioma do sistema operacional.
    """
    try:
        from qgis.core import QgsApplication
        value = QgsApplication.locale()
    except (ImportError, AttributeError, RuntimeError):
        # Permite testar os catálogos sem iniciar uma sessão do QGIS.
        import locale
        value = locale.getlocale()[0] or "en"
    return normalize_language(value)


@lru_cache(maxsize=8)
def _catalog(language):
    path = Path(__file__).resolve().parent / "i18n" / (language + ".json")
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as stream:
        translations = json.load(stream)
    if not isinstance(translations, dict):
        raise ValueError("O catálogo de traduções deve ser um objeto JSON.")
    return {k: v for k, v in translations.items() if isinstance(v, str) and v}


def _template_regex(key):
    """Converte 'A {0} B' em regex; chaves '{{'/'}}' representam chaves literais."""
    pattern, literal_size, position = [], 0, 0
    for match in _PLACEHOLDER.finditer(key):
        literal = key[position:match.start()].replace('{{', '{').replace('}}', '}')
        literal_size += len(literal.strip())
        pattern.append(re.escape(literal))
        pattern.append(r'(.+?)' if match.end() < len(key) else r'(.+)')
        position = match.end()
    tail = key[position:].replace('{{', '{').replace('}}', '}')
    literal_size += len(tail.strip())
    pattern.append(re.escape(tail))
    return re.compile(''.join(pattern) + r'\Z', re.DOTALL), literal_size


@lru_cache(maxsize=8)
def _templates(language):
    compiled = []
    for key, value in _catalog(language).items():
        if not _PLACEHOLDER.search(key):
            continue
        regex, size = _template_regex(key)
        if size >= _MIN_LITERAL:
            compiled.append((size, regex, value))
    compiled.sort(key=lambda item: -item[0])  # o modelo mais específico vence
    return tuple((regex, value) for _size, regex, value in compiled)


def _lookup(text, language, depth):
    exact = _catalog(language).get(text)
    if exact:
        return exact
    if depth > _MAX_DEPTH or len(text) > 4000:
        return None
    for regex, value in _templates(language):
        match = regex.match(text)
        if match is None:
            continue
        parts = [_translate(part, language, depth + 1) for part in match.groups()]
        try:
            return value.format(*parts)
        except (IndexError, KeyError, ValueError):
            return None
    return None


def _translate(text, language, depth=0):
    if language == "pt":
        return text
    result = _lookup(text, language, depth)
    if result is None and language != "en":
        result = _lookup(text, "en", depth)  # inglês: idioma de reserva
    return text if result is None else result


@lru_cache(maxsize=4096)
def translate_for_locale(text, locale_name):
    """Traduz exclusivamente strings conhecidas; não interfere nos dados."""
    if not isinstance(text, str) or not text:
        return text
    return _translate(text, normalize_language(locale_name))


def tr(text):
    """Tradução no idioma da GUI do QGIS, calculado na chamada.

    Aceita qualquer objeto: valores que não são texto retornam inalterados.
    """
    if not isinstance(text, str) or not text:
        return text
    return translate_for_locale(text, qgis_language())
