"""Monitoria vetorial direta (QGIS 4.x): interseção de duas camadas poligonais.

Execução na thread da GUI: as camadas QgsVectorLayer fornecidas pelo projeto nunca
são deslocadas para uma QgsTask. Arquivos de saída são publicados juntos.
"""
import gc
import os
import shutil
import tempfile

from .vector_evaluation_core import category_key
from .vector_monitoring_core import aggregate_transitions, make_transition, write_reports


def validate_vector_monitoring(before, after, field_before, field_after, destination,
                               name_before='', name_after=''):
    from qgis.core import Qgis, QgsVectorLayer
    from pathlib import Path
    if not before or not after or not isinstance(before, QgsVectorLayer) or not isinstance(after, QgsVectorLayer):
        raise ValueError('Selecione duas camadas vetoriais.')
    if not before.isValid() or not after.isValid():
        raise ValueError('Uma das camadas vetoriais não está disponível.')
    if before is after or before.id() == after.id():
        raise ValueError('Selecione duas camadas distintas para comparar os períodos.')
    for layer, field, legend in ((before, field_before, name_before),
                                 (after, field_after, name_after)):
        if layer.geometryType() != Qgis.GeometryType.Polygon:
            raise ValueError(f'{layer.name()}: o arquivo deve conter polígonos.')
        if layer.isEditable():
            raise ValueError(f'{layer.name()}: salve ou descarte as edições pendentes.')
        if field not in layer.fields().names():
            raise ValueError(f'{layer.name()}: campo de classe inexistente: {field}.')
        if legend and legend not in layer.fields().names():
            raise ValueError(f'{layer.name()}: campo de legenda inexistente: {legend}.')
        if layer.featureCount() == 0:
            raise ValueError(f'{layer.name()}: a camada está vazia.')
        if not layer.crs().isValid():
            raise ValueError(f'{layer.name()}: defina um SRC válido.')
    if before.crs() != after.crs():
        raise ValueError('Os dois mapas devem ter o mesmo SRC; reprojete um deles antes da Monitoria.')
    target = Path(destination).resolve()
    if target.suffix.lower() != '.gpkg':
        raise ValueError('A saída da Monitoria vetorial deve terminar em .gpkg.')
    if not target.parent.is_dir():
        raise ValueError('Pasta de saída inexistente.')
    # Não sobrescreve nenhum arquivo-fonte, mesmo se a camada aberta for uma subcamada de GeoPackage.
    for layer in (before, after):
        raw_path = layer.source().split('|', 1)[0]
        if os.path.isfile(raw_path) and os.path.normcase(os.path.abspath(raw_path)) == os.path.normcase(str(target)):
            raise ValueError('A saída não pode substituir uma camada de entrada.')
    return str(target)


def _prepare_layer(layer, field, name_field, out_field, out_name, progress=None, cancelled=None):
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsFeature, QgsField, QgsGeometry, QgsVectorLayer
    mem = QgsVectorLayer('MultiPolygon', 'VISTA_TEMP_' + out_field, 'memory')
    mem.setCrs(layer.crs())
    if not mem.isValid():
        raise RuntimeError('Falha ao criar camada temporária para interseção.')
    provider = mem.dataProvider()
    if not provider.addAttributes([QgsField(out_field, QVariant.String),
                                   QgsField(out_name, QVariant.String)]):
        raise RuntimeError('Não foi possível criar campos temporários de classes.')
    mem.updateFields()
    pending = []
    retained, omitted = 0, 0
    for feature in layer.getFeatures():
        if cancelled and cancelled():
            raise InterruptedError('Monitoria vetorial cancelada.')
        code = category_key(feature[field])
        geom = feature.geometry()
        if code is None or geom.isNull() or geom.isEmpty():
            omitted += 1
            continue
        if not geom.isGeosValid():
            raise ValueError(f'{layer.name()}: geometria inválida na feição {feature.id()}; '
                             'execute Corrigir geometrias no QGIS antes da monitoria.')
        geom = QgsGeometry(geom)
        if not geom.isMultipart():
            geom.convertToMultiType()
        if name_field:
            label = category_key(feature[name_field]) or ''
        elif isinstance(feature[field], str):
            # Campo de texto já é a legenda temática.
            label = code
        else:
            label = ''
        temporary = QgsFeature(mem.fields())
        temporary.setGeometry(geom)
        temporary.setAttributes([code, label])
        pending.append(temporary)
        retained += 1
        if len(pending) == 500:
            if not provider.addFeatures(pending)[0]:
                raise OSError(f'{layer.name()}: falha ao preparar dados vetoriais.')
            pending.clear()
            if progress:
                progress(None)
    if pending and not provider.addFeatures(pending)[0]:
        raise OSError(f'{layer.name()}: falha ao copiar últimas feições.')
    if not retained:
        raise ValueError(f'{layer.name()}: nenhuma feição possui geometria e classe válidas.')
    mem.updateExtents()
    return mem, omitted


def run_vector_monitoring(before, after, field_before, field_after, destination, *,
                          name_before='', name_after='', initial='Inicial', final='Final',
                          title='', progress=None, cancelled=None):
    """Escreve .gpkg, _transicoes.csv, _matriz.csv e _resumo.txt.

    As áreas são determinadas com a mesma rotina já homologada na Avaliação
    Espacial vetorial. Apenas a cobertura comum é avaliada. Não há rasterização.
    """
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsField, QgsProject, QgsProcessingFeedback, QgsVectorFileWriter, QgsVectorLayer
    from .vector_evaluation_writer import _area_function, _publish_set
    import processing

    destination = validate_vector_monitoring(before, after, field_before, field_after,
                                              destination, name_before, name_after)
    parent = os.path.dirname(destination)
    basename = os.path.splitext(destination)[0]
    staging = tempfile.mkdtemp(prefix='.vistasaga_monitoria_vetorial_', dir=parent)
    result_layer = None
    intersection = None
    mem_initial = mem_final = None
    try:
        if progress:
            progress(1)
        mem_initial, omitted_initial = _prepare_layer(before, field_before, name_before,
                                                       'COD_INI', 'NOME_INI', progress, cancelled)
        if progress:
            progress(12)
        mem_final, omitted_final = _prepare_layer(after, field_after, name_after,
                                                   'COD_FIM', 'NOME_FIM', progress, cancelled)
        if progress:
            progress(22)
        if cancelled and cancelled():
            raise InterruptedError('Monitoria vetorial cancelada.')
        class Feedback(QgsProcessingFeedback):
            def setProgress(self, percent):
                super().setProgress(percent)
                if progress:
                    progress(22 + int(40 * percent / 100))
            def isCanceled(self):
                return bool((cancelled and cancelled()) or super().isCanceled())
        feedback = Feedback()
        cross_file = os.path.join(staging, 'intersecao.gpkg')
        try:
            result = processing.run('native:intersection', {
                'INPUT': mem_initial, 'OVERLAY': mem_final,
                'INPUT_FIELDS': [], 'OVERLAY_FIELDS': [],
                'OVERLAY_FIELDS_PREFIX': '', 'OUTPUT': cross_file,
            }, feedback=feedback)
        except Exception as exc:
            if cancelled and cancelled():
                raise InterruptedError('Monitoria vetorial cancelada.') from exc
            raise RuntimeError(f'Falha na interseção das camadas: {exc}') from exc
        if cancelled and cancelled():
            raise InterruptedError('Monitoria vetorial cancelada.')
        intersection = QgsVectorLayer(str(result['OUTPUT']), 'Interseção', 'ogr')
        if not intersection.isValid() or not intersection.featureCount():
            raise ValueError('Os dois mapas não possuem área comum de interseção.')
        base_fields = intersection.fields().names()
        if not {'COD_INI', 'NOME_INI', 'COD_FIM', 'NOME_FIM'} <= set(base_fields):
            raise RuntimeError('A interseção não preservou os campos temáticos esperados.')
        tmp_gpkg = os.path.join(staging, 'monitoria.gpkg')
        save = QgsVectorFileWriter.SaveVectorOptions()
        save.driverName = 'GPKG'
        save.fileEncoding = 'UTF-8'
        save.layerName = 'monitoria_vetorial'
        response = QgsVectorFileWriter.writeAsVectorFormatV3(
            intersection, tmp_gpkg, QgsProject.instance().transformContext(), save)
        if int(response[0]) != 0:
            raise OSError('Falha ao escrever o GeoPackage intermediário: ' + str(response))
        intersection = None
        result_layer = QgsVectorLayer(tmp_gpkg + '|layername=monitoria_vetorial',
                                      'Monitoria vetorial', 'ogr')
        if not result_layer.isValid():
            raise OSError('O GeoPackage intermediário não pôde ser aberto.')
        extra = [QgsField('ID_TRANS', QVariant.Int), QgsField('SITUACAO', QVariant.String),
                 QgsField('LEGENDA', QVariant.String), QgsField('DEIXOU_SER', QVariant.String),
                 QgsField('TORNOU_SE', QVariant.String), QgsField('AREA_M2', QVariant.Double),
                 QgsField('AREA_HA', QVariant.Double), QgsField('PCT_AREA', QVariant.Double)]
        provider = result_layer.dataProvider()
        if not provider.addAttributes(extra):
            raise OSError('Não foi possível acrescentar os campos de monitoria e áreas.')
        result_layer.updateFields()
        index = {f.name(): result_layer.fields().indexOf(f.name()) for f in extra}
        if any(value < 0 for value in index.values()):
            raise OSError('Campos de saída ausentes após a gravação.')
        measure = _area_function(result_layer)

        def records():
            for feat in result_layer.getFeatures():
                if cancelled and cancelled():
                    raise InterruptedError('Monitoria vetorial cancelada.')
                geom = feat.geometry()
                if geom.isEmpty() or geom.isNull():
                    continue
                area = float(measure(geom))
                if area <= 0:
                    continue
                transition = make_transition(feat['COD_INI'], feat['COD_FIM'],
                                             feat['NOME_INI'], feat['NOME_FIM'])
                yield feat.id(), transition, area
        summary = aggregate_transitions(records())
        if progress:
            progress(76)
        row_lookup = {(r['codigo_inicial'], r['codigo_final'],
                       r['classe_inicial'], r['classe_final']): r for r in summary['linhas']}
        batch = {}
        for count, (fid, record, area) in enumerate(records(), 1):
            key = (record['codigo_inicial'], record['codigo_final'],
                   record['classe_inicial'], record['classe_final'])
            group = row_lookup[key]
            data = {'ID_TRANS': group['id'], 'SITUACAO': record['situacao'],
                    'LEGENDA': record['legenda'], 'DEIXOU_SER': record['deixou_ser'],
                    'TORNOU_SE': record['tornou_se'], 'AREA_M2': area,
                    'AREA_HA': area / 10000.,
                    'PCT_AREA': 100 * area / summary['area_total_m2']}
            batch[fid] = {index[name]: val for name, val in data.items()}
            if len(batch) >= 1000:
                if not provider.changeAttributeValues(batch):
                    raise OSError('Falha ao atualizar atributos da monitoria.')
                batch.clear()
                if progress:
                    progress(None)
        if batch and not provider.changeAttributeValues(batch):
            raise OSError('Falha ao gravar os atributos finais.')
        result_layer = None
        provider = None
        gc.collect()
        if cancelled and cancelled():
            raise InterruptedError('Monitoria vetorial cancelada.')
        stage_csv = os.path.join(staging, 'transicoes.csv')
        stage_matrix = os.path.join(staging, 'matriz.csv')
        stage_txt = os.path.join(staging, 'resumo.txt')
        write_reports(stage_csv, stage_matrix, stage_txt, summary,
                      title=title, initial=initial, final=final,
                      crs=before.crs().authid() or before.crs().description(),
                      input_sources=[before.name(), after.name()],
                      excluded=[f'{omitted_initial} feições do mapa inicial sem classe/geometria',
                                f'{omitted_final} feições do mapa final sem classe/geometria'])
        if cancelled and cancelled():
            raise InterruptedError('Monitoria vetorial cancelada.')
        pairs = [(tmp_gpkg, destination),
                 (stage_csv, basename + '_transicoes.csv'),
                 (stage_matrix, basename + '_matriz.csv'),
                 (stage_txt, basename + '_resumo.txt')]
        _publish_set(pairs, parent)
        summary['mapa'] = destination
        summary['csv'] = pairs[1][1]
        summary['matriz'] = pairs[2][1]
        summary['txt'] = pairs[3][1]
        summary['omitidas_inicial'] = omitted_initial
        summary['omitidas_final'] = omitted_final
        if progress:
            progress(100)
        return summary
    finally:
        result_layer = None
        intersection = None
        mem_initial = None
        mem_final = None
        gc.collect()
        shutil.rmtree(staging, ignore_errors=True)
