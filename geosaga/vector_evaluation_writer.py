"""Avaliação vetorial com atributos de área e relatórios de combinações.

Executar no thread principal PyQGIS. Fontes permanecem intocadas e as
substituições de GeoPackage + relatórios são publicadas em conjunto.
"""
import os
import shutil
import tempfile
from collections import defaultdict

from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsDistanceArea, QgsField, QgsProject,
                       QgsVectorFileWriter, QgsVectorLayer)

from .evaluation_reports import create_reports, MAX_COMBINATIONS
from .vector_evaluation_core import category_key, evaluate_record, validate_criteria

OUTPUT_FIELDS = ('AVALIACAO', 'VALIDO', 'MOTIVO', 'AREA_M2', 'AREA_HA', 'PCT_AREA')


def _area_function(layer):
    """Retorna área em metros quadrados; nunca mede graus² como metros²."""
    from osgeo import osr
    crs = layer.crs()
    if not crs.isValid():
        raise ValueError('A camada precisa ter SRC válido para calcular as áreas.')
    if crs.isGeographic():
        measure = QgsDistanceArea()
        measure.setSourceCrs(crs, QgsProject.instance().transformContext())
        ellipsoid = crs.ellipsoidAcronym() or 'WGS84'
        if not measure.setEllipsoid(ellipsoid):
            raise ValueError('Não foi possível configurar o elipsoide para áreas geodésicas.')
        return measure.measureArea
    srs = osr.SpatialReference()
    if srs.ImportFromWkt(crs.toWkt()) != 0 or not srs.IsProjected():
        raise ValueError('Não foi possível identificar as unidades lineares do SRC.')
    factor = srs.GetLinearUnits()
    if not factor or factor <= 0:
        raise ValueError('Unidade linear desconhecida; não é possível calcular áreas em m².')
    return lambda geom: geom.area() * factor ** 2


def _publish_set(staged_pairs, parent):
    """Substitui GeoPackage e relatórios em conjunto, restaurando os anteriores em erro."""
    backups = tempfile.mkdtemp(prefix='.vistasaga_backup_', dir=parent)
    saved, published = [], []
    restore_errors = []
    try:
        for i, (_, final) in enumerate(staged_pairs):
            if os.path.isdir(final):
                raise OSError('Destino é uma pasta: ' + final)
            if os.path.exists(final):
                backup = os.path.join(backups, f'{i:02d}.bak')
                os.replace(final, backup)
                saved.append((backup, final))
        for source, final in staged_pairs:
            os.replace(source, final)
            published.append(final)
    except Exception as error:
        for path in reversed(published):
            try:
                os.remove(path)
            except OSError as exc:
                restore_errors.append(str(exc))
        for backup, path in reversed(saved):
            try:
                os.replace(backup, path)
            except OSError as exc:
                restore_errors.append(str(exc))
        suffix = ' Backups preservados em ' + backups if restore_errors else ''
        raise OSError(f'Falha ao publicar o GeoPackage e os relatórios: {error}.{suffix}') from error
    finally:
        if not restore_errors:
            shutil.rmtree(backups, ignore_errors=True)


def evaluate_vector_layer(layer, criteria, scale, destination, progress=None,
                          cancelled=None, report_csv=True, report_txt=True,
                          report_criteria=None):
    """Mantém todas as feições; valores inválidos geram avaliação NULL.

    Grava os campos AREA_M2, AREA_HA e PCT_AREA em cada polígono; o percentual
    é calculado sobre a soma das áreas das feições do GeoPackage de saída.
    """
    if not layer or not layer.isValid():
        raise ValueError('A camada de polígonos não é válida.')
    if layer.isEditable():
        raise ValueError('Salve ou descarte as edições da camada antes de avaliá-la.')
    rules = validate_criteria(criteria, scale)
    existing = {field.name().casefold() for field in layer.fields()}
    names = list(OUTPUT_FIELDS) + [f'NOTA_{i:02d}' for i in range(1, len(rules) + 1)]
    if any(name.casefold() in existing for name in names):
        raise ValueError('A camada já contém um campo de resultado (' + ', '.join(names) + '). '
                         'Renomeie os campos de entrada ou use uma cópia da camada.')
    field_names = {field.name() for field in layer.fields()}
    if any(rule['field'] not in field_names for rule in rules):
        raise ValueError('Um dos campos selecionados não existe na camada.')
    destination = os.path.abspath(destination)
    if not destination.casefold().endswith('.gpkg'):
        raise ValueError('A saída vetorial deve ser GeoPackage (.gpkg).')
    source_path = os.path.abspath(layer.source().split('|', 1)[0])
    if source_path == destination:
        raise ValueError('O destino não pode sobrescrever a camada de entrada.')
    parent = os.path.dirname(destination)
    if not os.path.isdir(parent):
        raise ValueError('A pasta de saída não existe.')
    area_m2 = _area_function(layer)
    staging = tempfile.mkdtemp(prefix='.vistasaga_avaliacao_', dir=parent)
    tmpfile = os.path.join(staging, 'resultado.gpkg')
    try:
        if cancelled and cancelled():
            raise InterruptedError('Operação cancelada.')
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
        options.fileEncoding = 'UTF-8'
        options.layerName = 'avaliacao_espacial'
        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer, tmpfile, QgsProject.instance().transformContext(), options)
        if int(result[0]) != 0:
            raise OSError('Erro ao copiar camada para GeoPackage: ' + str(result))
        output_layer = QgsVectorLayer(tmpfile, 'Avaliação Espacial', 'ogr')
        if not output_layer.isValid():
            raise OSError('Não foi possível abrir o GeoPackage temporário.')
        provider = output_layer.dataProvider()
        extra = [QgsField('AVALIACAO', QVariant.Double), QgsField('VALIDO', QVariant.Int),
                 QgsField('MOTIVO', QVariant.String, len=254),
                 QgsField('AREA_M2', QVariant.Double), QgsField('AREA_HA', QVariant.Double),
                 QgsField('PCT_AREA', QVariant.Double)]
        extra.extend(QgsField(f'NOTA_{i:02d}', QVariant.Double) for i in range(1, len(rules) + 1))
        if not provider.addAttributes(extra):
            raise OSError('Não foi possível adicionar os atributos de avaliação e área.')
        output_layer.updateFields()
        indexes = [output_layer.fields().indexOf(name) for name in names]
        if -1 in indexes:
            raise OSError('Os campos de resultado não foram criados.')
        summary = {'validos': 0, 'excluidos_ou_sem_dado': 0, 'total': 0,
                   'area_total_ha': 0.0, 'area_avaliada_ha': 0.0}
        # Duas passagens de leitura evitam manter milhões de áreas na memória.
        total_area_m2 = 0.0
        for feature in output_layer.getFeatures():
            if cancelled and cancelled():
                raise InterruptedError('Operação cancelada.')
            geom = feature.geometry()
            area = float(area_m2(geom)) if not geom.isNull() and not geom.isEmpty() else 0.0
            if not 0 <= area < float('inf'):
                raise ValueError(f'Área inválida na feição {feature.id()}.')
            total_area_m2 += area
        summary['area_total_ha'] = total_area_m2 / 10000.0
        combinations = defaultdict(lambda: [0, 0.0])
        batch = {}
        total_features = max(1, output_layer.featureCount())
        for feature in output_layer.getFeatures():
            if cancelled and cancelled():
                raise InterruptedError('Operação cancelada.')
            attrs = {rule['field']: feature[rule['field']] for rule in rules}
            score, valid, reason, notes = evaluate_record(attrs, rules)
            geom = feature.geometry()
            area = float(area_m2(geom)) if not geom.isNull() and not geom.isEmpty() else 0.0
            pct = 100.0 * area / total_area_m2 if total_area_m2 > 0 else 0.0
            values = [score, valid, reason, area, area / 10000.0, pct] + notes
            batch[feature.id()] = dict(zip(indexes, values))
            summary['total'] += 1
            if valid:
                summary['validos'] += 1
                summary['area_avaliada_ha'] += area / 10000.0
                if report_txt or report_csv:
                    key = tuple(category_key(attrs[rule['field']]) for rule in rules)
                    counted = combinations[key]
                    counted[0] += 1
                    counted[1] += area / 10000.0
                    if len(combinations) > MAX_COMBINATIONS:
                        raise ValueError('Mais de 100 mil combinações; desative o relatório '
                                         'ou reclassifique os critérios.')
            else:
                summary['excluidos_ou_sem_dado'] += 1
            if len(batch) == 1000:
                if not provider.changeAttributeValues(batch):
                    raise OSError('Não foi possível gravar os resultados da avaliação.')
                batch.clear()
            if progress and summary['total'] % 250 == 0:
                progress(min(99, int(summary['total'] * 100 / total_features)))
        if batch and not provider.changeAttributeValues(batch):
            raise OSError('Não foi possível gravar o último bloco da avaliação.')
        output_layer = None
        provider = None
        if cancelled and cancelled():
            raise InterruptedError('Operação cancelada.')
        stem = os.path.splitext(destination)[0]
        pairs = [(tmpfile, destination)]
        if report_txt or report_csv:
            descriptions = []
            for i, rule in enumerate(rules):
                extra_meta = (report_criteria or [{}] * len(rules))[i]
                descriptions.append({'name': extra_meta.get('name', rule['field']),
                                     'source': extra_meta.get('source', layer.source()),
                                     'weight': rule['weight'], 'notes': rule['notes'],
                                     'excluded': rule['excluded'],
                                     'labels': extra_meta.get('labels', {})})
            report_t = os.path.join(staging, 'relatorio.txt') if report_txt else ''
            report_c = os.path.join(staging, 'relatorio.csv') if report_csv else ''
            create_reports(report_t, report_c,
                           combinations={k: tuple(v) for k, v in combinations.items()},
                           criteria=descriptions, total_units=summary['total'],
                           valid_units=summary['validos'],
                           total_area_ha=summary['area_total_ha'],
                           invalid_area_ha=summary['area_total_ha']-summary['area_avaliada_ha'],
                           crs=layer.crs().authid() or layer.crs().toWkt(),
                           unit_label='Feições', title=layer.name())
            if report_t:
                pairs.append((report_t, stem+'_relatorio.txt'))
                summary['relatorio_txt'] = stem+'_relatorio.txt'
            if report_c:
                pairs.append((report_c, stem+'_relatorio.csv'))
                summary['relatorio_csv'] = stem+'_relatorio.csv'
        _publish_set(pairs, parent)
        if progress:
            progress(100)
        return summary
    finally:
        shutil.rmtree(staging, ignore_errors=True)
