"""Assinatura na guia Raster (1.5.0): GDAL e RS2, sem PyQGIS.

O primeiro mapa da lista é a referência; as classes marcadas nela formam o limite, e todos os mapas da
lista (inclusive a referência) são assinados dentro dele. Regras de entrada (decisões do autor,
20/11/2026): só raster; mesmo SRC, projetado em metros (o plugin não reprojeta); mesma grade
(dimensões, resolução, extensão e alinhamento). Feição = classe inteira da referência.
"""
import json
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .core import valid_mask
from .gdal_scope import with_gdal_exceptions
from .signature_model import (
    NODATA_KEY, FeatureSignature, SignatureResult, is_special, label_for, raster_map_signature,
)

TILE_ROWS = 256
MAX_CLASSES = 10000
_SENTINEL = np.int64(-(2 ** 62))  # NoData dentro dos blocos de códigos


@dataclass
class RasterMap:
    path: str
    name: str
    kind: str  # 'rs2' | 'gdal'
    width: int
    height: int
    geotransform: tuple
    srs_wkt: str
    legend: dict = field(default_factory=dict)  # código -> nome, na ordem da legenda
    nodata: object = None


def _srs_from_text(text):
    from osgeo import osr
    srs = osr.SpatialReference()
    try:
        srs.SetFromUserInput(str(text))
    except RuntimeError as exc:
        raise ValueError(f'SRC não reconhecido: {text}') from exc
    return srs


def _gdal_legend(path, band):
    names = band.GetCategoryNames() or []
    legend = {i: str(name) for i, name in enumerate(names) if name}
    sidecar = Path(str(path) + '.rs2.json')
    if sidecar.is_file():
        try:
            info = json.loads(sidecar.read_text(encoding='utf-8'))
            if isinstance(info, dict) and info.get('format') == 'Vista SAGA RS2':
                from .rs2_format import sidecar_codes
                legend = {int(code): str(label) for code, label in
                          zip(sidecar_codes(info), info.get('labels') or [])}
        except (OSError, ValueError, TypeError):
            pass
    return legend


@with_gdal_exceptions
def open_raster_map(path, *, crs=''):
    """Abre um mapa categórico de uma banda (formatos do GDAL ou RS2).

    ``crs`` (EPSG ou WKT) é usado quando o arquivo não registra SRC: o RS2 nunca registra, e o SRC
    vem do ``.rs2.json`` ou da confirmação do usuário na janela. Nunca é deduzido das coordenadas.
    """
    path = str(path)
    name = os.path.basename(path)
    if not os.path.isfile(path):
        raise ValueError(f'Arquivo não encontrado: {path}')
    if path.lower().endswith('.rs2'):
        from .rs2_converter import sidecar_epsg
        from .rs2_format import RS2Reader
        header = RS2Reader(path).header
        text = crs or sidecar_epsg(path)
        if not text:
            raise ValueError(f'O RS2 {name} não registra SRC: informe o SRC do mapa.')
        geotransform = (float(header.xmin), header.pixel_x, 0.0, float(header.ymax), 0.0, -header.pixel_y)
        legend = {code: label for code, label, _color in header.legend()}
        return RasterMap(path, name, 'rs2', header.width, header.height, geotransform,
                         _srs_from_text(text).ExportToWkt(), legend)
    from osgeo import gdal
    try:
        ds = gdal.Open(path, gdal.GA_ReadOnly)
    except RuntimeError as exc:
        raise ValueError(f'Não foi possível abrir o raster: {path}') from exc
    if ds.RasterCount != 1:
        raise ValueError(f'O mapa {name} deve ter uma única banda de classes.')
    band = ds.GetRasterBand(1)
    if band.DataType in (gdal.GDT_CFloat32, gdal.GDT_CFloat64, gdal.GDT_CInt16, gdal.GDT_CInt32):
        raise ValueError('Rasters complexos não são suportados.')
    wkt = ds.GetProjection() or (_srs_from_text(crs).ExportToWkt() if crs else '')
    if not wkt:
        raise ValueError(f'O mapa {name} não tem SRC definido.')
    legend = _gdal_legend(path, band)
    nodata = band.GetNoDataValue()
    if nodata is not None and np.isfinite(nodata) and float(nodata).is_integer() and int(nodata) in legend:
        # NoData com nome na legenda (ex.: FUNDO de um RS2 convertido): conta como essa classe.
        nodata = None
    return RasterMap(path, name, 'gdal', ds.RasterXSize, ds.RasterYSize, tuple(ds.GetGeoTransform()),
                     wkt, legend, nodata)


@with_gdal_exceptions
def check_raster_maps(maps):
    """Mesmo SRC projetado em metros e mesma grade em todos os mapas. Devolve o nome do SRC."""
    from osgeo import osr
    if not maps:
        raise ValueError('Adicione pelo menos um mapa à lista.')
    ref = maps[0]
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ref.srs_wkt)
    if not srs.IsProjected():
        raise ValueError('O SRC dos mapas deve ser projetado, em metros; SRC geográfico (graus) não é aceito.')
    if abs(srs.GetLinearUnits() - 1.0) > 1e-9:
        raise ValueError('O SRC dos mapas deve ter unidade em metros.')
    gt = ref.geotransform
    if gt[2] or gt[4]:
        raise ValueError(f'O mapa {ref.name} tem grade rotacionada, que não é suportada.')
    tolerance = 1e-6 * max(abs(gt[1]), abs(gt[5]))
    for other in maps[1:]:
        o_srs = osr.SpatialReference()
        o_srs.ImportFromWkt(other.srs_wkt)
        if not srs.IsSame(o_srs):
            raise ValueError(f'O mapa {other.name} está em outro SRC. Todos os mapas devem estar no mesmo '
                             'SRC; o plugin não reprojeta.')
        if (other.width, other.height) != (ref.width, ref.height) or not np.allclose(
                gt, other.geotransform, rtol=0, atol=tolerance):
            raise ValueError(f'O mapa {other.name} não está na mesma grade da referência (resolução, '
                             'extensão ou alinhamento). Alinhe os mapas antes da assinatura.')
    return srs.GetName()


def _codes(block, nodata, name):
    """Converte um bloco em códigos inteiros; NoData vira o marcador interno."""
    valid = valid_mask(block, nodata) if block.dtype.kind == 'f' or nodata is not None else None
    if block.dtype.kind == 'f':
        finite = block[valid]
        if finite.size and not np.all(np.equal(np.floor(finite), finite)):
            raise ValueError(f'O mapa {name} tem valores fracionários; a assinatura requer classes inteiras.')
    codes = block.astype(np.int64, copy=False) if valid is None else np.where(
        valid, np.nan_to_num(block, nan=0).astype(np.int64), _SENTINEL)
    return codes


def _blocks(m):
    """Blocos de linhas (int64) na ordem da grade, do topo para baixo."""
    if m.kind == 'rs2':
        from .rs2_format import RS2Reader
        rows = []
        for row in RS2Reader(m.path).rows():
            rows.append(row.astype(np.int64))
            if len(rows) == TILE_ROWS:
                yield np.vstack(rows)
                rows = []
        if rows:
            yield np.vstack(rows)
        return
    from osgeo import gdal
    ds = gdal.Open(m.path, gdal.GA_ReadOnly)
    band = ds.GetRasterBand(1)
    for y in range(0, m.height, TILE_ROWS):
        h = min(TILE_ROWS, m.height - y)
        yield _codes(band.ReadAsArray(0, y, m.width, h), m.nodata, m.name)


def _key(code):
    return NODATA_KEY if code == _SENTINEL else int(code)


def _add(counter, values, counts):
    for value, count in zip(values.tolist(), counts.tolist()):
        counter[_key(value)] += count
    if len(counter) > MAX_CLASSES:
        raise ValueError('O mapa tem classes demais para uma assinatura; confira se é um mapa categórico.')


def _selected_mask(ref_block, selected):
    keys = [k for k in selected if k != NODATA_KEY]
    mask = np.isin(ref_block, np.asarray(keys, dtype=np.int64)) if keys else np.zeros(ref_block.shape, bool)
    if NODATA_KEY in selected:
        mask |= ref_block == _SENTINEL
    return mask


@with_gdal_exceptions
def scan_reference_classes(m):
    """Classes da referência para a lista da janela: (chave, nome, células), legenda primeiro."""
    totals = Counter()
    for block in _blocks(m):
        values, counts = np.unique(block, return_counts=True)
        _add(totals, values, counts)
    keys = list(m.legend) + sorted(k for k in totals if not isinstance(k, str) and k not in m.legend)
    if NODATA_KEY in totals:
        keys.append(NODATA_KEY)
    return [(k, label_for(k, m.legend), int(totals.get(k, 0))) for k in keys]


@with_gdal_exceptions
def run_raster_signature(maps, selected, *, per_feature=True, progress=None, cancelled=None):
    """Assina todos os ``maps`` dentro das classes ``selected`` do primeiro (a referência).

    ``selected``: códigos inteiros e/ou ``NODATA_KEY``. Devolve um :class:`SignatureResult` com a
    união da seleção e, se ``per_feature``, um recorte por classe marcada.
    """
    srs_name = check_raster_maps(maps)
    selected = list(dict.fromkeys(selected))
    if not selected:
        raise ValueError('Selecione pelo menos uma classe do mapa de referência.')
    ref = maps[0]
    cell_ha = abs(ref.geotransform[1] * ref.geotransform[5]) / 10000.0
    totals = [Counter() for _ in maps]
    inside = [Counter() for _ in maps]
    by_class = [{k: Counter() for k in selected} for _ in maps] if per_feature else None
    done = 0
    for blocks in zip(*(_blocks(m) for m in maps)):
        if cancelled and cancelled():
            raise InterruptedError('Assinatura cancelada.')
        mask = _selected_mask(blocks[0], selected)
        ref_inside = blocks[0][mask]
        for i, block in enumerate(blocks):
            values, counts = np.unique(block, return_counts=True)
            _add(totals[i], values, counts)
            sub = block[mask]
            values, counts = np.unique(sub, return_counts=True)
            _add(inside[i], values, counts)
            if per_feature and sub.size:
                pairs, counts = np.unique(np.stack([ref_inside, sub], axis=1), axis=0, return_counts=True)
                for (ref_code, code), count in zip(pairs.tolist(), counts.tolist()):
                    by_class[i][_key(ref_code)][_key(code)] += count
        done += blocks[0].shape[0]
        if progress:
            progress(done / ref.height)
    if not sum(inside[0].values()):
        raise ValueError('As classes selecionadas não têm nenhuma célula no mapa de referência.')
    union = FeatureSignature('UNIAO', 'União da seleção', [
        raster_map_signature(m.name, m.legend, totals[i], inside[i], cell_ha) for i, m in enumerate(maps)])
    warnings = []
    features = []
    if per_feature:
        for key in selected:
            name = label_for(key, ref.legend)
            if not sum(by_class[0][key].values()):
                warnings.append(f'A classe {name} não tem células no mapa de referência.')
            features.append(FeatureSignature(key, name, [
                raster_map_signature(m.name, m.legend, totals[i], by_class[i][key], cell_ha)
                for i, m in enumerate(maps)]))
    selection = [label_for(k, ref.legend) if is_special(k) else f'{k} - {label_for(k, ref.legend)}'
                 for k in selected]
    return SignatureResult('raster', ref.name, selection, union, features, srs_name, cell_ha, warnings)
