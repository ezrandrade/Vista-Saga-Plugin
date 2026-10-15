"""Combinação de camadas poligonais independentes pelo cruzamento das geometrias.

QGIS 4 / GDAL: mantém os códigos e legendas, sem pesos ou notas.
Apenas a cobertura comum recebe IDs; fontes não são editadas.
"""
import os
import shutil
import tempfile
from collections import defaultdict

from .combination_core import (normalized_code, combination_index,
                               composition_rows, write_combination_reports)


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
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsGeometry, QgsFeature, QgsField, QgsVectorLayer, QgsSpatialIndex
    temporary = QgsVectorLayer('MultiPolygon', 'Mapa temporário', 'memory')
    temporary.setCrs(source.crs())
    if not temporary.isValid():
        raise RuntimeError('Falha na criação da camada temporária.')
    code_name, label_name = f'C{index:02d}', f'L{index:02d}'
    provider = temporary.dataProvider()
    if not provider.addAttributes([QgsField(code_name, QVariant.String),
                                   QgsField(label_name, QVariant.String)]):
        raise RuntimeError('Falha ao criar os campos temáticos temporários.')
    temporary.updateFields()
    feats = []
    index = QgsSpatialIndex()
    geometries = {}
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
            if not crossing.isEmpty() and crossing.area() > max(
                    1e-14, min(geom.area(), prior.area()) * 1e-10):
                raise ValueError(f'{source.name()}: polígonos temáticos se sobrepõem '
                                 f'(feições {prior_id} e {feat.id()}). '
                                 'Corrija a topologia antes de combinar para não duplicar áreas.')
        index.addFeature(feat)
        geometries[feat.id()] = QgsGeometry(geom)
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
    temporary.updateExtents()
    if not temporary.featureCount():
        raise ValueError(f'{source.name()}: nenhuma classe válida foi encontrada.')
    return temporary


def run_vector_combination(sources, fields, labels, destination, *, progress=None, cancelled=None):
    """Cria GPKG e relatórios, combinando polígonos por interseção de N mapas."""
    from qgis.PyQt.QtCore import QVariant
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
        for idx, (layer, field, legend) in enumerate(zip(sources, fields, labels), 1):
            prepared.append(_make_thematic(layer, field, legend, idx, cancelled))
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
                raise RuntimeError(f'Falha na interseção do mapa {idx}: {exc}') from exc
            joined = QgsVectorLayer(str(processed['OUTPUT']), 'Mapas combinados', 'ogr')
            if not joined.isValid() or joined.featureCount() == 0:
                raise ValueError('Não existe cobertura comum aos mapas selecionados.')
            required = [f'C{j:02d}' for j in range(1,idx+1)]
            if any(col not in joined.fields().names() for col in required):
                raise RuntimeError('Campos das classes não foram preservados pela interseção.')
            if progress:progress(15+int(45*(idx-1)/(len(sources)-1)))
        gpkg = os.path.join(staging, 'combinacao.gpkg')
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
        options.fileEncoding = 'UTF-8'
        options.layerName = 'combinacao_mapas'
        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            joined, gpkg, QgsProject.instance().transformContext(), options)
        if int(result[0]) != 0:
            raise OSError('Erro ao gravar GeoPackage temporário: ' + str(result))
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
            key = tuple(normalized_code(feat[f'C{j:02d}']) for j in range(1,len(fields)+1))
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
                    legend = feat[f'L{j:02d}']
                    legend_map[code] = str(legend) if legend else f'Classe {code}'
                elif feat[f'L{j:02d}'] and legend_map[code] != str(feat[f'L{j:02d}']):
                    raise ValueError(f'Mapa {j}: código {code} possui legendas inconsistentes.')
        ids = combination_index(counts)
        rows = composition_rows(counts, names, vector=True)
        additional = [QgsField('ID_COMB', QVariant.Int), QgsField('LEGENDA', QVariant.String),
                      QgsField('AREA_M2', QVariant.Double), QgsField('AREA_HA', QVariant.Double),
                      QgsField('PCT_AREA', QVariant.Double)]
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
                                  area_method='QgsDistanceArea para CRS geográfico; unidades projetadas convertidas para m².')
        if cancelled and cancelled():
            raise InterruptedError('Combinação cancelada.')
        _publish_set(list(zip((gpkg,staged_csv,staged_txt), destinations)), parent)
        if progress:progress(100)
        return {'output':destinations[0], 'csv':destinations[1],'txt':destinations[2],
                'combinations':len(rows),'features':len(feature_data),
                'area_ha':total_area/10000,'rows':rows}
    finally:
        output = None
        joined = None
        prepared.clear()
        shutil.rmtree(staging,ignore_errors=True)
