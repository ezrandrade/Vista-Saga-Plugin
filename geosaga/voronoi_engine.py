"""Voronoi raster simples, massa, atrito e massa+atrito para QGIS 4.x.

Não modifica nenhuma fonte; produz GeoTIFF classificado e relatórios.
A poligonização opcional cria GeoPackage com cada região contígua.
"""
import csv
import math
import os
import shutil
import time
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
from .voronoi_friction import (validate_friction, assign_friction_window,
                               MAX_FRICTION_CELLS)
from .voronoi_core import (assign_window, assign_window_nearest,
                           build_nearest_index, validate_generators,
                           counts_as_rows, pixel_area_m2)

MAX_CELLS = 50_000_000
MAX_GENERATORS = 1000


def grid_from_extent(bounds, resolution, *, margin_pixels=8):
    minx, miny, maxx, maxy = [float(x) for x in bounds]
    resolution = float(resolution)
    if not math.isfinite(resolution) or resolution <= 0:
        raise ValueError('Resolução deve ser positiva.')
    if not all(math.isfinite(x) for x in (minx,miny,maxx,maxy)):
        raise ValueError('Extensão espacial inválida.')
    if maxx < minx or maxy < miny:
        raise ValueError('Extensão espacial invertida.')
    # Pontos alinhados em um único eixo continuam gerando grade válida.
    span_x = max(maxx - minx, resolution)
    span_y = max(maxy - miny, resolution)
    margin = max(margin_pixels*resolution, .1*max(span_x, span_y))
    minx -= margin
    miny -= margin
    maxx += margin
    maxy += margin
    width = max(1, int(math.ceil((maxx-minx)/resolution)))
    height = max(1, int(math.ceil((maxy-miny)/resolution)))
    if width * height > MAX_CELLS:
        raise ValueError('A grade excede 50 milhões de pixels; aumente a resolução.')
    return (minx, resolution, 0., maxy, 0., -resolution), width, height


def _write_reports(csv_path, txt_path, mode, rows, excluded, pixel_area):
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['ID','CENTRO','MASSA','PIXELS','AREA_M2','AREA_HA','PCT_AREA'], delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('Vista Saga Plugin — Análises Voronoi\n')
        f.write(f'Modalidade: {"Com Massa e Atrito" if mode == "mass_friction" else ("Com Atrito" if mode == "friction" else ("Com Massa" if mode == "mass" else "Simples"))}\n')
        if mode in ('friction','mass_friction'):
            f.write('Critério experimental: minimizar distância euclidiana × soma (1 + atrito)\n'
                    'ao longo das células atravessadas pelo segmento reto centro→pixel.\n'
                    'Atrito zero = custo basal 1; NoData no caminho = barreira.\n'
                    'Não é percurso de custo mínimo. Não validado numericamente no Vista SAGA original.\n')
            if mode == 'mass_friction':
                f.write('Com massa: cada índice D × soma(1 + atrito) é dividido pela massa positiva do gerador.\n')
        else:
            f.write('Critério: menor distância euclidiana' +
                    (' dividida pela massa positiva do ponto' if mode == 'mass' else '') + '\n')
        f.write('Critério de empate: primeiro ponto da lista.\n')
        f.write(f'Área de pixel: {pixel_area:.9f} m²\n')
        f.write(f'Pixels excluídos por máscara: {excluded}\n\n')
        f.write('ID | Centro | Massa | Pixels | Área (ha) | % área avaliada\n')
        for item in rows:
            f.write(f"{item['ID']} | {item['CENTRO']} | {item['MASSA']:.6g} | "
                    f"{item['PIXELS']} | {item['AREA_HA']:.6f} | {item['PCT_AREA']:.4f}\n")
        f.write('\nNota: os limites são discretizados na grade raster; ' 
                'a equivalência com o Vista SAGA original ainda depende de validação comparativa.\n')


def _polygonize(raster_path, gpkg_path, generator_rows, units_to_meters, cancelled=None):
    from osgeo import gdal, ogr, osr
    ds = gdal.Open(raster_path, gdal.GA_ReadOnly)
    if ds is None:
        raise RuntimeError('Não foi possível abrir o GeoTIFF intermediário para vetorização.')
    driver = ogr.GetDriverByName('GPKG')
    vector = driver.CreateDataSource(gpkg_path)
    if vector is None:
        raise RuntimeError('Não foi possível criar o GeoPackage.')
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds.GetProjectionRef())
    layer = vector.CreateLayer('voronoi_espacial', srs, ogr.wkbPolygon)
    if layer is None:
        raise RuntimeError('Não foi possível criar a camada de polígonos.')
    for name, datatype in [('CENTRO_ID',ogr.OFTInteger),('CENTRO',ogr.OFTString),
                            ('MASSA',ogr.OFTReal),('AREA_HA',ogr.OFTReal)]:
        field = ogr.FieldDefn(name, datatype)
        if name == 'CENTRO': field.SetWidth(254)
        layer.CreateField(field)
    band = ds.GetRasterBand(1)
    result = gdal.Polygonize(band, band.GetMaskBand(), layer, 0, [])
    if result != 0:
        raise RuntimeError('Falha na poligonização GDAL.')
    info = {row['ID']:row for row in generator_rows}
    layer.ResetReading()
    for feature in layer:
        if cancelled and cancelled():
            raise InterruptedError('Voronoi cancelado durante a vetorização.')
        row = info.get(int(feature.GetField('CENTRO_ID')))
        if row is None:
            continue
        feature.SetField('CENTRO',row['CENTRO'])
        feature.SetField('MASSA',row['MASSA'])
        feature.SetField('AREA_HA',feature.GetGeometryRef().GetArea() * units_to_meters**2/10000)
        if layer.SetFeature(feature) != 0:
            raise RuntimeError('Erro ao gravar os atributos da feição.')
    layer = None
    vector = None
    ds = None


def run_voronoi(points, destination, projection_wkt, geotransform, width, height, *,
                mode='simple', units_to_meters=1., mask=None, vectorize=False,
                progress=None, cancelled=None, friction_path=None, friction_components=None):
    """Executa Voronoi em janelas e retorna caminhos/estatísticas.

    points: lista de Generator com coordenadas no SRC da grade.
    mask: máscara numpy opcional (TRUE para células válidas); não usada no GUI 0.7.0.
    """
    from osgeo import gdal, osr
    weighted = mode in ('mass','mass_friction')
    if mode not in ('simple','mass','friction','mass_friction'):
        raise ValueError('Modalidade de Voronoi desconhecida.')
    if mode in ('friction','mass_friction') and not (friction_path or friction_components):
        raise ValueError('A modalidade com Atrito exige selecionar um GeoTIFF de resistência territorial.')
    validate_generators(points, weighted=weighted)
    if len(points) > MAX_GENERATORS:
        raise ValueError('Limite de 1.000 pontos na versão 0.7.0; divida a análise em áreas.')
    if len(points) > 2**31-2:
        raise ValueError('Quantidade de pontos excede a codificação Int32.')
    width, height = int(width), int(height)
    if width <= 0 or height <= 0 or width*height > MAX_CELLS:
        raise ValueError('A grade deve ter entre 1 e 50 milhões de células.')
    # A comparação pixels × centros estima tempo no algoritmo direto,
    # mas não constitui limite de capacidade nem de memória. Processar
    # por janelas evita bloquear análises válidas de muitos centros.
    if mask is not None and mask.shape != (height,width):
        raise ValueError('Máscara não corresponde à grade de saída.')
    if not projection_wkt:
        raise ValueError('Defina um SRC projetado.')
    srs = osr.SpatialReference()
    if srs.ImportFromWkt(projection_wkt) != 0 or not srs.IsProjected():
        raise ValueError('O Voronoi exige SRC projetado; use uma projeção adequada.')
    units_to_meters = srs.GetLinearUnits()
    if not units_to_meters or units_to_meters <= 0:
        raise ValueError('Unidades lineares do SRC desconhecidas.')
    destination = os.path.abspath(str(destination))
    if not destination.lower().endswith(('.tif','.tiff')):
        raise ValueError('Resultado Voronoi deve ser salvo em GeoTIFF.')
    parent = os.path.dirname(destination)
    if not os.path.isdir(parent):
        raise ValueError('Pasta de destino inexistente.')
    prefix = os.path.splitext(destination)[0]
    files = [destination, prefix+'_centros.csv', prefix+'_resumo.txt']
    if vectorize:
        files.append(prefix+'.gpkg')
    if any(os.path.isdir(f) for f in files):
        raise ValueError('Uma saída coincide com um diretório.')
    # A superfície de atrito é aberta e descarregada na thread da tarefa,
    # sem compartilhar objetos GDAL ou objetos Qt entre threads.
    friction = None
    if mode in ('friction','mass_friction') and friction_components:
        from .voronoi_friction_stack import read_friction_stack
        paths = [os.path.abspath(str(spec['path'])) for spec in friction_components]
        if destination in paths or any(os.path.normcase(os.path.realpath(path)) ==
                                       os.path.normcase(os.path.realpath(destination)) for path in paths):
            raise ValueError('A saída não pode substituir uma superfície de atrito.')
        if width*height > MAX_FRICTION_CELLS:
            raise ValueError('O atrito excede 8 milhões de células; recorte ou reduza a resolução.')
        friction = read_friction_stack(friction_components, gdal, projection_wkt,
                                      geotransform, width, height, osr)
        validate_friction(friction, geotransform, points)
    elif mode in ('friction','mass_friction'):
        friction_path = os.path.abspath(str(friction_path))
        if not os.path.isfile(friction_path):
            raise ValueError('Arquivo raster de atrito não encontrado no disco.')
        if os.path.normcase(os.path.realpath(friction_path)) == os.path.normcase(os.path.realpath(destination)):
            raise ValueError('A saída não pode substituir o raster de atrito.')
        source = gdal.Open(friction_path, gdal.GA_ReadOnly)
        if source is None or source.RasterCount != 1:
            raise ValueError('O mapa de atrito precisa ser um GeoTIFF de banda única.')
        if source.RasterXSize != width or source.RasterYSize != height:
            raise ValueError('A grade do atrito não coincide com as dimensões do resultado.')
        source_t = source.GetGeoTransform()
        if any(abs(a-b)>1e-8 for a,b in zip(source_t,geotransform)):
            raise ValueError('Resolução/extensão não coincidem com o raster de atrito.')
        source_crs = osr.SpatialReference()
        if source_crs.ImportFromWkt(source.GetProjectionRef()) != 0 or not source_crs.IsSame(srs):
            raise ValueError('O SRC do raster de atrito não coincide com o resultado.')
        if width*height > MAX_FRICTION_CELLS:
            raise ValueError('O mapa de atrito excede 8 milhões de células nesta etapa. Recorte ou reduza a resolução.')
        band_in = source.GetRasterBand(1)
        friction = band_in.ReadAsArray().astype(np.float64)
        nodata = band_in.GetNoDataValue()
        if nodata is not None:
            if np.isnan(nodata):
                friction[np.isnan(friction)] = np.nan
            else:
                friction[friction == nodata] = np.nan
        # O GDAL pode possuir máscara de validade distinta do valor NoData.
        valid_mask = band_in.GetMaskBand().ReadAsArray() != 0
        friction[~valid_mask] = np.nan
        source = None
        validate_friction(friction, geotransform, points)
        # O antigo limite fixo de 700 milhões de travessias supunha avaliar
        # todos os centros para cada pixel. O avaliador com limites inferiores
        # descarta centros que matematicamente não podem vencer o resultado.
        # Esse limite estimado não corresponde à carga real e não deve bloquear
        # antecipadamente a análise. O usuário pode cancelar a tarefa Qt.
    stage = tempfile.mkdtemp(prefix='.vista_voronoi_', dir=parent)
    # O arquivo de saída só é substituído ao término de todo o processamento.
    created = []
    raster = None
    try:
        local_tif = os.path.join(stage,os.path.basename(destination))
        raster = gdal.GetDriverByName('GTiff').Create(local_tif,width,height,1,gdal.GDT_Int32,
               options=['TILED=YES','COMPRESS=LZW','BIGTIFF=IF_SAFER'])
        if raster is None: raise OSError('Não foi possível criar GeoTIFF.')
        raster.SetGeoTransform(tuple(float(v) for v in geotransform))
        raster.SetProjection(projection_wkt)
        band = raster.GetRasterBand(1)
        band.SetNoDataValue(0)
        band.Fill(0)
        processing_started = time.perf_counter()
        count = Counter()
        excluded = 0
        friction_stats = {'candidate_pairs': 0, 'traced_paths': 0, 'visited_cells': 0, 'early_stops': 0}
        # Limita o tamanho em memória de cada bloco, independente do
        # número de centros e da largura da grade raster.
        target_pixels_per_window = 200_000
        rows_per_window = max(1, min(128, target_pixels_per_window // width))
        nearest_index = build_nearest_index(points) if mode == 'simple' else None
        for y in range(0, height, rows_per_window):
            if cancelled and cancelled():
                raise InterruptedError('Voronoi cancelado pelo usuário.')
            h = min(rows_per_window, height-y)
            segment = mask[y:y+h] if mask is not None else None
            if mode in ('friction','mass_friction'):
                values = assign_friction_window(points,friction,geotransform,y,h,
                                                cancelled=cancelled, mass_weighted=(mode == 'mass_friction'),
                                                stats=friction_stats)
                if segment is not None: values[~segment.astype(bool)] = 0
            elif mode == 'simple':
                values = assign_window_nearest(points,geotransform,width,y,h,
                                               mask=segment,index=nearest_index)
            else:
                values = assign_window(points,geotransform,width,y,h,
                                       mode='mass',mask=segment)
            if band.WriteArray(values,0,y) != 0:
                raise OSError('Falha ao gravar GeoTIFF.')
            keys, amounts = np.unique(values[values>0],return_counts=True)
            count.update({int(k):int(n) for k,n in zip(keys,amounts)})
            excluded += int(np.count_nonzero(values==0))
            if progress: progress(int(80*(y+h)/height))
        analysis_seconds = time.perf_counter() - processing_started
        raster.SetMetadataItem('VISTASAGA_MODE',mode)
        if mode in ('friction','mass_friction'):
            raster.SetMetadataItem('VISTASAGA_FRICTION_MODEL','D * SUM(1 + C_k), straight-line DDA' if mode == 'friction' else 'D * SUM(1 + C_k) / M, straight-line DDA')
            raster.SetMetadataItem('VISTASAGA_FRICTION_BASE','1')
            if friction_components:
                raster.SetMetadataItem('VISTASAGA_FRICTION_STACK','weighted_mean; common_valid_area')
                raster.SetMetadataItem('VISTASAGA_FRICTION_STACK_WEIGHTS',
                                       ','.join(str(spec['weight']) for spec in friction_components))
                raster.SetMetadataItem('VISTASAGA_FRICTION_STACK_LAYERS',
                                       str(len(friction_components)))
            raster.SetMetadataItem('VISTASAGA_FRICTION_SEARCH','Exact lower-bound pruning; no approximation')
            if mode == 'mass_friction':
                raster.SetMetadataItem('VISTASAGA_MASS_MODEL','D * SUM(1 + C_k) / M')
            raster.SetMetadataItem('VISTASAGA_FRICTION_VALIDATION','experimental; not yet compared to Vista SAGA')
            raster.SetMetadataItem('VISTASAGA_TESTED_CANDIDATES',str(friction_stats['candidate_pairs']))
            raster.SetMetadataItem('VISTASAGA_TRACED_PATHS',str(friction_stats['traced_paths']))
            raster.SetMetadataItem('VISTASAGA_VISITED_CELLS',str(friction_stats['visited_cells']))
            raster.SetMetadataItem('VISTASAGA_EARLY_STOPS',str(friction_stats['early_stops']))
            raster.SetMetadataItem('VISTASAGA_RASTER_CALC_SECONDS',f'{analysis_seconds:.4f}')
        raster.SetMetadataItem('VISTASAGA_GENERATORS',str(len(points)))
        raster.FlushCache()
        band = None
        raster = None
        if cancelled and cancelled(): raise InterruptedError('Voronoi cancelado pelo usuário.')
        if not sum(count.values()):
            raise ValueError('Nenhum ponto gerador influencia a grade informada.')
        rows = counts_as_rows(points,count,geotransform,units_to_meters)
        local_csv = os.path.join(stage,os.path.basename(files[1]))
        local_txt = os.path.join(stage,os.path.basename(files[2]))
        _write_reports(local_csv,local_txt,mode,rows,excluded,pixel_area_m2(geotransform,units_to_meters))
        if mode in ('friction','mass_friction'):
            with open(local_txt,'a',encoding='utf-8') as report:
                report.write('\nDiagnóstico computacional da poda de centros\n')
                report.write(f"Pares célula × gerador: {friction_stats['candidate_pairs']}\n")
                report.write(f"Trajetórias calculadas: {friction_stats['traced_paths']}\n")
                report.write(f"Pares descartados: {friction_stats['candidate_pairs'] - friction_stats['traced_paths']}\n")
                report.write(f"Trajetórias interrompidas durante o cálculo (poda exata): {friction_stats['early_stops']}\n")
                report.write(f"Células atravessadas e avaliadas: {friction_stats['visited_cells']}\n")
                report.write(f"Tempo do cálculo matricial (s): {analysis_seconds:.3f}\n")
                if friction_stats['traced_paths']:
                    report.write(f"Média de células por trajetória: {friction_stats['visited_cells'] / friction_stats['traced_paths']:.2f}\n")
        if friction_components:
            with open(local_txt,'a',encoding='utf-8') as report:
                report.write('\nSuperfícies de atrito integradas (média ponderada)\n')
                for n, spec in enumerate(friction_components, 1):
                    report.write(f"{n}. {os.path.basename(spec['path'])}; peso={spec['weight']}; "
                                 f"notas={spec.get('notes','') or 'valores originais'}\n")
                report.write('NoData em qualquer superfície: barreira; custo por célula = 1 + atrito integrado.\n')
        if vectorize:
            if progress: progress(83)
            local_vec = os.path.join(stage,os.path.basename(files[3]))
            _polygonize(local_tif,local_vec,rows,units_to_meters,cancelled)
            if progress: progress(96)
        if cancelled and cancelled(): raise InterruptedError('Voronoi cancelado pelo usuário.')
        # Backup com rollback dos arquivos já existentes.
        backup = os.path.join(stage, '_anteriores')
        os.makedirs(backup)
        originals = []
        try:
            for p in files:
                if os.path.isfile(p):
                    saved = os.path.join(backup,str(len(originals)))
                    os.replace(p,saved)
                    originals.append((saved,p))
            for p in files:
                local = os.path.join(stage,os.path.basename(p))
                os.replace(local,p)
                created.append(p)
        except Exception:
            for p in created:
                if os.path.exists(p): os.remove(p)
            for saved,p in originals:
                if os.path.exists(saved): os.replace(saved,p)
            raise
        if progress: progress(100)
        return {'output':files[0], 'csv':files[1], 'txt':files[2],
                'gpkg':files[3] if vectorize else None,'rows':rows,
                'pixels_valid':sum(count.values()),'pixels_excluded':excluded,
                'raster_calc_seconds':analysis_seconds,
                'friction_diagnostics':dict(friction_stats) if mode in ('friction','mass_friction') else None}
    finally:
        raster = None
        shutil.rmtree(stage,ignore_errors=True)


def grid_from_bbox(bounds, resolution):
    """Grade de resolução explícita e extensão fornecida, sem acrescentar margem."""
    xmin,ymin,xmax,ymax=map(float,bounds)
    resolution=float(resolution)
    if not all(math.isfinite(v) for v in (xmin,ymin,xmax,ymax,resolution)):
        raise ValueError('Extensão/resolução não finitas.')
    if resolution<=0 or xmax<=xmin or ymax<=ymin:
        raise ValueError('Extensão e resolução precisam ser positivas.')
    width=max(1,int(math.ceil((xmax-xmin)/resolution)))
    height=max(1,int(math.ceil((ymax-ymin)/resolution)))
    if width*height>MAX_CELLS:
        raise ValueError('A grade excede 50 milhões de pixels; aumente a resolução.')
    return (xmin,resolution,0.,ymax,0.,-resolution),width,height
