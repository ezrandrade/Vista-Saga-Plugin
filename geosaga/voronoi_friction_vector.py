"""Superfície de atrito vetorial (1.4.0): polígonos com nota → grade de notas para o Voronoi.

O cálculo do atrito do Vista SAGA é célula a célula, então os polígonos são rasterizados na grade
da análise (extensão e resolução escolhidas pelo usuário), pela regra do centro da célula (a
célula recebe a nota do polígono que contém o seu centro). Onde polígonos se sobrepõem, vale o
último na ordem das feições.

A nota de cada polígono vem de uma tabela classe → nota (como na Avaliação) ou de uma coluna
numérica da camada. A área sem polígono recebe uma nota informada pelo usuário ou é barreira; o
plugin nunca supõe uma nota. Barreira = NoData: a célula não recebe resultado e nenhuma reta
passa por ela.

Os dados chegam já extraídos do QGIS na thread principal (WKB + nota); aqui só há GDAL/OGR, na
thread da tarefa. Sem reprojeção: as geometrias precisam estar no SRC da grade.
"""
import math

import numpy as np

BARRIER = 'barreira'
_OUTSIDE = -1.0   # sentinela: célula sem polígono (notas são >= 0)
_BLOCKED = -2.0   # sentinela: polígono de classe marcada como barreira


def check_rating(value, label):
    """Nota finita e >= 0, ou a barreira; devolve float ou BARRIER."""
    if value == BARRIER:
        return BARRIER
    try:
        rating = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'Nota de atrito não numérica: {label}.') from None
    if not math.isfinite(rating) or rating < 0:
        raise ValueError(f'Nota de atrito inválida (use valor >= 0): {label}.')
    return rating


def ratings_from_classes(values, notes, barriers=()):
    """Traduz o valor de classe de cada feição em nota; None (campo vazio) fica fora da grade.

    values: valor do campo de classe por feição (None = vazio). notes: {classe (texto): nota}.
    barriers: classes marcadas como barreira. Classes sem nota bloqueiam (lista na mensagem).
    """
    barriers = {str(code) for code in barriers}
    out, missing = [], []
    for value in values:
        if value is None:
            out.append(None)
            continue
        key = str(value)
        if key in barriers:
            out.append(BARRIER)
        elif key in notes:
            out.append(check_rating(notes[key], key))
        else:
            out.append(None)
            if key not in missing:
                missing.append(key)
    if missing:
        shown = ', '.join(missing[:20]) + (', …' if len(missing) > 20 else '')
        raise ValueError(f'Classes sem nota de atrito: {shown}. Atribua uma nota ou marque "Barreira".')
    return out


def ratings_from_column(values):
    """Coluna numérica com a nota de cada feição; vazio (None) fica fora da grade."""
    return [None if value is None else check_rating(value, f'feição {index + 1}')
            for index, value in enumerate(values)]


def rasterize_friction(features, outside, geotransform, width, height, projection_wkt):
    """Grade float64 de notas (NaN = barreira) a partir de [(wkb, nota | BARRIER)].

    outside: nota da área sem polígono, BARRIER, ou None (exige cobertura total; células
    descobertas geram erro). Retorna (grade, estatísticas).
    """
    from osgeo import gdal, ogr, osr
    from .gdal_scope import with_gdal_exceptions

    @with_gdal_exceptions
    def burn():
        srs = osr.SpatialReference()
        if srs.ImportFromWkt(projection_wkt) != 0:
            raise ValueError('SRC inválido para a superfície de atrito vetorial.')
        source = None
        # GDAL < 3.11: driver vetorial "Memory"; a partir da 3.11 ele foi fundido ao "MEM".
        for name in ('Memory', 'MEM'):
            driver = ogr.GetDriverByName(name)
            if driver is not None and driver.GetMetadataItem('DCAP_VECTOR') == 'YES':
                source = driver.CreateDataSource('atrito')
                break
        if source is None:
            raise RuntimeError('GDAL sem driver vetorial em memória para o atrito vetorial.')
        layer = source.CreateLayer('atrito', srs, ogr.wkbUnknown)
        layer.CreateField(ogr.FieldDefn('NOTA', ogr.OFTReal))
        definition = layer.GetLayerDefn()
        used = 0
        for wkb, rating in features:
            if rating is None:
                continue
            geometry = ogr.CreateGeometryFromWkb(bytes(wkb))
            if geometry is None or geometry.IsEmpty():
                continue
            feature = ogr.Feature(definition)
            feature.SetGeometry(geometry)
            feature.SetField('NOTA', _BLOCKED if rating == BARRIER else float(rating))
            layer.CreateFeature(feature)
            used += 1
        target = gdal.GetDriverByName('MEM').Create('', int(width), int(height), 1, gdal.GDT_Float64)
        target.SetGeoTransform(tuple(float(v) for v in geotransform))
        target.SetProjection(projection_wkt)
        band = target.GetRasterBand(1)
        band.Fill(_OUTSIDE)
        if used:
            gdal.RasterizeLayer(target, [1], layer, options=['ATTRIBUTE=NOTA', 'ALL_TOUCHED=FALSE'])
        grid = band.ReadAsArray().astype(np.float64)
        return grid, used

    grid, used = burn()
    uncovered = grid == _OUTSIDE
    blocked = grid == _BLOCKED
    stats = {'features': used, 'uncovered_cells': int(uncovered.sum()),
             'barrier_cells': int(blocked.sum())}
    if uncovered.any():
        if outside is None:
            raise ValueError(f'{stats["uncovered_cells"]} células da grade não são cobertas por '
                             'polígonos: informe a nota da área sem polígono ou marque-a como barreira.')
        grid[uncovered] = np.nan if outside == BARRIER else check_rating(outside, 'área sem polígono')
    grid[blocked] = np.nan
    return grid, stats


def describe(spec, stats, resolution):
    """Linhas do relatório _resumo.txt sobre a superfície vetorial."""
    lines = ['', 'Superfície de atrito vetorial',
             f"Camada: {spec.get('layer_name', '')}"]
    if spec.get('class_field'):
        lines.append(f"Notas por classe do campo {spec['class_field']} (tabela classe → nota):")
        for code, rating in sorted(spec.get('notes', {}).items(), key=lambda item: str(item[0])):
            lines.append(f'  {code}: {rating:g}')
        for code in spec.get('barriers', []):
            lines.append(f'  {code}: barreira')
    else:
        lines.append(f"Notas da coluna {spec.get('rating_field', '')}.")
    outside = spec.get('outside')
    lines.append('Área sem polígono: ' + ('barreira' if outside == BARRIER else
                 'não informada (exige cobertura total)' if outside is None else f'nota {outside:g}'))
    lines.append(f'Rasterização pelo centro da célula, resolução {resolution:g} unidades do SRC; '
                 'em sobreposições vale a última feição.')
    lines.append(f"Feições usadas: {stats['features']}; células sem polígono: {stats['uncovered_cells']}; "
                 f"células de barreira: {stats['barrier_cells']}.")
    if spec.get('skipped'):
        lines.append(f"Feições com o campo vazio (tratadas como área sem polígono): {spec['skipped']}.")
    return '\n'.join(lines) + '\n'
