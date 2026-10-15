"""Assinatura Ambiental em raster ou vetor temático, por área poligonal.

Todas as operações PyQGIS ocorrem na thread principal; GDAL/OGR são importados
somente em tempo de execução dentro do QGIS. Publicação atômica de três arquivos.
"""
import math
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from .signature_core import category_code, summarize_area, write_signature_reports


def validate_signature(thematic, aoi, mode, field, destination, name_field='', area_name_field=''):
    from qgis.core import Qgis, QgsRasterLayer, QgsVectorLayer
    if mode not in ('raster', 'vector'):
        raise ValueError('Selecione Raster ou Vetor temático.')
    if not isinstance(aoi, QgsVectorLayer) or not aoi.isValid():
        raise ValueError('Selecione uma camada válida de áreas poligonais.')
    if aoi.geometryType() != Qgis.GeometryType.Polygon or aoi.featureCount() < 1:
        raise ValueError('As áreas de análise devem ser polígonos não vazios.')
    if not aoi.crs().isValid():
        raise ValueError('Defina um SRC válido para as áreas de análise.')
    if aoi.isEditable():
        raise ValueError('Salve ou descarte as edições pendentes da camada de áreas.')
    if area_name_field and area_name_field not in aoi.fields().names():
        raise ValueError('Campo de identificação das áreas não encontrado.')
    if mode == 'raster':
        if not isinstance(thematic, QgsRasterLayer) or not thematic.isValid():
            raise ValueError('Selecione um GeoTIFF temático válido.')
        if thematic.bandCount() != 1:
            raise ValueError('A Assinatura raster requer um mapa categórico monobanda.')
    else:
        if not isinstance(thematic, QgsVectorLayer) or not thematic.isValid():
            raise ValueError('Selecione uma camada temática vetorial válida.')
        if thematic.geometryType() != Qgis.GeometryType.Polygon:
            raise ValueError('O mapa temático vetorial deve conter polígonos.')
        if field not in thematic.fields().names():
            raise ValueError('Campo de classe temática inexistente.')
        if name_field and name_field not in thematic.fields().names():
            raise ValueError('Campo de legenda temática inexistente.')
        if thematic.isEditable():
            raise ValueError('Salve ou descarte as edições do mapa temático.')
    if not thematic.crs().isValid():
        raise ValueError('Defina um SRC válido para o mapa temático.')
    if not str(destination).lower().endswith('.csv'):
        raise ValueError('A saída principal deve ser um arquivo .csv.')
    target = Path(destination).resolve()
    if not target.parent.is_dir():
        raise ValueError('Pasta de saída inexistente.')
    if len(str(target)) > 240 and os.name == 'nt':
        raise ValueError('Caminho de saída muito longo para o Windows.')
    finals = _outpaths(str(target))
    for layer in (aoi, thematic):
        source = layer.source().split('|', 1)[0]
        if os.path.exists(source) and any(os.path.normcase(os.path.abspath(source)) ==
                                          os.path.normcase(os.path.abspath(x)) for x in finals):
            raise ValueError('A saída não pode sobrescrever uma camada de entrada.')
    return str(target)


def _outpaths(path):
    stem = str(Path(path).with_suffix(''))
    return (stem + '.csv', stem + '_resumo.txt', stem + '_areas.gpkg')


def _geometry_for_feature(feature, transform=None):
    from qgis.core import QgsGeometry
    geom = QgsGeometry(feature.geometry())
    if geom.isNull() or geom.isEmpty():
        return None
    if not geom.isGeosValid():
        raise ValueError(f'Geometria inválida na feição {feature.id()}; use Corrigir geometrias no QGIS.')
    if transform:
        geom.transform(transform)
    return geom


def _raster_counts(dataset, geometry, *, cancel=None):
    """Lê apenas a janela da geometria; mascara pixels pelo centro da célula."""
    import numpy as np
    from osgeo import gdal, ogr
    from .core import valid_mask
    gt = dataset.GetGeoTransform()
    inv = gdal.InvGeoTransform(gt)
    if inv is None:
        raise ValueError('Transformação geográfica do raster inválida.')
    box = geometry.boundingBox()
    corners = ((box.xMinimum(), box.yMinimum()), (box.xMaximum(), box.yMinimum()),
               (box.xMaximum(), box.yMaximum()), (box.xMinimum(), box.yMaximum()))
    xy = [gdal.ApplyGeoTransform(inv, x, y) for x, y in corners]
    x0 = max(0, math.floor(min(p[0] for p in xy)) - 1)
    x1 = min(dataset.RasterXSize, math.ceil(max(p[0] for p in xy)) + 1)
    y0 = max(0, math.floor(min(p[1] for p in xy)) - 1)
    y1 = min(dataset.RasterYSize, math.ceil(max(p[1] for p in xy)) + 1)
    if x1 <= x0 or y1 <= y0:
        return Counter()
    memory = ogr.GetDriverByName('Memory').CreateDataSource('')
    geom_layer = memory.CreateLayer('mask', geom_type=ogr.wkbUnknown)
    feature = ogr.Feature(geom_layer.GetLayerDefn())
    feature.SetGeometry(ogr.CreateGeometryFromWkb(bytes(geometry.asWkb())))
    if geom_layer.CreateFeature(feature) != 0:
        raise OSError('Não foi possível preparar o polígono de análise.')
    feature = None
    counts = Counter()
    band = dataset.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    gmem = gdal.GetDriverByName('MEM')
    for yy in range(y0, y1, 512):
        hh = min(512, y1 - yy)
        for xx in range(x0, x1, 512):
            if cancel and cancel():
                raise InterruptedError('Assinatura cancelada.')
            ww = min(512, x1 - xx)
            mask = gmem.Create('', ww, hh, 1, gdal.GDT_Byte)
            newgt = (gt[0] + xx * gt[1] + yy * gt[2], gt[1], gt[2],
                     gt[3] + xx * gt[4] + yy * gt[5], gt[4], gt[5])
            mask.SetGeoTransform(newgt)
            mask.GetRasterBand(1).Fill(0)
            if gdal.RasterizeLayer(mask, [1], geom_layer, burn_values=[1]) != 0:
                raise RuntimeError('Falha ao rasterizar a área de análise.')
            data = band.ReadAsArray(xx, yy, ww, hh)
            selected = mask.GetRasterBand(1).ReadAsArray() != 0
            valid = selected & valid_mask(data, nodata)
            if valid.any():
                distinct, n = np.unique(data[valid], return_counts=True)
                if len(counts) + len(distinct) > 10000:
                    raise ValueError('O mapa contém muitas classes distintas; '
                                     'a Assinatura requer raster categórico.')
                counts.update({category_code(code): int(value) for code, value in zip(distinct, n)})
            mask = None
    memory = None
    return counts


def _resolve_class_geometries(class_geometries, measure_area, *,
                              overlap_policy='exclude', geometry_class=None):
    """Calcula área única por classe, evitando contagem dupla de polígonos.

    Geometrias repetidas de MESMA classe são dissolvidas. Quando categorias
    DIFERENTES disputam uma superfície, o usuário escolhe entre interromper
    ('strict') ou excluir a interseção ambígua ('exclude'). Nunca atribui
    uma interseção a uma categoria arbitrária.

    Retorna ({codigo: area_em_ha}, area_ambigua_ha). Requer geometrias no
    mesmo SRC. A área é obtida por measure_area para respeitar o elipsoide.
    """
    if overlap_policy not in ('exclude', 'strict'):
        raise ValueError('Tratamento de sobreposição não reconhecido.')
    if geometry_class is None:
        from qgis.core import QgsGeometry
        geometry_class = QgsGeometry

    dissolved = {}
    for code, geoms in class_geometries.items():
        if not geoms:
            continue
        union = geometry_class.unaryUnion(geoms) if len(geoms) > 1 else geoms[0]
        if union.isNull() or union.isEmpty():
            raise ValueError(f'Falha ao dissolver polígonos da classe {code}.')
        dissolved[code] = union

    conflicts = []
    first_pair = None
    codes = sorted(dissolved)
    for i, code_a in enumerate(codes):
        ga = dissolved[code_a]
        for code_b in codes[i + 1:]:
            gb = dissolved[code_b]
            if not ga.boundingBox().intersects(gb.boundingBox()):
                continue
            intersection = ga.intersection(gb)
            if intersection.isNull() or intersection.isEmpty():
                continue
            area = float(measure_area(intersection))
            # Ignorar apenas artefatos abaixo de 0,01 m² (contatos de borda,
            # ruídos numéricos sem significado cartográfico). NÃO aplicar
            # limiar proporcional que oculte conflitos em mapas grandes.
            if area > 0.01:
                conflicts.append(intersection)
                if first_pair is None:
                    first_pair = (code_a, code_b)
    ambiguous = None
    conflict_m2 = 0.0
    if conflicts:
        ambiguous = (geometry_class.unaryUnion(conflicts) if len(conflicts) > 1
                     else conflicts[0])
        if ambiguous.isNull() or ambiguous.isEmpty():
            raise ValueError('Não foi possível determinar as áreas temáticas conflitantes.')
        conflict_m2 = float(measure_area(ambiguous))
        if overlap_policy == 'strict':
            raise ValueError(
                'Há áreas sobrepostas entre classes temáticas diferentes '
                f'(por exemplo, {first_pair[0]} e {first_pair[1]}): '
                f'{conflict_m2 / 10000:.6f} ha. '
                'Para processar sem contagem dupla, selecione em '
                '"Sobreposição entre classes" a opção de excluir '
                'apenas as áreas de classificação ambígua.')

    totals = {}
    for code, geom in dissolved.items():
        if ambiguous is not None:
            geom = geom.difference(ambiguous)
            if geom.isNull():
                raise ValueError(f'Falha ao retirar conflitos da classe {code}.')
        if geom.isEmpty():
            continue
        area_m2 = float(measure_area(geom))
        if area_m2 > 0:
            totals[code] = area_m2 / 10000.0
    return totals, conflict_m2 / 10000.0


def _vector_counts(thematic, aoi_geom, field, label_field, measure_area, *,
                   index=None, cancel=None, overlap_policy='exclude'):
    """Assinatura por união de classe; conflitos reais ficam documentados."""
    from qgis.core import QgsFeatureRequest, QgsSpatialIndex
    if index is None:
        index = QgsSpatialIndex(thematic.getFeatures())
    candidates = index.intersects(aoi_geom.boundingBox())
    grouped = defaultdict(list)
    names = {}
    for feature in thematic.getFeatures(QgsFeatureRequest().setFilterFids(candidates)):
        if cancel and cancel():
            raise InterruptedError('Assinatura cancelada.')
        code = category_code(feature[field])
        if code is None:
            continue
        geom = _geometry_for_feature(feature)
        if geom is None or not geom.intersects(aoi_geom):
            continue
        clipped_geom = geom.intersection(aoi_geom)
        if clipped_geom.isNull() or clipped_geom.isEmpty():
            continue
        if float(measure_area(clipped_geom)) <= 0:
            continue
        grouped[code].append(clipped_geom)
        label = (category_code(feature[label_field]) or code) if label_field else code
        if code in names and names[code] != label:
            raise ValueError(f'Código {code} apresenta legendas diferentes na mesma camada.')
        names[code] = label
    totals, conflict_ha = _resolve_class_geometries(
        grouped, measure_area, overlap_policy=overlap_policy)
    return totals, names, conflict_ha


def _write_area_geopackage(path, features, summaries, source_layer):
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsFeature, QgsField, QgsProject, QgsVectorFileWriter, QgsVectorLayer
    layer = QgsVectorLayer('MultiPolygon', 'Assinatura - áreas de análise', 'memory')
    layer.setCrs(source_layer.crs())
    if not layer.isValid():
        raise RuntimeError('Falha ao preparar camada de polígonos do resultado.')
    provider = layer.dataProvider()
    fields = [QgsField('AREA_ID', QVariant.String), QgsField('AREA_NOME', QVariant.String),
              QgsField('AREA_AOI_HA', QVariant.Double), QgsField('AREA_ANAL_HA', QVariant.Double),
              QgsField('COBERT_PCT', QVariant.Double), QgsField('CLASSES_N', QVariant.Int),
              QgsField('PREDOMINA', QVariant.String),
              QgsField('AREA_CONF_HA', QVariant.Double), QgsField('PCT_CONF', QVariant.Double)]
    if not provider.addAttributes(fields):
        raise OSError('Não foi possível preparar os campos de Assinatura.')
    layer.updateFields()
    for geom, s in zip(features, summaries):
        if geom is None:
            continue
        if not geom.isMultipart():
            from qgis.core import QgsGeometry
            geom = QgsGeometry(geom)
            geom.convertToMultiType()
        feat = QgsFeature(layer.fields())
        feat.setGeometry(geom)
        feat.setAttributes([s['id'], s['name'], s['aoi_ha'], s['analyzed_ha'],
                            s['coverage_pct'], s['classes'], s['dominant'],
                            s.get('conflict_ha'), s.get('conflict_pct')])
        if not provider.addFeatures([feat])[0]:
            raise OSError('Falha na escrita da área de análise.')
    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = 'GPKG'
    opts.layerName = 'assinatura_areas'
    opts.fileEncoding = 'UTF-8'
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, str(path), QgsProject.instance().transformContext(), opts)
    if int(result[0]) != 0:
        raise OSError('Não foi possível gravar o GeoPackage das áreas: ' + str(result))


def run_signature(thematic, aoi, mode, field, destination, *,
                  name_field='', area_name_field='', title='',
                  progress=None, cancelled=None, overlap_policy='exclude'):
    from qgis.core import QgsCoordinateTransform, QgsProject
    from .vector_evaluation_writer import _area_function, _publish_set
    from .algorithms.common import area_ha
    from .monitoring_engine import _band_labels
    from osgeo import gdal

    destination = validate_signature(thematic, aoi, mode, field, destination,
                                      name_field, area_name_field)
    files = _outpaths(destination)
    staging = tempfile.mkdtemp(prefix='.vistasaga_assinatura_', dir=str(Path(destination).parent))
    ds = None
    try:
        measure_aoi = _area_function(aoi)
        measure_theme = _area_function(thematic) if mode == 'vector' else None
        theme_index = None
        if mode == 'vector':
            from qgis.core import QgsSpatialIndex
            theme_index = QgsSpatialIndex(thematic.getFeatures())
        transform = None
        if aoi.crs() != thematic.crs():
            transform = QgsCoordinateTransform(aoi.crs(), thematic.crs(), QgsProject.instance())
        pixel_ha = None
        names = {}
        if mode == 'raster':
            path = thematic.source().split('|', 1)[0]
            ds = gdal.Open(path, gdal.GA_ReadOnly)
            if not ds or ds.RasterCount != 1 or not ds.GetProjection():
                raise ValueError('Raster não disponível como arquivo monobanda georreferenciado via GDAL.')
            pixel_ha = area_ha(ds)
            names = {category_code(k): v for k, v in _band_labels(path, ds.GetRasterBand(1)).items()}
        summaries, records, polygons = [], [], []
        total_conflict_ha = 0.0
        number = aoi.featureCount()
        for i, feature in enumerate(aoi.getFeatures()):
            if cancelled and cancelled():
                raise InterruptedError('Assinatura cancelada.')
            geom = _geometry_for_feature(feature)
            if geom is None:
                continue
            name = (category_code(feature[area_name_field]) if area_name_field else None) or f'Área {feature.id()}'
            id_value = str(feature.id())
            aoi_area_ha = measure_aoi(geom) / 10000
            theme_geom = _geometry_for_feature(feature, transform)
            if mode == 'raster':
                counts = _raster_counts(ds, theme_geom, cancel=cancelled)
                thematic_names = names
                conflict_ha = None
            else:
                counts, thematic_names, conflict_ha = _vector_counts(
                    thematic, theme_geom, field, name_field, measure_theme,
                    index=theme_index, cancel=cancelled, overlap_policy=overlap_policy)
                total_conflict_ha += conflict_ha
            rows, summary = summarize_area(id_value, name, counts, kind=mode,
                                           pixel_ha=pixel_ha, thematic_names=thematic_names,
                                           area_aoi_ha=aoi_area_ha)
            summary['conflict_ha'] = conflict_ha
            summary['conflict_pct'] = (100.0 * conflict_ha / aoi_area_ha
                                       if conflict_ha is not None and aoi_area_ha > 0 else None)
            if summary['coverage_pct'] is not None and summary['coverage_pct'] > 100.05:
                # Pixel-center no raster pode extrapolar ligeiramente a borda.
                if mode == 'vector':
                    raise ValueError('Área temática superior à área poligonal; '
                                     'verifique geometrias, SRC e sobreposições.')
            records.extend(rows)
            summaries.append(summary)
            polygons.append(geom)
            if progress:
                progress(5 + int(84 * (i + 1) / max(1, number)))
        if not summaries:
            raise ValueError('Nenhum polígono utilizável foi encontrado na área de análise.')
        if not records and not (mode == 'vector' and total_conflict_ha > 0):
            raise ValueError('Nenhuma classe válida foi encontrada nas áreas selecionadas.')
        temp_csv = str(Path(staging) / 'assinatura.csv')
        temp_txt = str(Path(staging) / 'assinatura_resumo.txt')
        temp_gpkg = str(Path(staging) / 'assinatura_areas.gpkg')
        write_signature_reports(temp_csv, temp_txt, summaries, records, title=title,
                                theme=thematic.name(), mode=mode, crs=thematic.crs().authid(),
                                area_source=aoi.name())
        _write_area_geopackage(temp_gpkg, polygons, summaries, aoi)
        ds = None
        _publish_set([(temp_csv, files[0]), (temp_txt, files[1]), (temp_gpkg, files[2])],
                     str(Path(destination).parent))
        if progress:
            progress(100)
        return dict(csv=files[0], txt=files[1], gpkg=files[2],
                    areas=summaries, rows=records,
                    note=(('ATENÇÃO: ' + f'{total_conflict_ha:.6f} ha de áreas com classes '
                           'sobrepostas foram excluídos da distribuição. Consulte TXT/CSV.')
                          if mode == 'vector' and total_conflict_ha > 0 else
                          'Para rasters em SRC geográfico, áreas em ha das classes ficam vazias.'
                          if mode == 'raster' and pixel_ha is None else ''))
    finally:
        ds = None
        shutil.rmtree(staging, ignore_errors=True)
