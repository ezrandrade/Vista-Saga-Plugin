"""Vetorização de mapas RS2 do Vista SAGA, usando GDAL/OGR do QGIS 4.

Cria polígonos por regiões contíguas de pixels de mesmo código.
Nunca interpreta as cores RGB como valores matriciais.
"""
from pathlib import Path
import os
import shutil
import tempfile

from .rs2_format import RS2Error, RS2Reader
from .rs2_converter import convert_rs2_to_tif, _gdal

# Formatos vetoriais de arquivo com suporte amplo em instalações GDAL/QGIS.
VECTOR_FORMATS = {
    '.gpkg': ('GPKG', 'GeoPackage'),
    '.shp': ('ESRI Shapefile', 'ESRI Shapefile'),
    '.geojson': ('GeoJSON', 'GeoJSON'),
    '.fgb': ('FlatGeobuf', 'FlatGeobuf'),
}


def vector_format(extension):
    result = VECTOR_FORMATS.get(str(extension).lower())
    if result is None:
        raise RS2Error('Formato vetorial não suportado. Selecione GeoPackage, Shapefile, GeoJSON ou FlatGeobuf.')
    return result


def vector_family(path):
    """Arquivos da camada que pertencem ao formato escolhido (sem metadados alheios)."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == '.shp':
        return [p.with_suffix(ext) for ext in
                ('.shp', '.shx', '.dbf', '.prj', '.cpg', '.qix', '.sbn', '.sbx')]
    if suffix == '.gpkg':
        return [p, Path(str(p) + '-wal'), Path(str(p) + '-shm')]
    if suffix in ('.geojson', '.fgb'):
        return [p]
    vector_format(suffix)
    return [p]


def vector_conflicts(path):
    return [p for p in vector_family(path) if p.exists()]


def _publish_vector(stage, target):
    """Substituição coordenada dos arquivos vetoriais, com rollback."""
    stage, target = Path(stage), Path(target)
    incoming, outputs = vector_family(stage), vector_family(target)
    if not stage.is_file():
        raise RS2Error('A camada vetorial temporária não foi produzida.')
    if stage.suffix.lower() == '.shp':
        for ext in ('.shx', '.dbf'):
            if not stage.with_suffix(ext).is_file():
                raise RS2Error(f'Arquivo obrigatório do Shapefile não produzido: {ext}')
    if stage.resolve() == target.resolve():
        raise RS2Error('O arquivo temporário não pode ser a própria saída.')
    backup_folder = Path(tempfile.mkdtemp(prefix='.vista_vector_backup_', dir=target.parent))
    backups, published = [], []
    keep_backups = False
    try:
        for i, p in enumerate(outputs):
            if p.is_dir():
                raise RS2Error(f'Não é possível substituir uma pasta: {p}')
            if p.exists():
                old = backup_folder / f'{i}.bak'
                os.replace(p, old)
                backups.append((old, p))
        for p, output in zip(incoming, outputs):
            if p.is_file():
                os.replace(p, output)
                published.append(output)
    except Exception as exc:
        for p in reversed(published):
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
        failed = []
        for old, p in reversed(backups):
            try:
                os.replace(old, p)
            except OSError as rollback_exc:
                failed.append(str(rollback_exc))
        keep_backups = bool(failed)
        note = f' Cópias de segurança: {backup_folder}' if failed else ''
        raise RS2Error(f'Falha na substituição da saída vetorial: {exc}.{note}') from exc
    finally:
        if not keep_backups:
            shutil.rmtree(backup_folder, ignore_errors=True)


def class_attributes(header):
    """Valores das três colunas, preservando o índice e os RGB originais."""
    values = []
    for code, label in enumerate(header.labels):
        rgb = header.colors[code][:3]
        values.append((code, label, '#' + ''.join(f'{int(c):02X}' for c in rgb)))
    return values


def _layer_name(path):
    # Simples, compatível com camadas do GPKG; nomes longos desnecessários.
    return 'rs2_' + ''.join(c if c.isalnum() or c == '_' else '_'
                         for c in Path(path).stem)[:45]


def convert_rs2_to_vector(rs2_path, vector_path, epsg='', progress=None,
                          ignore_background=True, eight_connected=False):
    """Converte RS2 diretamente para polígonos em formato vetorial GDAL.

    `progress(done, total)` retorna False para cancelar. O TIFF temporário é
    interno, descartado ao terminar. Não dissolve feições desconectadas;
    opcionalmente considera pixels diagonais adjacentes (8 conexões).
    """
    source = Path(rs2_path)
    target = Path(vector_path)
    if not source.is_file() or source.suffix.lower() != '.rs2':
        raise RS2Error('Selecione um arquivo RS2 existente para vetorização.')
    driver_name, _ = vector_format(target.suffix)
    from osgeo import ogr, osr
    if target.resolve() == source.resolve():
        raise RS2Error('A saída não pode sobrescrever o mapa original.')
    target.parent.mkdir(parents=True, exist_ok=True)
    driver = ogr.GetDriverByName(driver_name)
    if driver is None:
        raise RS2Error(f'Driver GDAL/OGR não disponível nesta instalação: {driver_name}.')
    h = RS2Reader(source).header
    codes = class_attributes(h)
    gdal, _ = _gdal()

    def notify(value):
        if progress is not None and progress(int(max(0., min(1., value)) * 1000), 1000) is False:
            raise RS2Error('Operação cancelada pelo usuário.')

    with tempfile.TemporaryDirectory(prefix='.vista_vector_', dir=target.parent) as td:
        folder = Path(td)
        temp_tif = folder / 'categories.tif'
        stage = folder / target.name
        work_gpkg = folder / 'work_classes.gpkg'
        raster = None
        dataset = None
        layer = None
        try:
            convert_rs2_to_tif(
                source, temp_tif, epsg,
                lambda row, total: notify(.32 * row / max(total, 1)) is None,
                mark_background_nodata=ignore_background,
            )
            notify(.34)
            raster = gdal.Open(str(temp_tif), gdal.GA_ReadOnly)
            if raster is None:
                raise RS2Error('Não foi possível reabrir o raster temporário.')
            band = raster.GetRasterBand(1)
            # Sem mask de NoData: inclui a classe 0, se solicitado.
            mask = band.GetMaskBand() if ignore_background else None
            # OGR Polygonize escreve a coluna CODIGO primeiro. Os demais
            # campos exigem SetFeature, operação não suportada por todos os
            # drivers (ex.: arquivos de escrita sequencial FlatGeobuf).
            # GeoPackage temporário garante atualizações; VectorTranslate
            # exporta o resultado pronto ao formato pedido.
            gpkg_driver = ogr.GetDriverByName('GPKG')
            if gpkg_driver is None:
                raise RS2Error('Driver GDAL GeoPackage indisponível.')
            dataset = gpkg_driver.CreateDataSource(str(work_gpkg))
            if dataset is None:
                raise RS2Error('Não foi possível criar o banco temporário de polígonos.')
            srs = None
            if epsg:
                if not str(epsg).upper().startswith('EPSG:'):
                    raise RS2Error('Selecione um SRC válido na interface do QGIS.')
                srs = osr.SpatialReference()
                if srs.ImportFromEPSG(int(str(epsg).split(':')[1])) != 0 or not srs.IsProjected():
                    raise RS2Error('É necessário informar um SRC projetado confirmado.')
            layer = dataset.CreateLayer(_layer_name(target), srs=srs,
                                        geom_type=ogr.wkbPolygon)
            if layer is None:
                raise RS2Error('Falha ao criar camada vetorial.')
            for name, kind in [('CODIGO', ogr.OFTInteger), ('CLASSE', ogr.OFTString),
                               ('COR_HEX', ogr.OFTString)]:
                field = ogr.FieldDefn(name, kind)
                if name == 'CLASSE' and target.suffix.lower() == '.shp':
                    field.SetWidth(254)
                if name == 'COR_HEX':
                    field.SetWidth(7)
                if layer.CreateField(field) != 0:
                    raise RS2Error(f'Falha ao criar campo {name}.')
            def poly_progress(frac, message, user_data):
                try:
                    notify(.34 + .52 * float(frac))
                    return 1
                except RS2Error:
                    return 0
            options = ['8CONNECTED=8'] if eight_connected else []
            code_field = layer.GetLayerDefn().GetFieldIndex('CODIGO')
            err = gdal.Polygonize(band, mask, layer, code_field, options, poly_progress)
            if err != 0:
                raise RS2Error('Falha ou cancelamento durante a poligonização GDAL.')
            count = layer.GetFeatureCount()
            # Persistir texto/cor sem modificar o campo categórico do GDAL.
            for i, feat in enumerate(layer):
                code = int(feat.GetField('CODIGO'))
                if code < 0 or code >= len(codes):
                    raise RS2Error(f'Código inesperado na vetorização: {code}.')
                _, label, color = codes[code]
                feat.SetField('CLASSE', label)
                feat.SetField('COR_HEX', color)
                if layer.SetFeature(feat) != 0:
                    raise RS2Error(f'Falha ao atualizar os atributos da categoria {code}.')
                if i % 250 == 0:
                    notify(.86 + .13 * i / max(count, 1))
            layer.SyncToDisk()
            layer = None
            dataset = None
            raster = None
            notify(.99)
            if target.suffix.lower() == '.gpkg':
                os.replace(work_gpkg, stage)
            else:
                opts = gdal.VectorTranslateOptions(
                    format=driver_name,
                    layerName=(None if target.suffix.lower() == '.shp'
                               else _layer_name(target)),
                    layerCreationOptions=(['ENCODING=UTF-8']
                                          if target.suffix.lower() == '.shp' else []))
                translated = gdal.VectorTranslate(str(stage), str(work_gpkg), options=opts)
                if translated is None:
                    raise RS2Error(f'Falha na exportação para {driver_name}.')
                translated = None
            _publish_vector(stage, target)
            # A publicação já ocorreu: não considerar cancelamento posterior.
            return target
        finally:
            layer = None
            dataset = None
            raster = None
