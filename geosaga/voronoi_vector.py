"""Voronoi euclidiano vetorial exato (no plano do SRC), sem rasterização.

Recorta células por semiplanos das bissetrizes e, opcionalmente, pelo
polígono de estudo em PyQGIS. Os limites de saída são finitos e explícitos.
"""
import csv
import math
import os
import shutil
import tempfile
import time
from .voronoi_core import validate_generators
from .voronoi_output import LAYER_NAME, VECTOR_FORMATS, export_vector, publish_outputs


def _clip_halfplane(polygon, sx, sy, tx, ty, eps=1e-10):
    """Conserva pontos mais próximos de S=(sx,sy) que de T=(tx,ty)."""
    dx, dy = tx-sx, ty-sy
    threshold = (dx*dx+dy*dy)/2.
    def signed(p):
        return (p[0]-sx)*dx+(p[1]-sy)*dy-threshold
    if not polygon:
        return []
    result = []
    prev = polygon[-1]
    prev_value = signed(prev)
    for current in polygon:
        value = signed(current)
        inside = value <= eps
        was_inside = prev_value <= eps
        if inside != was_inside:
            denom = prev_value-value
            fraction = prev_value/denom if denom else .5
            fraction = max(0.,min(1.,fraction))
            result.append((prev[0]+fraction*(current[0]-prev[0]),
                           prev[1]+fraction*(current[1]-prev[1])))
        if inside:
            result.append(current)
        prev, prev_value = current, value
    return result


def simple_voronoi_polygons(generators, bounds, *, cancelled=None, progress=None):
    """Produz um polígono fechado (lista x,y) por centro, recortado à bbox.

    Não usa SciPy nem depende da ordem dos triângulos. Em caso de empate exato
    na bissetriz, as regiões compartilham a fronteira (área zero).
    """
    validate_generators(generators)
    xmin, ymin, xmax, ymax = map(float,bounds)
    if not all(math.isfinite(v) for v in (xmin,ymin,xmax,ymax)) or xmin>=xmax or ymin>=ymax:
        raise ValueError('A extensão do Voronoi precisa ter área positiva.')
    if len(generators)>1000:
        raise ValueError('Esta versão aceita até 1.000 centros; divida a análise.')
    rectangle=[(xmin,ymin),(xmax,ymin),(xmax,ymax),(xmin,ymax)]
    for idx, centre in enumerate(generators):
        if cancelled and cancelled():
            raise InterruptedError('Voronoi cancelado.')
        polygon=list(rectangle)
        for other in generators:
            if other.identifier == centre.identifier:
                continue
            polygon=_clip_halfplane(polygon,centre.x,centre.y,other.x,other.y)
            if len(polygon)<3:
                break
        if progress:
            progress(int((idx+1)*75/len(generators)))
        if len(polygon)>=3:
            yield centre,polygon+[polygon[0]]


DEFAULT_ARC_TOLERANCE_M = 0.01


def _ogr_polygon(points):
    from osgeo import ogr
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in points:
        ring.AddPoint_2D(float(x), float(y))
    ring.CloseRings()
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    return polygon


def _apollonius_disk(light, heavy):
    """Disco em que o centro mais leve vence: d_leve / d_pesado < k, k = √(M_leve / M_pesado) < 1.

    Lei M/d² do Vista SAGA (1.4.0): M_leve/d_leve² > M_pesado/d_pesado² ⇔ d_leve/d_pesado < k.
    """
    k = math.sqrt(float(light.mass) / float(heavy.mass))
    factor = 1. - k*k
    cx = (light.x - k*k*heavy.x) / factor
    cy = (light.y - k*k*heavy.y) / factor
    radius = k * math.hypot(light.x-heavy.x, light.y-heavy.y) / factor
    return cx, cy, radius


def _disk_relation(cx, cy, radius, envelope):
    """'contains' (disco cobre o envelope), 'disjoint' ou 'partial'."""
    xmin, xmax, ymin, ymax = envelope
    if all(math.hypot(x-cx, y-cy) <= radius
           for x, y in ((xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax))):
        return 'contains'
    nx, ny = min(max(cx, xmin), xmax), min(max(cy, ymin), ymax)
    return 'disjoint' if math.hypot(nx-cx, ny-cy) >= radius else 'partial'


def _disk_polygon(cx, cy, radius, box, tolerance):
    """Disco restrito à caixa ``box``, com arco de desvio máximo ``tolerance``.

    A caixa é sempre a extensão inteira (com margem), para que os dois centros
    de um par usem exatamente o mesmo polígono e a fronteira comum coincida.
    Com o centro fora da caixa, gera só o setor que a enxerga (setor = disco
    nesses ângulos), o que mantém poucos vértices mesmo em círculos muito
    grandes (massas quase iguais).
    """
    xmin, ymin, xmax, ymax = box
    corners = ((xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax))
    step = 2.*math.acos(max(-1., 1.-tolerance/radius)) if radius > tolerance else math.pi/2.
    step = max(step, 1.e-7)
    inside = xmin <= cx <= xmax and ymin <= cy <= ymax
    if inside:
        start, end = 0., 2.*math.pi
    else:
        angles = [math.atan2(y-cy, x-cx) for x, y in corners]
        base = angles[0]
        unwrapped = [base + math.remainder(a-base, 2.*math.pi) for a in angles]
        start, end = min(unwrapped), max(unwrapped)
    count = max(8 if inside else 2, int(math.ceil((end-start)/step)))
    if count > 200000:
        raise ValueError('Arco de influência com vértices demais; aumente a tolerância ou reduza a extensão.')
    arc = [(cx + radius*math.cos(start + (end-start)*i/count),
            cy + radius*math.sin(start + (end-start)*i/count)) for i in range(count + (0 if inside else 1))]
    # O polígono inscrito fica dentro do círculo. Deslocar os vértices para fora
    # em 2/3 da flecha zera o viés médio de área (o arco desvia da corda, em
    # média, 2/3 da flecha); o desvio máximo fica em 2/3 da tolerância.
    sagitta = radius*(1.-math.cos((end-start)/count/2.))
    scale = (radius + 2.*sagitta/3.)/radius
    arc = [(cx + (x-cx)*scale, cy + (y-cy)*scale) for x, y in arc]
    return _ogr_polygon(arc if inside else [(cx, cy)] + arc)


def _halfplane_polygon(centre, other, box):
    """Semiplano mais próximo de ``centre`` (massas iguais), restrito à caixa."""
    xmin, ymin, xmax, ymax = box
    rectangle = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
    clipped = _clip_halfplane(rectangle, centre.x, centre.y, other.x, other.y)
    if len(clipped) < 3:
        from osgeo import ogr
        return ogr.Geometry(ogr.wkbPolygon)
    return _ogr_polygon(clipped)


def _clean(geometry):
    if geometry is None or geometry.IsEmpty() or geometry.IsValid():
        return geometry
    fixed = geometry.MakeValid()
    if fixed is None:
        raise ValueError('Geometria inválida durante o Voronoi com Massa.')
    return fixed


def _collect_polygons(geometry, target):
    """Copia só as partes poligonais (descarta linhas e pontos de contato)."""
    from osgeo import ogr
    kind = ogr.GT_Flatten(geometry.GetGeometryType())
    if kind == ogr.wkbPolygon:
        if geometry.GetArea() > 0:
            target.AddGeometry(geometry)
    elif kind in (ogr.wkbMultiPolygon, ogr.wkbGeometryCollection):
        for i in range(geometry.GetGeometryCount()):
            _collect_polygons(geometry.GetGeometryRef(i), target)


def mass_voronoi_polygons(generators, bounds, *, tolerance, cancelled=None, progress=None):
    """Voronoi Com Massa exato (maior M/d² vence, lei do Vista SAGA), em vetor.

    Para cada centro i, a região é a caixa intersectada com os discos de
    Apolônio em que i vence os centros mais pesados, menos os discos em que
    os mais leves vencem i, e cortada pelas bissetrizes dos centros de massa
    igual. Os arcos são aproximados por segmentos com desvio máximo
    ``tolerance`` (unidades do SRC). Regiões podem ser desconexas.
    Retorna pares (centro, geometria OGR).
    """
    from osgeo import ogr
    validate_generators(generators, weighted=True)
    xmin, ymin, xmax, ymax = map(float, bounds)
    if not all(math.isfinite(v) for v in (xmin, ymin, xmax, ymax)) or xmin >= xmax or ymin >= ymax:
        raise ValueError('A extensão do Voronoi precisa ter área positiva.')
    if len(generators) > 1000:
        raise ValueError('Esta versão aceita até 1.000 centros; divida a análise.')
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError('Tolerância dos arcos inválida.')
    margin = max(tolerance, 1.e-6*max(xmax-xmin, ymax-ymin))
    box = (xmin-margin, ymin-margin, xmax+margin, ymax+margin)
    rectangle = _ogr_polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])
    results = []
    for idx, centre in enumerate(generators):
        if cancelled and cancelled():
            raise InterruptedError('Voronoi cancelado.')
        heavier, equal, lighter = [], [], []
        for other in generators:
            if other.identifier == centre.identifier:
                continue
            ratio = float(centre.mass)/float(other.mass)
            if abs(1.-ratio*ratio) < 1.e-12:
                equal.append(other)
            elif ratio < 1.:
                heavier.append((_apollonius_disk(centre, other), other))
            else:
                lighter.append((_apollonius_disk(other, centre), other))
        region = rectangle.Clone()
        # Discos que contêm o centro primeiro, do menor para o maior: encolhem a região cedo.
        for (cx, cy, radius), _ in sorted(heavier, key=lambda item: item[0][2]):
            relation = _disk_relation(cx, cy, radius, region.GetEnvelope())
            if relation == 'contains':
                continue
            if relation == 'disjoint':
                region = None
                break
            region = _clean(region.Intersection(_disk_polygon(cx, cy, radius, box, tolerance)))
            if region is None or region.IsEmpty():
                break
        if region is not None and not region.IsEmpty():
            for other in equal:
                region = _clean(region.Intersection(_halfplane_polygon(centre, other, box)))
                if region is None or region.IsEmpty():
                    break
        if region is not None and not region.IsEmpty():
            for (cx, cy, radius), _ in lighter:
                relation = _disk_relation(cx, cy, radius, region.GetEnvelope())
                if relation == 'disjoint':
                    continue
                disk = _disk_polygon(cx, cy, radius, box, tolerance)
                if relation == 'contains' and disk.Contains(region):
                    region = None
                    break
                region = _clean(region.Difference(disk))
                if region is None or region.IsEmpty():
                    break
        if progress:
            progress(int((idx+1)*75/len(generators)))
        if region is None or region.IsEmpty():
            continue
        polygons = ogr.Geometry(ogr.wkbMultiPolygon)
        _collect_polygons(region, polygons)
        if polygons.GetGeometryCount():
            results.append((centre, polygons))
    return results


# Partes abaixo da escala (1.4.0-dev6, decisão do autor): só informadas no resumo, sem alterar a
# geometria. Limiar = (5 m)², o PEC Classe A a 1:10.000 (Decreto 89.817/1984), escala dos mapas
# de atrito do autor; igual a 1 pixel de 5 m.
SMALL_PART_M2 = 25.0


def _small_parts_text(records, units):
    """Linhas do resumo sobre partes com área < SMALL_PART_M2 (geometria inalterada)."""
    from osgeo import ogr
    from .voronoi_friction_continuous import small_parts
    regions = []
    for generator, geometry, _ in records:
        if not isinstance(geometry, ogr.Geometry):
            geometry = ogr.CreateGeometryFromWkb(bytes(geometry.asWkb()))
        if ogr.GT_Flatten(geometry.GetGeometryType()) == ogr.wkbPolygon:
            geometry = ogr.ForceToMultiPolygon(geometry)
        regions.append((generator, geometry))
    found = small_parts(regions, units, SMALL_PART_M2)
    head = f'Partes com área menor que {SMALL_PART_M2:g} m² ((5 m)², abaixo da escala 1:10.000; PEC Classe A): '
    if not found:
        return head + 'nenhuma.\n'
    count = sum(n for _, n, _ in found)
    area = sum(a for _, _, a in found)
    lines = [head + f'{count}, somando {area:.1f} m². Mantidas na geometria (só informadas):']
    for generator, n, a in found:
        lines.append(f'  {generator.label or f"Centro {generator.identifier}"}: {n} parte(s), {a:.1f} m²')
    return '\n'.join(lines) + '\n'


def save_simple_voronoi(generators,bounds,destination,projection_wkt,**kw):
    """Compatibilidade: Voronoi Simples vetorial direto."""
    return save_vector_voronoi(generators,bounds,destination,projection_wkt,mode='simple',**kw)


def save_vector_voronoi(generators,bounds,destination,projection_wkt,*,mode='simple',
                        study_geometry=None,progress=None,cancelled=None,
                        arc_tolerance_m=DEFAULT_ARC_TOLERANCE_M,friction_features=None,
                        search_spacing=None,friction_info=None,friction_tolerance_m=None):
    """Grava a camada vetorial (formato pela extensão) + CSV/TXT com substituição segura.

    mode: 'simple' (bissetrizes), 'mass' (maior M/d²; círculos de Apolônio com arcos de desvio
    máximo ``arc_tolerance_m`` metros) ou, desde a 1.4.0, 'friction' / 'mass_friction' (modelo
    contínuo do atrito, voronoi_friction_continuous): friction_features = [(wkb, nota ou None)];
    search_spacing = espaçamento da malha de busca (unidades do SRC; None = automático, o padrão da
    interface desde a 1.4.0); friction_tolerance_m = tolerância das fronteiras em metros (None =
    padrão de 0,5 m). friction_info: camada, coluna e feições sem nota, para o relatório.
    study_geometry: QgsGeometry já transformada para o SRC de saída.
    """
    from osgeo import ogr, osr
    if mode not in ('simple','mass','friction','mass_friction'):
        raise ValueError('Modalidade de Voronoi desconhecida.')
    friction=mode in ('friction','mass_friction')
    if friction and not friction_features:
        raise ValueError('O vetor direto com atrito exige polígonos de atrito com a coluna de notas.')
    if friction and search_spacing is not None and not (math.isfinite(search_spacing) and search_spacing > 0):
        raise ValueError('Informe o espaçamento da busca (positivo).')
    validate_generators(generators, weighted=mode in ('mass','mass_friction'))
    srs=osr.SpatialReference()
    if not projection_wkt or srs.ImportFromWkt(projection_wkt) or not srs.IsProjected():
        raise ValueError('Voronoi requer SRC projetado válido.')
    units=srs.GetLinearUnits()
    if not units or units<=0:
        raise ValueError('Não foi possível determinar as unidades lineares do SRC.')
    if study_geometry is not None and (study_geometry.isNull() or study_geometry.isEmpty() or not study_geometry.isGeosValid()):
        raise ValueError('Polígonos da área de estudo inválidos. Corrija a geometria.')
    destination=os.path.abspath(str(destination))
    if os.path.splitext(destination)[1].lower() not in VECTOR_FORMATS:
        raise ValueError('Escolha um arquivo vetorial: GeoPackage (.gpkg), Shapefile (.shp), '
                         'GeoJSON (.geojson) ou FlatGeobuf (.fgb).')
    folder=os.path.dirname(destination)
    if not os.path.isdir(folder):
        raise ValueError('Diretório de saída inexistente.')
    stem=os.path.splitext(destination)[0]
    outputs=[destination,stem+'_centros.csv',stem+'_resumo.txt']
    if any(os.path.isdir(path) for path in outputs):
        raise ValueError('Uma das saídas coincide com uma pasta.')
    stage=tempfile.mkdtemp(prefix='.vista_voronoi_vet_',dir=folder)
    datasource=None
    try:
        local=os.path.join(stage,os.path.basename(destination))
        # GeoPackage de trabalho; outros formatos são exportados dele no fim.
        work=local if local.lower().endswith('.gpkg') else os.path.splitext(local)[0]+'_trabalho.gpkg'
        datasource=ogr.GetDriverByName('GPKG').CreateDataSource(work)
        if datasource is None:
            raise OSError('Falha ao criar o GeoPackage.')
        layer=datasource.CreateLayer(LAYER_NAME,srs=srs,geom_type=ogr.wkbMultiPolygon)
        if layer is None:
            raise OSError('Falha ao criar camada GeoPackage.')
        for name,kind in [('CENTRO_ID',ogr.OFTInteger),('CENTRO',ogr.OFTString),
                          ('MASSA',ogr.OFTReal),('AREA_M2',ogr.OFTReal),
                          ('AREA_HA',ogr.OFTReal),('PCT_AREA',ogr.OFTReal)]:
            if layer.CreateField(ogr.FieldDefn(name,kind)) != ogr.OGRERR_NONE:
                raise OSError(f'Falha ao criar campo {name}')
        records=[]
        started=time.perf_counter()
        clip_slivers=0
        if mode=='simple':
            from qgis.core import QgsGeometry, QgsPointXY
            for generator,ring in simple_voronoi_polygons(generators,bounds,cancelled=cancelled,progress=progress):
                geometry=QgsGeometry.fromPolygonXY([[QgsPointXY(*xy) for xy in ring]])
                if study_geometry is not None:
                    geometry=geometry.intersection(study_geometry)
                if geometry.isNull() or geometry.isEmpty():
                    continue
                if not geometry.isGeosValid():
                    raise ValueError(f'Polígono resultante inválido para o centro {generator.identifier}.')
                area=geometry.area()*(units**2)
                if area<=1.e-10:
                    continue
                records.append((generator,geometry,area))
        else:
            # Geometrias OGR do começo ao fim; a área de estudo entra pelo WKB.
            study=(ogr.CreateGeometryFromWkb(bytes(study_geometry.asWkb()))
                   if study_geometry is not None else None)
            if friction:
                from .voronoi_friction_continuous import friction_voronoi_polygons
                outside=(friction_info or {}).get('outside')
                regions,friction_stats=friction_voronoi_polygons(
                    generators,friction_features,bounds,
                    outside_rating=None if outside in (None,'barreira') else float(outside),
                    spacing=None if search_spacing is None else float(search_spacing),
                    tolerance=None if friction_tolerance_m is None else friction_tolerance_m/units,
                    units_to_meters=units,mass_weighted=mode=='mass_friction',
                    cancelled=cancelled,progress=(lambda v: progress(int(v*.75))) if progress else None)
            else:
                regions=mass_voronoi_polygons(generators,bounds,tolerance=arc_tolerance_m/units,
                                              cancelled=cancelled,progress=progress)
            if study is not None:
                clipped_regions=[]
                for generator,geometry in regions:
                    clipped=_clean(geometry.Intersection(study))
                    geometry=ogr.Geometry(ogr.wkbMultiPolygon)
                    if clipped is not None and not clipped.IsEmpty():
                        _collect_polygons(clipped,geometry)
                    clipped_regions.append((generator,geometry))
                regions=clipped_regions
                if friction:
                    # Lascas do recorte final: mesma regra das faces-fio do traçado (1.4.0-dev6).
                    from .voronoi_friction_continuous import absorb_clip_slivers
                    regions,clip_slivers=absorb_clip_slivers(regions,friction_stats['tolerance'])
            for generator,geometry in regions:
                if geometry.IsEmpty() or not geometry.GetGeometryCount():
                    continue
                if not geometry.IsValid():
                    raise ValueError(f'Polígono resultante inválido para o centro {generator.identifier}.')
                area=geometry.GetArea()*(units**2)
                if area<=1.e-10:
                    continue
                records.append((generator,geometry,area))
        elapsed=time.perf_counter()-started
        total=sum(entry[2] for entry in records)
        if not total:
            raise ValueError('A área de análise não contém regiões de influência válidas.')
        rows=[]
        for idx,(point,geometry,area) in enumerate(records):
            if cancelled and cancelled():
                raise InterruptedError('Voronoi cancelado.')
            geom_ogr=(geometry.Clone() if isinstance(geometry,ogr.Geometry)
                      else ogr.CreateGeometryFromWkb(bytes(geometry.asWkb())))
            if geom_ogr is None:
                raise OSError('Não foi possível converter a geometria para OGR.')
            if geom_ogr.GetGeometryType() not in (ogr.wkbMultiPolygon,ogr.wkbMultiPolygon25D):
                geom_ogr=ogr.ForceToMultiPolygon(geom_ogr)
            row={'CENTRO_ID':point.identifier,'CENTRO':point.label or f'Centro {point.identifier}',
                 'MASSA':float(point.mass),'AREA_M2':area,'AREA_HA':area/10000,
                 'PCT_AREA':100*area/total}
            feat=ogr.Feature(layer.GetLayerDefn())
            for key,val in row.items():
                feat.SetField(key,val)
            feat.SetGeometry(geom_ogr)
            if layer.CreateFeature(feat) != ogr.OGRERR_NONE:
                raise OSError('Falha ao gravar feição de Voronoi.')
            feat=None
            rows.append({'ID':row['CENTRO_ID'],'CENTRO':row['CENTRO'],'MASSA':row['MASSA'],
                         'AREA_M2':row['AREA_M2'],'AREA_HA':row['AREA_HA'],
                         'PCT_AREA':row['PCT_AREA']})
            if progress:
                progress(75+int((idx+1)*20/len(records)))
        layer=None
        datasource=None
        if work!=local:
            export_vector(work,local)
            os.remove(work)
        csv_path=os.path.join(stage,os.path.basename(outputs[1]))
        txt_path=os.path.join(stage,os.path.basename(outputs[2]))
        with open(csv_path,'w',encoding='utf-8-sig',newline='') as report:
            writer=csv.DictWriter(report,fieldnames=['ID','CENTRO','MASSA','AREA_M2','AREA_HA','PCT_AREA'],delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
        with open(txt_path,'w',encoding='utf-8') as report:
            report.write('Vista Saga Plugin - Análises Voronoi\n')
            if mode=='simple':
                report.write('Modalidade: Simples; saída vetorial direta (sem rasterização)\n')
            elif friction:
                report.write(('Modalidade: Com Massa e Atrito' if mode=='mass_friction' else 'Modalidade: Com Atrito')
                             + '; saída vetorial direta (modelo contínuo, sem rasterização)\n')
                report.write('Critério: menor custo A = integral de s × nota ao longo do segmento reto polo-ponto '
                             '(s = distância ao polo)' + (', dividido pela massa (equivale a M/d²)' if mode=='mass_friction' else '')
                             + '. Versão contínua do atrito do Vista SAGA (não é cópia do cálculo célula a célula): coincide '
                             'com o Vista SAGA original em 99,5% a 99,6% das células no caso sintético e em 99,1% a 99,3% '
                             'numa bacia real (grade de 10 m), com diferenças também longe da fronteira. Para reproduzir '
                             'o Vista SAGA, use a guia Raster (99,4% a 99,7%).\n')
                info=friction_info or {}
                outside=info.get('outside')
                report.write(f"Polígonos de atrito: {info.get('layer_name','')}; notas da coluna "
                             f"{info.get('rating_field','')}. Área sem polígono e feições com a coluna vazia "
                             f"({info.get('skipped',0)}): "
                             + ('barreira (sem resultado e sem passagem). ' if outside in (None,'barreira') else
                                f'sem resultado, atravessáveis com nota {float(outside):g} (custo basal do Vista SAGA, '
                                'padrão da classe FUNDO). ')
                             + 'Em sobreposições vale a última feição.\n')
                spacing_used=friction_stats['spacing']*units
                tolerance_used=friction_stats['tolerance']*units
                report.write(f"Fronteiras traçadas numericamente, com refinamento local: espaçamento da busca de "
                             f"{spacing_used:.3g} m ({'automático: maior lado da extensão / 100, até 1/4 da largura do polígono de atrito mais estreito' if friction_stats.get('spacing_automatic') else 'informado'}) "
                             f"e tolerância de {tolerance_used:.3g} m (padrão: 0,5 m, ou 1/2000 do maior lado da extensão "
                             "se for menor; coerente com mapas temáticos 1:10.000, de erro-padrão de 3 m no PEC Classe A). "
                             "Regiões menores que o espaçamento podem não ser detectadas; a conferência automática abaixo "
                             "verifica o resultado.\n")
                report.write(f"Nós avaliados: {friction_stats['evaluations']}; células da malha adaptativa: "
                             f"{friction_stats['cells']}; vértices de fronteira: {friction_stats['boundary_vertices']}.\n")
                check=friction_stats.get('check') or {}
                report.write(f"Conferência automática: {check.get('samples',0)} pontos (um por célula da malha de busca) "
                             f"comparados com o modelo; {check.get('divergent',0)} divergência(s) longe da fronteira após "
                             f"{check.get('passes',0)} passada(s) de traçado"
                             + (f" (correção local em {check.get('forced_cells',0)} célula(s))" if check.get('forced_cells') else '')
                             + '.\n')
                if clip_slivers:
                    report.write(f"Recorte pela área de estudo: {clip_slivers} lasca(s) de largura média menor que "
                                 f"{2*tolerance_used:.3g} m (2 × tolerância) incorporada(s) à região vizinha de maior "
                                 "fronteira comum.\n")
                if check.get('divergent'):
                    report.write('ATENÇÃO: restaram divergências entre os polígonos e o modelo'
                                 + (' (limite de memória da correção atingido)' if check.get('budget_hit') else '')
                                 + '. Repita com um espaçamento da busca menor.\n')
            else:
                report.write('Modalidade: Com Massa (maior M/d², modelo do Vista SAGA); saída vetorial direta (sem rasterização)\n')
                report.write('Fronteiras entre centros de massas diferentes: arcos de círculos de Apolônio, '
                             f'aproximados por segmentos com desvio máximo de {2*arc_tolerance_m/3:.4g} m '
                             f'(tolerância {arc_tolerance_m:g} m); massas iguais: bissetrizes. '
                             'Regiões podem ter mais de uma parte (multipolígono).\n')
            report.write(f'Tempo de cálculo (s): {elapsed:.1f}\n')
            report.write(_small_parts_text(records,units))
            report.write(f'Formato: {VECTOR_FORMATS[os.path.splitext(destination)[1].lower()][1]}\n')
            report.write('Extensão finita definida pelo usuário; distâncias euclidianas no SRC projetado.\n')
            report.write('Áreas métricas planares calculadas nas unidades lineares do SRC.\n\n')
            report.write('ID | Centro | Massa | Área (m²) | Área (ha) | % da área avaliada\n')
            for row in rows:
                report.write(f"{row['ID']} | {row['CENTRO']} | {row['MASSA']:.3f} | "
                             f"{row['AREA_M2']:.3f} | {row['AREA_HA']:.6f} | {row['PCT_AREA']:.4f}\n")
            if mode in ('simple','mass'):
                report.write('\nSimples e Com Massa reproduziram 100% das células do Vista SAGA original no caso '
                             'sintético e numa bacia real (esta pela guia Raster, que coincide com este vetor '
                             'no centro das células), exceto empates.\n')
        # Mesmo padrão de backup/rollback do módulo raster (família vetorial inteira).
        publish_outputs(stage,outputs)
        if progress: progress(100)
        return {'output':None,'vector':destination,
                'gpkg':destination if destination.lower().endswith('.gpkg') else None,'csv':outputs[1],
                'txt':outputs[2],'rows':rows,'pixels_valid':None,
                'pixels_excluded':None,'vector_direct':True}
    finally:
        datasource=None
        shutil.rmtree(stage,ignore_errors=True)
