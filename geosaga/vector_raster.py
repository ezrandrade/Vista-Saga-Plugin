"""Rasterização categórica/numérica de vetores locais para GeoTIFF.

Não altera as quatro operações homologadas do conversor. Executado no GDAL/OGR
fornecido pelo QGIS; faz a publicação transacional dos arquivos auxiliares.

- Campo inteiro: mantém códigos, inclusive zero.
- Campo real: mantém valores decimais (Float64).
- Campo de texto: transforma cada categoria não vazia em código sequencial,
  com nomes e (quando presentes) cores preservados como legenda do GeoTIFF.
- O SRC é herdado da fonte; NÃO há reprojeção implícita.
- NoData (0 para campos categóricos, NaN para campos reais) nas células vazias.
"""

import math
from pathlib import Path
import tempfile

from .rs2_format import RS2Error
from .rs2_outputs import publish_geotiff

VECTOR_EXTENSIONS = frozenset({'.gpkg', '.shp', '.geojson', '.json', '.fgb'})
MAX_PIXELS = 100_000_000
MAX_TEXT_CLASSES = 32767


def split_vector_source(value):
    """Aceita caminho local e URI OGR do QGIS com ``|layername=``/``|layerid=``."""
    value = str(value or '').strip()
    if not value:
        raise RS2Error('Selecione uma camada vetorial de entrada.')
    parts = value.split('|')
    path = Path(parts[0])
    if path.suffix.lower() not in VECTOR_EXTENSIONS:
        raise RS2Error('Utilize um vetor local GPKG, SHP, GeoJSON ou FlatGeobuf.')
    if not path.is_file():
        raise RS2Error('Arquivo vetorial não encontrado: ' + str(path))
    layername = None
    layerid = None
    for option in parts[1:]:
        if option.startswith('layername='):
            layername = option[len('layername='):]
        elif option.startswith('layerid='):
            try:
                layerid = int(option[len('layerid='):])
            except ValueError as exc:
                raise RS2Error('Identificador inválido de camada GeoPackage.') from exc
        elif option:
            raise RS2Error('Opção não reconhecida na URI da camada: ' + option)
    if layername == '':
        raise RS2Error('Nome da camada vetorial não pode estar vazio.')
    return path, layername, layerid


def raster_dimensions(extent, pixel_size):
    """Grade norte-acima, ancorada no mínimo X e máximo Y da fonte."""
    try:
        x_min, x_max, y_min, y_max = map(float, extent)
        res = float(pixel_size)
    except (ValueError, TypeError) as exc:
        raise RS2Error('Resolução ou extensão vetorial inválida.') from exc
    if not all(math.isfinite(v) for v in (x_min, x_max, y_min, y_max, res)):
        raise RS2Error('Resolução e extensão devem conter números finitos.')
    if res <= 0 or x_max < x_min or y_max < y_min:
        raise RS2Error('Resolução positiva e extensão ordenada são necessárias.')
    # Pontos e linhas horizontais/verticais podem ter extensão nula num eixo.
    if x_max == x_min:
        x_min -= res / 2
        x_max += res / 2
    if y_max == y_min:
        y_min -= res / 2
        y_max += res / 2
    cols = math.ceil((x_max - x_min) / res - 1e-10)
    rows = math.ceil((y_max - y_min) / res - 1e-10)
    if cols <= 0 or rows <= 0 or cols * rows > MAX_PIXELS:
        raise RS2Error('A grade teria mais de 100 milhões de células (ou seria vazia). '
                       'Aumente o tamanho do pixel ou reduza a área de entrada.')
    return cols, rows, (x_min, res, 0., y_max, 0., -res)


def field_mode(ogr_type, ogr):
    if ogr_type in (ogr.OFTInteger, ogr.OFTInteger64):
        return 'int'
    if ogr_type == ogr.OFTReal:
        return 'real'
    if ogr_type == ogr.OFTString:
        return 'text'
    raise RS2Error('O campo escolhido deve ser inteiro, decimal ou texto. '
                   'Campos de data e valores binários não são suportados.')


def normalize_color(value):
    """Aproveita somente cores HEX válidas, sem supor a semântica da cor."""
    s = str(value or '').strip()
    if s.startswith('#') and len(s) == 7 and all(c in '0123456789ABCDEFabcdef' for c in s[1:]):
        return s.upper()
    return ''


def _check_field(layer, name, ogr):
    field_index = layer.GetLayerDefn().GetFieldIndex(str(name))
    if field_index < 0:
        raise RS2Error(f'Campo não encontrado no vetor: {name!r}.')
    fld = layer.GetLayerDefn().GetFieldDefn(field_index)
    return field_index, field_mode(fld.GetType(), ogr)


def _open_ogr_layer(ogr, source):
    path, layer_name, layer_id = split_vector_source(source)
    ds = ogr.Open(str(path), 0)
    if ds is None:
        raise RS2Error('GDAL/OGR não conseguiu abrir o vetor: ' + str(path))
    layer = (ds.GetLayerByName(layer_name) if layer_name is not None else
             ds.GetLayer(layer_id) if layer_id is not None else ds.GetLayer(0))
    if layer is None:
        raise RS2Error('A camada solicitada não existe no arquivo vetorial.')
    return ds, layer


def _write_categories(band, categories, gdal):
    """Cria legenda associada ao pixel, sempre que os códigos forem consecutivos."""
    if not categories:
        return
    keys = list(categories)
    if any(v < 0 or v >= MAX_TEXT_CLASSES for v in keys):
        return
    if max(keys) > 4096:
        return  # evita metadados e paleta enormes para código numérico esparso
    maximum = max(keys)
    names = ['FUNDO'] + [f'Classe {i}' for i in range(1, maximum + 1)]
    colors = gdal.ColorTable()
    colors.SetColorEntry(0, (255, 255, 255, 255))
    has_palette = False
    for value, (label, color) in categories.items():
        names[value] = label
        if color:
            rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
            colors.SetColorEntry(value, (*rgb, 255))
            has_palette = True
    band.SetCategoryNames(names)
    if has_palette and maximum <= 255:
        band.SetRasterColorTable(colors)
        band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)


def convert_vector_to_tif(vector_source, tiff_path, field_name, pixel_size,
                          progress=None, all_touched=False):
    """Rasteriza uma camada vetorial por atributo, sem alterar SRC/geometrias.

    `progress(done,total)` interrompe quando retornar False. Não reprojeta.
    A resolução é medida nas unidades do SRC da camada, não necessariamente metros.
    SRC geográfico usa graus; SRC projetado usa as unidades do sistema.
    """
    output = Path(tiff_path)
    source_path, _, _ = split_vector_source(vector_source)
    if output.suffix.lower() not in ('.tif', '.tiff'):
        raise RS2Error('A saída deve ser um GeoTIFF .tif ou .tiff.')
    if output.resolve() == source_path.resolve():
        raise RS2Error('O GeoTIFF de saída não pode substituir o vetor de entrada.')
    from osgeo import gdal, ogr
    gdal.UseExceptions()
    src_ds, src_layer = _open_ogr_layer(ogr, vector_source)
    source_field, mode = _check_field(src_layer, field_name, ogr)
    spatial_ref = src_layer.GetSpatialRef()
    if spatial_ref is None:
        raise RS2Error('A camada não possui SRC. Defina-o no QGIS antes de rasterizar.')
    if src_layer.GetFeatureCount() == 0:
        raise RS2Error('A camada vetorial não contém feições.')
    cols, rows, geo = raster_dimensions(src_layer.GetExtent(), pixel_size)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Trabalho em arquivo temporário: não afeta arquivos de saída anteriores.
    with tempfile.TemporaryDirectory(prefix='.vista_vector_raster_', dir=output.parent) as tmp:
        stage = Path(tmp) / 'classificados.tif'
        work = Path(tmp) / 'classes.gpkg'
        vdriver = ogr.GetDriverByName('GPKG')
        if vdriver is None:
            raise RS2Error('Driver GeoPackage do GDAL não disponível.')
        intermediary = vdriver.CreateDataSource(str(work))
        if intermediary is None:
            raise RS2Error('Não foi possível criar a camada temporária.')
        writer = intermediary.CreateLayer('pixels', srs=spatial_ref,
                                          geom_type=src_layer.GetGeomType())
        if writer is None:
            raise RS2Error('Falha ao criar camada temporária de rasterização.')
        if writer.CreateField(ogr.FieldDefn('VS_VALUE', ogr.OFTReal if mode == 'real' else ogr.OFTInteger)) != 0:
            raise RS2Error('Não foi possível criar o campo de valores raster.')
        cols_per_field = src_layer.GetLayerDefn()
        label_field = cols_per_field.GetFieldIndex('CLASSE')
        color_field = cols_per_field.GetFieldIndex('COR_HEX')
        seen = {}
        categories = {}
        source_count = max(1, src_layer.GetFeatureCount())
        valid_count = 0
        for i, feature in enumerate(src_layer):
            if progress is not None and i % 100 == 0:
                if progress(i, source_count * 2) is False:
                    raise RS2Error('Operação cancelada pelo usuário.')
            geometry = feature.GetGeometryRef()
            if geometry is None or geometry.IsEmpty() or not feature.IsFieldSetAndNotNull(source_field):
                continue
            value = feature.GetField(source_field)
            if mode == 'text':
                name = str(value).strip()
                if not name:
                    continue
                if name not in seen:
                    if len(seen) >= MAX_TEXT_CLASSES - 1:
                        raise RS2Error('Mais de 32766 categorias textuais; simplifique o atributo.')
                    seen[name] = len(seen) + 1
                    color = (normalize_color(feature.GetField(color_field)) if color_field >= 0 and
                             feature.IsFieldSetAndNotNull(color_field) else '')
                    categories[seen[name]] = (name, color)
                code = seen[name]
            elif mode == 'int':
                code = int(value)
                if code < 0 or code > 2_147_483_647:
                    raise RS2Error('Valores inteiros negativos ou superiores a Int32 não '
                                   'são suportados nesta conversão categórica.')
                if code not in categories:
                    class_label = (str(feature.GetField(label_field)) if label_field >= 0 and
                                   feature.IsFieldSetAndNotNull(label_field) else
                                   ('FUNDO' if code == 0 else f'Classe {code}'))
                    class_color = (normalize_color(feature.GetField(color_field)) if color_field >= 0 and
                                   feature.IsFieldSetAndNotNull(color_field) else '')
                    categories[code] = (class_label, class_color)
            else:
                code = float(value)
                if not math.isfinite(code):
                    raise RS2Error('Valores decimais não finitos não são admitidos.')
            feature_out = ogr.Feature(writer.GetLayerDefn())
            feature_out.SetField('VS_VALUE', code)
            feature_out.SetGeometry(geometry)
            if writer.CreateFeature(feature_out) != 0:
                raise RS2Error('Falha ao transferir feição para a rasterização.')
            feature_out = None
            valid_count += 1
        if valid_count == 0:
            raise RS2Error('Nenhuma feição possui geometria e atributo válidos.')
        writer.SyncToDisk()
        max_code = max(categories, default=0)
        gtype = (gdal.GDT_Float64 if mode == 'real' else
                 gdal.GDT_Byte if max_code <= 255 else
                 gdal.GDT_UInt16 if max_code <= 65535 else gdal.GDT_Int32)
        raster = gdal.GetDriverByName('GTiff').Create(str(stage), cols, rows, 1, gtype,
                    options=['TILED=YES', 'COMPRESS=DEFLATE', 'BIGTIFF=IF_SAFER'])
        if raster is None:
            raise RS2Error('Não foi possível criar o GeoTIFF.')
        raster.SetGeoTransform(geo)
        raster.SetProjection(spatial_ref.ExportToWkt())
        raster.SetMetadataItem('VISTA_SAGA_SOURCE_FIELD', str(field_name))
        raster.SetMetadataItem('VISTA_SAGA_RASTER_MODE', mode)
        band = raster.GetRasterBand(1)
        if mode == 'real':
            fill = float('nan')
        else:
            fill = 0
        band.Fill(fill)
        band.SetNoDataValue(fill)
        # Não aplicar NoData=0 indiscriminadamente às classes de código 0?
        # Aqui 0 é reservado para FUNDO (mesma convenção do formato RS2).
        if mode != 'real':
            _write_categories(band, categories, gdal)
        options = ['ATTRIBUTE=VS_VALUE'] + (['ALL_TOUCHED=TRUE'] if all_touched else [])
        callback_failed = [False]
        def raster_progress(fraction, message, unused):
            if progress is None:
                return 1
            if progress(source_count + round(fraction * source_count), source_count * 2) is False:
                callback_failed[0] = True
                return 0
            return 1
        status = gdal.RasterizeLayer(raster, [1], writer, options=options,
                                     callback=raster_progress)
        if status != 0:
            raise RS2Error('Rasterização cancelada.' if callback_failed[0] else 'Falha na rasterização GDAL.')
        band.FlushCache()
        raster.FlushCache()
        band = raster = None
        writer = intermediary = None
        src_layer = src_ds = None
        # A família de auxiliares gerada junto ao raster deve ser publicada atomicamente.
        publish_geotiff(stage, output)
    return output
