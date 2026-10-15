"""Avaliação Espacial por sobreposição de camadas poligonais independentes.

Fluxo: selecionar um atributo por mapa -> copiar somente geometrias e chave da
classe -> interseção geométrica sucessiva -> calcular os mesmos pesos e notas
usados pela avaliação de atributos -> gravar novo GeoPackage. Nenhuma camada de
origem é editada. A saída cobre apenas a área comum a TODOS os mapas.
"""
import os
import shutil
import tempfile

from .vector_evaluation_core import category_key, validate_criteria


def validate_overlay_plan(criteria, min_layers=2):
    """Parte verificável sem PyQGIS: cada mapa ocupa exatamente um critério."""
    if len(criteria) < min_layers:
        raise ValueError('Adicione pelo menos duas camadas poligonais independentes.')
    ids = [c.get('layer_id') for c in criteria]
    if any(not ident for ident in ids) or len(set(ids)) != len(ids):
        raise ValueError('Cada camada pode participar uma vez. Para vários campos da mesma camada, use Avaliação por atributos.')
    names = [c.get('field') for c in criteria]
    if len(set(names)) != len(names):
        raise ValueError('Os identificadores dos critérios não podem ser repetidos.')
    if any(not c.get('source_field') for c in criteria):
        raise ValueError('Cada mapa precisa de um campo de classificação.')
    return ids


def validate_source_layers(criteria, project):
    from qgis.core import Qgis, QgsVectorLayer
    validate_overlay_plan(criteria)
    sources = []
    reference_crs = None
    for criterion in criteria:
        layer = project.mapLayer(criterion['layer_id'])
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            raise ValueError(f'Camada não disponível no projeto: {criterion.get("label", criterion["field"])}.')
        if layer.geometryType() != Qgis.GeometryType.Polygon:
            raise ValueError(f'{layer.name()}: apenas camadas poligonais são aceitas.')
        if layer.isEditable():
            raise ValueError(f'{layer.name()}: salve ou descarte edições pendentes antes da avaliação.')
        if criterion['source_field'] not in layer.fields().names():
            raise ValueError(f'{layer.name()}: o campo {criterion["source_field"]} não existe mais.')
        if not layer.crs().isValid():
            raise ValueError(f'{layer.name()}: o SRC deve estar definido.')
        if reference_crs is None:
            reference_crs = layer.crs()
        elif layer.crs() != reference_crs:
            raise ValueError('As camadas precisam utilizar o mesmo SRC. Reprojete-as previamente no QGIS.')
        if layer.featureCount() == 0:
            raise ValueError(f'{layer.name()}: a camada não contém feições.')
        sources.append(layer)
    return sources


def _single_criterion_layer(source, criterion, cancelled=None, progress=None):
    """Cópia temporária com apenas um campo-chave, para evitar colisões de nomes."""
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsFeature, QgsField, QgsVectorLayer, QgsGeometry

    crs_id = source.crs().authid()
    uri = 'MultiPolygon?crs=' + crs_id if crs_id else 'MultiPolygon'
    result = QgsVectorLayer(uri, 'criterio_' + criterion['field'], 'memory')
    result.setCrs(source.crs())
    if not result.isValid():
        raise OSError('Não foi possível criar a camada vetorial temporária.')
    provider = result.dataProvider()
    if not provider.addAttributes([QgsField(criterion['field'], QVariant.String, len=254)]):
        raise OSError('Não foi possível criar o campo do critério temporário.')
    result.updateFields()
    pending = []
    count = 0
    for original in source.getFeatures():
        if cancelled and cancelled():
            raise InterruptedError('Avaliação cancelada pelo usuário.')
        geom = original.geometry()
        if geom.isNull() or geom.isEmpty():
            raise ValueError(f'{source.name()}: feição {original.id()} sem geometria. Corrija a camada primeiro.')
        if not geom.isGeosValid():
            raise ValueError(f'{source.name()}: geometria inválida na feição {original.id()}. '
                             'Execute Corrigir geometrias no QGIS antes da avaliação.')
        geom = QgsGeometry(geom)
        if not geom.isMultipart():
            geom.convertToMultiType()
        feat = QgsFeature(result.fields())
        feat.setGeometry(geom)
        feat.setAttributes([category_key(original[criterion['source_field']])])
        pending.append(feat)
        count += 1
        if len(pending) == 500:
            if not provider.addFeatures(pending)[0]:
                raise OSError(f'Falha ao copiar as geometrias de {source.name()}.')
            pending.clear()
        if progress and count % 500 == 0:
            progress(None)
    if pending and not provider.addFeatures(pending)[0]:
        raise OSError(f'Falha ao copiar as geometrias de {source.name()}.')
    result.updateExtents()
    return result


def evaluate_overlay(criteria, scale, destination, project, progress=None, cancelled=None,
                     report_csv=True, report_txt=True):
    """Sobrepõe por interseção, sem reprojetar nem alterar os mapas originais.

    Resultado: campo C01/C02... com classes originais, NOTA_XX, AVALIACAO,
    VALIDO e MOTIVO; regiões fora da interseção de TODAS as camadas não entram.
    """
    from qgis.core import QgsProcessingFeedback, QgsVectorLayer
    import processing
    from .vector_evaluation_writer import evaluate_vector_layer

    validate_overlay_plan(criteria)
    rules = validate_criteria([
        {'field': c['field'], 'weight': c['weight'], 'categories': set(c['counts']),
         'notes': dict(c['notes']), 'excluded': set(c['excluded'])}
        for c in criteria], scale=scale)
    sources = validate_source_layers(criteria, project)
    destination = os.path.abspath(destination)
    if not destination.lower().endswith('.gpkg'):
        raise ValueError('O resultado deve ter extensão .gpkg.')
    parent = os.path.dirname(destination)
    if not os.path.isdir(parent):
        raise ValueError('A pasta de saída não existe.')
    paths = [os.path.abspath(layer.source().split('|', 1)[0]) for layer in sources]
    if destination in paths:
        raise ValueError('A saída não pode substituir qualquer uma das camadas de entrada.')

    class Feedback(QgsProcessingFeedback):
        def isCanceled(self):
            return bool((cancelled and cancelled()) or super().isCanceled())

    feedback = Feedback()
    staging = tempfile.mkdtemp(prefix='.vistasaga_intersecao_', dir=parent)
    joined = None
    prepared = None
    try:
        prepared = _single_criterion_layer(sources[0], criteria[0], cancelled, progress)
        joined = prepared
        total = len(criteria) - 1
        for i, (source, criterion) in enumerate(zip(sources[1:], criteria[1:]), start=1):
            if cancelled and cancelled():
                raise InterruptedError('Avaliação cancelada pelo usuário.')
            current = _single_criterion_layer(source, criterion, cancelled, progress)
            intersection_file = os.path.join(staging, f'intersecao_{i:02d}.gpkg')
            try:
                output = processing.run('native:intersection', {
                    'INPUT': joined, 'OVERLAY': current,
                    'INPUT_FIELDS': [], 'OVERLAY_FIELDS': [],
                    'OVERLAY_FIELDS_PREFIX': '', 'OUTPUT': intersection_file,
                }, feedback=feedback)
            except Exception as exc:
                if cancelled and cancelled():
                    raise InterruptedError('Avaliação cancelada pelo usuário.') from exc
                raise RuntimeError('A interseção geométrica falhou. Verifique se as geometrias são válidas. '
                                   f'Detalhes: {exc}') from exc
            if cancelled and cancelled():
                raise InterruptedError('Avaliação cancelada pelo usuário.')
            previous = joined
            joined = QgsVectorLayer(str(output['OUTPUT']), 'Interseção de mapas', 'ogr')
            current = None
            if not joined.isValid():
                raise OSError('A camada intermediária de interseção não pôde ser aberta.')
            if not joined.featureCount():
                raise ValueError('Os mapas selecionados não possuem área de interseção comum.')
            expected = [item['field'] for item in criteria[:i + 1]]
            if any(field not in joined.fields().names() for field in expected):
                raise RuntimeError('Campos de critérios foram perdidos durante a interseção.')
            previous = None
            if progress:
                progress(min(65, int(65 * i / total)))
        summary = evaluate_vector_layer(joined, [
            {'field': c['field'], 'weight': c['weight'], 'categories': set(c['counts']),
             'notes': dict(c['notes']), 'excluded': set(c['excluded'])}
            for c in criteria], scale, destination,
            progress=(lambda value: progress(65 + int(value * .35))) if progress else None,
            cancelled=cancelled, report_csv=report_csv, report_txt=report_txt,
            report_criteria=[{'name': c.get('label', c['field']), 'source': source.source()}
                             for c, source in zip(criteria, sources)])
        summary['camadas'] = len(criteria)
        summary['tipo_cobertura'] = 'intersecao'
        return summary
    finally:
        joined = None
        prepared = None
        # Intermediários não pertencem ao projeto nem substituem as fontes.
        shutil.rmtree(staging, ignore_errors=True)
