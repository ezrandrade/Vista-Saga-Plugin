"""Arquivo de pesos e notas das avaliações vetoriais (sem PyQGIS).

O arquivo ``*.geosaga.json`` guarda o que o usuário configurou — camada de
origem, campo, peso, notas e classes não avaliadas — para que a mesma
configuração seja reaproveitada em outra avaliação. Ele não contém
resultados: estes ficam no GeoPackage e nos relatórios CSV/TXT.

Formato (versão 1)::

    {"formato": "geosaga-avaliacao-atributos" | "geosaga-avaliacao-sobreposicao",
     "versao": 1, "escala": 10 | 100,
     "criterios": [{"camada": "Solos", "fonte": "solos.gpkg|layername=solos",
                    "campo": "CLASSE", "peso": 50.0,
                    "notas": {"1": 7.0, "Argissolo": 3.5},
                    "nao_avaliar": ["99"]}]}

``fonte`` é gravada relativa à pasta do arquivo quando possível, como no
projeto da avaliação raster, para que a pasta inteira possa ser movida.
"""
import json
import math
import os

MODALITIES = {
    'atributos': 'geosaga-avaliacao-atributos',
    'sobreposicao': 'geosaga-avaliacao-sobreposicao',
}
VERSION = 1
MAX_SIZE = 5_000_000
MAX_CRITERIA = 50
SUFFIX = '.geosaga.json'


def config_path_for(destination):
    """Caminho do arquivo de pesos e notas gravado ao lado do resultado."""
    return os.path.splitext(os.path.abspath(destination))[0] + '_pesos_notas' + SUFFIX


def split_source(source):
    """Separa 'arquivo|layername=x' em ('arquivo', '|layername=x')."""
    text = str(source or '')
    path, sep, rest = text.partition('|')
    return path, (sep + rest) if sep else ''


def same_source(a, b):
    """Compara fontes OGR pelo arquivo normalizado e pelas opções da subcamada."""
    pa, sa = split_source(a)
    pb, sb = split_source(b)
    if not pa or not pb:
        return False
    norm = lambda p: os.path.normcase(os.path.realpath(os.path.abspath(p)))
    return norm(pa) == norm(pb) and sa == sb


def relative_source(source, base_dir):
    path, suffix = split_source(source)
    if not path or not os.path.isabs(path):
        return str(source or '')
    try:
        path = os.path.relpath(path, base_dir)
    except ValueError:  # outra unidade no Windows
        pass
    return path.replace(os.sep, '/') + suffix


def resolve_source(source, base_dir):
    path, suffix = split_source(source)
    if not path:
        return ''
    if not os.path.isabs(path):
        path = os.path.normpath(os.path.join(base_dir, path))
    return path + suffix


def build_config(modality, scale, criteria, base_dir):
    """criteria: dicts com camada, fonte, campo, peso, notas e nao_avaliar."""
    if modality not in MODALITIES:
        raise ValueError(f'Modalidade de avaliação desconhecida: {modality}.')
    records = []
    for c in criteria:
        records.append({
            'camada': str(c.get('camada', '')),
            'fonte': relative_source(c.get('fonte', ''), base_dir),
            'campo': str(c['campo']),
            'peso': round(float(c['peso']), 4),
            'notas': {str(k): float(v) for k, v in sorted(c.get('notas', {}).items())},
            'nao_avaliar': sorted(str(k) for k in c.get('nao_avaliar', ())),
        })
    return {'formato': MODALITIES[modality], 'versao': VERSION,
            'escala': int(scale), 'criterios': records}


def write_config(path, config):
    """Grava de forma atômica: um arquivo antigo nunca fica truncado."""
    path = os.path.abspath(path)
    temporary = path + '.tmp'
    with open(temporary, 'w', encoding='utf-8') as handle:
        json.dump(config, handle, ensure_ascii=False, indent=2)
    os.replace(temporary, path)
    return path


def parse_config(data, modality, base_dir):
    """Valida o conteúdo e devolve escala e critérios com fontes absolutas."""
    if not isinstance(data, dict):
        raise ValueError('Arquivo de pesos e notas inválido.')
    kind = data.get('formato')
    if kind not in MODALITIES.values():
        if kind == 'geosaga-avaliacao':
            raise ValueError('Este arquivo é um projeto da avaliação raster; abra-o na guia Raster.')
        raise ValueError('Arquivo de pesos e notas não reconhecido.')
    if kind != MODALITIES[modality]:
        other = 'Vetorial (Sobreposição)' if modality == 'atributos' else 'Vetorial (Atributos)'
        raise ValueError(f'Este arquivo pertence à outra modalidade vetorial; abra-o na guia {other}.')
    if data.get('versao') != VERSION:
        raise ValueError('Versão do arquivo de pesos e notas não suportada.')
    scale = data.get('escala')
    if scale not in (10, 100):
        raise ValueError('A escala de notas deve ser 0–10 ou 0–100.')
    records = data.get('criterios')
    if not isinstance(records, list) or not records or len(records) > MAX_CRITERIA:
        raise ValueError('Lista de critérios inválida.')
    criteria = []
    for i, rec in enumerate(records, 1):
        if not isinstance(rec, dict) or not str(rec.get('campo', '')).strip():
            raise ValueError(f'Critério {i}: campo ausente.')
        try:
            weight = float(rec.get('peso', 0))
        except (TypeError, ValueError) as exc:
            raise ValueError(f'Critério {i}: peso inválido.') from exc
        if not math.isfinite(weight) or not 0 <= weight <= 100:
            raise ValueError(f'Critério {i}: peso inválido.')
        notes = rec.get('notas', {})
        skipped = rec.get('nao_avaliar', [])
        if not isinstance(notes, dict) or not isinstance(skipped, list):
            raise ValueError(f'Critério {i}: notas inválidas.')
        clean = {}
        for key, value in notes.items():
            try:
                score = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f'Critério {i}: nota inválida para a classe {key}.') from exc
            if not math.isfinite(score) or not 0 <= score <= scale:
                raise ValueError(f'Critério {i}: nota fora da escala (classe {key}).')
            clean[str(key)] = score
        skipped = {str(k) for k in skipped}
        if skipped & set(clean):
            raise ValueError(f'Critério {i}: classe com nota e "Não avaliar" ao mesmo tempo.')
        criteria.append({'camada': str(rec.get('camada', '')),
                         'fonte': resolve_source(rec.get('fonte', ''), base_dir),
                         'campo': str(rec['campo']).strip(), 'peso': weight,
                         'notas': clean, 'nao_avaliar': skipped})
    return {'escala': scale, 'criterios': criteria}


def read_config(path, modality):
    path = os.path.abspath(path)
    if os.path.getsize(path) > MAX_SIZE:
        raise ValueError('Arquivo de projeto excessivamente grande.')
    with open(path, encoding='utf-8') as handle:
        data = json.load(handle)
    return parse_config(data, modality, os.path.dirname(path))


def apply_saved(criterion, saved):
    """Copia peso, notas e 'Não avaliar' só para as classes que existem hoje.

    Retorna (classes do arquivo que não existem mais, classes atuais sem
    tratamento). O usuário precisa saber de ambas: a primeira indica que os
    dados mudaram; a segunda, que ainda há notas a atribuir.
    """
    present = set(criterion['counts'])
    criterion['weight'] = float(saved['peso'])
    criterion['notes'] = {k: v for k, v in saved['notas'].items() if k in present}
    criterion['excluded'] = {k for k in saved['nao_avaliar'] if k in present}
    obsolete = (set(saved['notas']) | set(saved['nao_avaliar'])) - present
    pending = present - set(criterion['notes']) - criterion['excluded']
    return obsolete, pending
