"""O catálogo oficial (plugins.qgis.org) lê o metadata.txt com ConfigParser, que interpreta '%'.

Na 1.6.0 o envio foi recusado porque o "about" e o changelog tinham '%' ("100%"). Este teste lê o arquivo do
mesmo jeito e confere os campos obrigatórios do catálogo.
"""
import configparser
from pathlib import Path

METADATA = Path(__file__).resolve().parents[2] / 'geosaga' / 'metadata.txt'
REQUIRED = ('name', 'qgisMinimumVersion', 'description', 'about', 'version', 'author', 'email', 'repository',
            'tracker')


def test_metadata_le_como_no_catalogo():
    parser = configparser.ConfigParser()
    parser.read(METADATA, encoding='utf-8')
    general = parser['general']
    values = {key: general[key] for key in general}  # levanta InterpolationSyntaxError se houver '%' solto
    for key in REQUIRED:
        assert values.get(key.lower(), '').strip(), f'campo obrigatório vazio: {key}'


def test_metadata_sem_percentual_solto():
    assert '%' not in METADATA.read_text(encoding='utf-8'), "use 'percent' no lugar de '%' no metadata.txt"
