"""Teste de fumaça do Vista Saga Plugin dentro de um QGIS 4 real (offscreen).

Uso: qrun.sh tests/smoke_qgis.py <pasta_que_contém_geosaga> <pasta_de_saída>
Exercita: carga/descarga do plugin, abertura dos 7 diálogos, algoritmos
Processing e todos os motores numéricos com dados sintéticos.
"""
import json
import os
import shutil
import sys
import traceback

if os.environ.get('QGIS_PY'):  # instalação conda; no OSGeo4W/QGIS o qgis já é importável
    sys.path[:0] = [os.environ['QGIS_PY'], os.environ['QGIS_PY'] + '/plugins']
PLUGIN_PARENT = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
sys.path.insert(0, PLUGIN_PARENT)

import numpy as np  # noqa: E402
from osgeo import gdal, ogr, osr  # noqa: E402
from qgis.core import (  # noqa: E402
    QgsApplication, QgsProject, QgsRasterLayer, QgsVectorLayer, QgsGeometry,
    QgsRectangle, QgsProcessingContext, QgsProcessingFeedback,
)
from qgis.PyQt.QtCore import QCoreApplication, QSize  # noqa: E402
from qgis.PyQt.QtWidgets import QMainWindow, QToolBar, QMenu  # noqa: E402

app = QgsApplication([], True)
app.initQgis()
from processing.core.Processing import Processing  # noqa: E402
Processing.initialize()
import processing  # noqa: E402
# O Processing do QGIS liga exceções GDAL globalmente; o modo 'off' simula
# o QGIS com Processing desativado (gdal.Open retorna None em falhas).
GDAL_MODE = os.environ.get('VSP_GDAL_EXCEPTIONS', 'qgis')
if GDAL_MODE == 'off':
    for _m in (gdal, ogr, osr):
        _m.DontUseExceptions()
GDAL_STATE0 = (gdal.GetUseExceptions(), ogr.GetUseExceptions(), osr.GetUseExceptions())
print('Estado inicial de exceções GDAL/OGR/OSR:', GDAL_STATE0, flush=True)

RESULTS = []


def read_text(path):
    with open(path, encoding='utf-8-sig') as fh:
        return fh.read()


def check(name, func):
    try:
        info = func()
        RESULTS.append((name, 'PASS', '' if info is None else str(info)[:160]))
    except Exception as exc:  # o teste registra qualquer falha
        RESULTS.append((name, 'FAIL', f'{type(exc).__name__}: {exc}'))
        with open(os.path.join(OUT, 'tracebacks.txt'), 'a', encoding='utf-8') as fh:
            fh.write(f'==== {name}\n{traceback.format_exc()}\n')


# ----------------------------------------------------------------- dados
EPSG = 31983
SRS = osr.SpatialReference()
SRS.ImportFromEPSG(EPSG)
GT = (500000.0, 30.0, 0.0, 9000000.0, 0.0, -30.0)
W, H = 120, 90
rng = np.random.default_rng(42)


def make_raster(path, arr, nodata=0, dtype=gdal.GDT_Byte):
    ds = gdal.GetDriverByName('GTiff').Create(path, arr.shape[1], arr.shape[0], 1, dtype)
    ds.SetGeoTransform(GT)
    ds.SetProjection(SRS.ExportToWkt())
    band = ds.GetRasterBand(1)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    band.WriteArray(arr)
    ds = None
    return path


yy, xx = np.mgrid[0:H, 0:W]
cls_a = (1 + (xx // 30) % 4).astype(np.uint8)
cls_a[:5, :5] = 0
cls_b = cls_a.copy()
cls_b[(yy > 40) & (xx < 60)] = 2
cls_b[(yy > 60)] = 3
ras_a = make_raster(os.path.join(OUT, 'mapa_a.tif'), cls_a)
ras_b = make_raster(os.path.join(OUT, 'mapa_b.tif'), cls_b)
ras_t1 = make_raster(os.path.join(OUT, 't1.tif'), np.where(xx < 30, 2, cls_a).astype(np.uint8))
ras_t2 = make_raster(os.path.join(OUT, 't2.tif'), np.where(xx < 50, 2, cls_a).astype(np.uint8))
ras_t3 = make_raster(os.path.join(OUT, 't3.tif'), np.where(xx < 70, 2, cls_b).astype(np.uint8))
ras_c = make_raster(os.path.join(OUT, 'mapa_c.tif'), (1 + (yy // 45)).astype(np.uint8))
friction = make_raster(os.path.join(OUT, 'atrito.tif'),
                       (1 + 9 * rng.random((H, W))).astype(np.float32), None, gdal.GDT_Float32)
friction2 = make_raster(os.path.join(OUT, 'atrito2.tif'),
                        (1 + (xx // 40)).astype(np.uint8), None)
ras_float_nodata = make_raster(os.path.join(OUT, 'float_nd.tif'),
                               np.where(xx < 10, -9999.9, cls_a).astype(np.float32),
                               -9999.9, gdal.GDT_Float32)

X0, Y0 = GT[0], GT[3]
XMAX, YMIN = X0 + W * 30, Y0 - H * 30


def wkt_box(x1, y1, x2, y2):
    return f'POLYGON(({x1} {y1},{x2} {y1},{x2} {y2},{x1} {y2},{x1} {y1}))'


def make_vector(path, geomtype, fields, rows, layer='dados'):
    if os.path.exists(path):
        os.remove(path)
    ds = ogr.GetDriverByName('GPKG').CreateDataSource(path)
    lyr = ds.CreateLayer(layer, SRS, geomtype)
    for name, ftype in fields:
        lyr.CreateField(ogr.FieldDefn(name, ftype))
    for wkt, values in rows:
        f = ogr.Feature(lyr.GetLayerDefn())
        for (name, _), value in zip(fields, values):
            f.SetField(name, value)
        f.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
        lyr.CreateFeature(f)
    ds = None
    return path


midx, midy = (X0 + XMAX) / 2, (Y0 + YMIN) / 2
aoi_path = make_vector(os.path.join(OUT, 'aoi.gpkg'), ogr.wkbPolygon,
                       [('nome', ogr.OFTString)],
                       [(wkt_box(X0 + 100, YMIN + 100, midx + 300, midy), ['Área 1']),
                        (wkt_box(midx, midy - 200, XMAX - 100, Y0 - 100), ['Área 2'])])
the_a = make_vector(os.path.join(OUT, 'tema_a.gpkg'), ogr.wkbPolygon, [('classe', ogr.OFTString)],
                    [(wkt_box(X0, YMIN, midx, Y0), ['Mata']),
                     (wkt_box(midx, YMIN, XMAX, Y0), ['Pasto'])])
the_b = make_vector(os.path.join(OUT, 'tema_b.gpkg'), ogr.wkbPolygon, [('uso', ogr.OFTString)],
                    [(wkt_box(X0, YMIN, X0 + 1200, Y0), ['Mata']),
                     (wkt_box(X0 + 1200, YMIN, XMAX, Y0), ['Pasto'])])
the_c = make_vector(os.path.join(OUT, 'tema_c.gpkg'), ogr.wkbPolygon, [('solo', ogr.OFTInteger)],
                    [(wkt_box(X0, YMIN, XMAX, midy), [1]),
                     (wkt_box(X0, midy, XMAX, Y0), [2])])
pts = make_vector(os.path.join(OUT, 'centros.gpkg'), ogr.wkbPoint,
                  [('massa', ogr.OFTReal), ('nome', ogr.OFTString)],
                  [(f'POINT({X0 + 400} {Y0 - 400})', [10.0, 'A']),
                   (f'POINT({XMAX - 500} {Y0 - 900})', [5.0, 'B']),
                   (f'POINT({midx} {YMIN + 300})', [2.0, 'C'])])

project = QgsProject.instance()
L = {}
for key, path, prov in [('ras_a', ras_a, 'gdal'), ('ras_b', ras_b, 'gdal'), ('ras_c', ras_c, 'gdal'),
                        ('fric', friction, 'gdal'), ('aoi', aoi_path, 'ogr'), ('the_a', the_a, 'ogr'),
                        ('the_b', the_b, 'ogr'), ('the_c', the_c, 'ogr'), ('pts', pts, 'ogr')]:
    layer = (QgsRasterLayer(path, key) if prov == 'gdal' else QgsVectorLayer(path, key, 'ogr'))
    assert layer.isValid(), path
    project.addMapLayer(layer)
    L[key] = layer
project.setCrs(L['ras_a'].crs())


# ------------------------------------------------------- iface simulada
class FakeIface:
    """Subconjunto da QgisInterface com widgets Qt reais."""

    def __init__(self):
        self.window = QMainWindow()
        self.menus = {}

    def mainWindow(self):
        return self.window

    def addToolBar(self, name):
        bar = QToolBar(name, self.window)
        self.window.addToolBar(bar)
        return bar

    def _menu(self, kind, name):
        return self.menus.setdefault((kind, name), QMenu(name, self.window))

    def addPluginToMenu(self, name, action):
        self._menu('plugins', name).addAction(action)

    def addPluginToRasterMenu(self, name, action):
        self._menu('raster', name).addAction(action)

    def removePluginMenu(self, name, action):
        self._menu('plugins', name).removeAction(action)

    def removePluginRasterMenu(self, name, action):
        self._menu('raster', name).removeAction(action)

    def mapCanvas(self):
        from qgis.gui import QgsMapCanvas
        if not hasattr(self, '_canvas'):
            self._canvas = QgsMapCanvas(self.window)
            self._canvas.setDestinationCrs(L['ras_a'].crs())
            self._canvas.setExtent(L['ras_a'].extent())
        return self._canvas

    def messageBar(self):
        from qgis.gui import QgsMessageBar
        if not hasattr(self, '_bar'):
            self._bar = QgsMessageBar(self.window)
        return self._bar

    def activeLayer(self):
        return L['ras_a']

    def __getattr__(self, name):  # qualquer outro método: no-op registrado
        def _noop(*args, **kwargs):
            return None
        return _noop


iface = FakeIface()
import geosaga  # noqa: E402

# QMessageBox modal bloquearia o teste: registrar e responder automaticamente.
from qgis.PyQt.QtWidgets import QMessageBox  # noqa: E402
MESSAGES = []
for kind in ('information', 'warning', 'critical'):
    setattr(QMessageBox, kind, staticmethod(
        lambda *a, _k=kind, **k: MESSAGES.append((_k, a[1] if len(a) > 1 else '', a[2] if len(a) > 2 else ''))
        or QMessageBox.StandardButton.Ok))
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)

plugin_holder = {}


def plugin_cycle():
    for _ in range(2):  # carregar/descarregar duas vezes (atualização do plugin)
        plugin = geosaga.classFactory(iface)
        plugin.initGui()
        menu = plugin.toolbar_menu
        assert len(menu.actions()) == 7, len(menu.actions())
        for action in menu.actions():
            action.trigger()
            QCoreApplication.processEvents()
        for dlg in ('dialog', 'rs2_dialog', 'monitoring_dialog', 'signature_dialog',
                    'combination_dialog', 'voronoi_dialog', 'sequence_dialog'):
            assert getattr(plugin, dlg) is not None, f'{dlg} não abriu'
        plugin_holder['last'] = [a.text() for a in menu.actions()]
        plugin.unload()
        QCoreApplication.processEvents()
    return plugin_holder['last']


check('plugin: initGui + 7 diálogos + unload (2 ciclos)', plugin_cycle)
dialog_errors = [m for m in MESSAGES if m[0] == 'critical']
check('plugin: nenhum erro ao abrir diálogos', lambda: (_ for _ in ()).throw(
    RuntimeError(dialog_errors)) if dialog_errors else 'ok')

# ----------------------------------------------------------- Processing
from geosaga.provider import GeoSAGAProvider  # noqa: E402
provider = GeoSAGAProvider()
QgsApplication.processingRegistry().addProvider(provider)
CFG = json.dumps({'camadas': [{'peso': 60, 'notas': {'1': 10, '2': 7, '3': 3, '4': 1}},
                              {'peso': 40, 'notas': {'1': 9, '2': 5, '3': 1, '4': 0}}]})


def alg_avaliacao():
    out = os.path.join(OUT, 'proc_avaliacao.tif')
    r = processing.run('geosaga:avaliacao', {'RASTERS': [ras_a, ras_b], 'REGRAS': CFG, 'OUTPUT': out})
    arr = gdal.Open(r['OUTPUT']).ReadAsArray()
    valid = arr[arr != -9999]
    assert valid.size and valid.min() >= 0 and valid.max() <= 10
    # verificação numérica de um pixel: classe 1 e 1 -> (60*10+40*9)/100 = 9.6
    assert abs(arr[10, 10] - 9.6) < 1e-5, arr[10, 10]
    assert arr[0, 0] == -9999  # NoData propagado
    return f'min={valid.min():.2f} max={valid.max():.2f}'


def alg_monitoria():
    r = processing.run('geosaga:monitoria', {'ANTES': ras_a, 'DEPOIS': ras_b,
                       'OUTPUT': os.path.join(OUT, 'proc_monit.tif'),
                       'TABELA': os.path.join(OUT, 'proc_monit.csv')})
    rows = read_text(r['TABELA']).splitlines()
    assert len(rows) > 2
    return f'{len(rows) - 1} transições'


def alg_assinatura():
    r = processing.run('geosaga:assinatura', {'RASTER': ras_a, 'POLIGONOS': aoi_path,
                       'TABELA': os.path.join(OUT, 'proc_assin.csv')})
    rows = read_text(r['TABELA']).splitlines()
    total = sum(float(x.split(';')[2]) for x in rows[1:])
    assert abs(total - 100) < 1e-3
    return f'{len(rows) - 1} classes, soma%={total:.3f}'


def alg_assinatura_reprojetada():
    # polígonos em EPSG:4326 sobre raster em EPSG:31983 (reprojeção no algoritmo)
    params = {'INPUT': aoi_path, 'TARGET_CRS': 'EPSG:4326', 'OUTPUT': os.path.join(OUT, 'aoi_4326.gpkg')}
    reproj = processing.run('native:reprojectlayer', params)['OUTPUT']
    r = processing.run('geosaga:assinatura', {'RASTER': ras_a, 'POLIGONOS': reproj,
                       'TABELA': os.path.join(OUT, 'proc_assin_4326.csv')})
    return read_text(r['TABELA']).count('\n')


def alg_erro_controlado():
    try:
        processing.run('geosaga:avaliacao', {'RASTERS': [ras_a], 'REGRAS': '{"x":1}',
                       'OUTPUT': os.path.join(OUT, 'erro.tif')})
    except Exception as exc:  # deve ser QgsProcessingException, sem crash
        return f'erro tratado: {exc}'
    raise AssertionError('JSON inválido não foi rejeitado')


check('processing: geosaga:avaliacao', alg_avaliacao)
check('processing: geosaga:monitoria', alg_monitoria)
check('processing: geosaga:assinatura', alg_assinatura)
check('processing: geosaga:assinatura (vetor EPSG:4326)', alg_assinatura_reprojetada)
check('processing: JSON inválido tratado', alg_erro_controlado)

# --------------------------------------------------------------- motores
from geosaga import raster_engine, monitoring_engine, signature_engine  # noqa: E402
from geosaga import combination_raster, combination_vector, voronoi_engine  # noqa: E402
from geosaga import voronoi_vector, rs2_converter, rs2_vector, tiff_vector  # noqa: E402
from geosaga import vector_raster, vector_monitoring_engine, gif_codec  # noqa: E402
from geosaga import vector_evaluation_writer, vector_overlay_engine  # noqa: E402
from geosaga.voronoi_core import Generator  # noqa: E402


def eng_evaluation():
    s = raster_engine.run_evaluation([ras_a, ras_b], json.loads(CFG), os.path.join(OUT, 'eng_aval.tif'),
                                     report=os.path.join(OUT, 'eng_aval.csv'), title='t', author='a',
                                     report_txt=os.path.join(OUT, 'eng_aval.txt'))
    return s


def eng_scan_float_nodata():
    classes = raster_engine.scan_classes(ras_float_nodata)
    return classes


def eng_monitoring():
    return monitoring_engine.run_monitoring(ras_a, ras_b, os.path.join(OUT, 'eng_monit.tif'), before_label='2000', after_label='2020',
                                            title='Teste', temporal_files=[(2005, ras_t1), (2010, ras_t2), (2015, ras_t3)])


def eng_signature_raster():
    return signature_engine.run_signature(L['ras_a'], L['aoi'], 'raster', '',
                                          os.path.join(OUT, 'eng_assin_r.csv'), area_name_field='nome')


def eng_signature_vector():
    return signature_engine.run_signature(L['the_a'], L['aoi'], 'vector', 'classe',
                                          os.path.join(OUT, 'eng_assin_v.csv'), area_name_field='nome')


def eng_comb_raster():
    return combination_raster.run_raster_combination([ras_a, ras_b, ras_c],
                                                     os.path.join(OUT, 'eng_comb.tif'))


def eng_comb_vector():
    return combination_vector.run_vector_combination([L['the_a'], L['the_c']], ['classe', 'solo'],
                                                     ['', ''], os.path.join(OUT, 'eng_comb.gpkg'))


GENS = [Generator(1, X0 + 400, Y0 - 400, 10.0, 'A'), Generator(2, XMAX - 500, Y0 - 900, 5.0, 'B'),
        Generator(3, midx, YMIN + 300, 2.0, 'C')]


def voronoi(mode, **kw):
    def run():
        r = voronoi_engine.run_voronoi(GENS, os.path.join(OUT, f'eng_vor_{mode}{len(kw)}.tif'),
                                       SRS.ExportToWkt(), GT, W, H, mode=mode, vectorize=True, **kw)
        return {k: r[k] for k in r if k in ('pixels_valid',)}
    return run


def eng_voronoi_vector():
    bounds = (X0, YMIN, XMAX, Y0)
    r = voronoi_vector.save_simple_voronoi(GENS, bounds, os.path.join(OUT, 'eng_vor_vec.gpkg'),
                                           SRS.ExportToWkt())
    return len(r['rows'])


def eng_rs2_roundtrip():
    rs2 = os.path.join(OUT, 'eng.rs2')
    rs2_converter.convert_tif_to_rs2(ras_a, rs2)
    back = os.path.join(OUT, 'eng_rs2_back.tif')
    rs2_converter.convert_rs2_to_tif(rs2, back, epsg=f'EPSG:{EPSG}')
    a = gdal.Open(ras_a).ReadAsArray()
    b = gdal.Open(back).ReadAsArray()
    assert a.shape == b.shape
    return f'iguais(sem nodata)={(a[a != 0] == b[a != 0]).all()}'


def eng_rs2_vector():
    rs2 = os.path.join(OUT, 'eng.rs2')
    return rs2_vector.convert_rs2_to_vector(rs2, os.path.join(OUT, 'eng_rs2_vec.gpkg'), epsg=f'EPSG:{EPSG}')


def eng_tif_vector():
    return tiff_vector.convert_tif_to_vector(ras_a, os.path.join(OUT, 'eng_tif_vec.gpkg'))


def eng_tif_vector_continuous():
    return tiff_vector.convert_tif_to_vector(friction, os.path.join(OUT, 'eng_tif_vec_cont.gpkg'),
                                             continuous_classes=5)


def eng_vector_tif():
    return vector_raster.convert_vector_to_tif(the_c, os.path.join(OUT, 'eng_vec2tif.tif'), 'solo', 30)


def eng_vector_monitoring():
    return vector_monitoring_engine.run_vector_monitoring(
        L['the_a'], L['the_b'], 'classe', 'uso', os.path.join(OUT, 'eng_vmon.gpkg'), title='T')


CRIT = [{'field': 'classe', 'weight': 100, 'categories': {'Mata', 'Pasto'},
         'notes': {'Mata': 10, 'Pasto': 4}, 'excluded': set()}]


def eng_vector_eval():
    return vector_evaluation_writer.evaluate_vector_layer(L['the_a'], CRIT, 10,
                                                          os.path.join(OUT, 'eng_veval.gpkg'))


def eng_overlay():
    crit = [{'layer_id': L['the_a'].id(), 'field': 'C01', 'source_field': 'classe', 'weight': 60, 'label': 'Uso',
             'counts': {'Mata': 1, 'Pasto': 1}, 'notes': {'Mata': 10, 'Pasto': 4}, 'excluded': [], 'missing': 0},
            {'layer_id': L['the_c'].id(), 'field': 'C02', 'source_field': 'solo', 'weight': 40, 'label': 'Solo',
             'counts': {'1': 1, '2': 1}, 'notes': {'1': 8, '2': 2}, 'excluded': [], 'missing': 0}]
    return vector_overlay_engine.evaluate_overlay(crit, 10, os.path.join(OUT, 'eng_overlay.gpkg'), project)


def eng_gif():
    frames = [np.full((20, 30, 3), i * 40, dtype=np.uint8) for i in range(4)]
    gif_codec.encode_gif(os.path.join(OUT, 'eng.gif'), [f.tobytes() for f in frames], 30, 20)
    return os.path.getsize(os.path.join(OUT, 'eng.gif'))


for name, fn in [
    ('motor: avaliação raster', eng_evaluation),
    ('motor: classes com NoData float', eng_scan_float_nodata),
    ('motor: monitoria raster + tendências', eng_monitoring),
    ('motor: assinatura raster', eng_signature_raster),
    ('motor: assinatura vetorial', eng_signature_vector),
    ('motor: combinação raster', eng_comb_raster),
    ('motor: combinação vetorial', eng_comb_vector),
    ('motor: Voronoi simples', voronoi('simple')),
    ('motor: Voronoi massa', voronoi('mass')),
    ('motor: Voronoi atrito', voronoi('friction', friction_path=friction)),
    ('motor: Voronoi massa+atrito', voronoi('mass_friction', friction_path=friction)),
    ('motor: Voronoi atrito múltiplo', voronoi('friction', friction_components=[
        {'path': friction, 'weight': 70, 'notes': ''},
        {'path': friction2, 'weight': 30, 'notes': '1=2;2=8;3=5'}])),
    ('motor: Voronoi vetorial direto', eng_voronoi_vector),
    ('motor: GeoTIFF→RS2→GeoTIFF', eng_rs2_roundtrip),
    ('motor: RS2→vetor', eng_rs2_vector),
    ('motor: GeoTIFF→vetor (categórico)', eng_tif_vector),
    ('motor: GeoTIFF→vetor (contínuo)', eng_tif_vector_continuous),
    ('motor: vetor→GeoTIFF', eng_vector_tif),
    ('motor: monitoria vetorial', eng_vector_monitoring),
    ('motor: avaliação vetorial', eng_vector_eval),
    ('motor: sobreposição vetorial', eng_overlay),
    ('motor: GIF', eng_gif),
]:
    check(name, fn)


# ------------------------------------------------------ robustez/estado
def gdal_state_preserved():
    state = (gdal.GetUseExceptions(), ogr.GetUseExceptions(), osr.GetUseExceptions())
    assert state == GDAL_STATE0, f'estado global do GDAL alterado: {GDAL_STATE0} -> {state}'
    return state


def gif_decodes_with_qt():
    from qgis.PyQt.QtGui import QImageReader
    reader = QImageReader(os.path.join(OUT, 'eng.gif'))
    assert reader.canRead(), reader.errorString()
    frames = 0
    while True:
        img = reader.read()
        if img.isNull():
            break
        frames += 1
        assert (img.width(), img.height()) == (30, 20)
    assert frames == 4, frames
    return f'{frames} quadros decodificados'


def cancel(fn, outputs):
    def run():
        for path in outputs:
            if os.path.exists(path):
                os.remove(path)
        try:
            fn()
        except InterruptedError:
            pass
        else:
            raise AssertionError('cancelamento ignorado')
        leftovers = [p for p in outputs if os.path.exists(p)]
        assert not leftovers, f'arquivos parciais deixados: {leftovers}'
        return 'cancelado sem resíduos'
    return run


YES = lambda: True  # noqa: E731
c_eval = os.path.join(OUT, 'c_aval.tif')
c_mon = os.path.join(OUT, 'c_monit.tif')
c_comb = os.path.join(OUT, 'c_comb.tif')
c_vor = os.path.join(OUT, 'c_vor.tif')
c_vmon = os.path.join(OUT, 'c_vmon.gpkg')
for name, fn in [
    ('estado global do GDAL preservado após conversões', gdal_state_preserved),
    ('GIF decodificado pelo Qt (decodificador independente)', gif_decodes_with_qt),
    ('cancelar avaliação raster', cancel(lambda: raster_engine.run_evaluation(
        [ras_a, ras_b], json.loads(CFG), c_eval, cancelled=YES), [c_eval])),
    ('cancelar monitoria raster', cancel(lambda: monitoring_engine.run_monitoring(
        ras_a, ras_b, c_mon, cancelled=YES), [c_mon])),
    ('cancelar combinação raster', cancel(lambda: combination_raster.run_raster_combination(
        [ras_a, ras_b], c_comb, cancelled=YES), [c_comb])),
    ('cancelar Voronoi atrito', cancel(lambda: voronoi_engine.run_voronoi(
        GENS, c_vor, SRS.ExportToWkt(), GT, W, H, mode='friction', friction_path=friction,
        cancelled=YES), [c_vor])),
    ('cancelar monitoria vetorial', cancel(lambda: vector_monitoring_engine.run_vector_monitoring(
        L['the_a'], L['the_b'], 'classe', 'uso', c_vmon, cancelled=YES), [c_vmon])),
]:
    check(name, fn)


def expect_error(fn, fragment=''):
    def run():
        try:
            fn()
        except (ValueError, RuntimeError, OSError) as exc:
            assert fragment in str(exc), str(exc)
            return f'{type(exc).__name__}: {exc}'[:120]
        raise AssertionError('entrada inválida aceita')
    return run


geo = os.path.join(OUT, 'geografico.tif')
ds = gdal.GetDriverByName('GTiff').Create(geo, 10, 10, 1, gdal.GDT_Byte)
ds.SetGeoTransform((-40, 0.01, 0, -9, 0, -0.01))
s4326 = osr.SpatialReference(); s4326.ImportFromEPSG(4326); ds.SetProjection(s4326.ExportToWkt())
ds.GetRasterBand(1).Fill(1); ds.GetRasterBand(1).SetNoDataValue(0); ds = None
allnd = make_raster(os.path.join(OUT, 'so_nodata.tif'), np.zeros((H, W), dtype=np.uint8))
for name, fn in [
    ('erro: grades diferentes na avaliação', expect_error(lambda: raster_engine.run_evaluation(
        [ras_a, geo], json.loads(CFG), os.path.join(OUT, 'x1.tif')))),
    ('erro: raster só com NoData na monitoria', expect_error(lambda: monitoring_engine.run_monitoring(
        allnd, ras_b, os.path.join(OUT, 'x2.tif')))),
    ('erro: arquivo inexistente na combinação', expect_error(lambda: combination_raster.run_raster_combination(
        [ras_a, os.path.join(OUT, 'nao_existe.tif')], os.path.join(OUT, 'x3.tif')))),
    ('erro: saída sobre a entrada', expect_error(lambda: raster_engine.run_evaluation(
        [ras_a, ras_b], json.loads(CFG), ras_a))),
    ('erro: Voronoi em SRC geográfico', expect_error(lambda: voronoi_engine.run_voronoi(
        GENS, os.path.join(OUT, 'x4.tif'), s4326.ExportToWkt(), (-40, 0.01, 0, -9, 0, -0.01), 10, 10))),
    ('erro: centros duplicados no Voronoi', expect_error(lambda: voronoi_engine.run_voronoi(
        [GENS[0], GENS[0]], os.path.join(OUT, 'x5.tif'), SRS.ExportToWkt(), GT, W, H))),
    ('erro: RS2 corrompido', expect_error(lambda: (open(os.path.join(OUT, 'ruim.rs2'), 'wb').write(b'lixo' * 10),
        rs2_converter.convert_rs2_to_tif(os.path.join(OUT, 'ruim.rs2'), os.path.join(OUT, 'x6.tif'),
                                         epsg=f'EPSG:{EPSG}')))),
    ('estado global do GDAL preservado após erros', gdal_state_preserved),
]:
    check(name, fn)


def english_messages():
    from geosaga.i18n import translate_for_locale
    try:
        raster_engine.run_evaluation([ras_a], json.loads(CFG), os.path.join(OUT, 'x7.tif'))
    except ValueError as exc:
        english = translate_for_locale(str(exc), 'en_US')
        assert english != str(exc) and 'rasters were selected' in english, english
        return english
    raise AssertionError('erro esperado')


check('mensagem de erro traduzida para inglês', english_messages)

ok = sum(1 for r in RESULTS if r[1] == 'PASS')
for name, status, info in RESULTS:
    print(f'[{status}] {name} :: {info}')
print(f'\nTOTAL {ok}/{len(RESULTS)} aprovados')
with open(os.path.join(OUT, 'results.json'), 'w', encoding='utf-8') as fh:
    json.dump(RESULTS, fh, ensure_ascii=False, indent=1)
sys.stdout.flush()
app.exitQgis()
os._exit(0 if ok == len(RESULTS) else 1)
