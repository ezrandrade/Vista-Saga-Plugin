"""Resultados da Assinatura (1.5.0), comuns às guias Raster e Vetorial (sem PyQGIS e sem GDAL).

Modelo do Vista SAGA, conferido contra relatórios do programa original (caso de referência do autor,
20/11/2026): para cada mapa assinado e cada classe,

- ``total``: a classe no mapa inteiro;
- ``asn``: a classe dentro do limite (seleção feita no mapa de referência);
- ``% Área Asn.`` = asn / área do limite;
- ``% Categoria`` = asn / total da classe no mapa inteiro.

Todas as classes da legenda aparecem, inclusive as zeradas. FUNDO (RS2) e NoData (GeoTIFF) contam como
classe qualquer, dentro da base. Na guia Vetorial, a parte do limite sem polígono do mapa é a linha
"Sem classe" e a sobreposição de classes excluída é a linha "Sobreposição excluída", ambas dentro da base.
"""
from dataclasses import dataclass, field

NODATA_KEY = 'NODATA'
NO_CLASS_KEY = 'SEM_CLASSE'
CONFLICT_KEY = 'SOBREPOSICAO'

SPECIAL_LABELS = {
    NODATA_KEY: 'NoData',
    NO_CLASS_KEY: 'Sem classe',
    CONFLICT_KEY: 'Sobreposição excluída',
}


@dataclass
class ClassRow:
    """Uma classe de um mapa assinado. Em vetor, as contagens de células ficam ``None``."""
    key: object
    label: str
    total_ha: float
    asn_ha: float
    pct_area: float
    pct_category: object  # None quando não se aplica ("Sem classe")
    total_cells: object = None
    asn_cells: object = None

    @property
    def code_text(self):
        return '' if is_special(self.key) else str(self.key)

    @property
    def display(self):
        """Rótulo de tabela: "código - nome", ou só o nome quando o código já é o próprio nome (vetor)."""
        code = self.code_text
        return self.label if not code or code == self.label else f'{code} - {self.label}'


@dataclass
class MapSignature:
    name: str
    rows: list
    total_ha: float
    asn_ha: float
    total_cells: object = None
    asn_cells: object = None


@dataclass
class FeatureSignature:
    """Resultado de um recorte: a união da seleção ou uma feição (classe, no raster)."""
    key: object
    name: str
    maps: list


@dataclass
class SignatureResult:
    kind: str  # 'raster' | 'vector'
    reference: str
    selection: list  # rótulos do que foi selecionado na referência
    union: FeatureSignature
    features: list = field(default_factory=list)
    srs_name: str = ''
    cell_ha: object = None
    warnings: list = field(default_factory=list)
    notes: list = field(default_factory=list)  # registros sem alerta (ex.: lascas toleradas)


def is_special(key):
    return isinstance(key, str) and key in SPECIAL_LABELS


def label_for(key, legend):
    if is_special(key):
        return SPECIAL_LABELS[key]
    return legend.get(key) or f'Classe {key}'


def sort_key(key):
    """Números antes de textos, cada grupo na ordem natural."""
    return (isinstance(key, str), key if not isinstance(key, str) else key.casefold())


def ordered_keys(legend, present):
    """Legenda na ordem gravada; depois códigos presentes fora dela; por último as linhas especiais."""
    keys = list(legend)
    extra = sorted((k for k in present if not is_special(k) and k not in legend), key=sort_key)
    special = [k for k in (NODATA_KEY, CONFLICT_KEY, NO_CLASS_KEY) if k in present]
    return keys + extra + special


def _pct(part, whole):
    return 100.0 * part / whole if whole else 0.0


def raster_map_signature(name, legend, totals, inside, cell_ha):
    """Monta a assinatura de um mapa raster a partir das contagens de células por código."""
    mask_cells = sum(inside.values())
    rows = []
    for key in ordered_keys(legend, set(totals) | set(inside)):
        total = int(totals.get(key, 0))
        asn = int(inside.get(key, 0))
        rows.append(ClassRow(key, label_for(key, legend), total * cell_ha, asn * cell_ha,
                             _pct(asn, mask_cells), _pct(asn, total), total, asn))
    total_cells = int(sum(totals.values()))
    return MapSignature(name, rows, total_cells * cell_ha, mask_cells * cell_ha,
                        total_cells, int(mask_cells))


def vector_map_signature(name, legend, totals_ha, inside_ha, mask_ha, conflict_total_ha=0.0,
                         conflict_inside_ha=0.0, no_class_ha=None):
    """Assinatura de um mapa vetorial a partir das áreas (ha) por classe.

    ``no_class_ha``: área do limite sem polígono do mapa ("Sem classe"), já sem as frestas toleradas.
    Sem ela, a diferença entre a área do limite e a soma das classes e da sobreposição excluída vira
    "Sem classe".
    """
    inside = dict(inside_ha)
    totals = dict(totals_ha)
    if conflict_total_ha > 0 or conflict_inside_ha > 0:
        totals[CONFLICT_KEY] = conflict_total_ha
        inside[CONFLICT_KEY] = conflict_inside_ha
    missing = mask_ha - sum(inside.values()) if no_class_ha is None else no_class_ha
    # Resíduo numérico de interseções (abaixo de 1 cm², em ha) não é falta de dado.
    if missing > 1e-8:
        inside[NO_CLASS_KEY] = missing
    rows = []
    for key in ordered_keys(legend, set(totals) | set(inside)):
        asn = float(inside.get(key, 0.0))
        total = float(totals.get(key, 0.0)) if key != NO_CLASS_KEY else 0.0
        category = None if key == NO_CLASS_KEY else _pct(asn, total)
        rows.append(ClassRow(key, label_for(key, legend), total, asn, _pct(asn, mask_ha), category))
    map_total = sum(v for k, v in totals.items())
    return MapSignature(name, rows, map_total, mask_ha)
