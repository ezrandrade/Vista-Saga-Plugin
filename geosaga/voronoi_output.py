"""Saídas vetoriais das Análises Voronoi nos formatos padrão do plugin.

Os mesmos formatos do Conversor de Formatos (``rs2_vector.VECTOR_FORMATS``):
GeoPackage, Shapefile, GeoJSON e FlatGeobuf. A camada é montada primeiro num
GeoPackage de trabalho, que aceita atualização de atributos; os demais
formatos são exportados dele com ``gdal.VectorTranslate``, como no Conversor.
"""
import os

from .rs2_vector import VECTOR_FORMATS, vector_family

LAYER_NAME = 'voronoi_espacial'
DEFAULT_EXTENSION = '.gpkg'


def vector_extension(path_or_extension):
    """Extensão vetorial validada (minúscula), a partir de um caminho ou sufixo."""
    text = str(path_or_extension)
    extension = (os.path.splitext(text)[1] or text).lower()
    if extension not in VECTOR_FORMATS:
        raise ValueError('Formato vetorial não suportado. Selecione GeoPackage, Shapefile, '
                         'GeoJSON ou FlatGeobuf.')
    return extension


def layer_uri(path):
    """Fonte OGR para carregar a camada no QGIS."""
    if str(path).lower().endswith('.gpkg'):
        return f'{path}|layername={LAYER_NAME}'
    return str(path)


def export_vector(work_gpkg, target):
    """Grava ``target`` a partir do GeoPackage de trabalho (mesma pasta de preparo)."""
    extension = vector_extension(target)
    if extension == '.gpkg':
        os.replace(work_gpkg, target)
        return
    from osgeo import gdal
    driver_name = VECTOR_FORMATS[extension][0]
    if gdal.GetDriverByName(driver_name) is None:
        raise RuntimeError(f'Driver GDAL/OGR não disponível nesta instalação: {driver_name}.')
    options = gdal.VectorTranslateOptions(
        format=driver_name,
        layerName=None if extension == '.shp' else LAYER_NAME,
        layerCreationOptions=['ENCODING=UTF-8'] if extension == '.shp' else [])
    translated = gdal.VectorTranslate(str(target), str(work_gpkg), options=options)
    if translated is None:
        raise RuntimeError(f'Falha na exportação para {driver_name}.')
    translated = None
    if not os.path.isfile(target):
        raise RuntimeError(f'Falha na exportação para {driver_name}.')


def output_family(path):
    """Arquivos que compõem uma saída: a família vetorial ou o próprio arquivo."""
    extension = os.path.splitext(str(path))[1].lower()
    if extension in VECTOR_FORMATS:
        return [str(p) for p in vector_family(path)]
    return [str(path)]


def publish_outputs(stage, outputs):
    """Move as saídas preparadas em ``stage`` para os destinos, com reversão.

    Para cada destino, todos os arquivos da família (ex.: .shp, .shx, .dbf,
    .prj, .cpg) existentes são guardados antes; arquivos antigos da família que
    o novo resultado não recria não ficam misturados ao resultado novo.
    """
    backup = os.path.join(stage, '_anteriores')
    os.makedirs(backup, exist_ok=True)
    originals = []
    created = []
    targets = [target for output in outputs for target in output_family(output)]
    try:
        for target in targets:
            if os.path.isfile(target):
                saved = os.path.join(backup, str(len(originals)))
                os.replace(target, saved)
                originals.append((saved, target))
        for target in targets:
            local = os.path.join(stage, os.path.basename(target))
            if os.path.isfile(local):
                os.replace(local, target)
                created.append(target)
        missing = [output for output in outputs if not os.path.isfile(output)]
        if missing:
            raise RuntimeError('Saída não produzida: ' + ', '.join(missing))
    except Exception:
        for path in created:
            if os.path.exists(path):
                os.remove(path)
        for saved, original in originals:
            if os.path.exists(saved):
                os.replace(saved, original)
        raise
    return created
