"""Assinatura na guia Vetorial (1.5.0): geometrias exatas com OGR/GEOS, sem PyQGIS.

A janela entrega WKB e valores de classe já lidos das camadas do QGIS; este módulo só faz geometria e
contas, e por isso é testável sem o QGIS. Regras (decisões do autor, 20/11/2026): só vetor; mesmo SRC,
projetado em metros (o plugin não reprojeta); limite = feições selecionadas na referência (união e,
opcionalmente, uma por feição); parte do limite sem polígono = "Sem classe".

Sobreposição entre classes diferentes de um mesmo mapa (tratamento da 0.5.1): ``'exclude'`` retira a
região ambígua de todas as classes e a informa à parte; ``'strict'`` interrompe. Polígonos sobrepostos
da mesma classe contam uma vez (dissolvidos).
"""
from dataclasses import dataclass, field

from .gdal_scope import with_gdal_exceptions
from .signature_model import FeatureSignature, SignatureResult, sort_key, vector_map_signature

OVERLAP_POLICIES = ('exclude', 'strict')
_AREA_EPS_M2 = 1e-4  # 1 cm²: abaixo disso, interseção é resíduo numérico


@dataclass
class VectorMap:
    """Um mapa vetorial: ``features`` = [(id, wkb, código, nome da classe)]."""
    name: str
    srs_wkt: str
    features: list = field(default_factory=list)


def _geometry(wkb, fid, map_name):
    from osgeo import ogr
    try:
        geom = ogr.CreateGeometryFromWkb(bytes(wkb))
    except RuntimeError:
        geom = None
    if geom is None or geom.IsEmpty():
        raise ValueError(f'Geometria vazia ou ilegível na feição {fid} do mapa {map_name}.')
    if geom.HasCurveGeometry():
        geom = geom.GetLinearGeometry()
    geom.FlattenTo2D()
    if ogr.GT_Flatten(geom.GetGeometryType()) not in (ogr.wkbPolygon, ogr.wkbMultiPolygon):
        raise ValueError(f'O mapa {map_name} deve conter apenas polígonos.')
    if not geom.IsValid():
        raise ValueError(f'Geometria inválida na feição {fid} do mapa {map_name}; use Corrigir '
                         'geometrias no QGIS.')
    return geom


def _polygons(geom):
    """Partes poligonais de uma geometria (interseções podem devolver coleções com linhas e pontos)."""
    from osgeo import ogr
    kind = ogr.GT_Flatten(geom.GetGeometryType())
    if kind == ogr.wkbPolygon:
        yield geom
    elif kind in (ogr.wkbMultiPolygon, ogr.wkbGeometryCollection):
        for i in range(geom.GetGeometryCount()):
            yield from _polygons(geom.GetGeometryRef(i))


def _union(geoms):
    from osgeo import ogr
    multi = ogr.Geometry(ogr.wkbMultiPolygon)
    for geom in geoms:
        for part in _polygons(geom):
            multi.AddGeometry(part)
    return multi.UnionCascaded() if multi.GetGeometryCount() else multi


def _area(geom):
    return 0.0 if geom is None or geom.IsEmpty() else geom.GetArea()


def _check_srs(maps):
    from osgeo import osr
    ref = osr.SpatialReference()
    if not maps[0].srs_wkt or ref.ImportFromWkt(maps[0].srs_wkt) != 0:
        raise ValueError(f'O mapa {maps[0].name} não tem SRC definido.')
    if not ref.IsProjected():
        raise ValueError('O SRC dos mapas deve ser projetado, em metros; SRC geográfico (graus) não é aceito.')
    if abs(ref.GetLinearUnits() - 1.0) > 1e-9:
        raise ValueError('O SRC dos mapas deve ter unidade em metros.')
    for other in maps[1:]:
        srs = osr.SpatialReference()
        if not other.srs_wkt or srs.ImportFromWkt(other.srs_wkt) != 0 or not ref.IsSame(srs):
            raise ValueError(f'O mapa {other.name} está em outro SRC. Todos os mapas devem estar no mesmo '
                             'SRC; o plugin não reprojeta.')
    return ref.GetName()


def _classes(vmap, warnings, cancelled):
    """Geometrias dissolvidas por classe e legenda (código -> nome) de um mapa."""
    parts, legend, skipped = {}, {}, 0
    for fid, wkb, code, label in vmap.features:
        if cancelled and cancelled():
            raise InterruptedError('Assinatura cancelada.')
        if code is None or (isinstance(code, str) and not code.strip()):
            skipped += 1
            continue
        label = str(label) if label not in (None, '') else str(code)
        if code in legend and legend[code] != label:
            raise ValueError(f'Código {code} apresenta legendas diferentes no mapa {vmap.name}.')
        legend[code] = label
        parts.setdefault(code, []).append(_geometry(wkb, fid, vmap.name))
    if skipped:
        warnings.append(f'Mapa {vmap.name}: {skipped} feições sem classe foram ignoradas.')
    order = sorted(parts, key=sort_key)
    return {code: _union(parts[code]) for code in order}, {code: legend[code] for code in order}


def _resolve(classes, policy, map_name):
    """Retira a sobreposição entre classes diferentes (``exclude``) ou interrompe (``strict``)."""
    codes = list(classes)
    pieces = []
    for i, a in enumerate(codes):
        for b in codes[i + 1:]:
            inter = classes[a].Intersection(classes[b])
            if inter is not None and _area(inter) > _AREA_EPS_M2:
                if policy == 'strict':
                    raise ValueError(f'Classes diferentes se sobrepõem no mapa {map_name} (códigos {a} e {b}). '
                                     'Corrija a camada ou escolha excluir a sobreposição.')
                pieces.append(inter)
    if not pieces:
        return classes, None
    conflict = _union(pieces)
    return {code: geom.Difference(conflict) for code, geom in classes.items()}, conflict


def _map_signature(vmap, legend, classes, conflict, mask, mask_ha):
    totals = {code: _area(geom) / 10000.0 for code, geom in classes.items()}
    inside = {code: _area(geom.Intersection(mask)) / 10000.0 for code, geom in classes.items()}
    conflict_total = _area(conflict) / 10000.0
    conflict_inside = _area(conflict.Intersection(mask)) / 10000.0 if conflict is not None else 0.0
    return vector_map_signature(vmap.name, legend, totals, inside, mask_ha, conflict_total, conflict_inside)


@with_gdal_exceptions
def run_vector_signature(maps, selected, *, per_feature=True, overlap='exclude', progress=None,
                         cancelled=None):
    """Assina todos os ``maps`` dentro das feições ``selected`` do primeiro (a referência).

    ``selected``: [(id, nome, wkb)] das feições selecionadas na referência.
    """
    if not maps:
        raise ValueError('Adicione pelo menos um mapa à lista.')
    if overlap not in OVERLAP_POLICIES:
        raise ValueError('Tratamento de sobreposição não reconhecido.')
    if not selected:
        raise ValueError('Selecione pelo menos uma feição do mapa de referência.')
    srs_name = _check_srs(maps)
    reference = maps[0]
    cuts = [(fid, str(name) if name not in (None, '') else str(fid), _geometry(wkb, fid, reference.name))
            for fid, name, wkb in selected]
    union_geom = _union([g for _fid, _name, g in cuts])
    union_ha = _area(union_geom) / 10000.0
    if union_ha <= 0:
        raise ValueError('As feições selecionadas não têm área.')
    warnings = []
    prepared = []
    for i, vmap in enumerate(maps):
        classes, legend = _classes(vmap, warnings, cancelled)
        classes, conflict = _resolve(classes, overlap, vmap.name)
        if conflict is not None:
            warnings.append(f'Mapa {vmap.name}: {_area(conflict) / 10000.0:.4f} ha de sobreposição entre '
                            'classes diferentes foram excluídos.')
        prepared.append((vmap, legend, classes, conflict))
        if progress:
            progress(0.5 * (i + 1) / len(maps))
    union_maps = [_map_signature(v, lg, c, cf, union_geom, union_ha) for v, lg, c, cf in prepared]
    for signature in union_maps:
        missing = sum(r.asn_ha for r in signature.rows if r.key == 'SEM_CLASSE')
        if missing > 0:
            warnings.append(f'Mapa {signature.name}: {missing:.4f} ha do limite sem polígono (Sem classe).')
    features = []
    if per_feature:
        for n, (fid, name, geom) in enumerate(cuts):
            if cancelled and cancelled():
                raise InterruptedError('Assinatura cancelada.')
            area_ha = _area(geom) / 10000.0
            features.append(FeatureSignature(fid, name, [
                _map_signature(v, lg, c, cf, geom, area_ha) for v, lg, c, cf in prepared]))
            if progress:
                progress(0.5 + 0.5 * (n + 1) / len(cuts))
    selection = [name for _fid, name, _geom in cuts]
    union = FeatureSignature('UNIAO', 'União da seleção', union_maps)
    return SignatureResult('vector', reference.name, selection, union, features, srs_name, None, warnings)
