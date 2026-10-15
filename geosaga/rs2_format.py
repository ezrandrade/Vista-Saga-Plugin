"""Leitor e gravador *experimental* do RS2 legado Vista SAGA/UFRJ.

Especificação deduzida por análise independente dos arquivos GEOM/COTA/USO/LITO/DECL
fornecidos para testes; nenhum código do programa original foi utilizado.

Layout observado (little endian):
- 11 bytes de metadados legados (sem semântica inteiramente identificada);
- ymin, xmin, ymax, xmax: quatro uint32 (coordenadas em unidades projetadas);
- height, width: uint16;
- number_of_labels: uint32;
- label 0: cadeia em CP1252 terminada por NUL;
- labels 1..n-1: código uint16, cadeia CP1252 terminada por NUL;
- cada linha: índice 1-based uint32; sucessivos pares
  (run_length:uint16, category:uint16) até preencher width; byte NUL;
- tabela final fixa de 32769 cores RGBA (quatro bytes por entrada).

Observado: componente alpha sempre zero; as três primeiras componentes são RGB.
O RS2 não armazena explicitamente identificação inequívoca de datum ou zona UTM.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional
import os
import struct
import tempfile

import numpy as np

UINT16 = struct.Struct('<H')
PAIR = struct.Struct('<HH')
UINT32 = struct.Struct('<I')
BOUNDS = struct.Struct('<IIIIHHI')
HEADER_BYTES = 11
PALETTE_SIZE = 32769 * 4
MAX_PIXELS = 250_000_000
DEFAULT_PREFIX = bytes.fromhex('10 00 00 12 0c 13 0a 00 19 00 01')


class RS2Error(ValueError):
    """Arquivo RS2 incompatível ou corrompido."""


@dataclass
class RS2Header:
    width: int
    height: int
    xmin: int
    ymin: int
    xmax: int
    ymax: int
    labels: list[str]
    colors: list[tuple[int, int, int, int]]
    prefix: bytes = DEFAULT_PREFIX
    data_offset: int = 0
    raster_end: int = 0
    # Paleta original: permite regravar integralmente a tabela de cores.
    raw_palette: Optional[bytes] = None

    @property
    def pixel_x(self) -> float:
        return (self.xmax - self.xmin) / self.width

    @property
    def pixel_y(self) -> float:
        return (self.ymax - self.ymin) / self.height

    @property
    def num_classes(self) -> int:
        return len(self.labels)


def _read_header(data: bytes) -> RS2Header:
    if len(data) < HEADER_BYTES + BOUNDS.size + PALETTE_SIZE + 6:
        raise RS2Error('Arquivo menor que o cabeçalho e a tabela de cores RS2.')
    prefix = data[:HEADER_BYTES]
    # A variante analisada utiliza a assinatura observada 0x10, 0x00, 0x00.
    if prefix[:3] != DEFAULT_PREFIX[:3]:
        raise RS2Error('Cabeçalho RS2 não reconhecido nesta variante do formato.')
    ymin, xmin, ymax, xmax, height, width, n = BOUNDS.unpack_from(data, HEADER_BYTES)
    if not 0 < height <= 65535 or not 0 < width <= 65535:
        raise RS2Error('Dimensões RS2 inválidas.')
    if width * height > MAX_PIXELS:
        raise RS2Error('Raster excede o limite de segurança de células.')
    if xmax <= xmin or ymax <= ymin:
        raise RS2Error('Extensão espacial RS2 inválida.')
    if not (1 <= n <= 32769):
        raise RS2Error('Quantidade de classes RS2 inválida.')
    if ((xmax - xmin) / width) <= 0 or ((ymax - ymin) / height) <= 0:
        raise RS2Error('Resolução espacial RS2 inválida.')
    pos = HEADER_BYTES + BOUNDS.size
    limit = len(data) - PALETTE_SIZE
    labels = []
    for i in range(n):
        if i:
            if pos + 2 > limit:
                raise RS2Error('Legenda RS2 truncada.')
            code = UINT16.unpack_from(data, pos)[0]
            pos += 2
            if code != i:
                raise RS2Error(f'Código de legenda inesperado: {code}, esperado: {i}.')
        end = data.find(b'\0', pos, min(pos + 8193, limit))
        if end < 0:
            raise RS2Error('Nome de categoria truncado ou excessivamente longo.')
        labels.append(data[pos:end].decode('cp1252'))
        pos = end + 1
    pal = data[-PALETTE_SIZE:]
    colors = [tuple(pal[i*4:(i+1)*4]) for i in range(n)]
    return RS2Header(width, height, xmin, ymin, xmax, ymax, labels,
                     colors, prefix, pos, len(data) - PALETTE_SIZE, pal)


class RS2Reader:
    """Lê o RS2 preservando códigos categóricos, coordenadas e paleta."""

    def __init__(self, filename):
        self.path = Path(filename)
        # Os arquivos RS2 legados são RLE e relativamente pequenos. Lê-los de
        # uma vez mantém o parser desacoplado de GDAL e QGIS.
        self._data = self.path.read_bytes()
        self.header = _read_header(self._data)

    def rows(self) -> Iterator[np.ndarray]:
        """Fornece uma linha uint16 por vez; valida a estrutura inteira."""
        d = self._data
        h = self.header
        pos = h.data_offset
        for y in range(h.height):
            if pos + 9 > h.raster_end:
                raise RS2Error(f'Linha {y + 1}: fluxo RLE truncado.')
            line_id = UINT32.unpack_from(d, pos)[0]
            pos += 4
            if line_id != y + 1:
                raise RS2Error(f'Linha {y + 1}: identificador inesperado ({line_id}).')
            line = np.empty(h.width, dtype=np.uint16)
            x = 0
            while x < h.width:
                if pos + 4 > h.raster_end:
                    raise RS2Error(f'Linha {y + 1}: sequência RLE incompleta.')
                length, cat = PAIR.unpack_from(d, pos)
                pos += 4
                if not 0 < length <= h.width - x:
                    raise RS2Error(f'Linha {y + 1}: extensão RLE inválida ({length}).')
                if cat >= h.num_classes:
                    raise RS2Error(f'Linha {y + 1}: classe {cat} ausente da legenda.')
                line[x:x + length] = cat
                x += length
            if pos >= h.raster_end or d[pos] != 0:
                raise RS2Error(f'Linha {y + 1}: terminador RLE inválido.')
            pos += 1
            yield line
        if pos != h.raster_end:
            raise RS2Error('Há bytes inesperados entre a matriz RLE e a paleta.')

    def validate(self) -> dict[int, int]:
        """Percorre todas as linhas e devolve as contagens por categoria."""
        counts = np.zeros(self.header.num_classes, dtype=np.int64)
        for row in self.rows():
            counts += np.bincount(row, minlength=len(counts))
        return {i: int(c) for i, c in enumerate(counts)}


def _pack_legend(labels: list[str]) -> bytes:
    if not 1 <= len(labels) <= 32769:
        raise RS2Error('Número de categorias fora do intervalo suportado.')
    out = bytearray()
    for i, name in enumerate(labels):
        if not isinstance(name, str) or '\0' in name:
            raise RS2Error(f'Nome da classe {i} inválido.')
        if i:
            out.extend(UINT16.pack(i))
        try:
            encoded = name.encode('cp1252')
        except UnicodeEncodeError as exc:
            raise RS2Error(f'O nome da classe {i} não é representável em CP1252.') from exc
        if len(encoded) > 8192:
            raise RS2Error(f'Nome da classe {i} excede o limite de caracteres.')
        out.extend(encoded)
        out.append(0)
    return bytes(out)


def _palette_bytes(header: RS2Header) -> bytes:
    if header.raw_palette is not None and len(header.raw_palette) == PALETTE_SIZE:
        pal = bytearray(header.raw_palette)
    else:
        pal = bytearray(PALETTE_SIZE)
        # Entradas não utilizadas recebem branco por segurança visual.
        for i in range(256):
            pal[4*i:4*i+4] = b'\xff\xff\xff\x00'
    if len(header.colors) < len(header.labels):
        raise RS2Error('Tabela de cores menor que a legenda.')
    for code, entry in enumerate(header.colors[:len(header.labels)]):
        if len(entry) not in (3, 4) or any(not 0 <= int(c) <= 255 for c in entry):
            raise RS2Error(f'Cor RGB inválida para categoria {code}.')
        pal[4*code:4*code+4] = bytes(entry[:3]) + b'\0'
    return bytes(pal)


def _normalized_row(row, width, category_count):
    a = np.asarray(row)
    if a.ndim != 1 or len(a) != width:
        raise RS2Error('Linha de pixels não corresponde à largura da matriz.')
    if a.dtype.kind not in 'iu':
        raise RS2Error('RS2 aceita somente códigos inteiros não negativos.')
    if np.any(a < 0) or np.any(a >= category_count):
        raise RS2Error('Há valores de pixel não previstos nas categorias RS2.')
    return a.astype(np.uint16, copy=False)


def write_rs2(filename, header: RS2Header, rows: Iterable,
              progress=None) -> None:
    """Grava RS2 usando o layout observado; compatibilidade externa ainda experimental.

    A escrita é atômica (arquivo temporário + substituição) e aceita um iterador
    de linhas uint8/uint16, sem precisar carregar o raster inteiro.
    """
    h = header
    if not (0 < h.width <= 65535 and 0 < h.height <= 65535):
        raise RS2Error('Dimensões acima dos limites do formato RS2 analisado.')
    if h.width * h.height > MAX_PIXELS:
        raise RS2Error('Raster excede o limite de segurança.')
    if not (0 <= h.xmin < h.xmax < 2**32 and 0 <= h.ymin < h.ymax < 2**32):
        raise RS2Error('Coordenadas RS2 devem ser inteiros positivos de 32 bits.')
    if len(h.prefix) != HEADER_BYTES:
        raise RS2Error('Prefixo do cabeçalho RS2 inválido.')
    legend = _pack_legend(h.labels)
    palette = _palette_bytes(h)
    out_path = Path(filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.vista_rs2_', suffix='.tmp', dir=out_path.parent)
    try:
        with os.fdopen(fd, 'wb') as dest:
            dest.write(h.prefix)
            dest.write(BOUNDS.pack(h.ymin, h.xmin, h.ymax, h.xmax,
                                   h.height, h.width, h.num_classes))
            dest.write(legend)
            it = iter(rows)
            for y in range(h.height):
                try:
                    row = _normalized_row(next(it), h.width, h.num_classes)
                except StopIteration as exc:
                    raise RS2Error('Faltam linhas para completar o raster.') from exc
                indices = np.flatnonzero(row[1:] != row[:-1]) + 1
                edges = np.concatenate(([0], indices, [h.width]))
                dest.write(UINT32.pack(y + 1))
                for a, b in zip(edges[:-1], edges[1:]):
                    dest.write(PAIR.pack(int(b - a), int(row[a])))
                dest.write(b'\0')
                if progress and y % 100 == 0 and progress(y + 1, h.height) is False:
                    raise RS2Error('Operação cancelada pelo usuário.')
            try:
                next(it)
            except StopIteration:
                pass
            else:
                raise RS2Error('Há linhas excedentes no raster de entrada.')
            dest.write(palette)
        os.replace(tmp, out_path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
