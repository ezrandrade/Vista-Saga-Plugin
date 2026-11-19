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

import numpy as np
from .voronoi_friction import (validate_friction, assign_friction_window,
                               MAX_FRICTION_CELLS, FRICTION_MODEL, MASS_FRICTION_MODEL)
from .voronoi_output import (DEFAULT_EXTENSION, LAYER_NAME, VECTOR_FORMATS, export_vector,
                             publish_outputs, vector_extension)
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


def _write_reports(csv_path, txt_path, mode, rows, excluded, pixel_area, passage_note=None, study_cells=None):
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['ID','CENTRO','MASSA','PIXELS','AREA_M2','AREA_HA','PCT_AREA'], delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('Vista Saga Plugin - Análises Voronoi\n')
        f.write(f'Modalidade: {"Com Massa e Atrito" if mode == "mass_friction" else ("Com Atrito" if mode == "friction" else ("Com Massa" if mode == "mass" else "Simples"))}\n')
        if mode in ('friction','mass_friction'):
            f.write('Critério (modelo do Vista SAGA): menor custo acumulado A = soma de\n'
                    'distância ao polo × nota × passo (diagonal = √2) nas células da reta polo-célula.\n'
                    'A nota entra direto como custo (nota 1 = custo basal).\n'
                    'Não é percurso de custo mínimo. Validado contra o Vista SAGA original, célula a célula:\n'
                    '99,7% das células no caso sintético e 99,4% a 99,6% numa bacia real (grade de 10 m);\n'
                    'as diferenças ficam na fronteira entre regiões.\n')
            if passage_note:
                f.write(passage_note + '\n')
            if mode == 'mass_friction':
                f.write('Com massa: o custo A é dividido pela massa do polo (equivale a M / d²).\n')
        elif mode == 'mass':
            f.write('Critério (modelo do Vista SAGA): maior M / d², isto é, menor distância euclidiana\n'
                    'dividida pela raiz quadrada da massa do polo.\n')
        else:
            f.write('Critério: menor distância euclidiana\n')
        f.write('Critério de empate: primeiro ponto da lista.\n')
        f.write(f'Área de pixel: {pixel_area:.9f} m²\n')
        if study_cells is not None:
            f.write(f'Recorte pela área de estudo (camada poligonal, regra do centro da célula): '
                    f'{study_cells} pixels dentro; os de fora ficam sem resultado'
                    + (' (no atrito, continuam atravessáveis com a própria nota)' if mode in ('friction', 'mass_friction') else '')
                    + '.\n')
        f.write(f'Pixels sem resultado (fora da área de estudo, sem nota de atrito ou sem polo): {excluded}\n\n')
        f.write('ID | Centro | Massa | Pixels | Área (ha) | % área avaliada\n')
        for item in rows:
            f.write(f"{item['ID']} | {item['CENTRO']} | {item['MASSA']:.6g} | "
                    f"{item['PIXELS']} | {item['AREA_HA']:.6f} | {item['PCT_AREA']:.4f}\n")
        f.write('\nNota: os limites são discretizados na grade raster. Simples e Com Massa reproduziram\n'
                '100% das células do Vista SAGA original (caso sintético e bacia real), exceto empates.\n')


def _polygonize(raster_path, vector_path, generator_rows, units_to_meters, cancelled=None):
    """Poligoniza o GeoTIFF de centros no formato vetorial indicado pela extensão.

    A camada é montada num GeoPackage de trabalho (aceita SetFeature) e, se
    outro formato foi pedido, exportada dele, como no Conversor de Formatos.
    """
    from osgeo import gdal, ogr, osr
    extension = vector_extension(vector_path)
    gpkg_path = (vector_path if extension == '.gpkg'
                 else os.path.splitext(vector_path)[0] + '_trabalho.gpkg')
    ds = gdal.Open(raster_path, gdal.GA_ReadOnly)
    if ds is None:
        raise RuntimeError('Não foi possível abrir o GeoTIFF intermediário para vetorização.')
    driver = ogr.GetDriverByName('GPKG')
    vector = driver.CreateDataSource(gpkg_path)
    if vector is None:
        raise RuntimeError('Não foi possível criar o GeoPackage.')
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds.GetProjectionRef())
    layer = vector.CreateLayer(LAYER_NAME, srs, ogr.wkbPolygon)
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
    if extension != '.gpkg':
        export_vector(gpkg_path, vector_path)
        os.remove(gpkg_path)


def run_voronoi(points, destination, projection_wkt, geotransform, width, height, *,
                mode='simple', units_to_meters=1., mask=None, vectorize=False,
                progress=None, cancelled=None, friction_path=None, friction_components=None,
                vector_format=DEFAULT_EXTENSION, keep_raster=True, friction_vector=None,
                study_wkb=None):
    """Executa Voronoi em janelas e retorna caminhos/estatísticas.

    vectorize: poligoniza o resultado no formato ``vector_format`` (.gpkg,
    .shp, .geojson ou .fgb), com o mesmo nome-base de ``destination``.
    keep_raster: False descarta o GeoTIFF depois da poligonização (saída só
    vetorial); o cálculo continua o mesmo, feito na grade raster.

    points: lista de Generator com coordenadas no SRC da grade.
    mask: máscara numpy opcional (TRUE para células válidas).
    study_wkb: área de estudo (WKB, no SRC da grade), usada quando a extensão vem de camada
    poligonal (1.4.0-dev6, decisão do autor): só as células com o centro dentro dela recebem
    resultado, como o recorte da guia Vetorial; no atrito, as de fora continuam atravessáveis.
    friction_vector: superfície de atrito vetorial (1.4.0), dicionário com 'features'
    [(wkb, nota | 'barreira')], 'outside' (nota de passagem da área sem polígono, sem resultado) e os
    campos descritivos de voronoi_friction_vector.describe;
    os polígonos são rasterizados nesta grade.
    """
    from osgeo import gdal, osr
    weighted = mode in ('mass','mass_friction')
    if mode not in ('simple','mass','friction','mass_friction'):
        raise ValueError('Modalidade de Voronoi desconhecida.')
    if mode in ('friction','mass_friction') and not (friction_path or friction_components or friction_vector):
        raise ValueError('A modalidade com Atrito exige uma superfície de atrito (raster ou vetorial).')
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
    if not keep_raster and not vectorize:
        raise ValueError('Sem GeoTIFF, a saída precisa ser vetorial.')
    prefix = os.path.splitext(destination)[0]
    files = [destination, prefix+'_centros.csv', prefix+'_resumo.txt']
    if vectorize:
        files.append(prefix+vector_extension(vector_format))
    if any(os.path.isdir(f) for f in files):
        raise ValueError('Uma saída coincide com um diretório.')
    # A superfície de atrito é aberta e descarregada na thread da tarefa,
    # sem compartilhar objetos GDAL ou objetos Qt entre threads.
    friction = None
    vector_stats = None
    no_result = None
    nodata_cells = 0
    study_cells = None
    if study_wkb is not None:
        study_mask = _study_mask(study_wkb, geotransform, width, height, projection_wkt)
        study_cells = int(study_mask.sum())
        if not study_cells:
            raise ValueError('Nenhuma célula da grade tem o centro dentro da área de estudo; use células menores.')
        mask = study_mask if mask is None else (np.asarray(mask, dtype=bool) & study_mask)
    if mode in ('friction','mass_friction') and friction_vector:
        from .voronoi_friction_vector import rasterize_friction
        if width*height > MAX_FRICTION_CELLS:
            raise ValueError('O atrito excede 8 milhões de células; recorte ou aumente a resolução.')
        friction, vector_stats, no_result = rasterize_friction(
            friction_vector['features'], friction_vector.get('outside'), geotransform, width, height, projection_wkt)
        validate_friction(friction, geotransform, points)
        if no_result is not None:
            for point in points:
                col = int((point.x - geotransform[0]) / geotransform[1])
                row = int((point.y - geotransform[3]) / geotransform[5])
                if no_result[row, col]:
                    raise ValueError(f'Centro {point.identifier} fora dos polígonos de atrito (ou sobre barreira).')
    elif mode in ('friction','mass_friction') and friction_components:
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
        no_result, nodata_cells = _nodata_as_passage(friction)
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
        no_result, nodata_cells = _nodata_as_passage(friction)
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
                if no_result is not None:
                    values[no_result[y:y+h]] = 0  # atravessadas, sem resultado
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
            raster.SetMetadataItem('VISTASAGA_FRICTION_MODEL',FRICTION_MODEL if mode == 'friction' else MASS_FRICTION_MODEL)
            raster.SetMetadataItem('VISTASAGA_FRICTION_COST','nota direta (nota 1 = custo basal)')
            if friction_components:
                raster.SetMetadataItem('VISTASAGA_FRICTION_STACK','weighted_mean; common_valid_area')
                raster.SetMetadataItem('VISTASAGA_FRICTION_STACK_WEIGHTS',
                                       ','.join(str(spec['weight']) for spec in friction_components))
                raster.SetMetadataItem('VISTASAGA_FRICTION_STACK_LAYERS',
                                       str(len(friction_components)))
            raster.SetMetadataItem('VISTASAGA_FRICTION_SOURCE','vector' if vector_stats is not None else 'raster')
            raster.SetMetadataItem('VISTASAGA_FRICTION_SEARCH','Exact lower-bound pruning; no approximation')
            if mode == 'mass_friction':
                raster.SetMetadataItem('VISTASAGA_MASS_MODEL','A / M (equivale a M / d2)')
            raster.SetMetadataItem('VISTASAGA_FRICTION_VALIDATION','Vista SAGA original: caso sintetico 80x60, 99,7% das celulas; bacia real 495x1107 (10 m), 99,4 a 99,6%')
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
        # Regra de passagem conforme a fonte do atrito; a vetorial já sai em describe(), mais abaixo.
        passage_note = None
        if mode in ('friction','mass_friction') and vector_stats is None:
            passage_note = (f'NoData da superfície de atrito ({nodata_cells} células): sem resultado, '
                            'atravessável com nota 1 (custo basal do Vista SAGA, padrão da classe FUNDO).')
        _write_reports(local_csv,local_txt,mode,rows,excluded,pixel_area_m2(geotransform,units_to_meters),
                       passage_note=passage_note, study_cells=study_cells)
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
        if vector_stats is not None:
            from .voronoi_friction_vector import describe
            with open(local_txt,'a',encoding='utf-8') as report:
                report.write(describe(friction_vector, vector_stats, abs(geotransform[1])))
        if friction_components:
            with open(local_txt,'a',encoding='utf-8') as report:
                report.write('\nSuperfícies de atrito integradas (média ponderada)\n')
                for n, spec in enumerate(friction_components, 1):
                    report.write(f"{n}. {os.path.basename(spec['path'])}; peso={spec['weight']}; "
                                 f"notas={spec.get('notes','') or 'valores originais'}\n")
                report.write('NoData em qualquer superfície: célula sem resultado, atravessável com nota 1; '
                             'custo por célula = nota integrada.\n')
        if vectorize:
            with open(local_txt,'a',encoding='utf-8') as report:
                report.write('\nSaída vetorial\n')
                report.write('Polígonos obtidos por poligonização da grade raster: as bordas seguem os pixels '
                             f'(célula de {abs(geotransform[1]):g} × {abs(geotransform[5]):g} unidades do SRC).\n')
                report.write(f'Formato: {VECTOR_FORMATS[vector_extension(vector_format)][1]}.\n')
                if not keep_raster:
                    report.write('O GeoTIFF intermediário foi descartado; o cálculo é o mesmo da saída raster.\n')
            if progress: progress(83)
            local_vec = os.path.join(stage,os.path.basename(files[3]))
            _polygonize(local_tif,local_vec,rows,units_to_meters,cancelled)
            if progress: progress(96)
        if cancelled and cancelled(): raise InterruptedError('Voronoi cancelado pelo usuário.')
        # Backup com rollback dos arquivos já existentes (família vetorial inteira).
        published = files if keep_raster else files[1:]
        created.extend(publish_outputs(stage, published))
        if progress: progress(100)
        vector_path = files[3] if vectorize else None
        return {'output':files[0] if keep_raster else None, 'csv':files[1], 'txt':files[2],
                'vector':vector_path,
                'gpkg':vector_path if vector_path and vector_path.lower().endswith('.gpkg') else None,
                'rows':rows,
                'pixels_valid':sum(count.values()),'pixels_excluded':excluded,
                'raster_calc_seconds':analysis_seconds,
                'study_cells':study_cells,'friction_nodata_cells':nodata_cells,
                'friction_diagnostics':dict(friction_stats) if mode in ('friction','mass_friction') else None}
    finally:
        raster = None
        shutil.rmtree(stage,ignore_errors=True)


def _nodata_as_passage(friction):
    """NoData do raster de atrito: sem resultado, atravessável com nota 1 (1.4.0-dev6).

    Decisão do autor, pela coerência com a área sem polígono do atrito vetorial (dev5): uma célula
    sem nota não recebe resultado, mas as retas polo-célula passam por ela com o custo basal do
    Vista SAGA (nota 1, padrão da classe FUNDO). Antes era barreira. Os centros sobre NoData
    continuam recusados (``validate_friction``). Altera ``friction`` no lugar; devolve
    (máscara das células sem resultado ou None, quantidade).
    """
    from .voronoi_friction_vector import OUTSIDE_RATING
    missing = ~np.isfinite(friction)
    count = int(missing.sum())
    if not count:
        return None, 0
    friction[missing] = OUTSIDE_RATING
    return missing, count


def _study_mask(study_wkb, geotransform, width, height, projection_wkt):
    """Máscara booleana das células com o centro dentro da área de estudo (WKB no SRC da grade)."""
    from osgeo import gdal, ogr, osr
    from .gdal_scope import with_gdal_exceptions

    @with_gdal_exceptions
    def burn():
        geometry = ogr.CreateGeometryFromWkb(bytes(study_wkb))
        if geometry is None or geometry.IsEmpty():
            raise ValueError('Área de estudo vazia ou inválida.')
        srs = osr.SpatialReference()
        srs.ImportFromWkt(projection_wkt)
        source = None
        # GDAL < 3.11: driver vetorial "Memory"; a partir da 3.11 ele foi fundido ao "MEM".
        for name in ('Memory', 'MEM'):
            driver = ogr.GetDriverByName(name)
            if driver is not None and driver.GetMetadataItem('DCAP_VECTOR') == 'YES':
                source = driver.CreateDataSource('estudo')
                break
        if source is None:
            raise RuntimeError('GDAL sem driver vetorial em memória para o recorte pela área de estudo.')
        layer = source.CreateLayer('estudo', srs, ogr.wkbUnknown)
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetGeometry(geometry)
        layer.CreateFeature(feature)
        target = gdal.GetDriverByName('MEM').Create('', int(width), int(height), 1, gdal.GDT_Byte)
        target.SetGeoTransform(tuple(float(v) for v in geotransform))
        target.SetProjection(projection_wkt)
        target.GetRasterBand(1).Fill(0)
        gdal.RasterizeLayer(target, [1], layer, burn_values=[1], options=['ALL_TOUCHED=FALSE'])
        return target.GetRasterBand(1).ReadAsArray() != 0

    return burn()


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
