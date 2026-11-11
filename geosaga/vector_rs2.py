"""Vetor → RS2: rasterização direta de uma camada vetorial no formato Vista SAGA.

Sexta operação do conversor. Não altera as cinco operações anteriores.

O RS2 é uma matriz categórica (RLE), não um formato vetorial. Portanto esta
conversão é, necessariamente, uma *rasterização*, com as restrições do formato
legado deduzido em ``rs2_format.py``:

- coordenadas de borda inteiras e não negativas (uint32): o SRC da camada deve
  ser projetado; SRC geográfico (graus) é recusado, sem reprojeção implícita;
- no máximo 65.535 linhas/colunas e 32.769 categorias (0 = FUNDO);
- códigos consecutivos 0..n, com nome CP1252 e cor por categoria;
- apenas atributos inteiros ou textuais (valores decimais não são categorias).

A grade pode ser copiada de um **RS2 de referência** (mesma origem, resolução e
dimensões, para análise célula a célula com outros mapas da mesma área) ou,
sem referência, alinhada a múltiplos inteiros do tamanho do pixel.

O SRC é registrado somente no arquivo lateral ``.rs2.json``, nunca no RS2.
"""

from dataclasses import dataclass, field
import colorsys
import json
import math
from pathlib import Path
import tempfile

import numpy as np

from .gdal_scope import with_gdal_exceptions
from .rs2_format import DEFAULT_PREFIX, RS2Error, RS2Header, RS2Reader, write_rs2
from .vector_raster import (MAX_PIXELS, _check_field, _open_ogr_layer,
                            normalize_color, split_vector_source)

RS2_MAX_CODE = 32768          # 32.769 categorias, incluindo 0 = FUNDO
RS2_MAX_SIDE = 65535          # linhas e colunas são uint16 no cabeçalho
CODE_MODES = ('auto', 'preserve', 'renumber')
BACKGROUND_LABEL = 'FUNDO'
BACKGROUND_COLOR = (255, 255, 255, 0)


@dataclass(frozen=True)
class RS2Grid:
    """Grade norte-acima com bordas inteiras, como gravada no cabeçalho RS2."""
    width: int
    height: int
    xmin: int
    ymin: int
    xmax: int
    ymax: int

    @property
    def pixel_x(self):
        return (self.xmax - self.xmin) / self.width

    @property
    def pixel_y(self):
        return (self.ymax - self.ymin) / self.height

    @property
    def geotransform(self):
        return (float(self.xmin), self.pixel_x, 0., float(self.ymax), 0., -self.pixel_y)


@dataclass
class VectorRS2Result:
    """Caminho do RS2 gravado e resumo do processamento (também no .rs2.json)."""
    path: Path
    summary: dict = field(default_factory=dict)

    def __str__(self):
        return str(self.path)

    def __fspath__(self):
        return str(self.path)


def _check_grid_limits(width, height, xmin, ymin, xmax, ymax):
    if not (0 < width <= RS2_MAX_SIDE and 0 < height <= RS2_MAX_SIDE):
        raise RS2Error(f'A grade teria {width} × {height} células; o RS2 admite no máximo '
                       f'{RS2_MAX_SIDE} linhas e colunas. Aumente o tamanho do pixel.')
    if width * height > MAX_PIXELS:
        raise RS2Error('A grade teria mais de 100 milhões de células. '
                       'Aumente o tamanho do pixel ou reduza a área de entrada.')
    if not (0 <= xmin < xmax < 2**32 and 0 <= ymin < ymax < 2**32):
        raise RS2Error('O RS2 grava coordenadas inteiras e não negativas (32 bits). '
                       'A extensão do vetor está fora desse intervalo: use um SRC '
                       'projetado com coordenadas positivas (por exemplo, UTM).')


def plan_rs2_grid(extent, pixel_size):
    """Planeja a grade a partir da extensão OGR ``(xmin, xmax, ymin, ymax)``.

    As bordas são alinhadas a múltiplos inteiros de ``pixel_size`` (que deve ser
    inteiro), de modo que vetores diferentes rasterizados com a mesma resolução
    compartilhem a mesma malha e possam ser cruzados célula a célula.
    """
    try:
        x_min, x_max, y_min, y_max = map(float, extent)
        res = float(pixel_size)
    except (TypeError, ValueError) as exc:
        raise RS2Error('Resolução ou extensão vetorial inválida.') from exc
    if not all(math.isfinite(v) for v in (x_min, x_max, y_min, y_max, res)):
        raise RS2Error('Resolução e extensão devem conter números finitos.')
    if x_max < x_min or y_max < y_min:
        raise RS2Error('Extensão vetorial inválida.')
    step = round(res)
    if step < 1 or abs(res - step) > 1e-9:
        raise RS2Error('Sem RS2 de referência, o tamanho do pixel deve ser um número '
                       'inteiro positivo (por exemplo, 10), pois o RS2 só grava '
                       'coordenadas inteiras. Para outra grade, informe um RS2 de referência.')
    eps = 1e-9
    gx0 = math.floor(x_min / step + eps) * step
    gy0 = math.floor(y_min / step + eps) * step
    gx1 = math.ceil(x_max / step - eps) * step
    gy1 = math.ceil(y_max / step - eps) * step
    if gx1 <= gx0:   # ponto isolado ou linha vertical: ao menos uma coluna
        gx1 = gx0 + step
    if gy1 <= gy0:
        gy1 = gy0 + step
    width, height = (gx1 - gx0) // step, (gy1 - gy0) // step
    _check_grid_limits(width, height, gx0, gy0, gx1, gy1)
    return RS2Grid(int(width), int(height), int(gx0), int(gy0), int(gx1), int(gy1))


def grid_from_reference(header):
    """Copia exatamente a grade (origem, extensão e dimensões) de um RS2 existente."""
    _check_grid_limits(header.width, header.height, header.xmin, header.ymin,
                       header.xmax, header.ymax)
    return RS2Grid(header.width, header.height, header.xmin, header.ymin,
                   header.xmax, header.ymax)


def extent_intersects_grid(extent, grid):
    x_min, x_max, y_min, y_max = map(float, extent)
    return not (x_max < grid.xmin or x_min > grid.xmax or
                y_max < grid.ymin or y_min > grid.ymax)


def default_color(index):
    """Cor determinística e distinguível para categorias sem ``COR_HEX``."""
    hue = (index * 0.618033988749895) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.55, 0.92)
    return (round(r * 255), round(g * 255), round(b * 255), 0)


def _hex_to_rgba(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5)) + (0,)


def _cp1252_label(label, code):
    text = str(label).strip().replace('\0', '')
    try:
        text.encode('cp1252')
    except UnicodeEncodeError as exc:
        raise RS2Error(f'O nome da classe {code} ({text!r}) contém caracteres que o RS2 '
                       '(codificação CP1252) não representa. Corrija o atributo.') from exc
    return text


def plan_codes(field_mode, values, code_mode='auto'):
    """Define o código RS2 de cada valor do atributo e a legenda correspondente.

    ``values`` associa cada valor original (int ou texto) a ``(rótulo, cor_hex)``;
    rótulo ou cor podem ser vazios. Retorna ``(mapeamento, códigos, rótulos,
    cores, modo)``: a legenda contém apenas o FUNDO (0) e os códigos usados,
    em ordem crescente, como o próprio Vista SAGA grava (códigos não precisam ser
    consecutivos). ``modo`` é o efetivamente aplicado: ``'preserve'``,
    ``'renumber'`` ou ``'text'``.
    """
    if code_mode not in CODE_MODES:
        raise RS2Error(f'Modo de códigos desconhecido: {code_mode!r}.')
    if not values:
        raise RS2Error('Nenhuma feição possui geometria e atributo válidos.')
    if field_mode == 'text':
        # Ordem alfabética: o mesmo vetor gera sempre os mesmos códigos,
        # independentemente da ordem das feições no arquivo.
        keys = sorted(values, key=lambda v: (v.casefold(), v))
        effective = 'text'
    elif field_mode == 'int':
        keys = sorted(values)
        if keys[0] < 0:
            raise RS2Error('O RS2 não admite códigos negativos. Corrija o atributo ou '
                           'use um campo textual.')
        preservable = keys[0] >= 1 and keys[-1] <= RS2_MAX_CODE
        if code_mode == 'preserve':
            if keys[0] == 0:
                raise RS2Error('Há feições com código 0, reservado ao FUNDO no RS2. '
                               'Escolha a renumeração dos códigos ou altere o atributo.')
            if not preservable:
                raise RS2Error(f'O maior código ({keys[-1]}) excede o limite RS2 de '
                               f'{RS2_MAX_CODE}. Escolha a renumeração dos códigos.')
            effective = 'preserve'
        elif code_mode == 'renumber':
            effective = 'renumber'
        else:
            # Códigos esparsos (por exemplo, 125 e 158) são preservados sem classes
            # vazias; só se renumera o que o RS2 não comporta (0 ou acima de 32768).
            effective = 'preserve' if preservable else 'renumber'
    else:
        raise RS2Error('O RS2 armazena apenas categorias: use um campo inteiro ou '
                       'textual. Campos decimais devem ser classificados antes.')
    if effective != 'preserve' and len(keys) > RS2_MAX_CODE:
        raise RS2Error(f'Há {len(keys)} categorias distintas; o RS2 admite no máximo '
                       f'{RS2_MAX_CODE} além do FUNDO. Simplifique o atributo.')

    if effective == 'preserve':
        mapping = {k: k for k in keys}
    else:
        mapping = {k: i for i, k in enumerate(keys, start=1)}
    codes, labels, colors = [0], [BACKGROUND_LABEL], [BACKGROUND_COLOR]
    for original, code in sorted(mapping.items(), key=lambda item: item[1]):
        label, color = values[original]
        if field_mode == 'text':
            name = original
        elif label and str(label).strip():
            name = label
        else:
            name = f'Classe {original}'
        hex_color = normalize_color(color)
        codes.append(code)
        labels.append(_cp1252_label(name, code))
        colors.append(_hex_to_rgba(hex_color) if hex_color else default_color(code))
    return mapping, codes, labels, colors, effective


def _scaled(progress, start, end):
    """Converte o progresso de uma etapa para a escala total 0..1000."""
    def callback(done, total):
        if progress is None:
            return True
        value = start + (end - start) * (done / max(total, 1))
        return progress(round(value), 1000) is not False
    return callback


def _sidecar_path(path):
    return Path(str(path) + '.rs2.json')


@with_gdal_exceptions
def convert_vector_to_rs2(vector_source, rs2_path, field_name, pixel_size=None,
                          progress=None, all_touched=False, reference_rs2=None,
                          code_mode='auto'):
    """Rasteriza uma camada vetorial por atributo e grava o resultado em RS2.

    ``progress(done, total)`` interrompe a operação quando retornar False.
    Não reprojeta: a camada precisa estar num SRC projetado. Com
    ``reference_rs2``, a grade do RS2 indicado é copiada e ``pixel_size`` é
    ignorado; a correspondência de SRC entre ambos não pode ser verificada pelo
    RS2 e é responsabilidade do usuário.
    """
    output = Path(rs2_path)
    if output.suffix.lower() != '.rs2':
        raise RS2Error('A saída deve ser um arquivo .rs2.')
    source_path, _, _ = split_vector_source(vector_source)
    if output.resolve() == source_path.resolve():
        raise RS2Error('O RS2 de saída não pode substituir o vetor de entrada.')
    reference_header = None
    if reference_rs2:
        reference = Path(reference_rs2)
        if not reference.is_file():
            raise RS2Error('RS2 de referência não encontrado: ' + str(reference))
        if reference.resolve() == output.resolve():
            raise RS2Error('A saída não pode substituir o RS2 de referência.')
        reference_header = RS2Reader(reference).header
    if code_mode not in CODE_MODES:
        raise RS2Error(f'Modo de códigos desconhecido: {code_mode!r}.')

    from osgeo import gdal, ogr
    src_ds, src_layer = _open_ogr_layer(ogr, vector_source)
    field_index, mode = _check_field(src_layer, field_name, ogr)
    if mode == 'real':
        raise RS2Error('O RS2 armazena apenas categorias: use um campo inteiro ou '
                       'textual. Campos decimais devem ser classificados antes.')
    spatial_ref = src_layer.GetSpatialRef()
    if spatial_ref is None:
        raise RS2Error('A camada não possui SRC. Defina-o no QGIS antes de converter.')
    if spatial_ref.IsGeographic():
        raise RS2Error('A camada está em SRC geográfico (graus). O RS2 grava coordenadas '
                       'inteiras projetadas: reprojete a camada no QGIS para um SRC '
                       'projetado (por exemplo, SIRGAS 2000 / UTM) antes de converter.')
    total_features = src_layer.GetFeatureCount()
    if total_features == 0:
        raise RS2Error('A camada vetorial não contém feições.')
    extent = src_layer.GetExtent()
    grid = (grid_from_reference(reference_header) if reference_header is not None
            else plan_rs2_grid(extent, pixel_size))
    if not extent_intersects_grid(extent, grid):
        raise RS2Error('A camada não intersecta a grade do RS2 de referência. Verifique '
                       'se o vetor e o RS2 de referência estão no mesmo SRC.')

    defn = src_layer.GetLayerDefn()
    label_field = defn.GetFieldIndex('CLASSE')
    color_field = defn.GetFieldIndex('COR_HEX')

    def key_of(feature):
        geometry = feature.GetGeometryRef()
        if geometry is None or geometry.IsEmpty() or not feature.IsFieldSetAndNotNull(field_index):
            return None
        raw = feature.GetField(field_index)
        if mode == 'text':
            text = str(raw).strip()
            return text or None
        return int(raw)

    # Etapa 1 (0–20 %): inventário das categorias, sem copiar geometrias.
    step1 = _scaled(progress, 0, 200)
    values = {}
    src_layer.ResetReading()
    for i, feature in enumerate(src_layer):
        if i % 200 == 0 and step1(i, total_features) is False:
            raise RS2Error('Operação cancelada pelo usuário.')
        key = key_of(feature)
        if key is None or key in values:
            continue
        label = (feature.GetField(label_field) if mode == 'int' and label_field >= 0 and
                 feature.IsFieldSetAndNotNull(label_field) else '')
        color = (feature.GetField(color_field) if color_field >= 0 and
                 feature.IsFieldSetAndNotNull(color_field) else '')
        values[key] = (label or '', color or '')
    mapping, codes, labels, colors, effective = plan_codes(mode, values, code_mode)

    output.parent.mkdir(parents=True, exist_ok=True)
    # ignore_cleanup_errors: no Windows, o GDAL pode reter temporários após uma falha.
    with tempfile.TemporaryDirectory(prefix='.vista_vector_rs2_', dir=output.parent,
                                     ignore_cleanup_errors=True) as tmp:
        work = Path(tmp) / 'classes.gpkg'
        stage = Path(tmp) / 'codigos.tif'
        coverage = Path(tmp) / 'cobertura.tif'
        vdriver = ogr.GetDriverByName('GPKG')
        if vdriver is None:
            raise RS2Error('Driver GeoPackage do GDAL não disponível.')
        intermediary = vdriver.CreateDataSource(str(work))
        if intermediary is None:
            raise RS2Error('Não foi possível criar a camada temporária.')
        writer = intermediary.CreateLayer('pixels', srs=spatial_ref, geom_type=ogr.wkbUnknown)
        if writer is None or writer.CreateField(ogr.FieldDefn('VS_CODE', ogr.OFTInteger)) != 0:
            raise RS2Error('Falha ao criar a camada temporária de rasterização.')

        # Etapa 2 (20–40 %): cópia das geometrias com o código RS2 já definido.
        step2 = _scaled(progress, 200, 400)
        valid = 0
        src_layer.ResetReading()
        writer.StartTransaction()
        for i, feature in enumerate(src_layer):
            if i % 200 == 0 and step2(i, total_features) is False:
                raise RS2Error('Operação cancelada pelo usuário.')
            key = key_of(feature)
            if key is None:
                continue
            out = ogr.Feature(writer.GetLayerDefn())
            out.SetField('VS_CODE', int(mapping[key]))
            out.SetGeometry(feature.GetGeometryRef())
            if writer.CreateFeature(out) != 0:
                raise RS2Error('Falha ao transferir feição para a rasterização.')
            out = None
            valid += 1
        writer.CommitTransaction()
        writer.SyncToDisk()
        skipped = total_features - valid

        # Etapa 3 (40–70 %): rasterização dos códigos e da contagem de cobertura.
        driver = gdal.GetDriverByName('GTiff')
        tiff_options = ['TILED=YES', 'COMPRESS=DEFLATE', 'BIGTIFF=IF_SAFER']
        codes_ds = driver.Create(str(stage), grid.width, grid.height, 1,
                                 gdal.GDT_UInt16, options=tiff_options)
        cover_ds = driver.Create(str(coverage), grid.width, grid.height, 1,
                                 gdal.GDT_UInt16, options=tiff_options)
        if codes_ds is None or cover_ds is None:
            raise RS2Error('Não foi possível criar a grade temporária.')
        wkt = spatial_ref.ExportToWkt()
        for raster in (codes_ds, cover_ds):
            raster.SetGeoTransform(grid.geotransform)
            raster.SetProjection(wkt)
            raster.GetRasterBand(1).Fill(0)
        touched = ['ALL_TOUCHED=TRUE'] if all_touched else []
        cancelled = [False]

        def gdal_progress(start, end):
            scaled = _scaled(progress, start, end)

            def callback(fraction, message, data):
                if scaled(fraction, 1) is False:
                    cancelled[0] = True
                    return 0
                return 1
            return callback

        try:
            status = gdal.RasterizeLayer(codes_ds, [1], writer,
                                         options=['ATTRIBUTE=VS_CODE'] + touched,
                                         callback=gdal_progress(400, 600))
            if status == 0:
                status = gdal.RasterizeLayer(cover_ds, [1], writer, burn_values=[1],
                                             options=['MERGE_ALG=ADD'] + touched,
                                             callback=gdal_progress(600, 700))
        except RuntimeError as exc:
            # Com exceções GDAL ativas (with_gdal_exceptions), o cancelamento chega como exceção.
            if cancelled[0]:
                raise RS2Error('Operação cancelada pelo usuário.') from exc
            raise RS2Error(f'Falha na rasterização GDAL: {exc}') from exc
        if status != 0:
            raise RS2Error('Rasterização cancelada.' if cancelled[0] else
                           'Falha na rasterização GDAL.')
        codes_ds.FlushCache()
        cover_ds.FlushCache()
        writer = intermediary = None
        del src_layer, src_ds  # libera o arquivo vetorial (Windows)

        overlap_cells = 0
        cover_band = cover_ds.GetRasterBand(1)
        for y in range(0, grid.height, 256):
            block = cover_band.ReadAsArray(0, y, grid.width, min(256, grid.height - y))
            overlap_cells += int(np.count_nonzero(block > 1))
        cover_band = cover_ds = None

        # Etapa 4 (70–100 %): contagem por classe; a legenda gravada contém apenas
        # o FUNDO e as classes com células, como nos arquivos regravados pelo Vista SAGA.
        band = codes_ds.GetRasterBand(1)
        tally = np.zeros(RS2_MAX_CODE + 1, dtype=np.int64)
        for y in range(0, grid.height, 256):
            block = band.ReadAsArray(0, y, grid.width, min(256, grid.height - y))
            tally += np.bincount(block.ravel(), minlength=tally.size)[:tally.size]
        empty = [label for code, label in zip(codes[1:], labels[1:]) if tally[code] == 0]
        legend = [(c, n, k) for c, n, k in zip(codes, labels, colors) if c == 0 or tally[c]]
        if len(legend) == 1:
            raise RS2Error('Nenhuma feição ocupou células da grade. Reduza o tamanho do pixel, '
                           'use ALL_TOUCHED ou confira o RS2 de referência.')
        final_codes = [c for c, _, _ in legend]
        header = RS2Header(grid.width, grid.height, grid.xmin, grid.ymin,
                           grid.xmax, grid.ymax, [n for _, n, _ in legend],
                           [k for _, _, k in legend], DEFAULT_PREFIX,
                           codes=None if final_codes == list(range(len(legend))) else final_codes)

        def rows():
            for y in range(grid.height):
                line = band.ReadAsArray(0, y, grid.width, 1)
                if line is None:
                    raise RS2Error(f'Falha de leitura da grade temporária na linha {y + 1}.')
                yield line.reshape(-1)

        write_rs2(output, header, rows(), progress=_scaled(progress, 700, 1000))
        band = codes_ds = None

    summary = {
        'cells': grid.width * grid.height,
        'background_cells': int(tally[0]),
        'overlap_cells': overlap_cells,
        'features': total_features,
        'skipped_features': skipped,
        'classes': len(legend) - 1,
        # Classes do vetor sem nenhuma célula: não entram na legenda do RS2.
        'empty_classes': empty,
        'code_mode': effective,
    }
    manifest = {
        'format': 'Vista SAGA RS2',
        'origin': 'Vetor rasterizado pelo Vista Saga Plugin',
        'version': 1,
        'epsg': None,
        'source_wkt': wkt,
        'reference_system_note': 'O SRC está registrado apenas neste arquivo; '
                                 'o RS2 não o armazena de forma inequívoca.',
        'source_header_hex': DEFAULT_PREFIX.hex(),
        'legacy_palette_zlib_b64': None,
        'width': grid.width,
        'height': grid.height,
        'xmin': grid.xmin,
        'ymin': grid.ymin,
        'xmax': grid.xmax,
        'ymax': grid.ymax,
        'labels': list(header.labels),
        'colors': [list(c[:3]) for c in header.colors],
        'codes': header.legend_codes,
        'background_code': 0,
        'rasterization': {
            'source_vector': str(vector_source),
            'field': str(field_name),
            'field_type': mode,
            'grid': 'reference' if reference_header is not None else 'aligned',
            'reference_rs2': str(reference_rs2) if reference_header is not None else None,
            'pixel_size': [grid.pixel_x, grid.pixel_y],
            'all_touched': bool(all_touched),
            'code_mode': effective,
            'code_mapping': [{'codigo_rs2': int(code), 'valor_original': original,
                              'classe': name, 'celulas': int(tally[code])}
                             for (original, code), name in zip(
                                 sorted(mapping.items(), key=lambda item: item[1]), labels[1:])],
            'overlap_cells': overlap_cells,
            'overlap_rule': 'Em sobreposição, prevalece a última feição processada.',
            'skipped_features': skipped,
        },
    }
    _sidecar_path(output).write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                     encoding='utf-8')
    return VectorRS2Result(output, summary)
