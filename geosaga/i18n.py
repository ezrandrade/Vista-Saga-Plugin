"""Localização do Vista Saga Plugin baseada no idioma efetivo da interface QGIS.

Textos de origem: português brasileiro. Idiomas sem catálogo usam inglês.
Os nomes internos dos algoritmos, campos e parâmetros não são traduzidos.
"""
import json
from functools import lru_cache
from pathlib import Path


def normalize_language(locale_name):
    """Normaliza pt_BR, en_US, es_ES etc. sem confundir região e idioma."""
    language = str(locale_name or "en").strip().replace("-", "_").split("_")[0].lower()
    return "pt" if language == "pt" else ("en" if language == "en" else language)


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
    return translations


def translate_for_locale(text, locale_name):
    """Traduz exclusivamente strings conhecidas; não interfere nos dados."""
    if not isinstance(text, str) or not text:
        return text
    lang = normalize_language(locale_name)
    if lang == "pt":
        return text  # O código-fonte já contém as mensagens originais.
    localized = _catalog(lang).get(text)
    if isinstance(localized, str) and localized:
        return localized
    # Inglês é idioma de fallback para quaisquer localidades sem catálogo.
    english = _catalog("en").get(text)
    return english if isinstance(english, str) and english else text


def tr(text):
    """Tradução no idioma da GUI do QGIS, calculado na chamada."""
    return translate_for_locale(text, qgis_language())
