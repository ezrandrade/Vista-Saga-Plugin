"""Codificador GIF89a em Python puro, sem FFmpeg/Pillow em tempo de execução.

Recebe quadros RGB de dimensões idênticas. Preserva integralmente todas as
cores quando o conjunto de quadros possui até 256 cores; acima disso, aplica
quantização determinística 3-3-2 (8 bits), evitando dependências externas.
"""
from pathlib import Path
import struct


def _compress_lzw(pixels):
    """Códigos GIF-LZW, bytes com ordem LSB, tamanho inicial 8."""
    pixels = bytes(pixels)
    clear = 256
    finish = 257
    table = {}
    code_size = 9
    next_code = 258
    output = bytearray()
    bit_buffer = 0
    bit_count = 0

    def emit(code, bits):
        nonlocal bit_buffer, bit_count
        bit_buffer |= code << bit_count
        bit_count += bits
        while bit_count >= 8:
            output.append(bit_buffer & 255)
            bit_buffer >>= 8
            bit_count -= 8

    emit(clear, code_size)
    if not pixels:
        emit(finish, code_size)
        if bit_count: output.append(bit_buffer & 255)
        return bytes(output)
    prior = pixels[0]
    for value in pixels[1:]:
        key = (prior, value)
        found = table.get(key)
        if found is not None:
            prior = found
            continue
        emit(prior, code_size)
        if next_code < 4096:
            table[key] = next_code
            next_code += 1
            # GIF decoder only installs the dictionary entry on receipt of
            # the NEXT code. A threshold one entry later aligns bit widths.
            if next_code > (1 << code_size) and code_size < 12:
                code_size += 1
        else:
            emit(clear, code_size)
            table.clear()
            code_size = 9
            next_code = 258
        prior = value
    emit(prior, code_size)
    emit(finish, code_size)
    if bit_count:
        output.append(bit_buffer & 255)
    return bytes(output)


def _palette(frames):
    # A análise global é necessária para manter as mesmas cores em todos os
    # quadros, evitando mudança de cores entre anos.
    colors = {}
    for frame in frames:
        for offset in range(0, len(frame), 3):
            rgb = frame[offset:offset+3]
            if rgb not in colors:
                if len(colors) == 256:
                    return None
                colors[rgb] = len(colors)
    return colors


def _encode_frames(frames, palette):
    indexed = []
    if palette is not None:
        for frame in frames:
            indexed.append(bytes(palette[frame[i:i+3]] for i in range(0,len(frame),3)))
        colors = list(palette)
        colors.extend([b'\0\0\0'] * (256-len(colors)))
        return indexed, b''.join(colors), False
    pal = bytearray()
    for n in range(256):
        r = (n >> 5) & 7
        g = (n >> 2) & 7
        b = n & 3
        pal.extend((r * 255 // 7, g * 255 // 7, b * 255 // 3))
    for frame in frames:
        out = bytearray(len(frame)//3)
        for j, i in enumerate(range(0,len(frame),3)):
            out[j] = (frame[i] & 0xE0) | ((frame[i+1] & 0xE0) >> 3) | (frame[i+2] >> 6)
        indexed.append(bytes(out))
    return indexed, bytes(pal), True


def encode_gif(path, rgb_frames, width, height, *, delay_cs=100, loop=0, max_pixels=3_000_000):
    """Grava GIF animado a partir de bytes RGB888, retorna metadados.

    path: caminho final. delay_cs: centésimos de segundo por quadro.
    loop=0 repete indefinidamente; 1 executa duas vezes conforme GIF NETSCAPE.
    """
    width,height,delay_cs,loop = map(int,(width,height,delay_cs,loop))
    if width <= 0 or height <= 0 or width > 65535 or height > 65535:
        raise ValueError('Dimensões do GIF inválidas.')
    if width * height > max_pixels:
        raise ValueError('GIF excede o limite de pixels por quadro; reduza as dimensões.')
    if not 2 <= delay_cs <= 65535:
        raise ValueError('Intervalo entre quadros deve estar entre 0,02 e 655,35 s.')
    if not 0 <= loop <= 65535:
        raise ValueError('Repetições fora do intervalo GIF.')
    frames = [bytes(frame) for frame in rgb_frames]
    if not frames:
        raise ValueError('Adicione pelo menos uma imagem.')
    expected = width*height*3
    if any(len(frame) != expected for frame in frames):
        raise ValueError('Todos os quadros precisam ter dimensões RGB idênticas.')
    indices, colors, quantized = _encode_frames(frames, _palette(frames))
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + '.part')
    try:
        with temporary.open('wb') as f:
            f.write(b'GIF89a')
            f.write(struct.pack('<HHBBB',width,height,0xF7,0,0))
            f.write(colors)
            f.write(b'\x21\xFF\x0BNETSCAPE2.0\x03\x01')
            f.write(struct.pack('<H',loop))
            f.write(b'\0')
            for frame in indices:
                f.write(b'\x21\xF9\x04\0')
                f.write(struct.pack('<H',delay_cs))
                f.write(b'\0\0')
                f.write(b'\x2C')
                f.write(struct.pack('<HHHHB',0,0,width,height,0))
                f.write(b'\x08')
                packed = _compress_lzw(frame)
                for off in range(0,len(packed),255):
                    segment = packed[off:off+255]
                    f.write(bytes((len(segment),)))
                    f.write(segment)
                f.write(b'\0')
            f.write(b'\x3B')
        temporary.replace(target)
    finally:
        if temporary.exists(): temporary.unlink()
    return {'path':str(target), 'frames':len(frames),'width':width,'height':height,
            'palette_quantized':quantized,'delay_cs':delay_cs}
