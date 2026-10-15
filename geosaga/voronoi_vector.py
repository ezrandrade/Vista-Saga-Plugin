"""Voronoi euclidiano vetorial exato (no plano do SRC), sem rasterização.

Recorta células por semiplanos das bissetrizes e, opcionalmente, pelo
polígono de estudo em PyQGIS. Os limites de saída são finitos e explícitos.
"""
import csv
import math
import os
import shutil
import tempfile
from .voronoi_core import validate_generators


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


def save_simple_voronoi(generators,bounds,destination,projection_wkt,*,
                        study_geometry=None,progress=None,cancelled=None):
    """Grava GeoPackage + CSV/TXT com substituição segura.

    study_geometry: QgsGeometry já transformada para o SRC de saída.
    """
    from osgeo import ogr, osr
    from qgis.core import QgsGeometry, QgsPointXY
    validate_generators(generators)
    srs=osr.SpatialReference()
    if not projection_wkt or srs.ImportFromWkt(projection_wkt) or not srs.IsProjected():
        raise ValueError('Voronoi requer SRC projetado válido.')
    units=srs.GetLinearUnits()
    if not units or units<=0:
        raise ValueError('Não foi possível determinar as unidades lineares do SRC.')
    if study_geometry is not None and (study_geometry.isNull() or study_geometry.isEmpty() or not study_geometry.isGeosValid()):
        raise ValueError('Polígonos da área de estudo inválidos. Corrija a geometria.')
    destination=os.path.abspath(str(destination))
    if not destination.lower().endswith('.gpkg'):
        raise ValueError('Escolha um arquivo GeoPackage (.gpkg).')
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
        datasource=ogr.GetDriverByName('GPKG').CreateDataSource(local)
        if datasource is None:
            raise OSError('Falha ao criar o GeoPackage.')
        layer=datasource.CreateLayer('voronoi_espacial',srs=srs,geom_type=ogr.wkbMultiPolygon)
        if layer is None:
            raise OSError('Falha ao criar camada GeoPackage.')
        for name,kind in [('CENTRO_ID',ogr.OFTInteger),('CENTRO',ogr.OFTString),
                          ('MASSA',ogr.OFTReal),('AREA_M2',ogr.OFTReal),
                          ('AREA_HA',ogr.OFTReal),('PCT_AREA',ogr.OFTReal)]:
            if layer.CreateField(ogr.FieldDefn(name,kind)) != ogr.OGRERR_NONE:
                raise OSError('Falha ao criar campo '+name)
        records=[]
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
        total=sum(entry[2] for entry in records)
        if not total:
            raise ValueError('A área de análise não contém regiões de influência válidas.')
        rows=[]
        for idx,(point,geometry,area) in enumerate(records):
            if cancelled and cancelled():
                raise InterruptedError('Voronoi cancelado.')
            geom_ogr=ogr.CreateGeometryFromWkb(bytes(geometry.asWkb()))
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
        csv_path=os.path.join(stage,os.path.basename(outputs[1]))
        txt_path=os.path.join(stage,os.path.basename(outputs[2]))
        with open(csv_path,'w',encoding='utf-8-sig',newline='') as report:
            writer=csv.DictWriter(report,fieldnames=['ID','CENTRO','MASSA','AREA_M2','AREA_HA','PCT_AREA'],delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
        with open(txt_path,'w',encoding='utf-8') as report:
            report.write('Vista Saga Plugin — Análises Voronoi\n')
            report.write('Modalidade: Simples; saída vetorial direta (sem rasterização)\n')
            report.write('Extensão finita definida pelo usuário; distâncias euclidianas no SRC projetado.\n')
            report.write('Áreas métricas planares calculadas nas unidades lineares do SRC.\n\n')
            report.write('ID | Centro | Massa | Área (m²) | Área (ha) | % da área avaliada\n')
            for row in rows:
                report.write(f"{row['ID']} | {row['CENTRO']} | {row['MASSA']:.3f} | "
                             f"{row['AREA_M2']:.3f} | {row['AREA_HA']:.6f} | {row['PCT_AREA']:.4f}\n")
            report.write('\nA equivalência com o Vista SAGA original depende de validação comparativa.\n')
        # Usa o mesmo padrão de backup/rollback do módulo raster.
        backup=os.path.join(stage,'_backup')
        os.makedirs(backup)
        originals=[]
        created=[]
        try:
            for destination_path in outputs:
                if os.path.isfile(destination_path):
                    saved=os.path.join(backup,str(len(originals)))
                    os.replace(destination_path,saved)
                    originals.append((saved,destination_path))
            for destination_path in outputs:
                os.replace(os.path.join(stage,os.path.basename(destination_path)),destination_path)
                created.append(destination_path)
        except Exception:
            for path in created:
                if os.path.exists(path): os.remove(path)
            for saved,original in originals:
                if os.path.exists(saved): os.replace(saved,original)
            raise
        if progress: progress(100)
        return {'output':None,'gpkg':destination,'csv':outputs[1],
                'txt':outputs[2],'rows':rows,'pixels_valid':None,
                'pixels_excluded':None,'vector_direct':True}
    finally:
        datasource=None
        shutil.rmtree(stage,ignore_errors=True)
