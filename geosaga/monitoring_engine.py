"""Monitoria raster GDAL em segundo plano; sem acesso a objetos GUI/QGIS."""
from collections import Counter
import os
from pathlib import Path
import shutil
import tempfile
import json
import csv

import numpy as np

from .core import NODATA_OUT, pixel_area_ha, transition_counts, valid_mask
from .monitoring_core import (transitions_summary, write_monitoring_reports,
                              write_mk_csv, append_mk_txt)
from .monitoring_trends import MIN_DATES, temporal_rows

TILE = 512
MAX_TRANSITIONS = 10000
MAX_MATRIX_CLASSES = 512


def _windows(width, height):
    for y in range(0, height, TILE):
        h = min(TILE, height - y)
        for x in range(0, width, TILE):
            yield x, y, min(TILE, width - x), h


def _same_grid(a, b, osr):
    if (a.RasterXSize, a.RasterYSize) != (b.RasterXSize, b.RasterYSize):
        raise ValueError('As dimensões dos mapas são diferentes. Utilize Alinhar rasters do QGIS.')
    # Diferenças de representação decimal muito menores que um pixel não
    # justificam reprojeção. Nunca aceita deslocamento >= 0,000005 pixel.
    gt_a, gt_b = a.GetGeoTransform(), b.GetGeoTransform()
    pixel_sizes = [abs(gt_a[1]), abs(gt_a[5]), abs(gt_b[1]), abs(gt_b[5])]
    if not all(np.isfinite(gt_a)) or not all(np.isfinite(gt_b)) or min(pixel_sizes) <= 0:
        raise ValueError('Transformações espaciais inválidas.')
    epsilon = min(pixel_sizes) * 5e-6
    if not np.allclose(gt_a, gt_b, rtol=0, atol=epsilon):
        raise ValueError('Extensão, resolução ou alinhamento de pixels distintos. Alinhe os mapas antes da monitoria.')
    aw, bw = a.GetProjection(), b.GetProjection()
    if bool(aw) != bool(bw):
        raise ValueError('Um dos mapas não tem SRC. Defina o SRC correto antes de comparar.')
    if aw != bw and aw:
        sa, sb = osr.SpatialReference(), osr.SpatialReference()
        if sa.ImportFromWkt(aw) != 0 or sb.ImportFromWkt(bw) != 0 or not bool(sa.IsSame(sb)):
            raise ValueError('Os mapas possuem SRC diferentes. Reprojete antes da monitoria.')


def _hectares_per_pixel(ds, osr):
    wkt = ds.GetProjection()
    if not wkt:
        return None
    srs = osr.SpatialReference()
    if srs.ImportFromWkt(wkt) != 0 or not srs.IsProjected():
        return None
    units = float(srs.GetLinearUnits())
    return pixel_area_ha(ds.GetGeoTransform(), True, units) if units > 0 else None


def _check_cancel(cancelled):
    if cancelled and cancelled():
        raise InterruptedError('Monitoria cancelada.')


def _install_outputs(staged, final):
    """Substituição com backup/rollback quando houver saída anterior."""
    backups = {}
    installed = []
    try:
        for source, destination in zip(staged, final):
            if os.path.exists(destination):
                backup = source + '.old'
                os.replace(destination, backup)
                backups[destination] = backup
            os.replace(source, destination)
            installed.append(destination)
    except Exception:
        for destination in installed:
            if os.path.exists(destination):
                os.remove(destination)
        for destination, backup in backups.items():
            if os.path.exists(backup):
                os.replace(backup, destination)
        raise


def _band_labels(path, band):
    """Legendas GDAL e .rs2.json, quando existirem. Não inventa nomes temáticos."""
    labels = {}
    category_names = getattr(band, 'GetCategoryNames', lambda: None)() or []
    for code, name in enumerate(category_names):
        if name and str(name).strip():
            labels[float(code)] = str(name).strip()
    sidecar = str(path) + '.rs2.json'
    if os.path.isfile(sidecar):
        try:
            with open(sidecar, encoding='utf-8') as source:
                data = json.load(source)
            for code, name in enumerate(data.get('labels') or []):
                if name and str(name).strip():
                    labels[float(code)] = str(name).strip()
        except (OSError, ValueError, TypeError):
            pass
    return labels


def _read_legend_lookup(csv_path, initial_label, final_label):
    if not csv_path:
        return {}, {}
    if not os.path.isfile(csv_path):
        raise ValueError(f'CSV de legendas não encontrado: {csv_path}')
    initial, final = {}, {}
    with open(csv_path, encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream, delimiter=';')
        if not reader.fieldnames or not {'PERIODO', 'CODIGO', 'CLASSE'} <= set(reader.fieldnames):
            raise ValueError('O CSV de legendas precisa das colunas PERIODO;CODIGO;CLASSE.')
        for idx, row in enumerate(reader, 2):
            try:
                code = float(row['CODIGO'].strip())
            except (TypeError, ValueError, AttributeError) as e:
                raise ValueError(f'CSV de legendas, linha {idx}: código inválido.') from e
            if not np.isfinite(code):
                raise ValueError(f'CSV de legendas, linha {idx}: código não finito.')
            period = (row['PERIODO'] or '').strip().casefold()
            label = (row['CLASSE'] or '').strip()
            if not label:
                raise ValueError(f'CSV de legendas, linha {idx}: classe vazia.')
            if period in ('inicial', 'inicio', initial_label.casefold()):
                initial[code] = label
            elif period in ('final', 'fim', final_label.casefold()):
                final[code] = label
            else:
                raise ValueError(f'CSV de legendas, linha {idx}: período desconhecido ({period}).')
    return initial, final


def _temporal_analysis(before, after, extras, before_label, after_label,
                       reference, osr, progress, cancelled):
    """MK de áreas por classe usando área espacial comparável em todas as datas."""
    # 'Inicial'/'Final' são descritores válidos para a comparação, mas não anos.
    if not extras:
        return {'status': 'nao_aplicavel', 'n': 2,
                'mensagem': 'Mann–Kendall não aplicável a 2 datas. '
                            'Adicione pelo menos 3 mapas datados para totalizar 5 observações. '
                            'As mudanças entre os dois mapas são descritivas.'}
    try:
        entries = [(int(before_label), str(before)), (int(after_label), str(after))]
        entries.extend((int(year), str(path)) for year, path in extras)
    except (ValueError, TypeError) as error:
        raise ValueError('Para a série Mann–Kendall, informe anos numéricos de 4 dígitos nos períodos e nos mapas adicionais.') from error
    entries.sort(key=lambda row: row[0])
    years = [yr for yr, _ in entries]
    if len(years) != len(set(years)) or any(year < 1800 or year > 2200 for year in years):
        raise ValueError('Série Mann–Kendall: anos duplicados ou fora do intervalo 1800–2200.')
    if len({os.path.realpath(path) for _, path in entries}) != len(entries):
        raise ValueError('Série Mann–Kendall: não reutilize o mesmo arquivo em duas datas.')
    if len(entries) < MIN_DATES:
        return {'status': 'nao_aplicavel', 'n': len(entries),
                'mensagem': f'Mann–Kendall não aplicável com {len(entries)} datas. '
                            'Exige-se pelo menos 5 observações (preferencialmente 8–10 ou mais).'}
    from osgeo import gdal
    datasets = []
    try:
        for year, path in entries:
            if not os.path.isfile(path):
                raise ValueError(f'Série temporal: raster ausente no ano {year}: {path}')
            ds = gdal.Open(path, gdal.GA_ReadOnly)
            if ds is None or ds.RasterCount != 1:
                raise ValueError(f'Série temporal: raster inválido/possui múltiplas bandas ({year}).')
            _same_grid(reference, ds, osr)
            datasets.append(ds)
        bands = [d.GetRasterBand(1) for d in datasets]
        nds = [b.GetNoDataValue() for b in bands]
        counts = [Counter() for _ in bands]
        valid_total = 0
        for ix, (x,y,w,h) in enumerate(_windows(reference.RasterXSize, reference.RasterYSize)):
            _check_cancel(cancelled)
            data = [b.ReadAsArray(x,y,w,h) for b in bands]
            if any(a is None for a in data):
                raise ValueError('Série temporal: falha na leitura de pixels.')
            common = np.ones((h,w), dtype=bool)
            for a, nd in zip(data, nds):
                common &= valid_mask(a, nd)
            valid_total += int(common.sum())
            if common.any():
                for arr, counter in zip(data, counts):
                    unique, freq = np.unique(arr[common], return_counts=True)
                    counter.update({float(v): int(c) for v, c in zip(unique, freq)})
        classes = {key for counter in counts for key in counter}
        if len(classes) > MAX_MATRIX_CLASSES:
            raise ValueError('Série temporal contém mais de 512 classes; reclassifique antes do teste.')
        rows = temporal_rows(years, counts, valid_total)
        return {'status': 'calculado', 'n': len(years), 'anos': years,
                'validos': valid_total, 'linhas': rows}
    finally:
        datasets.clear()


def run_monitoring(before, after, output, *, before_label='Inicial', after_label='Final',
                   title='', progress=None, cancelled=None,
                   descriptive_legend=True, temporal_files=None, legend_lookup=''):
    """Cria GeoTIFF Int32 de transições + CSV detalhado + matriz + TXT.

    Todas as operações de I/O são feitas por caminhos locais na thread da tarefa.
    A codificação é reproduzível: pares ordenados por código de classe.
    """
    from osgeo import gdal, osr

    paths = [os.path.abspath(str(p)) for p in (before, after)]
    destination = os.path.abspath(str(output))
    if not destination.lower().endswith(('.tif', '.tiff')):
        raise ValueError('A saída da monitoria deve ser GeoTIFF (.tif).')
    if any(not os.path.isfile(p) for p in paths):
        raise ValueError('Selecione dois rasters existentes em arquivos locais.')
    stem = str(Path(destination).with_suffix(''))
    outputs = [destination, stem + '_transicoes.csv', stem + '_matriz.csv',
               stem + '_resumo.txt', stem + '_tendencias_mk.csv']
    for path in paths:
        if os.path.realpath(path) in [os.path.realpath(o) for o in outputs]:
            raise ValueError('Os arquivos de saída não podem substituir os mapas de entrada.')
    ds_a, ds_b = gdal.Open(paths[0], gdal.GA_ReadOnly), gdal.Open(paths[1], gdal.GA_ReadOnly)
    if ds_a is None or ds_b is None:
        raise ValueError('Não foi possível abrir os arquivos via GDAL.')
    if ds_a.RasterCount != 1 or ds_b.RasterCount != 1:
        raise ValueError('Selecione rasters categóricos monobanda. Converta RGB em classes antes da monitoria.')
    _same_grid(ds_a, ds_b, osr)
    ba, bb = ds_a.GetRasterBand(1), ds_b.GetRasterBand(1)
    if ba.DataType in (gdal.GDT_CFloat32, gdal.GDT_CFloat64) or bb.DataType in (gdal.GDT_CFloat32, gdal.GDT_CFloat64):
        raise ValueError('Rasters com valores complexos não são suportados.')
    nd_a, nd_b = ba.GetNoDataValue(), bb.GetNoDataValue()
    count = Counter()
    width, height = ds_a.RasterXSize, ds_a.RasterYSize
    windows = list(_windows(width, height))
    nwin = len(windows)
    for idx, (x, y, w, h) in enumerate(windows):
        _check_cancel(cancelled)
        a, b = ba.ReadAsArray(x, y, w, h), bb.ReadAsArray(x, y, w, h)
        if a is None or b is None:
            raise ValueError('Falha na leitura de blocos raster.')
        pairs, _ = transition_counts(a, b, nd_a, nd_b)
        count.update(pairs)
        if len(count) > MAX_TRANSITIONS:
            raise ValueError('Há mais de 10.000 combinações: reclassifique os rasters antes da monitoria.')
        if progress:
            progress(45 * (idx + 1) / nwin)
    if not count:
        raise ValueError('Não há pixels comuns válidos nos mapas selecionados.')
    initial_n = len({p[0] for p in count})
    final_n = len({p[1] for p in count})
    if max(initial_n, final_n) > MAX_MATRIX_CLASSES:
        raise ValueError('Há mais de 512 classes em um dos períodos. Use mapas categóricos reclassificados.')
    before_names = _band_labels(paths[0], ba)
    after_names = _band_labels(paths[1], bb)
    lookup_a, lookup_b = _read_legend_lookup(legend_lookup, before_label, after_label)
    before_names.update(lookup_a)
    after_names.update(lookup_b)
    summary = transitions_summary(count, width * height, _hectares_per_pixel(ds_a, osr),
                                  before_names, after_names)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    workspace = tempfile.mkdtemp(prefix='.vistasaga_monitoria_', dir=os.path.dirname(destination))
    temporary = [os.path.join(workspace, os.path.basename(p)) for p in outputs]
    dst = None
    try:
        driver = gdal.GetDriverByName('GTiff')
        if driver is None:
            raise ValueError('Driver GeoTIFF GDAL indisponível.')
        dst = driver.Create(temporary[0], width, height, 1, gdal.GDT_Int32,
                            options=['TILED=YES', 'COMPRESS=DEFLATE', 'PREDICTOR=2', 'BIGTIFF=IF_SAFER'])
        if dst is None:
            raise OSError('Falha ao criar o mapa de transições.')
        dst.SetGeoTransform(ds_a.GetGeoTransform())
        dst.SetProjection(ds_a.GetProjection())
        dst.GetRasterBand(1).SetNoDataValue(int(NODATA_OUT))
        # Legenda e tabela de correspondência no próprio TIFF para que a
        # vetorização não dependa da presença dos CSVs na mesma pasta.
        from .monitoring_vector import META_KEY, serialize_monitoring_rows
        band_out = dst.GetRasterBand(1)
        if callable(getattr(band_out, 'SetMetadataItem', None)):
            encoded = serialize_monitoring_rows(summary['linhas'])
            # Metadados muito grandes permanecem no CSV associado.
            if len(encoded.encode('utf-8')) <= 512 * 1024:
                band_out.SetMetadataItem(META_KEY, encoded)
        for idx, (x, y, w, h) in enumerate(windows):
            _check_cancel(cancelled)
            a, b = ba.ReadAsArray(x, y, w, h), bb.ReadAsArray(x, y, w, h)
            _, valid = transition_counts(a, b, nd_a, nd_b)
            encoded = np.full((h, w), int(NODATA_OUT), dtype=np.int32)
            if valid.any():
                pairs, inv = np.unique(np.column_stack((a[valid], b[valid])), axis=0,
                                       return_inverse=True)
                local_ids = np.array([summary['ids'][(float(c[0]), float(c[1]))]
                                      for c in pairs], dtype=np.int32)
                encoded[valid] = local_ids[inv]
            dst.GetRasterBand(1).WriteArray(encoded, x, y)
            if progress:
                progress(45 + 45 * (idx + 1) / nwin)
        dst.FlushCache()
        dst = None
        _check_cancel(cancelled)
        res = ds_a.GetGeoTransform()
        write_monitoring_reports(temporary[1], temporary[2], temporary[3], summary,
                                 title=title, before_label=before_label,
                                 after_label=after_label, crs=ds_a.GetProjection(),
                                 resolution=f'{abs(res[1]):g} x {abs(res[5]):g} (unidades do SRC)',
                                 use_descriptive=descriptive_legend)
        _check_cancel(cancelled)
        temporal = _temporal_analysis(paths[0], paths[1], temporal_files or [],
                                      before_label, after_label, ds_a, osr, progress, cancelled)
        write_mk_csv(temporary[4], temporal)
        append_mk_txt(temporary[3], temporal)
        _check_cancel(cancelled)
        _install_outputs(temporary, outputs)
        if progress:
            progress(100)
        return {**summary, 'mapa': outputs[0], 'transicoes': outputs[1],
                'matriz': outputs[2], 'resumo': outputs[3],
                'tendencias': outputs[4], 'temporal': temporal}
    finally:
        dst = None
        ds_a = None
        ds_b = None
        shutil.rmtree(workspace, ignore_errors=True)
