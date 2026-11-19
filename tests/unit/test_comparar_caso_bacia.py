"""Comparação Vista SAGA × plugin sobre o mesmo RS2 (scripts/comparar_caso_bacia.py), com dados sintéticos."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip('osgeo.gdal')

from geosaga.rs2_format import RS2Header, write_rs2  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('comparar_bacia', ROOT / 'scripts' / 'comparar_caso_bacia.py')
comparar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparar)

CORES = [(255, 255, 255, 0), (106, 143, 235, 0), (181, 235, 106, 0), (235, 106, 219, 0)]


def _rs2(path, matriz, nomes, codigos=None, res=10):
    h, w = matriz.shape
    header = RS2Header(width=w, height=h, xmin=200000, ymin=8930000, xmax=200000 + w * res,
                       ymax=8930000 + h * res, labels=list(nomes), colors=CORES[:len(nomes)], codes=codigos)
    write_rs2(path, header, list(matriz.astype(np.uint16)))


def _caso(tmp_path):
    classes = np.zeros((30, 40), dtype=np.uint16)
    classes[3:27, 4:36] = 1            # área de estudo
    classes[3:27, 18:22] = 5           # faixa de atrito alto
    entrada = tmp_path / 'entrada.rs2'
    _rs2(entrada, classes, ['FUNDO', 'Classe 1', 'Classe 5'], codigos=[0, 1, 5])
    pontos = tmp_path / 'pontos.txt'
    pontos.write_bytes('A;4;8:10\r\nB;1;32:20\r\n[ATRITOS]\r\n1\r\n1\r\n5\r\n'.encode('cp1252'))
    return entrada, pontos


def test_le_codigos_fora_da_legenda(tmp_path):
    entrada, _ = _caso(tmp_path)
    h, classes, extras = comparar.ler_rs2(entrada)
    assert extras == {} and classes.shape == (30, 40)
    # Saída com um código fora da legenda (como o 11 das saídas vazias do Vista SAGA): lida e informada.
    # O gravador recusa código fora da legenda: grava-se uma matriz válida e troca-se o código no RLE.
    import geosaga.rs2_format as rf
    caminho = tmp_path / 'saida.rs2'
    _rs2(caminho, np.full((30, 40), 2, dtype=np.uint16), ['Ponto', 'A', 'B'])
    dados = bytearray(caminho.read_bytes())
    header = rf.RS2Reader(caminho).header
    pos = header.data_offset
    for _ in range(header.height):
        pos += 4
        n, c = rf.PAIR.unpack_from(dados, pos)
        rf.PAIR.pack_into(dados, pos, n, 11)
        pos += 5
    caminho.write_bytes(bytes(dados))
    _, matriz, extras = comparar.ler_rs2(caminho)
    assert extras == {11: 1200} and (matriz == 11).all()


def test_pontos_e_notas(tmp_path):
    _, pontos = _caso(tmp_path)
    polos, notas = comparar.ler_pontos(pontos)
    assert polos == [('A', 4.0, 8, 10), ('B', 1.0, 32, 20)]
    assert notas == [1.0, 1.0, 5.0]


def test_criterios_com_o_proprio_plugin(tmp_path, capsys):
    """Uma "saída do Vista SAGA" igual à do plugin atende os três critérios com 100%."""
    entrada, pontos = _caso(tmp_path)
    h, classes, _ = comparar.ler_rs2(entrada)
    polos, notas = comparar.ler_pontos(pontos)
    from osgeo import osr
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(31985)
    rot = comparar.rodar_raster(h, classes, notas, polos, srs.ExportToWkt(), 'mass_friction', str(tmp_path))
    vs = rot.astype(np.uint16)
    for _, _, c, l in polos:
        vs[l - 1, c - 1] = 0                       # células "Ponto"
    saida = tmp_path / 'vs_massa_atrito.rs2'
    _rs2(saida, vs, ['Ponto', 'A', 'B'])
    comparar.main(['--rs2', str(entrada), '--pontos', str(pontos), '--epsg', '31985',
                   '--massa-atrito', str(saida), '--saida', str(tmp_path / 'out')])
    texto = capsys.readouterr().out
    assert 'células "Ponto" nas posições do arquivo: sim' in texto
    assert '100.000%' in texto and 'atende' in texto and 'NÃO atende' not in texto
    estudo = classes != 0
    c1, ndif, c2, c3, _ = comparar.avaliar(vs, rot, estudo, 2, 0.01)
    assert (c1, ndif, c3) == (100.0, 0, 0.0)


def test_criterios_detectam_regiao_trocada():
    vs = np.ones((20, 20), dtype=np.uint16)
    vs[:, 10:] = 2
    plugin = vs.copy()
    plugin[2:6, 2:6] = 2                           # mancha longe da fronteira
    estudo = np.ones(vs.shape, dtype=bool)
    c1, ndif, c2, c3, regioes = comparar.avaliar(vs, plugin, estudo, 2, 1.0)
    assert ndif == 16 and c1 == pytest.approx(96.0)
    assert c2 == 0.0                               # nenhuma divergência na fronteira
    assert c3 == pytest.approx(8.0)                # região 1: 200 → 184 células (16/200)
