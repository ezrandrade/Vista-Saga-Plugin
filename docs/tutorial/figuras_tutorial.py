"""Figuras do tutorial, desenhadas a partir dos arquivos que os módulos gravaram (nada é recalculado aqui).

Uso:  python3.12 docs/tutorial/figuras_tutorial.py <trabalho> [pt|en|es]
"""
import csv
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from osgeo import gdal, ogr  # noqa: E402

SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
INK, MUTED, GRID = '#1f2933', '#616e7c', '#d9dee3'
USO_RGB = {1: '#d73027', 2: '#1a783c', 3: '#f0c846', 4: '#b4dc78', 5: '#3182bd'}
SOLO_RGB = {1: '#cd853f', 2: '#b22222', 3: '#a0a0c8'}
DECL_RGB = {1: '#edf8e9', 2: '#bae4b3', 3: '#74c476', 4: '#238b45'}
EXTENT = (0, 2, 0, 2)  # km

T = {
    'pt': {'uso': ['Área urbana', 'Vegetação nativa', 'Agricultura', 'Pastagem', 'Água'],
           'solos': ['Argissolo', 'Latossolo', 'Neossolo flúvico'],
           'decl': ['Plano (0-3%)', 'Suave ondulado (3-8%)', 'Ondulado (8-20%)', 'Forte ondulado (> 20%)'],
           'bairros': ['Beira-Rio', 'Centro', 'Alto da Serra', 'Porto', 'Jardim Novo', 'Vila Verde'],
           'p_uso2000': 'Uso do solo 2000', 'p_uso2020': 'Uso do solo 2020', 'p_solos': 'Solos',
           'p_decl': 'Declividade', 'p_bairros': 'Bairros e escolas', 'km': 'km',
           'sig_title': 'Uso do solo 2020: % da área de cada recorte', 'sig_groups': ['Centro', 'Beira-Rio', 'Vila Serena inteira'],
           'mon_map': 'Transições 2000 → 2020', 'perm': 'Permanência', 'mon_bar': 'Área por classe (ha)',
           'trans': {(4, 1): 'Pastagem → Área urbana', (2, 4): 'Vegetação → Pastagem', (2, 1): 'Vegetação → Área urbana',
                     (2, 3): 'Vegetação → Agricultura', (3, 1): 'Agricultura → Área urbana'},
           'comb_title': 'Uso do solo 2020 × Solos: área de cada combinação (ha)',
           'av_map': 'Aptidão à expansão urbana (nota 0 a 10)', 'av_bar': 'Área por nota final (ha)', 'water': 'Água (não avaliada)',
           'vor': ['Simples', 'Com Massa (matrículas)', 'Com Atrito'], 'seq': ['2000', '2010', '2020'],
           'conv_title': ['bairros.gpkg (vetor)', 'bairros.tif (Conversor)']},
    'en': {'uso': ['Urban area', 'Native vegetation', 'Farming', 'Pasture', 'Water'],
           'solos': ['Argisol', 'Latosol', 'Fluvic neosol'],
           'decl': ['Flat (0-3%)', 'Gently rolling (3-8%)', 'Rolling (8-20%)', 'Strongly rolling (> 20%)'],
           'bairros': ['Riverside', 'Downtown', 'Hilltop', 'Harbour', 'New Garden', 'Green Village'],
           'p_uso2000': 'Land use 2000', 'p_uso2020': 'Land use 2020', 'p_solos': 'Soils',
           'p_decl': 'Slope', 'p_bairros': 'Districts and schools', 'km': 'km',
           'sig_title': 'Land use 2020: % of the area of each cut', 'sig_groups': ['Downtown', 'Riverside', 'Whole Vila Serena'],
           'mon_map': 'Transitions 2000 → 2020', 'perm': 'Persistence', 'mon_bar': 'Area per class (ha)',
           'trans': {(4, 1): 'Pasture → Urban', (2, 4): 'Vegetation → Pasture', (2, 1): 'Vegetation → Urban',
                     (2, 3): 'Vegetation → Farming', (3, 1): 'Farming → Urban'},
           'comb_title': 'Land use 2020 × Soils: area of each combination (ha)',
           'av_map': 'Suitability for urban growth (score 0 to 10)', 'av_bar': 'Area per final score (ha)', 'water': 'Water (not evaluated)',
           'vor': ['Simple', 'With Mass (enrolment)', 'With Friction'], 'seq': ['2000', '2010', '2020'],
           'conv_title': ['bairros.gpkg (vector)', 'bairros.tif (Format converter)']},
    'es': {'uso': ['Área urbana', 'Vegetación nativa', 'Agricultura', 'Pastizal', 'Agua'],
           'solos': ['Argisol', 'Latosol', 'Neosol flúvico'],
           'decl': ['Plano (0-3%)', 'Suave ondulado (3-8%)', 'Ondulado (8-20%)', 'Fuerte ondulado (> 20%)'],
           'bairros': ['Ribera', 'Centro', 'Alto de la Sierra', 'Puerto', 'Jardín Nuevo', 'Villa Verde'],
           'p_uso2000': 'Uso del suelo 2000', 'p_uso2020': 'Uso del suelo 2020', 'p_solos': 'Suelos',
           'p_decl': 'Pendiente', 'p_bairros': 'Barrios y escuelas', 'km': 'km',
           'sig_title': 'Uso del suelo 2020: % del área de cada recorte', 'sig_groups': ['Centro', 'Ribera', 'Vila Serena entera'],
           'mon_map': 'Transiciones 2000 → 2020', 'perm': 'Permanencia', 'mon_bar': 'Área por clase (ha)',
           'trans': {(4, 1): 'Pastizal → Urbana', (2, 4): 'Vegetación → Pastizal', (2, 1): 'Vegetación → Urbana',
                     (2, 3): 'Vegetación → Agricultura', (3, 1): 'Agricultura → Urbana'},
           'comb_title': 'Uso del suelo 2020 × Suelos: área de cada combinación (ha)',
           'av_map': 'Aptitud para la expansión urbana (nota 0 a 10)', 'av_bar': 'Área por nota final (ha)', 'water': 'Agua (no evaluada)',
           'vor': ['Simple', 'Con masa (matrícula)', 'Con fricción'], 'seq': ['2000', '2010', '2020'],
           'conv_title': ['bairros.gpkg (vector)', 'bairros.tif (Conversor)']},
}


def _read(path):
    ds = gdal.Open(path)
    array = ds.GetRasterBand(1).ReadAsArray()
    ds = None
    return array


def _style(ax, title):
    ax.set_title(title, fontsize=10, color=INK, loc='left', pad=6)
    ax.set_xticks([0, 1, 2])
    ax.set_yticks([0, 1, 2])
    ax.tick_params(labelsize=7, colors=MUTED, length=0)
    for spine in ax.spines.values():
        spine.set_color(GRID)


def _classmap(ax, array, colors, title):
    keys = sorted(colors)
    lut = np.zeros(max(keys) + 1, dtype=int)
    for i, k in enumerate(keys):
        lut[k] = i
    ax.imshow(lut[array], cmap=ListedColormap([colors[k] for k in keys]), vmin=0, vmax=len(keys) - 1,
              extent=EXTENT, interpolation='nearest')
    _style(ax, title)


def _legend(ax, colors, names, ncol=1, loc='upper left', anchor=(1.02, 1)):
    ax.legend(handles=[Patch(facecolor=c, edgecolor='white', label=n) for c, n in zip(colors, names)],
              loc=loc, bbox_to_anchor=anchor, fontsize=7.5, frameon=False, ncol=ncol)


def _points(data):
    ds = ogr.Open(os.path.join(data, 'escolas.gpkg'))
    pts = [(f.GetGeometryRef().GetX(), f.GetGeometryRef().GetY(), f.GetField('NOME'), f.GetField('MATRICULAS'))
           for f in ds.GetLayer(0)]
    ds = None
    return [((x - 200000) / 1000, (y - 8930000) / 1000, n, m) for x, y, n, m in pts]


def _save(fig, path):
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def build(work, lang):
    t = T[lang]
    data, res = os.path.join(work, 'dados'), os.path.join(work, 'resultados')
    out = os.path.join(work, f'figuras_{lang}')
    os.makedirs(out, exist_ok=True)
    numbers = json.load(open(os.path.join(work, 'numeros.json'), encoding='utf-8'))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.edgecolor': GRID})
    pts = _points(data)

    # f01 - dados
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6))
    _classmap(axes[0], _read(os.path.join(data, 'uso_solo_2000.tif')), USO_RGB, t['p_uso2000'])
    _classmap(axes[1], _read(os.path.join(data, 'uso_solo_2020.tif')), USO_RGB, t['p_uso2020'])
    _legend(axes[1], list(USO_RGB.values()), t['uso'], ncol=3, loc='upper left', anchor=(-1.15, -0.08))
    _classmap(axes[2], _read(os.path.join(data, 'solos.tif')), SOLO_RGB, t['p_solos'])
    _legend(axes[2], list(SOLO_RGB.values()), t['solos'], loc='upper left', anchor=(0, -0.08))
    _classmap(axes[3], _read(os.path.join(data, 'declividade.tif')), DECL_RGB, t['p_decl'])
    _legend(axes[3], list(DECL_RGB.values()), t['decl'], ncol=2, loc='upper left', anchor=(-0.05, -0.08))
    _save(fig, os.path.join(out, 'f01_dados.png'))

    # f02 - bairros e escolas
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    ax.imshow(np.ones((2, 2)), cmap=ListedColormap(['#f5f7fa']), extent=EXTENT)
    xs, ys = [0, 0.7, 1.3, 2], [2, 1, 0]
    order = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)]
    for (col, row), name in zip(order, t['bairros']):
        ax.add_patch(plt.Rectangle((xs[col], ys[row + 1]), xs[col + 1] - xs[col], ys[row] - ys[row + 1],
                                   fill=False, edgecolor=MUTED, linewidth=1))
        ax.text((xs[col] + xs[col + 1]) / 2, ys[row] - 0.08, name, ha='center', va='top', fontsize=8.5, color=INK)
    for x, y, name, mass in pts:
        ax.scatter(x, y, s=mass / 6, color=SERIES[0], edgecolor='white', linewidth=1.5, zorder=3)
        ax.text(x, y + 0.07, f'{name} ({mass})', ha='center', va='bottom', fontsize=6.3, color=MUTED,
                bbox=dict(facecolor='#f5f7fa', edgecolor='none', pad=0.6))
    _style(ax, t['p_bairros'])
    _save(fig, os.path.join(out, 'f02_bairros_escolas.png'))

    # f03 - conversor: vetor x raster
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.9))
    for (col, row), name in zip(order, t['bairros']):
        axes[0].add_patch(plt.Rectangle((xs[col], ys[row + 1]), xs[col + 1] - xs[col], ys[row] - ys[row + 1],
                                        facecolor=SERIES[order.index((col, row))], alpha=.35, edgecolor=INK))
    axes[0].set_xlim(0, 2)
    axes[0].set_ylim(0, 2)
    axes[0].set_aspect('equal')
    _style(axes[0], t['conv_title'][0])
    _classmap(axes[1], _read(os.path.join(res, 'bairros.tif')), {i + 1: SERIES[i] for i in range(6)}, t['conv_title'][1])
    _legend(axes[1], SERIES[:6], [f'{i + 1} - {n}' for i, n in enumerate(t['bairros'])])
    _save(fig, os.path.join(out, 'f03_conversor.png'))

    # f04 - assinatura: % área assinada do uso 2020 (Centro, Beira-Rio, Vila Serena inteira)
    sig = numbers['assinatura']
    centro = sig['2']['uso_solo_2020.tif']   # 2 = Centro, 1 = Beira-Rio (códigos dos bairros)
    beira = sig['1']['uso_solo_2020.tif']
    whole = _read(os.path.join(data, 'uso_solo_2020.tif'))
    total = [float((whole == c).mean() * 100) for c in range(1, 6)]
    rows = [k for k in centro if k != '0']
    values = [[centro[k][1] for k in rows], [beira[k][1] for k in rows], total]
    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    height = 0.26
    y = np.arange(len(rows))
    for i, (vals, label) in enumerate(zip(values, t['sig_groups'])):
        bars = ax.barh(y + (i - 1) * height, vals, height=height - 0.03, color=SERIES[i], label=label)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_width() + 0.6, bar.get_y() + bar.get_height() / 2, f'{v:.1f}', va='center',
                    fontsize=7, color=INK)
    ax.set_yticks(y, t['uso'], fontsize=8.5, color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, max(max(v) for v in values) * 1.15)
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    ax.tick_params(axis='x', labelsize=7, colors=MUTED)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.set_title(t['sig_title'], fontsize=10, color=INK, loc='left')
    ax.legend(fontsize=8, frameon=False, loc='lower right')
    _save(fig, os.path.join(out, 'f04_assinatura.png'))

    # f05 - monitoria: mapa de transições + área por classe 2000 x 2020
    before = _read(os.path.join(data, 'uso_solo_2000.tif'))
    after = _read(os.path.join(data, 'uso_solo_2020.tif'))
    code = np.zeros(before.shape, dtype=int)
    colors = ['#e4e7eb']
    labels = [t['perm']]
    palette = [SERIES[1], SERIES[3], SERIES[7], SERIES[2], SERIES[4]]
    for i, ((a, b), name) in enumerate(t['trans'].items(), 1):
        code[(before == a) & (after == b)] = i
        colors.append(palette[i - 1])
        labels.append(name)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.1), gridspec_kw={'width_ratios': [1, 1.1]})
    axes[0].imshow(code, cmap=ListedColormap(colors), vmin=0, vmax=len(colors) - 1, extent=EXTENT,
                   interpolation='nearest')
    _style(axes[0], t['mon_map'])
    _legend(axes[0], colors, labels, loc='upper left', anchor=(0, -0.07), ncol=2)
    area = [[float((m == c).sum() * 0.01) for c in range(1, 6)] for m in (before, after)]
    y = np.arange(5)
    for i, (vals, label, color) in enumerate(zip(area, ['2000', '2020'], [SERIES[0], SERIES[1]])):
        bars = axes[1].barh(y + (i - 0.5) * 0.36, vals, height=0.33, color=color, label=label)
        for bar, v in zip(bars, vals):
            axes[1].text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2, f'{v:.1f}', va='center',
                         fontsize=7, color=INK)
    axes[1].set_yticks(y, t['uso'], fontsize=8.5)
    axes[1].invert_yaxis()
    axes[1].xaxis.grid(True, color=GRID)
    axes[1].set_axisbelow(True)
    axes[1].tick_params(axis='x', labelsize=7, colors=MUTED)
    for side in ('top', 'right', 'left'):
        axes[1].spines[side].set_visible(False)
    axes[1].set_title(t['mon_bar'], fontsize=10, color=INK, loc='left')
    axes[1].legend(fontsize=8, frameon=False, loc='lower right')
    _save(fig, os.path.join(out, 'f05_monitoria.png'))

    # f06 - combinação: barras ordenadas
    with open(os.path.join(res, 'uso2020_x_solos_combinacoes.csv'), encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream, delimiter=';'))
    rows.sort(key=lambda r: -float(r['AREA_HA']))
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    labels = [f"{t['uso'][int(r['COD_01']) - 1]} | {t['solos'][int(r['COD_02']) - 1]}" for r in rows]
    vals = [float(r['AREA_HA']) for r in rows]
    bars = ax.barh(range(len(rows)), vals, color=[USO_RGB[int(r['COD_01'])] for r in rows], height=0.72)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2, f'{v:.1f}', va='center', fontsize=7, color=INK)
    ax.set_yticks(range(len(rows)), labels, fontsize=7.8)
    ax.invert_yaxis()
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    ax.tick_params(axis='x', labelsize=7, colors=MUTED)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.set_title(t['comb_title'], fontsize=10, color=INK, loc='left')
    _save(fig, os.path.join(out, 'f06_combinacao.png'))

    # f07 - avaliação: mapa + área por nota
    grid = _read(os.path.join(res, 'aptidao_expansao.tif')).astype(float)
    masked = np.ma.masked_where(grid == -9999, grid)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.1), gridspec_kw={'width_ratios': [1, 1]})
    axes[0].imshow(np.where(grid == -9999, 1, np.nan), cmap=ListedColormap(['#9fb3c8']), extent=EXTENT)
    image = axes[0].imshow(masked, cmap='YlGn', vmin=0, vmax=10, extent=EXTENT, interpolation='nearest')
    _style(axes[0], t['av_map'])
    bar = fig.colorbar(image, ax=axes[0], fraction=0.046, pad=0.03)
    bar.ax.tick_params(labelsize=7, colors=MUTED)
    _legend(axes[0], ['#9fb3c8'], [t['water']], loc='upper left', anchor=(0, -0.07))
    per = numbers['avaliacao']['area_por_nota_ha']
    notes = sorted(per, key=int)
    cmap = plt.get_cmap('YlGn')
    bars = axes[1].bar(notes, [per[n] for n in notes], color=[cmap(int(n) / 10) for n in notes], edgecolor=MUTED,
                       linewidth=0.4, width=0.7)
    for b, n in zip(bars, notes):
        axes[1].text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, f'{per[n]:.1f}', ha='center', fontsize=7.5,
                     color=INK)
    axes[1].yaxis.grid(True, color=GRID)
    axes[1].set_axisbelow(True)
    axes[1].tick_params(labelsize=8, colors=MUTED)
    for side in ('top', 'right'):
        axes[1].spines[side].set_visible(False)
    axes[1].set_title(t['av_bar'], fontsize=10, color=INK, loc='left')
    _save(fig, os.path.join(out, 'f07_avaliacao.png'))

    # f08 - Voronoi: simples, com massa, com atrito
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
    for ax, name, title in zip(axes, ('simples', 'com_massa', 'com_atrito'), t['vor']):
        regions = _read(os.path.join(res, f'voronoi_{name}.tif'))
        ax.imshow(np.clip(regions, 1, 6) - 1, cmap=ListedColormap(SERIES[:6]), vmin=0, vmax=5, extent=EXTENT,
                  interpolation='nearest', alpha=0.55)
        river = _read(os.path.join(data, 'uso_solo_2020.tif')) == 5
        ax.imshow(np.where(river, 1, np.nan), cmap=ListedColormap(['#3182bd']), extent=EXTENT, alpha=0.6)
        for i, (x, y, _n, mass) in enumerate(pts):
            size = mass / 6 if name == 'com_massa' else 60
            ax.scatter(x, y, s=size, color=SERIES[i], edgecolor='white', linewidth=1.6, zorder=3)
        _style(ax, title)
    _legend(axes[2], SERIES[:6], [p[2] for p in pts])
    _save(fig, os.path.join(out, 'f08_voronoi.png'))

    # f09 - Sequenciador: quadros PNG gerados pelo próprio módulo
    frames = sorted(os.listdir(os.path.join(res, 'vila_serena_2000_2020_quadros_png')))
    fig, axes = plt.subplots(1, len(frames), figsize=(12, 4.2))
    for ax, frame in zip(axes, frames):
        ax.imshow(plt.imread(os.path.join(res, 'vila_serena_2000_2020_quadros_png', frame)))
        ax.set_axis_off()
    fig.tight_layout()
    _save(fig, os.path.join(out, 'f09_sequenciador.png'))
    print(lang, sorted(os.listdir(out)))


if __name__ == '__main__':
    work = os.path.abspath(sys.argv[1])
    for language in (sys.argv[2:] or ['pt']):
        build(work, language)
