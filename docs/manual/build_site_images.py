"""Imagens do site oficial (vistasagaplugin.wordpress.com): uma janela por módulo, versão atual.

Uso, na raiz do repositório:
    QT_SCALE_FACTOR=2 QT_QPA_PLATFORM=offscreen python3.12 docs/manual/capture_windows.py <trabalho> pt
    python3 docs/manual/build_site_images.py <trabalho>/pt/janelas <saida>

As capturas (dados sintéticos) recebem barra de título no estilo do sistema, borda e sombra suave, para
substituir as capturas antigas da página inicial. Saída em PNG com resolução 2x (o WordPress reduz).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

# (captura, nome do arquivo no site, título real da janela)
SHOTS = [
    ('assinatura_raster', '01_assinatura', 'Vista Saga Plugin - Assinatura'),
    ('monitoria_raster', '02_monitoria', 'Vista Saga Plugin - Monitoria'),
    ('avaliacao_raster', '03_avaliacao', 'Vista Saga Plugin - Avaliação'),
    ('voronoi_raster', '04_analises_voronoi', 'Vista Saga Plugin - Análises Voronoi'),
    ('combinacao_raster', '05_combinacao_mapas', 'Vista Saga Plugin - Combinação de Mapas'),
    ('conversor', '06_conversor_formatos', 'Vista Saga Plugin - Conversor de Formatos'),
    ('sequenciador', '07_sequenciador_mapas', 'Vista Saga Plugin - Sequenciador de Mapas'),
]


def framed(shot, title, scale=2):
    body = Image.open(shot).convert('RGB')
    w, h = body.size
    bar = 32 * scale
    border = 1 * scale
    pad = 18 * scale
    win = Image.new('RGB', (w + 2 * border, h + bar + 2 * border), (190, 190, 190))
    inner = Image.new('RGB', (w, h + bar), (255, 255, 255))
    draw = ImageDraw.Draw(inner)
    draw.rectangle([0, 0, w, bar], fill=(243, 243, 243))
    draw.line([0, bar - 1, w, bar - 1], fill=(225, 225, 225), width=1)
    icon = Image.open(os.path.join(ROOT, 'geosaga', 'icons', 'icon_48.png')).convert('RGBA')
    size = 18 * scale
    icon = icon.resize((size, size), Image.LANCZOS)
    inner.paste(icon, (10 * scale, (bar - size) // 2), icon)
    font = ImageFont.truetype(FONT, 12 * scale)
    draw.text((36 * scale, bar // 2), title, font=font, fill=(30, 30, 30), anchor='lm')
    cx, cy, r = w - 22 * scale, bar // 2, 5 * scale
    draw.line([cx - r, cy - r, cx + r, cy + r], fill=(60, 60, 60), width=scale)
    draw.line([cx - r, cy + r, cx + r, cy - r], fill=(60, 60, 60), width=scale)
    inner.paste(body, (0, bar))
    win.paste(inner, (border, border))
    # sombra suave sobre fundo branco
    canvas = Image.new('RGB', (win.width + 2 * pad, win.height + 2 * pad), (255, 255, 255))
    shadow = Image.new('L', canvas.size, 0)
    ImageDraw.Draw(shadow).rectangle([pad, pad + 3 * scale, pad + win.width, pad + win.height + 3 * scale],
                                     fill=70)
    shadow = shadow.filter(ImageFilter.GaussianBlur(8 * scale))
    canvas.paste((150, 150, 150), (0, 0), shadow)
    canvas.paste(win, (pad, pad))
    return canvas


def main(shots, out):
    os.makedirs(out, exist_ok=True)
    for name, target, title in SHOTS:
        image = framed(os.path.join(shots, f'{name}.png'), title)
        path = os.path.join(out, f'{target}.png')
        image.save(path, optimize=True)
        print(path, image.size)


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
