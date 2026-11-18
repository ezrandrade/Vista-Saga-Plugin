"""Conversor do caso real para o Vista SAGA (scripts/preparar_caso_vista_saga.py), com dados sintéticos."""
import importlib.util
import json
from pathlib import Path

import pytest

ogr = pytest.importorskip('osgeo.ogr')
osr = pytest.importorskip('osgeo.osr')

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('preparar', ROOT / 'scripts' / 'preparar_caso_vista_saga.py')
preparar_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparar_mod)

X0, Y0 = 200003.7, 8930001.2


def _poly(coords):
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in coords + [coords[0]]:
        ring.AddPoint_2D(X0 + x, Y0 + y)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return poly


def _write(path, geomtype, fields, rows):
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(31985)
    ds = ogr.GetDriverByName('GPKG').CreateDataSource(str(path))
    layer = ds.CreateLayer(path.stem, srs, geomtype)
    for name, kind in fields:
        layer.CreateField(ogr.FieldDefn(name, kind))
    for geometry, values in rows:
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetGeometry(geometry)
        for (name, _), value in zip(fields, values):
            if value is not None:
                feature.SetField(name, value)
        layer.CreateFeature(feature)
    ds = None
    return str(path)


@pytest.fixture
def inputs(tmp_path):
    bacia = _write(tmp_path / 'bacia.gpkg', ogr.wkbPolygon, [],
                   [(_poly([(0, 0), (1000, 0), (1000, 500), (500, 500), (500, 1000), (0, 1000)]), [])])
    uso = _write(tmp_path / 'uso.gpkg', ogr.wkbPolygon, [('CLASSE', ogr.OFTString), ('NOTA', ogr.OFTReal)],
                 [(_poly([(-20, -20), (1020, -20), (1020, 1020), (-20, 1020)]), ['Vegetação', 1.0]),
                  (_poly([(300, 0), (400, 0), (400, 1000), (300, 1000)]), ['Urbano', 3.0])])

    def pt(x, y):
        return ogr.CreateGeometryFromWkt(f'POINT({X0 + x} {Y0 + y})')
    pontos = _write(tmp_path / 'pontos.gpkg', ogr.wkbPoint, [('NOME', ogr.OFTString), ('POP', ogr.OFTReal)],
                    [(pt(150, 150), ['Bairro; A', 1520.5]), (pt(850, 250), ['Bairro B', 380.25])])
    return uso, bacia, pontos, tmp_path / 'saida'


def test_points_file_one_based_cp1252_crlf(inputs):
    uso, bacia, pontos, out = inputs
    info = preparar_mod.preparar(uso, 'NOTA', bacia, pontos, 'POP', str(out), campo_nome='NOME',
                                 campo_classe='CLASSE', escala_massa=4)
    raw = (out / 'pontos_vista_saga.txt').read_bytes()
    assert b'\r\n' in raw and b'\n\n' not in raw
    lines = raw.decode('cp1252').split('\r\n')
    # Origem alinhada a 5 m (200000): x = 200153,7 → coluna 30 a partir de 0 → 31 no arquivo.
    assert lines[0] == 'Bairro, A;6082;31:171'
    assert lines[1] == 'Bairro B;1521;171:151'
    assert lines[2:6] == ['[ATRITOS]', '1', '1', '3']
    assert [c['nome'] for c in info['classes']] == ['FUNDO', 'Vegetação', 'Urbano']
    assert info['grade']['xmin'] == 200000 and info['grade']['resolucao'] == 5
    saved = json.loads((out / 'caso.json').read_text(encoding='utf-8'))
    assert saved['polos'][0]['coluna'] == 30


def test_non_integer_mass_requires_scale(inputs):
    uso, bacia, pontos, out = inputs
    with pytest.raises(SystemExit, match='escala-massa'):
        preparar_mod.preparar(uso, 'NOTA', bacia, pontos, 'POP', str(out))
