"""GeoTIFF categórico, contínuo ou RGB -> polígonos; mantém grade e SRC do TIFF.

Novo módulo independente: não modifica o conversor RS2 homologado.
Usa GDAL/OGR presentes no QGIS (sem dependência de bibliotecas adicionais).
"""
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from .rs2_format import RS2Error
from .rs2_converter import _gdal
from .rs2_rgb import RS2RGBMapper, discover_rgb_palette
from .rs2_vector import _layer_name, _publish_vector, vector_format
from .continuous_vector import discretize_tiff
from .monitoring_vector import find_monitoring_transitions, polygon_area_m2, monitoring_color


_INTEGER_GDAL_NAMES = frozenset((
    'Byte', 'Int8', 'UInt16', 'Int16', 'UInt32', 'Int32', 'UInt64', 'Int64',
))


def _legend(path, band):
    """Paleta/legenda documentada do TIFF, sem inventar semântica das classes."""
    sidecar = Path(str(path) + '.rs2.json')
    mapping = {}
    # Interoperabilidade com GeoTIFFs criados pelo módulo Combinação de Mapas.
    # Somente arquivos com este identificador explícito são interpretados como
    # combinação; os formatos anteriores preservam a leitura original.
    ds = getattr(band, 'GetDataset', lambda: None)()
    if ds is not None and ds.GetMetadataItem('VISTA_SAGA_MODULE') == 'COMBINACAO_MAPAS':
        import colorsys
        from .combination_core import read_combination_legend
        csv_file = Path(str(path)).with_suffix('')
        csv_file = Path(str(csv_file) + '_combinacoes.csv')
        if not csv_file.is_file():
            raise RS2Error('Não foi encontrado o CSV de combinações junto ao GeoTIFF. '
                           'Mantenha _combinacoes.csv na mesma pasta para preservar as legendas.')
        try:
            labels = read_combination_legend(csv_file)
        except (OSError, ValueError) as exc:
            raise RS2Error('CSV de combinações inválido.') from exc
        for code, label in labels.items():
            rgb = colorsys.hsv_to_rgb((code * .61803398875) % 1, .48, .85)
            mapping[code] = (label, '#' + ''.join(f'{int(255 * v):02X}' for v in rgb))
        return mapping
    if sidecar.exists():
        try:
            obj = json.loads(sidecar.read_text(encoding='utf-8'))
            if obj.get('format') != 'Vista SAGA RS2':
                raise ValueError('identificador de formato inesperado')
            labels, colors = obj['labels'], obj['colors']
            if len(labels) != len(colors) or len(labels) > 32769:
                raise ValueError('quantidade de cores e classes inconsistente')
            for i, (label, color) in enumerate(zip(labels, colors)):
                if len(color) < 3 or any(not (0 <= int(c) <= 255) for c in color[:3]):
                    raise ValueError('cor inválida')
                mapping[i] = (str(label), '#' + ''.join(f'{int(v):02X}' for v in color[:3]))
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise RS2Error('Metadados .rs2.json do GeoTIFF inválidos.') from exc
        return mapping
    names = band.GetCategoryNames() or []
    colors = band.GetRasterColorTable()
    count = min(max(len(names), colors.GetCount() if colors else 0), 32769)
    for code in range(count):
        name = (names[code] if code < len(names) and names[code] else
                ('FUNDO' if code == 0 else f'Classe {code}'))
        hexcolor = ''
        if colors and code < colors.GetCount():
            c = colors.GetColorEntry(code)
            hexcolor = '#' + ''.join(f'{int(x):02X}' for x in c[:3])
        mapping[code] = (name, hexcolor)
    return mapping


def _validate_tiff(path, raster_count, datatype_name):
    if Path(path).suffix.lower() not in ('.tif', '.tiff'):
        raise RS2Error('Selecione um GeoTIFF (.tif ou .tiff) para vetorização.')
    if raster_count not in (1, 3, 4):
        raise RS2Error('A vetorização exige TIFF categórico monobanda ou RGB/RGBA de 3/4 bandas.')
    if raster_count == 1 and datatype_name not in _INTEGER_GDAL_NAMES | {'Float32', 'Float64'}:
        raise RS2Error('Tipo de pixel do GeoTIFF monobanda não suportado.')
    if raster_count > 1 and datatype_name != 'Byte':
        raise RS2Error('TIFF RGB deve possuir canais de 8 bits por cor.')


def _mask_dataset(gdal, file_path, width, height, source_band, ignore_background,
                  rgb=False, alpha_band=None, rgb_skip_zero=False):
    """Máscara Byte: válida=255, excluir=0; combina classe 0, NoData e transparência.

    Para monobanda, inclui a classe 0 quando solicitada, mesmo se 0 for NoData.
    Não converte valores inválidos em polígonos.
    """
    driver = gdal.GetDriverByName('GTiff')
    ds = driver.Create(str(file_path), width, height, 1, gdal.GDT_Byte,
                       options=['TILED=YES', 'COMPRESS=LZW', 'BIGTIFF=IF_SAFER'])
    if ds is None:
        raise RS2Error('Falha ao criar máscara temporária para poligonização.')
    mask = ds.GetRasterBand(1)
    no_data = None if rgb else source_band.GetNoDataValue()
    for y in range(0, height, 128):
        n = min(128, height - y)
        values = source_band.ReadAsArray(0, y, width, n)
        if values is None:
            raise RS2Error(f'Falha ao gerar máscara na linha {y+1}.')
        valid = np.ones((n, width), dtype=bool)
        if no_data is not None and not (not ignore_background and no_data == 0):
            if np.isnan(no_data):
                valid &= ~np.isnan(values)
            else:
                valid &= values != no_data
        if ignore_background and (not rgb or rgb_skip_zero):
            valid &= values != 0
        if alpha_band is not None:
            alpha = alpha_band.ReadAsArray(0, y, width, n)
            if alpha is None:
                raise RS2Error('Erro ao ler transparência do TIFF.')
            valid &= alpha > 0
        mask.WriteArray(np.where(valid, 255, 0).astype(np.uint8), 0, y)
    mask.FlushCache()
    return ds


def _indexed_rgb(gdal, ds, path, progress_callback):
    """Cria raster categórico temporário com 1 código por cor RGB distinta.

    Em RGB sem legenda/códigos, atribui novos códigos estáveis, não valores R/G/B.
    """
    for i in range(1, ds.RasterCount + 1):
        if ds.GetRasterBand(i).DataType != gdal.GDT_Byte:
            raise RS2Error('A vetorização RGB exige oito bits em todos os canais.')
    labels, colors = discover_rgb_palette(ds)
    mapper = RS2RGBMapper(colors)
    datatype = gdal.GDT_Byte if len(colors) <= 256 else gdal.GDT_UInt16
    driver = gdal.GetDriverByName('GTiff')
    out = driver.Create(str(path), ds.RasterXSize, ds.RasterYSize, 1, datatype,
                        options=['TILED=YES', 'COMPRESS=DEFLATE', 'BIGTIFF=IF_SAFER'])
    if out is None:
        raise RS2Error('Não foi possível criar o raster categórico temporário.')
    gt = ds.GetGeoTransform(can_return_null=True)
    if gt is not None:
        out.SetGeoTransform(gt)
    if ds.GetProjectionRef():
        out.SetProjection(ds.GetProjectionRef())
    b = out.GetRasterBand(1)
    h, w = ds.RasterYSize, ds.RasterXSize
    for y in range(h):
        block = ds.ReadAsArray(0, y, w, 1)
        alpha = block[3, 0] if ds.RasterCount == 4 else None
        codes = mapper.map_row(block[0, 0], block[1, 0], block[2, 0], alpha, y)
        b.WriteArray(codes.reshape(1, w), 0, y)
        if y % 128 == 0:
            progress_callback(.02 + .30 * y / max(h, 1))
    b.FlushCache()
    out.FlushCache()
    b = None
    out = None
    mapping = {i: (label, '#' + ''.join(f'{int(c):02X}' for c in color[:3]))
               for i, (label, color) in enumerate(zip(labels, colors))}
    # Somente branco/transparente identifica FUNDO automaticamente.
    has_background = labels[0].startswith('FUNDO')
    return mapping, has_background


def convert_tif_to_vector(tif_path, vector_path, epsg='', progress=None,
                          ignore_background=True, eight_connected=False,
                          manual_bounds=None, continuous_classes=5):
    """Vetorização independente de RS2. Monobanda inteiro, contínuo ou RGB/RGBA.

    Honra SRC e transformada do GeoTIFF; EPSG informado substitui apenas o SRC
    atribuído, sem reprojetar as geometrias. `progress(done,total)` cancela com False.
    """
    source = Path(tif_path)
    target = Path(vector_path)
    if source.suffix.lower() not in ('.tif', '.tiff') or not source.is_file():
        raise RS2Error('Selecione um arquivo GeoTIFF existente para vetorização.')
    if source.resolve() == target.resolve():
        raise RS2Error('A saída não pode sobrescrever a entrada GeoTIFF.')
    driver_name, _ = vector_format(target.suffix)
    from osgeo import ogr, osr
    gdal, _ = _gdal()
    driver = ogr.GetDriverByName(driver_name)
    if driver is None:
        raise RS2Error(f'Driver GDAL/OGR indisponível: {driver_name}.')
    ds = gdal.Open(str(source), gdal.GA_ReadOnly)
    if ds is None:
        raise RS2Error('Não foi possível abrir o GeoTIFF de entrada.')

    def notify(frac):
        if progress is not None and progress(round(max(0, min(1, frac)) * 1000), 1000) is False:
            raise RS2Error('Operação cancelada pelo usuário.')

    try:
        _validate_tiff(source, ds.RasterCount, gdal.GetDataTypeName(ds.GetRasterBand(1).DataType))
        gt = ds.GetGeoTransform(can_return_null=True)
        if gt is None and not manual_bounds:
            raise RS2Error('TIFF sem georreferenciamento: informe uma extensão manual para vetorizar.')
        if gt is None:
            from .rs2_converter import _parse_bounds
            xmin, ymin, xmax, ymax = _parse_bounds(manual_bounds, ds.RasterXSize, ds.RasterYSize)
            gt = (xmin, (xmax-xmin)/ds.RasterXSize, 0, ymax, 0, -(ymax-ymin)/ds.RasterYSize)
        if gt[1] == 0 or gt[5] == 0:
            raise RS2Error('Transformação espacial inválida no GeoTIFF.')
        srs = None
        if epsg:
            if not str(epsg).upper().startswith('EPSG:'):
                raise RS2Error('Selecione um SRC EPSG válido no QGIS.')
            srs = osr.SpatialReference()
            if srs.ImportFromEPSG(int(str(epsg).split(':')[1])) != 0:
                raise RS2Error('Não foi possível interpretar o EPSG selecionado.')
        elif ds.GetProjectionRef():
            srs = osr.SpatialReference()
            if srs.ImportFromWkt(ds.GetProjectionRef()) != 0:
                raise RS2Error('O SRC armazenado no GeoTIFF é inválido.')
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.vista_tif_vector_', dir=target.parent) as temp:
            tmp = Path(temp)
            stage = tmp / target.name
            work = tmp / 'work_classes.gpkg'
            dataset = None
            layer = None
            raster = None
            mask_ds = None
            try:
                rgb = ds.RasterCount in (3, 4)
                continuous = (ds.RasterCount == 1 and
                              gdal.GetDataTypeName(ds.GetRasterBand(1).DataType)
                              in ('Float32', 'Float64'))
                ranges = {}
                transitions = (find_monitoring_transitions(source, ds.GetRasterBand(1))
                               if ds.RasterCount == 1 and not continuous else {})
                if continuous:
                    ranges = discretize_tiff(gdal, ds, tmp / 'intervalos.tif',
                                            continuous_classes, notify, gt)
                    raster = gdal.Open(str(tmp / 'intervalos.tif'), gdal.GA_ReadOnly)
                    if raster is None:
                        raise RS2Error('Falha ao abrir raster temporário classificado.')
                    band = raster.GetRasterBand(1)
                    mapping = {code: (entry[0], '') for code, entry in ranges.items()}
                    # Classe 0 do raster temporário representa apenas NoData.
                    skip_background = True
                elif rgb:
                    mapping, background_present = _indexed_rgb(gdal, ds, tmp / 'indexed.tif', notify)
                    raster = gdal.Open(str(tmp / 'indexed.tif'), gdal.GA_ReadOnly)
                    band = raster.GetRasterBand(1)
                    # Sem cor branca nem transparência, a primeira cor é uma classe legítima.
                    skip_background = ignore_background and background_present
                else:
                    band = ds.GetRasterBand(1)
                    mapping = _legend(source, band)
                    if transitions:
                        mapping = {code: (entry['legenda'],
                                   monitoring_color(code, entry['situacao'] == 'Mudança'))
                                   for code, entry in transitions.items()}
                    skip_background = ignore_background
                notify(.34)
                mask_ds = _mask_dataset(gdal, tmp / 'valid.tif', ds.RasterXSize,
                    ds.RasterYSize, band, skip_background,
                    rgb=rgb, alpha_band=(ds.GetRasterBand(4) if ds.RasterCount == 4 else None),
                    rgb_skip_zero=skip_background)
                mask = mask_ds.GetRasterBand(1)
                gdriver = ogr.GetDriverByName('GPKG')
                if gdriver is None:
                    raise RS2Error('Driver GeoPackage necessário para vetorização indisponível.')
                dataset = gdriver.CreateDataSource(str(work))
                if dataset is None:
                    raise RS2Error('Não foi possível criar o arquivo vetorial temporário.')
                layer = dataset.CreateLayer(_layer_name(target), srs=srs, geom_type=ogr.wkbPolygon)
                if layer is None:
                    raise RS2Error('Não foi possível criar a camada vetorial.')
                fields = [('CODIGO', ogr.OFTInteger64), ('CLASSE', ogr.OFTString),
                          ('COR_HEX', ogr.OFTString)]
                if continuous:
                    fields.extend([('VALOR_MIN', ogr.OFTReal), ('VALOR_MAX', ogr.OFTReal)])
                if transitions:
                    # Nomes com até dez caracteres, compatíveis também com Shapefile.
                    fields.extend([
                        ('ID_TRANS', ogr.OFTInteger64), ('COD_INI', ogr.OFTReal),
                        ('COD_FIM', ogr.OFTReal), ('SITUACAO', ogr.OFTString),
                        ('DEIXOU_SER', ogr.OFTString), ('TORNOU_SE', ogr.OFTString),
                    ])
                fields.extend([('AREA_M2', ogr.OFTReal), ('AREA_HA', ogr.OFTReal),
                               ('PCT_AREA', ogr.OFTReal)])
                for name, kind in fields:
                    field = ogr.FieldDefn(name, kind)
                    if name == 'COR_HEX':
                        field.SetWidth(7)
                    if name == 'CLASSE' and target.suffix.lower() == '.shp':
                        field.SetWidth(254)
                    if layer.CreateField(field) != 0:
                        raise RS2Error(f'Falha ao criar o campo {name}.')

                def polygon_progress(frac, message, ignored):
                    try:
                        notify(.36 + .48 * float(frac))
                        return 1
                    except RS2Error:
                        return 0

                opt = ['8CONNECTED=8'] if eight_connected else []
                code_field = layer.GetLayerDefn().GetFieldIndex('CODIGO')
                err = gdal.Polygonize(band, mask, layer, code_field, opt, polygon_progress)
                if err != 0:
                    raise RS2Error('Poligonização cancelada ou malsucedida.')
                count = layer.GetFeatureCount()
                area_total = 0.0
                area_available = bool(srs)
                for i, feat in enumerate(layer):
                    code = int(feat.GetField('CODIGO'))
                    if transitions and code not in transitions:
                        raise RS2Error(f'ID de transição {code} não consta no relatório associado ao GeoTIFF.')
                    name, color = mapping.get(code, (f'Classe {code}', ''))
                    feat.SetField('CLASSE', name)
                    feat.SetField('COR_HEX', color)
                    if continuous:
                        _, lower, upper = ranges[code]
                        feat.SetField('VALOR_MIN', lower)
                        feat.SetField('VALOR_MAX', upper)
                    if transitions:
                        entry = transitions[code]
                        for key, value in (
                            ('ID_TRANS', code), ('COD_INI', entry['initial']),
                            ('COD_FIM', entry['final']), ('SITUACAO', entry['situacao']),
                            ('DEIXOU_SER', entry['deixou']), ('TORNOU_SE', entry['tornou'])):
                            feat.SetField(key, value)
                    area = polygon_area_m2(feat.GetGeometryRef(), srs)
                    if area is not None:
                        feat.SetField('AREA_M2', area)
                        feat.SetField('AREA_HA', area / 10000.0)
                        area_total += area
                    else:
                        area_available = False
                    if layer.SetFeature(feat) != 0:
                        raise RS2Error('Falha ao preencher atributos do vetor.')
                    if i % 250 == 0:
                        notify(.84 + .07 * i / max(count, 1))
                layer.ResetReading()
                if area_available and area_total > 0:
                    for i, feat in enumerate(layer):
                        feat.SetField('PCT_AREA', 100.0 * float(feat.GetField('AREA_M2')) / area_total)
                        if layer.SetFeature(feat) != 0:
                            raise RS2Error('Falha ao calcular percentuais de área.')
                        if i % 250 == 0:
                            notify(.91 + .07 * i / max(count, 1))
                layer.SyncToDisk()
                feat = None
                layer = None
                dataset = None
                mask = None
                mask_ds = None
                raster = None
                notify(.98)
                if target.suffix.lower() == '.gpkg':
                    os.replace(work, stage)
                else:
                    options = gdal.VectorTranslateOptions(
                        format=driver_name,
                        layerName=(None if target.suffix.lower() == '.shp'
                                   else _layer_name(target)),
                        layerCreationOptions=(['ENCODING=UTF-8']
                                              if target.suffix.lower() == '.shp' else []))
                    translated = gdal.VectorTranslate(str(stage), str(work), options=options)
                    if translated is None:
                        raise RS2Error(f'Falha na exportação para {driver_name}.')
                    translated = None
                _publish_vector(stage, target)
                return target
            finally:
                layer = None
                dataset = None
                mask = None
                mask_ds = None
                raster = None
    finally:
        ds = None
