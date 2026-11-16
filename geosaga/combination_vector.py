"""Combinação de camadas poligonais independentes pelo cruzamento das geometrias.

QGIS 4 / GDAL: mantém os códigos e legendas, sem pesos ou notas.
Apenas a cobertura comum recebe IDs; fontes não são editadas.
"""
import os
import shutil
import tempfile
from collections import defaultdict

from .combination_core import (normalized_code, combination_index,
                               composition_rows, write_combination_reports,
                               classify_overlap, sliver_report_lines, SLIVER_WIDTH_M,
                               is_residue, residue_report_lines)
from .errors import log_exception
from .i18n import tr

MAX_LISTED_OVERLAPS = 10


def code_field(position):
    """Campo do código da classe do mapa na posição dada (COD_01, COD_02…).

    Mesmo prefixo das colunas do _combinacoes.csv. Até a 1.1.0: C01, C02…"""
    return f'COD_{position:02d}'


def legend_field(position):
    """Campo da legenda da classe do mapa na posição dada (LEG_01…). Até a 1.1.0: L01…"""
    return f'LEG_{position:02d}'


def validate_vector_sources(sources, fields, labels, destination):
    from qgis.core import Qgis, QgsVectorLayer
    if len(sources) < 2 or len(sources) != len(fields) or len(sources) != len(labels):
        raise ValueError('Selecione duas ou mais camadas, cada uma com seu campo temático.')
    if len({id(layer) for layer in sources}) != len(sources):
        raise ValueError('Não repita a mesma camada em uma combinação.')
    crs = None
    for layer, field, name in zip(sources, fields, labels):
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            raise ValueError('Uma camada vetorial de entrada é inválida.')
        if layer.geometryType() != Qgis.GeometryType.Polygon:
            raise ValueError(f'{layer.name()}: somente polígonos são aceitos.')
        if layer.isEditable():
            raise ValueError(f'{layer.name()}: salve as edições pendentes antes de combinar.')
        if not layer.crs().isValid() or (crs and layer.crs() != crs):
            raise ValueError('Todos os mapas vetoriais devem possuir o mesmo SRC válido.')
        crs = layer.crs()
        if not field or field not in layer.fields().names():
            raise ValueError(f'{layer.name()}: campo de classe não encontrado ({field}).')
        if name and name not in layer.fields().names():
            raise ValueError(f'{layer.name()}: campo de legenda não encontrado ({name}).')
        if layer.featureCount() == 0:
            raise ValueError(f'{layer.name()}: a camada não contém feições.')
    dest = os.path.abspath(destination)
    if not dest.lower().endswith('.gpkg') or not os.path.isdir(os.path.dirname(dest)):
        raise ValueError('Defina um GeoPackage (.gpkg) em uma pasta existente.')
    for layer in sources:
        original = layer.source().split('|',1)[0]
        if os.path.isfile(original) and os.path.normcase(os.path.realpath(original)) == os.path.normcase(os.path.realpath(dest)):
            raise ValueError('A saída não pode substituir uma camada de entrada.')
    return dest


def _make_thematic(source, field, label_field, index, cancelled):
    """Copia a camada com os campos temáticos C<n>/L<n>, conferindo sobreposições.

    Devolve (camada temporária, estatística das lascas toleradas). Sobreposições
    internas mais espessas que SLIVER_WIDTH_M bloqueiam, listando todos os pares.
    """
    from qgis.PyQt.QtCore import QMetaType
    from qgis.core import (Qgis, QgsGeometry, QgsFeature, QgsField, QgsVectorLayer,
                           QgsSpatialIndex, QgsUnitTypes)
    temporary = QgsVectorLayer('MultiPolygon', 'Mapa temporário', 'memory')
    temporary.setCrs(source.crs())
    if not temporary.isValid():
        raise RuntimeError('Falha na criação da camada temporária.')
    code_name, label_name = code_field(index), legend_field(index)
    provider = temporary.dataProvider()
    if not provider.addAttributes([QgsField(code_name, QMetaType.Type.QString),
                                   QgsField(label_name, QMetaType.Type.QString)]):
        raise RuntimeError('Falha ao criar os campos temáticos temporários.')
    temporary.updateFields()
    # Metros -> unidades do SRC (em graus, conversão aproximada do próprio QGIS).
    factor = QgsUnitTypes.fromUnitToUnitFactor(Qgis.DistanceUnit.Meters, source.crs().mapUnits())
    if not factor or factor <= 0:
        factor = 1.0
    tolerance = SLIVER_WIDTH_M * factor
    feats = []
    index = QgsSpatialIndex()
    geometries = {}
    codes = {}
    tolerated_area = 0.0
    slivers = 0
    rejected = []
    for feat in source.getFeatures():
        if cancelled and cancelled():
            raise InterruptedError('Combinação vetorial cancelada.')
        code = normalized_code(feat[field])
        if code is None:
            continue
        geom = feat.geometry()
        if geom.isNull() or geom.isEmpty():
            continue
        if not geom.isGeosValid():
            raise ValueError(f'{source.name()}: geometria inválida na feição {feat.id()}. '
                             'Execute Corrigir geometrias no QGIS.')
        for prior_id in index.intersects(geom.boundingBox()):
            prior = geometries[prior_id]
            if not geom.intersects(prior):
                continue
            crossing = geom.intersection(prior)
            if crossing.isEmpty():
                continue
            pieces = [(part.area(), part.length()) for part in crossing.asGeometryCollection()
                      if part.type() == Qgis.GeometryType.Polygon]
            area_ok, count, area_bad, widest = classify_overlap(pieces, tolerance)
            tolerated_area += area_ok
            slivers += count
            if area_bad:
                rejected.append((prior_id, feat.id(), codes[prior_id], code, area_bad, widest))
        index.addFeature(feat)
        geometries[feat.id()] = QgsGeometry(geom)
        codes[feat.id()] = code
        value = feat[label_field] if label_field else None
        legend = (str(value).strip() if value is not None and not (
            hasattr(value, 'isNull') and value.isNull()) else '')
        if not legend:
            legend = str(feat[field]).strip() if isinstance(feat[field], str) else f'Classe {code}'
        geo = QgsGeometry(geom)
        if not geo.isMultipart():
            geo.convertToMultiType()
        copied = QgsFeature(temporary.fields())
        copied.setAttributes([code, legend])
        copied.setGeometry(geo)
        feats.append(copied)
        if len(feats) >= 500:
            if not provider.addFeatures(feats)[0]:
                raise OSError('Erro ao copiar feições para a combinação.')
            feats.clear()
    if feats and not provider.addFeatures(feats)[0]:
        raise OSError('Falha ao gravar feições temporárias.')
    if rejected:
        raise ValueError(_overlap_message(source.name(), rejected, factor))
    temporary.updateExtents()
    if not temporary.featureCount():
        raise ValueError(f'{source.name()}: nenhuma classe válida foi encontrada.')
    return temporary, {'name': source.name(), 'count': slivers,
                       'area_m2': tolerated_area / (factor * factor)}


def _overlap_message(name, rejected, factor):
    """Lista os pares que se sobrepõem acima da tolerância, com área e largura."""
    lines = [tr('{0}: {1} par(es) de polígonos da mesma camada se sobrepõem com largura média '
                'de pelo menos {2} cm. Corrija a topologia antes de combinar, para não '
                'duplicar áreas.').format(name, len(rejected), f'{SLIVER_WIDTH_M * 100:g}')]
    for first, second, code_a, code_b, area, width in rejected[:MAX_LISTED_OVERLAPS]:
        lines.append(tr('- feições {0} e {1} (classes {2} e {3}): {4} m², largura média {5} m').format(
            first, second, code_a, code_b, f'{area / (factor * factor):.4f}',
            f'{width / factor:.3f}'))
    if len(rejected) > MAX_LISTED_OVERLAPS:
        lines.append(tr('… e mais {0} pares.').format(len(rejected) - MAX_LISTED_OVERLAPS))
    return '\n'.join(lines)


def _absorb_residues(layer, staging, crs, feedback):
    """Incorpora os resíduos do cruzamento ao vizinho de maior fronteira comum.

    Decisão de método da 1.2.0 (opção C). Separa as partes do resultado, marca as
    de largura média < SLIVER_WIDTH_M e usa "Eliminar polígonos selecionados" do
    QGIS (modo: maior fronteira comum), que funde cada resíduo ao vizinho e mantém
    os atributos do vizinho. Assim, a área total não muda e não sobram combinações
    que só existem em tiras microscópicas. Resíduos sem vizinho são excluídos.
    """
    from qgis.core import Qgis, QgsApplication, QgsUnitTypes, QgsVectorLayer
    import processing

    factor = QgsUnitTypes.fromUnitToUnitFactor(Qgis.DistanceUnit.Meters, crs.mapUnits())
    if not factor or factor <= 0:
        factor = 1.0
    tolerance = SLIVER_WIDTH_M * factor
    area_m2 = 1.0 / (factor * factor)
    stats = {'count': 0, 'merged': 0, 'merged_m2': 0.0, 'removed': 0, 'removed_m2': 0.0}

    single_path = os.path.join(staging, 'partes.gpkg')
    processing.run('native:multiparttosingleparts',
                   {'INPUT': layer, 'OUTPUT': single_path}, feedback=feedback)
    singles = QgsVectorLayer(single_path, 'Partes', 'ogr')
    if not singles.isValid():
        raise RuntimeError('Falha ao separar as partes do resultado.')
    residues = {}
    for feat in singles.getFeatures():
        geom = feat.geometry()
        if geom.isNull() or is_residue(geom.area(), geom.length(), tolerance):
            residues[feat.id()] = 0.0 if geom.isNull() else geom.area()
    stats['count'] = len(residues)
    if not residues:
        return singles, stats
    if len(residues) == singles.featureCount():
        raise ValueError('Todas as partes do resultado têm menos de 1 cm de largura média; '
                         'confira o SRC e as unidades das camadas.')

    registry = QgsApplication.processingRegistry()
    algorithm = next((name for name in ('native:eliminateselectedpolygons',
                                        'qgis:eliminateselectedpolygons')
                      if registry.algorithmById(name) is not None), None)
    if algorithm is None:
        raise RuntimeError('Ferramenta "Eliminar polígonos selecionados" indisponível no QGIS.')
    singles.selectByIds(list(residues))
    merged_path = os.path.join(staging, 'sem_residuos.gpkg')
    processing.run(algorithm, {'INPUT': singles, 'MODE': 2, 'OUTPUT': merged_path},
                   feedback=feedback)                      # 2 = maior fronteira comum
    merged = QgsVectorLayer(merged_path, 'Sem resíduos', 'ogr')
    if not merged.isValid():
        raise RuntimeError('Falha ao incorporar os resíduos.')

    # O que não pôde ser fundido (resíduo isolado) é excluído e registrado.
    leftover = {}
    for feat in merged.getFeatures():
        geom = feat.geometry()
        if geom.isNull() or is_residue(geom.area(), geom.length(), tolerance):
            leftover[feat.id()] = 0.0 if geom.isNull() else geom.area()
    if leftover:
        if not merged.dataProvider().deleteFeatures(list(leftover)):
            raise OSError('Falha ao excluir resíduos sem vizinho.')
    total = sum(residues.values())
    stats['removed'] = len(leftover)
    stats['removed_m2'] = sum(leftover.values()) * area_m2
    stats['merged'] = len(residues) - len(leftover)
    stats['merged_m2'] = max(total - sum(leftover.values()), 0.0) * area_m2
    return merged, stats


def run_vector_combination(sources, fields, labels, destination, *, progress=None, cancelled=None):
    """Cria GPKG e relatórios, combinando polígonos por interseção de N mapas."""
    from qgis.PyQt.QtCore import QMetaType
    from qgis.core import (QgsField, QgsProcessingFeedback, QgsProject, QgsVectorLayer,
                           QgsVectorFileWriter)
    from .vector_evaluation_writer import _area_function, _publish_set
    import processing

    destination = validate_vector_sources(sources, fields, labels, destination)
    parent = os.path.dirname(destination)
    root = os.path.splitext(destination)[0]
    destinations = (destination, root+'_combinacoes.csv', root+'_resumo.txt')
    staging = tempfile.mkdtemp(prefix='.vistasaga_comb_vector_', dir=parent)
    prepared = []
    joined = None
    output = None
    try:
        sliver_stats = []
        for idx, (layer, field, legend) in enumerate(zip(sources, fields, labels), 1):
            thematic, stats = _make_thematic(layer, field, legend, idx, cancelled)
            prepared.append(thematic)
            sliver_stats.append(stats)
            if progress:progress(int(15*idx/len(sources)))
        joined = prepared[0]
        class Feedback(QgsProcessingFeedback):
            def isCanceled(self):
                return bool((cancelled and cancelled()) or super().isCanceled())
        for idx, source in enumerate(prepared[1:], 2):
            if cancelled and cancelled():
                raise InterruptedError('Combinação vetorial cancelada.')
            path = os.path.join(staging, f'intersecao_{idx}.gpkg')
            try:
                processed = processing.run('native:intersection', {
                    'INPUT': joined, 'OVERLAY': source, 'OUTPUT': path,
                    'INPUT_FIELDS': [], 'OVERLAY_FIELDS': [], 'OVERLAY_FIELDS_PREFIX': ''
                }, feedback=Feedback())
            except Exception as exc:
                if cancelled and cancelled():
                    raise InterruptedError('Combinação vetorial cancelada.') from exc
                log_exception()
                raise RuntimeError(f'Falha na interseção do mapa {idx}: {exc}') from exc
            joined = QgsVectorLayer(str(processed['OUTPUT']), 'Mapas combinados', 'ogr')
            if not joined.isValid() or joined.featureCount() == 0:
                raise ValueError('Não existe cobertura comum aos mapas selecionados.')
            required = [code_field(j) for j in range(1,idx+1)]
            if any(col not in joined.fields().names() for col in required):
                raise RuntimeError('Campos das classes não foram preservados pela interseção.')
            if progress:progress(15+int(45*(idx-1)/(len(sources)-1)))
        joined, residue_stats = _absorb_residues(joined, staging, sources[0].crs(), Feedback())
        if progress:progress(62)
        gpkg = os.path.join(staging, 'combinacao.gpkg')
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
        options.fileEncoding = 'UTF-8'
        options.layerName = 'combinacao_mapas'
        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            joined, gpkg, QgsProject.instance().transformContext(), options)
        if int(result[0]) != 0:
            raise OSError(f'Erro ao gravar GeoPackage temporário: {result}')
        joined = None
        output = QgsVectorLayer(gpkg+'|layername=combinacao_mapas', 'Combinação de Mapas', 'ogr')
        if not output.isValid():
            raise RuntimeError('GeoPackage de saída inválido.')
        measure = _area_function(output)
        counts = defaultdict(float)
        names = [dict() for _ in fields]
        feature_data = []
        for feat in output.getFeatures():
            if cancelled and cancelled():
                raise InterruptedError('Combinação cancelada.')
            key = tuple(normalized_code(feat[code_field(j)]) for j in range(1,len(fields)+1))
            if any(v is None for v in key):
                continue
            area = float(measure(feat.geometry()))
            if not 0 <= area < float('inf'):
                raise ValueError(f'Área inválida na feição {feat.id()}.')
            if area <= 0:
                continue
            feature_data.append((feat.id(),key,area))
            counts[key] += area
            for j,(code, legend_map) in enumerate(zip(key,names),1):
                if code not in legend_map:
                    legend = feat[legend_field(j)]
                    legend_map[code] = str(legend) if legend else f'Classe {code}'
                elif feat[legend_field(j)] and legend_map[code] != str(feat[legend_field(j)]):
                    raise ValueError(f'Mapa {j}: código {code} possui legendas inconsistentes.')
        ids = combination_index(counts)
        rows = composition_rows(counts, names, vector=True)
        additional = [QgsField('ID_COMB', QMetaType.Type.Int), QgsField('LEGENDA', QMetaType.Type.QString),
                      QgsField('AREA_M2', QMetaType.Type.Double), QgsField('AREA_HA', QMetaType.Type.Double),
                      QgsField('PCT_AREA', QMetaType.Type.Double)]
        provider = output.dataProvider()
        if not provider.addAttributes(additional):
            raise OSError('Erro ao adicionar atributos da combinação.')
        output.updateFields()
        index = {name:output.fields().indexOf(name) for name in
                 ('ID_COMB','LEGENDA','AREA_M2','AREA_HA','PCT_AREA')}
        if -1 in index.values():
            raise OSError('Atributos do resultado não foram encontrados.')
        total_area = sum(counts.values())
        batch = {}
        for fid,key,area in feature_data:
            label = ' | '.join(names[i][code] for i,code in enumerate(key))
            values = (ids[key],label,area,area/10000,100*area/total_area)
            batch[fid] = {index[name]:value for name,value in zip(index,values)}
            if len(batch) >= 500:
                if not provider.changeAttributeValues(batch):
                    raise OSError('Falha ao atualizar área e classes.')
                batch.clear()
        if batch and not provider.changeAttributeValues(batch):
            raise OSError('Falha ao atualizar últimos atributos.')
        # Libere a conexão OGR antes de publicar o arquivo no Windows.
        provider = None
        output = None
        import gc
        gc.collect()
        staged_csv = os.path.join(staging, 'combinacoes.csv')
        staged_txt = os.path.join(staging, 'resumo.txt')
        write_combination_reports(staged_csv, staged_txt, rows,
                                  [layer.name() for layer in sources], mode='Vetorial',
                                  crs=sources[0].crs().authid(),
                                  area_method='QgsDistanceArea para CRS geográfico; unidades projetadas convertidas para m².',
                                  notes=sliver_report_lines(sliver_stats)
                                  + residue_report_lines(residue_stats))
        if cancelled and cancelled():
            raise InterruptedError('Combinação cancelada.')
        _publish_set(list(zip((gpkg,staged_csv,staged_txt), destinations)), parent)
        if progress:progress(100)
        return {'output':destinations[0], 'csv':destinations[1],'txt':destinations[2],
                'combinations':len(rows),'features':len(feature_data),
                'area_ha':total_area/10000,'rows':rows,'slivers':sliver_stats,
                'residues':residue_stats}
    finally:
        output = None
        joined = None
        prepared.clear()
        shutil.rmtree(staging,ignore_errors=True)
