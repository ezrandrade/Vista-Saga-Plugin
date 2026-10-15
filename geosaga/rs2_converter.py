"""Conversão RS2 Vista SAGA <-> GeoTIFF usando GDAL fornecido pelo QGIS.

A identificação do SRC não faz parte da variante RS2 documentada: nunca deduzir
EPSG automaticamente das coordenadas numéricas. O usuário deve confirmá-lo.
"""

from pathlib import Path
import base64
import json
import zlib

import numpy as np

from .rs2_format import RS2Error, RS2Header, RS2Reader, write_rs2
from .rs2_rgb import RS2RGBMapper, discover_rgb_palette
from .rs2_outputs import publish_geotiff, output_conflicts, write_worldfile


def _gdal():
    # GDAL de QGIS (não requer pip nem rasterio no ambiente do plugin).
    from osgeo import gdal, osr
    gdal.UseExceptions()
    return gdal, osr


def _metadata(header: RS2Header, epsg: str = ''):
    return {
        'format': 'Vista SAGA RS2',
        'origin': 'RS2 legado Vista SAGA/UFRJ',
        'version': 1,
        'epsg': epsg or None,
        'reference_system_note': 'EPSG informado pelo usuário; o RS2 não o registra de forma inequívoca.',
        'source_header_hex': header.prefix.hex(),
        # Dados de paleta comprimidos permitem conversões de ida/volta sem
        # alterar entradas de cor legadas que não são categorias ativas.
        'legacy_palette_zlib_b64': (base64.b64encode(zlib.compress(header.raw_palette)).decode('ascii')
                                      if header.raw_palette is not None else None),
        'width': header.width,
        'height': header.height,
        'xmin': header.xmin,
        'ymin': header.ymin,
        'xmax': header.xmax,
        'ymax': header.ymax,
        'labels': list(header.labels),
        'colors': [list(c[:3]) for c in header.colors],
        'background_code': 0,
    }


def _sidecar_path(path):
    return Path(str(path) + '.rs2.json')


def convert_rs2_to_tif(rs2_path, tiff_path, epsg='', progress=None,
                       mark_background_nodata=True):
    """GeoTIFF de uma banda com códigos e colormap originais + JSON de metadados.

    Não é a simples imagem RGB do Vista SAGA: os pixels permanecem classificados.
    """
    gdal, osr = _gdal()
    reader = RS2Reader(rs2_path)
    h = reader.header
    epsg = str(epsg).strip().upper()
    if epsg and not epsg.startswith('EPSG:'):
        raise RS2Error('SRC deve ser informado como EPSG:XXXXX.')
    wkt = ''
    if epsg:
        try:
            epsg_code = int(epsg[5:])
            srs = osr.SpatialReference()
            if srs.ImportFromEPSG(epsg_code) != 0 or not srs.IsProjected():
                raise RS2Error('É necessário informar um EPSG projetado confirmado.')
            wkt = srs.ExportToWkt()
        except (ValueError, TypeError) as exc:
            raise RS2Error('Código EPSG inválido.') from exc
    target = Path(tiff_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = str(target) + '.part.tif'
    dst = None
    try:
        driver = gdal.GetDriverByName('GTiff')
        if driver is None:
            raise RS2Error('Driver GDAL GeoTIFF indisponível.')
        kind = gdal.GDT_Byte if h.num_classes <= 256 else gdal.GDT_UInt16
        dst = driver.Create(temp, h.width, h.height, 1, kind,
                            options=['TILED=YES', 'COMPRESS=DEFLATE',
                                     'BIGTIFF=IF_SAFER', 'NUM_THREADS=2'])
        if dst is None:
            raise RS2Error('Não foi possível criar arquivo GeoTIFF.')
        dst.SetGeoTransform((h.xmin, h.pixel_x, 0., h.ymax, 0., -h.pixel_y))
        if wkt:
            dst.SetProjection(wkt)
        band = dst.GetRasterBand(1)
        if mark_background_nodata:
            band.SetNoDataValue(0)
        band.SetCategoryNames(h.labels)
        color_table = gdal.ColorTable()
        for i, color in enumerate(h.colors):
            color_table.SetColorEntry(i, (int(color[0]), int(color[1]), int(color[2]), 255))
        band.SetRasterColorTable(color_table)
        band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)
        band.SetMetadataItem('RS2_FORMAT', 'Vista SAGA (legacy)')
        band.SetMetadataItem('RS2_BACKGROUND', '0')
        for y, row in enumerate(reader.rows()):
            band.WriteArray(row.reshape(1, h.width).astype('uint8' if kind == gdal.GDT_Byte else 'uint16'),
                            xoff=0, yoff=y)
            if progress and y % 100 == 0 and progress(y + 1, h.height) is False:
                raise RS2Error('Operação cancelada pelo usuário.')
        band.FlushCache()
        dst.FlushCache()
        band = None
        dst = None
        _sidecar_path(temp).write_text(json.dumps(_metadata(h, epsg),
                                                  ensure_ascii=False, indent=2),
                                       encoding='utf-8')
        write_worldfile(temp, h.xmin, h.ymax, h.pixel_x, h.pixel_y)
        publish_geotiff(temp, target)
        return target
    except Exception:
        dst = None
        for leftover in (Path(temp), Path(str(temp) + '.rs2.json'),
                         Path(str(temp) + '.aux.xml'), Path(str(temp) + '.xml'),
                         Path(temp).with_suffix('.tfw'), Path(str(temp) + 'w')):
            leftover.unlink(missing_ok=True)
        raise


def _parse_bounds(bounds, width, height):
    """Analisa extensão manual, usada só quando faltam coordenadas no TIFF."""
    if bounds is None or (isinstance(bounds, str) and not bounds.strip()):
        raise RS2Error(
            'O TIFF de entrada não possui georreferenciamento. Informe '
            'xmin, ymin, xmax, ymax no campo "Extensão manual", '
            'ou use um RS2 de referência para o RGB original.')
    try:
        if isinstance(bounds, str):
            items = [v.strip() for v in bounds.replace(';', ',').split(',')]
        else:
            items = list(bounds)
        if len(items) != 4:
            raise ValueError('quatro limites esperados')
        vals = tuple(int(v) if str(v).strip().lstrip('+').isdigit() else
                     round(float(v)) for v in items)
        if any(abs(float(v) - i) > 1e-5 for v, i in zip(items, vals)):
            raise ValueError('coordenadas devem ser inteiras')
    except (TypeError, ValueError) as exc:
        raise RS2Error(
            'Extensão manual inválida. Use quatro coordenadas inteiras: '
            'xmin, ymin, xmax, ymax.') from exc
    xmin, ymin, xmax, ymax = vals
    if not (0 <= xmin < xmax < 2**32 and 0 <= ymin < ymax < 2**32):
        raise RS2Error('Os limites devem ser positivos, com mínimo menor que máximo.')
    if not (0 < width <= 65535 and 0 < height <= 65535):
        raise RS2Error('As dimensões excedem o formato RS2 documentado.')
    return vals


def _validated_grid(ds, fallback_bounds=None):
    gt = ds.GetGeoTransform(can_return_null=True)
    if gt is None:
        return _parse_bounds(fallback_bounds, ds.RasterXSize, ds.RasterYSize)
    if abs(gt[2]) > 1e-10 or abs(gt[4]) > 1e-10 or gt[1] <= 0 or gt[5] >= 0:
        raise RS2Error('GeoTIFF deve ter grade norte-acima e sem rotação.')
    width, height = ds.RasterXSize, ds.RasterYSize
    xmin = gt[0]
    xmax = gt[0] + width*gt[1]
    ymax = gt[3]
    ymin = gt[3] + height*gt[5]
    values = (xmin, ymin, xmax, ymax)
    ints = tuple(round(v) for v in values)
    if any(abs(v - i) > 1e-5 for v, i in zip(values, ints)):
        raise RS2Error('RS2 armazena coordenadas inteiras; limites fracionários exigem adequação.')
    return ints


def _read_sidecar(path):
    fp = _sidecar_path(path)
    if not fp.exists():
        return None
    data = json.loads(fp.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('format') != 'Vista SAGA RS2':
        raise RS2Error('Metadados JSON de formato RS2 inválidos.')
    return data


def _category_legend_from_raster(band, max_category):
    existing = band.GetCategoryNames() or []
    ct = band.GetRasterColorTable()
    labels = []
    colors = []
    for i in range(max_category + 1):
        labels.append(existing[i] if i < len(existing) and existing[i] else
                      ('FUNDO' if i == 0 else f'Classe {i}'))
        if ct is not None and i < ct.GetCount():
            rgb = ct.GetColorEntry(i)
            colors.append((int(rgb[0]), int(rgb[1]), int(rgb[2]), 0))
        else:
            colors.append((255, 255, 255, 0) if i == 0 else (128, 128, 128, 0))
    return labels, colors


def _convert_rgb_to_rs2(ds, tiff_path, rs2_path, reference_rs2, progress, manual_bounds=None):
    """Reconstrói RS2 a partir de RGB e paleta/grade do RS2 original.

    TIFF RGB sem georreferenciamento é aceito SOMENTE com o RS2 de referência
    explícito, que fornece a única fonte verificável para legendas e grade.
    """
    gdal, _osr = _gdal()
    if not reference_rs2:
        return _convert_rgb_standalone(ds, tiff_path, rs2_path, progress, manual_bounds)
    ref_path = Path(reference_rs2)
    if not ref_path.is_file():
        raise RS2Error('O arquivo RS2 de referência não existe.')
    if Path(rs2_path).resolve() == ref_path.resolve():
        raise RS2Error(
            'O RS2 de saída não pode substituir o RS2 de referência. '
            'Escolha outro nome, por exemplo, MAPA_convertido.rs2.')
    h = RS2Reader(ref_path).header
    if (h.width, h.height) != (ds.RasterXSize, ds.RasterYSize):
        raise RS2Error(
            f'Dimensões do TIFF ({ds.RasterXSize} × {ds.RasterYSize}) '
            f'diferem do RS2 de referência ({h.width} × {h.height}).')
    if any(ds.GetRasterBand(i).DataType != gdal.GDT_Byte
           for i in range(1, ds.RasterCount + 1)):
        raise RS2Error('A conversão RGB exige TIFF de 8 bits por canal, sem alteração de cores.')
    # TIFFs exportados do Vista SAGA podem não conter geotransform.
    # Se ele existir, não permitimos que contradiga a referência.
    geotransform = ds.GetGeoTransform(can_return_null=True)
    if geotransform is None and manual_bounds:
        given = _parse_bounds(manual_bounds, h.width, h.height)
        expected = (h.xmin, h.ymin, h.xmax, h.ymax)
        if given != expected:
            raise RS2Error('A extensão manual não coincide com a grade do RS2 de referência.')
    if geotransform is not None:
        try:
            coords = _validated_grid(ds)
        except RS2Error as exc:
            raise RS2Error('O GeoTIFF RGB informa georreferenciamento incompatível: ' + str(exc)) from exc
        expected = (h.xmin, h.ymin, h.xmax, h.ymax)
        if coords != expected:
            raise RS2Error(
                f'Extensão geográfica do TIFF {coords} é diferente '
                f'do RS2 de referência {expected}.')
    mapper = RS2RGBMapper(h.colors)

    def source_rows():
        for y in range(h.height):
            pixels = ds.ReadAsArray(0, y, h.width, 1)
            if pixels is None or pixels.shape != (ds.RasterCount, 1, h.width):
                raise RS2Error(f'Falha na leitura das bandas RGB na linha {y + 1}.')
            red, green, blue = (pixels[i, 0, :] for i in range(3))
            alpha = pixels[3, 0, :] if ds.RasterCount == 4 else None
            yield mapper.map_row(red, green, blue, alpha, y)

    out = Path(rs2_path)
    write_rs2(out, h, source_rows(), progress=progress)
    manifest = _metadata(h)
    manifest['rgb_reference_rs2'] = str(ref_path)
    manifest['rgb_reference_note'] = (
        'Códigos recuperados por correspondência exata de cores. '
        'Origem geográfica e legenda fornecidas pelo RS2 de referência.')
    _sidecar_path(out).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return out


def _convert_rgb_standalone(ds, tiff_path, rs2_path, progress, manual_bounds):
    """Converte TIFF RGB sem RS2 auxiliar, criando NOVOS códigos por cor.

    Não é possível recuperar nomes/códigos legados de RGB isolado. Não
    inferimos SRC nem inventamos coordenadas; exigimos dados do TIFF ou usuário.
    """
    gdal, _osr = _gdal()
    if any(ds.GetRasterBand(i).DataType != gdal.GDT_Byte
           for i in range(1, ds.RasterCount + 1)):
        raise RS2Error('RGB independente exige bandas de 8 bits por canal.')
    coords = _validated_grid(ds, manual_bounds)
    labels, colors = discover_rgb_palette(ds)
    h = RS2Header(ds.RasterXSize, ds.RasterYSize, *coords, labels, colors)
    mapper = RS2RGBMapper(colors)

    def source_rows():
        for y in range(h.height):
            pixels = ds.ReadAsArray(0, y, h.width, 1)
            if pixels is None or pixels.shape != (ds.RasterCount, 1, h.width):
                raise RS2Error(f'Falha de leitura RGB na linha {y+1}.')
            alpha = pixels[3, 0, :] if ds.RasterCount == 4 else None
            yield mapper.map_row(pixels[0, 0, :], pixels[1, 0, :],
                                 pixels[2, 0, :], alpha, y)

    out = Path(rs2_path)
    write_rs2(out, h, source_rows(), progress=progress)
    manifest = _metadata(h)
    manifest['source_wkt'] = ds.GetProjectionRef() or ''
    manifest['rgb_auto_palette'] = True
    manifest['category_warning'] = (
        'Códigos atribuídos pela ordenação de cores RGB, e não recuperados '
        'do arquivo RS2 original. Rótulos genéricos. Revisar categoria 0 '
        'antes de utilizar o resultado em análises ambientais.')
    _sidecar_path(out).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return out


def convert_tif_to_rs2(tiff_path, rs2_path, progress=None, reference_rs2=None,
                       manual_bounds=None):
    """Gravação experimental de TIFF categórico ou RGB; referência é opcional."""
    if Path(tiff_path).suffix.lower() not in ('.tif', '.tiff'):
        raise RS2Error(
            'Entrada incompatível com TIFF → RS2. Você selecionou um arquivo '
            '"' + Path(tiff_path).suffix + '"; escolha RS2 → GeoTIFF para ler RS2.')
    gdal, _osr = _gdal()
    ds = gdal.Open(str(tiff_path), gdal.GA_ReadOnly)
    if ds is None:
        raise RS2Error('Não foi possível abrir o GeoTIFF.')
    try:
        if ds.RasterCount in (3, 4):
            return _convert_rgb_to_rs2(ds, tiff_path, rs2_path, reference_rs2,
                                       progress, manual_bounds)
        if ds.RasterCount != 1:
            raise RS2Error('O GeoTIFF deve conter 1 banda categórica ou 3/4 bandas RGB.')
        band = ds.GetRasterBand(1)
        if band.DataType not in (gdal.GDT_Byte, gdal.GDT_UInt16, gdal.GDT_Int16,
                                 gdal.GDT_UInt32, gdal.GDT_Int32):
            raise RS2Error('GeoTIFF deve conter valores categóricos inteiros.')
        sidecar = _read_sidecar(tiff_path)
        if sidecar is not None and manual_bounds is None:
            fallback = tuple(sidecar[k] for k in ('xmin', 'ymin', 'xmax', 'ymax'))
        else:
            fallback = manual_bounds
        coords = _validated_grid(ds, fallback)
        if sidecar:
            if (ds.RasterXSize != sidecar.get('width') or
                    ds.RasterYSize != sidecar.get('height') or
                    list(coords) != [sidecar[k] for k in ('xmin', 'ymin', 'xmax', 'ymax')]):
                raise RS2Error('A grade do GeoTIFF não coincide com os metadados RS2.')
            labels = sidecar.get('labels', [])
            colors = [tuple(color) + (0,) for color in sidecar.get('colors', [])]
            try:
                prefix = bytes.fromhex(sidecar.get('source_header_hex', ''))
            except ValueError as exc:
                raise RS2Error('Prefixo no JSON RS2 inválido.') from exc
            raw_palette = None
            if sidecar.get('legacy_palette_zlib_b64'):
                try:
                    compressed = base64.b64decode(sidecar['legacy_palette_zlib_b64'],
                                                  validate=True)
                    if len(compressed) > 1000000:
                        raise ValueError('Paleta comprimida excessivamente grande.')
                    dec = zlib.decompressobj()
                    raw_palette = dec.decompress(compressed, 131077)
                    if not dec.eof or dec.unconsumed_tail or len(raw_palette) != 131076:
                        raise ValueError('Comprimento inválido da paleta RS2.')
                except (ValueError, zlib.error) as exc:
                    raise RS2Error('Paleta original no JSON RS2 inválida.') from exc
        else:
            # Primeira leitura encontra o maior código sem carregar a matriz inteira.
            max_category = 0
            for y in range(0, ds.RasterYSize, 128):
                arr = band.ReadAsArray(0, y, ds.RasterXSize,
                                       min(128, ds.RasterYSize-y))
                if arr is None or np.any(arr < 0):
                    raise RS2Error('Há células negativas ou não legíveis no TIFF.')
                max_category = max(max_category, int(np.max(arr)))
                if max_category > 32768:
                    raise RS2Error('Máximo de 32769 categorias suportadas nesta variante RS2.')
            labels, colors = _category_legend_from_raster(band, max_category)
            from .rs2_format import DEFAULT_PREFIX
            prefix = DEFAULT_PREFIX
            raw_palette = None
        if not labels or len(labels) != len(colors):
            raise RS2Error('Legenda / paleta ausente ou inconsistente.')
        h = RS2Header(ds.RasterXSize, ds.RasterYSize, *coords,
                      labels, colors, prefix, raw_palette=raw_palette)
        # Ordem do construtor: width, height, xmin, ymin, xmax, ymax
        def source_rows():
            for y in range(h.height):
                pixels = band.ReadAsArray(0, y, h.width, 1)
                if pixels is None:
                    raise RS2Error(f'Falha de leitura do GeoTIFF na linha {y+1}.')
                yield pixels.reshape(-1)
        out = Path(rs2_path)
        write_rs2(out, h, source_rows(), progress=progress)
        # SRC somente em sidecar; formato legado não contém EPSG inequívoco.
        crs_wkt = ds.GetProjectionRef() or ''
        manifest = _metadata(h)
        manifest['source_wkt'] = crs_wkt
        _sidecar_path(out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                      encoding='utf-8')
        return out
    finally:
        ds = None
