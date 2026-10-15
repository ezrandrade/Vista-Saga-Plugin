"""Mapeamento exato RGB -> código temático a partir de paleta RS2.

Uma imagem RGB isolada não fornece legenda ou georreferenciamento. Só
reconstruímos classes quando há um RS2 de referência explícito com cores
não ambíguas, impedindo inferências silenciosas e perda de informação.
"""

import numpy as np
from .rs2_format import RS2Error


def _key(color):
    r, g, b = (int(c) for c in color[:3])
    return (r << 16) | (g << 8) | b


class RS2RGBMapper:
    """Traduz sequências de canais RGB para os códigos de uma legenda RS2.

    Exige bijeção entre as cores da legenda e os códigos, pois cores
    compartilhadas por classes distintas tornam a operação impossível.
    """

    def __init__(self, colors):
        if not colors or len(colors) > 32769:
            raise RS2Error('Paleta de referência ausente ou excessivamente grande.')
        pairs = sorted((_key(color), code) for code, color in enumerate(colors))
        for (previous_color, _), (next_color, _) in zip(pairs, pairs[1:]):
            if previous_color == next_color:
                raise RS2Error(
                    f'A paleta RS2 possui categorias distintas com a mesma cor '
                    f'RGB #{previous_color:06X}. Não é possível recuperar os códigos '
                    'sem ambiguidade a partir de um TIFF RGB.')
        self.keys = np.array([key for key, _ in pairs], dtype=np.uint32)
        self.codes = np.array([code for _, code in pairs], dtype=np.uint16)

    def map_row(self, red, green, blue, alpha=None, y=None):
        r, g, b = (np.asarray(c) for c in (red, green, blue))
        if r.shape != g.shape or r.shape != b.shape or r.ndim != 1:
            raise RS2Error('As bandas RGB não possuem dimensões compatíveis.')
        if any(c.dtype.kind not in 'ui' for c in (r, g, b)):
            raise RS2Error('Canais RGB devem conter valores inteiros.')
        keys = ((r.astype(np.uint32) << 16) |
                (g.astype(np.uint32) << 8) | b.astype(np.uint32))
        transparent = np.zeros(r.shape, dtype=bool)
        if alpha is not None:
            a = np.asarray(alpha)
            if a.shape != r.shape:
                raise RS2Error('Canal alfa com dimensão incompatível.')
            if np.any((a != 0) & (a != 255)):
                raise RS2Error('Canal alfa semitransparente: RGB não pode ser classificado sem perdas.')
            transparent = a == 0

        pos = np.searchsorted(self.keys, keys)
        bounded = np.minimum(pos, len(self.keys) - 1)
        valid = (pos < len(self.keys)) & (self.keys[bounded] == keys)
        bad = ~valid & ~transparent
        if np.any(bad):
            x = int(np.flatnonzero(bad)[0])
            address = f'linha {y + 1}, coluna {x + 1}' if y is not None else f'coluna {x + 1}'
            raise RS2Error(
                f'O TIFF contém a cor RGB #{int(keys[x]):06X} em {address}, '
                'ausente da paleta do RS2 de referência. Confira se são '
                'o mesmo mapa e se as cores não foram alteradas por edição ou compressão.')
        result = self.codes[bounded].copy()
        result[transparent] = 0
        return result


def discover_rgb_palette(ds, max_colors=32769):
    """Descobre cores presentes em RGB(A) GDAL sem criar classes semânticas fictícias.

    Retorna uma paleta determinística: código 0 para branco, se presente;
    ou para pixels transparentes; na ausência de ambos, a menor cor RGB.
    Os códigos são NOVOS, não equivalem aos valores categóricos antigos.
    """
    from .rs2_format import RS2Error

    width, height = ds.RasterXSize, ds.RasterYSize
    seen = set()
    has_transparency = False
    for y in range(0, height, 128):
        size = min(128, height-y)
        data = ds.ReadAsArray(0, y, width, size)
        if data is None or data.shape != (ds.RasterCount, size, width):
            raise RS2Error(f'Falha ao examinar as cores do TIFF, linha {y+1}.')
        r, g, b = (data[i].astype(np.uint32) for i in range(3))
        codes = (r << 16) | (g << 8) | b
        if ds.RasterCount == 4:
            alpha = data[3]
            if np.any((alpha != 0) & (alpha != 255)):
                raise RS2Error('TIFF tem pixels semitransparentes: não é possível reconstruir classes sem perda.')
            has_transparency |= bool(np.any(alpha == 0))
            codes = codes[alpha != 0]
        batch = np.unique(codes)
        seen.update(int(v) for v in batch)
        if len(seen) > max_colors:
            raise RS2Error(
                f'O TIFF possui mais de {max_colors} cores distintas. '
                'Pode ser fotografia ou raster interpolado; não é possível '
                'representá-lo como classes RS2 sem generalização.')
    white = 0xFFFFFF
    if white in seen:
        first = white
    elif has_transparency:
        first = white
    elif seen:
        first = min(seen)
    else:
        first = white
    ordered = [first] + sorted(seen - {first})
    if len(ordered) > max_colors:
        raise RS2Error('O raster tem cores demais para o formato RS2.')
    colors = [((k >> 16) & 255, (k >> 8) & 255, k & 255, 0) for k in ordered]
    labels = [f'Cor #{k:06X}' for k in ordered]
    if first == white and (white in seen or has_transparency):
        labels[0] = 'FUNDO (branco/transparente)'
    return labels, colors
