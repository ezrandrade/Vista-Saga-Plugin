"""Gera o caso de teste sintético do Voronoi com atrito para rodar no Vista SAGA original.

Uso: python scripts/gerar_caso_atrito.py PASTA_DE_SAIDA

Cria teste_atrito.rs2, pontos_pixel.txt, pontos_utm.txt e mapa_previa.png (requer Pillow).
O LEIA-ME com o roteiro está em docs/CONTEXTO_SESSOES_HISTORICO_ate_1.4.2.md. Os dados não representam lugar real.
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from geosaga.rs2_format import RS2Header, write_rs2, RS2Reader
from PIL import Image, ImageDraw

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
W, H, CEL = 80, 60, 10
XMIN, YMIN = 500000, 8900000
XMAX, YMAX = XMIN + W*CEL, YMIN + H*CEL

m = np.full((H, W), 1, dtype=np.uint16)          # atrito baixo
m[:, 40:] = 2                                     # atrito medio a leste
m[:, 30:40] = 3                                   # faixa de atrito alto
m[25:35, 30:40] = 1                               # corredor de atrito baixo na faixa
m[5:20, 55:70] = 3                                # bloco de atrito alto

labels = ['FUNDO', 'Atrito baixo', 'Atrito medio', 'Atrito alto']
colors = [(255,255,255,0), (200,230,170,0), (250,210,120,0), (190,80,60,0)]
notas  = [1, 1, 3, 5]
hdr = RS2Header(width=W, height=H, xmin=XMIN, ymin=YMIN, xmax=XMAX, ymax=YMAX,
                labels=labels, colors=colors)
rs2 = os.path.join(out, 'teste_atrito.rs2')
write_rs2(rs2, hdr, list(m))

# conferência: relê e compara
r = RS2Reader(rs2)
back = np.array(list(r.rows()) if hasattr(r, 'rows') else r.read_array())
assert (back == m).all(), 'releitura divergente'

# pontos: (nome, massa, coluna, linha), contagem a partir de 0
pts = [('Polo A', 9, 12, 15), ('Polo B', 4, 60, 50), ('Polo C', 1, 72, 10)]
for _, _, c, l in pts:
    assert m[l, c] != 3 and 0 <= c < W and 0 <= l < H

def grava(nome, linhas):
    with open(os.path.join(out, nome), 'w', encoding='cp1252', newline='\r\n') as f:
        for s in linhas: f.write(s + '\n')

at = ['[ATRITOS]'] + [str(n) for n in notas]
grava('pontos_pixel.txt', [f'{n};{mm};{c}:{l}' for n, mm, c, l in pts] + at)
grava('pontos_utm.txt', [f'{n};{mm};{XMIN + c*CEL + CEL//2}:{YMAX - l*CEL - CEL//2}'
                         for n, mm, c, l in pts] + at)

# pré-visualização ampliada
Z = 8
img = Image.new('RGB', (W*Z, H*Z)); d = ImageDraw.Draw(img)
for y in range(H):
    for x in range(W):
        d.rectangle([x*Z, y*Z, x*Z+Z-1, y*Z+Z-1], fill=colors[m[y, x]][:3])
for n, mm, c, l in pts:
    d.rectangle([c*Z, l*Z, c*Z+Z-1, l*Z+Z-1], fill=(0,0,0))
    t = f'{n[-1]} (M={mm}) col {c}, lin {l}'
    x0 = c*Z+Z+3 if c < W-20 else c*Z-3-int(d.textlength(t))
    d.text((x0, l*Z-4), t, fill=(0,0,0))
img.save(os.path.join(out, 'mapa_previa.png'))
print(open(os.path.join(out,'pontos_pixel.txt'),'rb').read())
print(open(os.path.join(out,'pontos_utm.txt'),'rb').read())
print(os.path.getsize(rs2), 'bytes; classes', np.unique(m, return_counts=True))
