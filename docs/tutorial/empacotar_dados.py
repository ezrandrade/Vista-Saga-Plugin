"""Pacotes de dados do tutorial para download (um por idioma): docs/tutorial/dados/dados_tutorial_vila_serena_<idioma>.zip

Uso, na raiz do repositório:  python3.12 docs/tutorial/empacotar_dados.py <pasta_de_trabalho>
Os números são os mesmos nos três idiomas: só mudam os nomes das classes, dos bairros e dos critérios.
"""
import json
import os
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gerar_dados  # noqa: E402
from executar_tutorial import EVALUATION  # noqa: E402

CRITERIA = {'pt': ['Declividade', 'Solos', 'Uso do solo 2020'], 'en': ['Slope', 'Soils', 'Land use 2020'],
            'es': ['Pendiente', 'Suelos', 'Uso del suelo 2020']}
README_NAME = {'pt': 'LEIA-ME.txt', 'en': 'README.txt', 'es': 'LEAME.txt'}
README = {
    'pt': """Vila Serena - dados do tutorial do Vista Saga Plugin 1.6.0

Cidade fictícia; todos os dados são sintéticos e de livre uso.
SRC: SIRGAS 2000 / UTM 25S (EPSG:31985). Rasters: 200 x 200 células de 10 m.

uso_solo_2000/2010/2020.tif    1 Área urbana, 2 Vegetação nativa, 3 Agricultura, 4 Pastagem, 5 Água
solos.tif                      1 Argissolo, 2 Latossolo, 3 Neossolo flúvico
declividade.tif                1 Plano, 2 Suave ondulado, 3 Ondulado, 4 Forte ondulado
atrito.tif                     nota de atrito (urbana 1, pastagem/agricultura 2, vegetação 4, água 10)
bairros.gpkg                   6 bairros (CODIGO, NOME)
escolas.gpkg                   6 escolas (NOME, MATRICULAS)
aptidao_expansao.geosaga.json  projeto da Avaliação (Abrir projeto...)

Mantenha os arquivos .aux.xml junto dos .tif: eles guardam os nomes das classes.
""",
    'en': """Vila Serena - tutorial data for Vista Saga Plugin 1.6.0

Fictitious town; all data are synthetic and free to use.
CRS: SIRGAS 2000 / UTM 25S (EPSG:31985). Rasters: 200 x 200 cells of 10 m.

uso_solo_2000/2010/2020.tif    land use: 1 Urban area, 2 Native vegetation, 3 Farming, 4 Pasture, 5 Water
solos.tif                      soils: 1 Argisol, 2 Latosol, 3 Fluvic neosol
declividade.tif                slope: 1 Flat, 2 Gently rolling, 3 Rolling, 4 Strongly rolling
atrito.tif                     friction rating (urban 1, pasture/farming 2, vegetation 4, water 10)
bairros.gpkg                   6 districts (CODIGO, NOME)
escolas.gpkg                   6 schools (NOME, MATRICULAS = enrolment)
aptidao_expansao.geosaga.json  Evaluation project (Open project...)

Keep the .aux.xml files next to the .tif files: they hold the class names.
""",
    'es': """Vila Serena - datos del tutorial del Vista Saga Plugin 1.6.0

Ciudad ficticia; todos los datos son sintéticos y de libre uso.
SRC: SIRGAS 2000 / UTM 25S (EPSG:31985). Rásteres: 200 x 200 celdas de 10 m.

uso_solo_2000/2010/2020.tif    uso del suelo: 1 Área urbana, 2 Vegetación nativa, 3 Agricultura, 4 Pastizal, 5 Agua
solos.tif                      suelos: 1 Argisol, 2 Latosol, 3 Neosol flúvico
declividade.tif                pendiente: 1 Plano, 2 Suave ondulado, 3 Ondulado, 4 Fuerte ondulado
atrito.tif                     nota de fricción (urbana 1, pastizal/agricultura 2, vegetación 4, agua 10)
bairros.gpkg                   6 barrios (CODIGO, NOME)
escolas.gpkg                   6 escuelas (NOME, MATRICULAS = matrícula)
aptidao_expansao.geosaga.json  proyecto de la Evaluación (Abrir proyecto...)

Mantenga los archivos .aux.xml junto a los .tif: guardan los nombres de las clases.
""",
}


def package(work, lang, out):
    folder = os.path.join(work, f'pacote_{lang}', 'dados')
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    gerar_dados.build(folder, lang)
    project = {'formato': 'geosaga-avaliacao', 'versao': 1, 'escala': EVALUATION['escala'],
               'camadas': [{'arquivo': f, 'nome': CRITERIA[lang][i], 'peso': w, 'notas': notes, 'bloqueadas': blocked}
                           for i, (f, _n, w, notes, blocked) in enumerate(EVALUATION['criterios'])]}
    with open(os.path.join(folder, 'aptidao_expansao.geosaga.json'), 'w', encoding='utf-8') as stream:
        json.dump(project, stream, ensure_ascii=False, indent=2)
    with open(os.path.join(folder, README_NAME[lang]), 'w', encoding='utf-8') as stream:
        stream.write(README[lang])
    target = os.path.join(out, f'dados_tutorial_vila_serena_{lang}.zip')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(os.listdir(folder)):
            archive.write(os.path.join(folder, name), f'vila_serena/dados/{name}')
    return target


if __name__ == '__main__':
    out = os.path.join(HERE, 'dados')
    os.makedirs(out, exist_ok=True)
    for language in ('pt', 'en', 'es'):
        path = package(os.path.abspath(sys.argv[1]), language, out)
        print(path, os.path.getsize(path))
