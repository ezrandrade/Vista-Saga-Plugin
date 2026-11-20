"""Infográficos do manual do usuário (1.6.0), nos três idiomas.

Uso, na raiz do repositório:
    QT_QPA_PLATFORM=offscreen python docs/manual/build_figures.py <pasta_de_saida>

As figuras conceituais usam os próprios motores do plugin (Voronoi, Assinatura) sobre dados sintéticos,
para mostrar o comportamento real. Paleta categórica validada (skill de visualização, modo claro).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
INK, INK2, MUTED, GRID, SURFACE = '#0b0b0b', '#52514e', '#8a8984', '#e4e3df', '#ffffff'
BRAND = '#1f5f8b'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': INK,
                     'axes.edgecolor': GRID, 'axes.labelcolor': INK2, 'xtick.color': INK2,
                     'ytick.color': INK2, 'figure.facecolor': SURFACE, 'savefig.facecolor': SURFACE})

T = {
 'pt': {
  'modules': ['Assinatura', 'Monitoria', 'Avaliação', 'Análises Voronoi', 'Combinação de Mapas',
              'Conversor de Formatos', 'Sequenciador de Mapas'],
  'module_q': ['Do que é feita\numa área?', 'O que mudou entre\ndois períodos?', 'Onde é mais\nadequado (ou crítico)?',
               'Qual a área de\ninfluência de cada ponto?', 'Que associações de\nclasses existem?',
               'Como levar dados entre\nRS2, GeoTIFF e vetor?', 'Como mostrar a evolução\nem animação?'],
  'overview_title': 'Sete módulos, uma lógica de uso',
  'flow': ['1. Entradas', '2. Configuração', '3. Executar', '4. Resultado', '5. Relatórios'],
  'flow_sub': ['camadas do QGIS\nou arquivos', 'campos com dicas\n(caixas amarelas)', 'janela de progresso\ncom Cancelar',
               'temporário ("Módulo -\noperação") ou salvo', 'TXT e CSV\nem português'],
  'flow_title': 'Rotina comum a todos os módulos',
  'sig_title': 'Assinatura: a seleção na referência recorta todos os mapas',
  'sig_maps': ['Referência (bairros)\nseleção = limite', 'Uso do solo', 'Solos'],
  'sig_bar_title': 'Uso do solo dentro do limite\n(% Área asn.)',
  'sig_classes': ['Edificada', 'Vegetação', 'Água', 'Agricultura'],
  'sig_f1': '% Área asn. = área da classe no limite ÷ área do limite\n→ do que o lugar é feito (soma 100%)',
  'sig_f2': '% Categoria = área da classe no limite ÷ área da classe no mapa\n→ quanto da classe se concentra ali',
  'vor_title': 'Análises Voronoi: as quatro modalidades (calculadas pelo plugin)',
  'vor_modes': ['Simples\n(menor distância)', 'Com Massa\n(maior M/d²)', 'Com Atrito\n(menor custo pela reta)',
                'Com Massa e Atrito\n(menor custo ÷ M)'],
  'vor_river': 'faixa de atrito alto (nota 8)', 'vor_mass': 'massa',
  'mon_title': 'Monitoria: permanências e mudanças entre dois períodos',
  'mon_maps': ['Período inicial', 'Período final', 'Mapa de transições'],
  'mon_keep': 'permaneceu', 'mon_change': 'mudou', 'mon_matrix': 'Matriz de transição (células)',
  'mon_axes': ('Classe final', 'Classe inicial'),
  'aval_title': 'Avaliação: média ponderada das notas',
  'aval_maps': ['Critério A: uso do solo\n(peso 60%)', 'Critério B: solos\n(peso 40%)', 'Resultado (0 a 10)'],
  'aval_formula': 'nota final = Σ (peso × nota da classe) ÷ Σ pesos',
  'aval_scores': 'notas', 'aval_low': 'menos adequado', 'aval_high': 'mais adequado',
  'comb_title': 'Combinação de Mapas: cada associação de classes vira um código',
  'comb_maps': ['Mapa 1: uso do solo', 'Mapa 2: solos', 'Mapa combinado'],
  'conv_title': 'Conversor de Formatos: seis conversões entre três formatos',
  'conv_nodes': ['RS2\n(Vista SAGA)', 'GeoTIFF\n(raster)', 'Vetor\n(polígonos)'],
  'conv_ops': ['RS2 → GeoTIFF', 'GeoTIFF → RS2', 'RS2 → Vetor', 'Vetor → RS2', 'GeoTIFF → Vetor', 'Vetor → GeoTIFF'],
  'seq_title': 'Sequenciador de Mapas: quadros em ordem → GIF animado (e PNGs)',
  'seq_frame': 'quadro', 'seq_gif': 'GIF animado',
  'dash_title': 'Validação contra o Vista SAGA original e qualidade',
  'kpis': [('7', 'módulos'), ('3', 'idiomas'), ('184', 'dicas novas\nna 1.6.0'), ('545', 'testes\nautomáticos')],
  'dash_vor': 'Voronoi: células iguais ao Vista SAGA (%)',
  'dash_vor_cases': ['Simples', 'Com Massa', 'Atrito\n(raster)', 'Massa+Atrito\n(raster)', 'Atrito\n(vetor)',
                     'Massa+Atrito\n(vetor)'],
  'dash_sig': 'Assinatura: classes coincidentes (%)',
  'dash_sig_cases': ['Mapa inteiro', '4 bairros', 'Barro Duro'],
  'dash_note': 'Diferenças: fronteiras entre regiões (Voronoi) e células ligadas só pela diagonal (Assinatura).',
 },
 'en': {
  'modules': ['Signature', 'Monitoring', 'Evaluation', 'Voronoi Analyses', 'Map Combination',
              'Format Converter', 'Map Sequencer'],
  'module_q': ['What is an area\nmade of?', 'What changed between\ntwo periods?', 'Where is it most\nsuitable (or critical)?',
               'What is the influence\narea of each point?', 'Which class associations\nexist?',
               'How to move data between\nRS2, GeoTIFF and vector?', 'How to show change\nas an animation?'],
  'overview_title': 'Seven modules, one way of working',
  'flow': ['1. Inputs', '2. Settings', '3. Run', '4. Result', '5. Reports'],
  'flow_sub': ['QGIS layers\nor files', 'fields with tooltips\n(yellow boxes)', 'progress window\nwith Cancel',
               'temporary ("Module -\noperation") or saved', 'TXT and CSV\nin Portuguese'],
  'flow_title': 'Routine shared by every module',
  'sig_title': 'Signature: the selection on the reference cuts every map',
  'sig_maps': ['Reference (districts)\nselection = boundary', 'Land use', 'Soils'],
  'sig_bar_title': 'Land use inside the boundary\n(% signed area)',
  'sig_classes': ['Built-up', 'Vegetation', 'Water', 'Agriculture'],
  'sig_f1': '% signed area = class area in the boundary ÷ boundary area\n→ what the place is made of (adds up to 100%)',
  'sig_f2': '% category = class area in the boundary ÷ class area in the map\n→ how much of the class is concentrated there',
  'vor_title': 'Voronoi analyses: the four modes (computed by the plugin)',
  'vor_modes': ['Simple\n(shortest distance)', 'With mass\n(largest M/d²)', 'With friction\n(lowest cost along the line)',
                'Mass and friction\n(lowest cost ÷ M)'],
  'vor_river': 'high-friction strip (rating 8)', 'vor_mass': 'mass',
  'mon_title': 'Monitoring: persistence and change between two periods',
  'mon_maps': ['Initial period', 'Final period', 'Transition map'],
  'mon_keep': 'unchanged', 'mon_change': 'changed', 'mon_matrix': 'Transition matrix (cells)',
  'mon_axes': ('Final class', 'Initial class'),
  'aval_title': 'Evaluation: weighted mean of the scores',
  'aval_maps': ['Criterion A: land use\n(weight 60%)', 'Criterion B: soils\n(weight 40%)', 'Result (0 to 10)'],
  'aval_formula': 'final score = Σ (weight × class score) ÷ Σ weights',
  'aval_scores': 'scores', 'aval_low': 'less suitable', 'aval_high': 'more suitable',
  'comb_title': 'Map Combination: each association of classes becomes a code',
  'comb_maps': ['Map 1: land use', 'Map 2: soils', 'Combined map'],
  'conv_title': 'Format Converter: six conversions between three formats',
  'conv_nodes': ['RS2\n(Vista SAGA)', 'GeoTIFF\n(raster)', 'Vector\n(polygons)'],
  'conv_ops': ['RS2 → GeoTIFF', 'GeoTIFF → RS2', 'RS2 → Vector', 'Vector → RS2', 'GeoTIFF → Vector', 'Vector → GeoTIFF'],
  'seq_title': 'Map Sequencer: frames in order → animated GIF (and PNGs)',
  'seq_frame': 'frame', 'seq_gif': 'animated GIF',
  'dash_title': 'Validation against the original Vista SAGA and quality',
  'kpis': [('7', 'modules'), ('3', 'languages'), ('184', 'new tooltips\nin 1.6.0'), ('545', 'automated\ntests')],
  'dash_vor': 'Voronoi: cells equal to Vista SAGA (%)',
  'dash_vor_cases': ['Simple', 'Mass', 'Friction\n(raster)', 'Mass+Friction\n(raster)', 'Friction\n(vector)',
                     'Mass+Friction\n(vector)'],
  'dash_sig': 'Signature: matching classes (%)',
  'dash_sig_cases': ['Whole map', '4 districts', 'Barro Duro'],
  'dash_note': 'Differences: region boundaries (Voronoi) and cells joined only diagonally (Signature).',
 },
 'es': {
  'modules': ['Firma espacial', 'Monitoreo', 'Evaluación', 'Análisis de Voronoi', 'Combinación de mapas',
              'Conversor de formatos', 'Secuenciador de mapas'],
  'module_q': ['¿De qué está hecha\nun área?', '¿Qué cambió entre\ndos períodos?', '¿Dónde es más\nadecuado (o crítico)?',
               '¿Cuál es el área de\ninfluencia de cada punto?', '¿Qué asociaciones de\nclases existen?',
               '¿Cómo llevar datos entre\nRS2, GeoTIFF y vector?', '¿Cómo mostrar la evolución\nen animación?'],
  'overview_title': 'Siete módulos, una lógica de uso',
  'flow': ['1. Entradas', '2. Configuración', '3. Ejecutar', '4. Resultado', '5. Informes'],
  'flow_sub': ['capas de QGIS\no archivos', 'campos con ayudas\n(recuadros amarillos)', 'ventana de progreso\ncon Cancelar',
               'temporal ("Módulo -\noperación") o guardado', 'TXT y CSV\nen portugués'],
  'flow_title': 'Rutina común a todos los módulos',
  'sig_title': 'Firma espacial: la selección en la referencia recorta todos los mapas',
  'sig_maps': ['Referencia (barrios)\nselección = límite', 'Uso del suelo', 'Suelos'],
  'sig_bar_title': 'Uso del suelo dentro del límite\n(% área firmada)',
  'sig_classes': ['Edificada', 'Vegetación', 'Agua', 'Agricultura'],
  'sig_f1': '% área firmada = área de la clase en el límite ÷ área del límite\n→ de qué está hecho el lugar (suma 100%)',
  'sig_f2': '% categoría = área de la clase en el límite ÷ área de la clase en el mapa\n→ cuánto de la clase se concentra allí',
  'vor_title': 'Análisis de Voronoi: las cuatro modalidades (calculadas por el complemento)',
  'vor_modes': ['Simple\n(menor distancia)', 'Con masa\n(mayor M/d²)', 'Con fricción\n(menor costo por la recta)',
                'Con masa y fricción\n(menor costo ÷ M)'],
  'vor_river': 'franja de fricción alta (nota 8)', 'vor_mass': 'masa',
  'mon_title': 'Monitoreo: permanencias y cambios entre dos períodos',
  'mon_maps': ['Período inicial', 'Período final', 'Mapa de transiciones'],
  'mon_keep': 'permaneció', 'mon_change': 'cambió', 'mon_matrix': 'Matriz de transición (celdas)',
  'mon_axes': ('Clase final', 'Clase inicial'),
  'aval_title': 'Evaluación: media ponderada de las notas',
  'aval_maps': ['Criterio A: uso del suelo\n(peso 60%)', 'Criterio B: suelos\n(peso 40%)', 'Resultado (0 a 10)'],
  'aval_formula': 'nota final = Σ (peso × nota de la clase) ÷ Σ pesos',
  'aval_scores': 'notas', 'aval_low': 'menos adecuado', 'aval_high': 'más adecuado',
  'comb_title': 'Combinación de Mapas: cada asociación de clases se vuelve un código',
  'comb_maps': ['Mapa 1: uso del suelo', 'Mapa 2: suelos', 'Mapa combinado'],
  'conv_title': 'Conversor de Formatos: seis conversiones entre tres formatos',
  'conv_nodes': ['RS2\n(Vista SAGA)', 'GeoTIFF\n(ráster)', 'Vector\n(polígonos)'],
  'conv_ops': ['RS2 → GeoTIFF', 'GeoTIFF → RS2', 'RS2 → Vector', 'Vector → RS2', 'GeoTIFF → Vector', 'Vector → GeoTIFF'],
  'seq_title': 'Secuenciador de Mapas: cuadros en orden → GIF animado (y PNG)',
  'seq_frame': 'cuadro', 'seq_gif': 'GIF animado',
  'dash_title': 'Validación frente al Vista SAGA original y calidad',
  'kpis': [('7', 'módulos'), ('3', 'idiomas'), ('184', 'ayudas nuevas\nen la 1.6.0'), ('545', 'pruebas\nautomáticas')],
  'dash_vor': 'Voronoi: celdas iguales al Vista SAGA (%)',
  'dash_vor_cases': ['Simple', 'Masa', 'Fricción\n(ráster)', 'Masa+Fricción\n(ráster)', 'Fricción\n(vector)',
                     'Masa+Fricción\n(vector)'],
  'dash_sig': 'Firma espacial: clases coincidentes (%)',
  'dash_sig_cases': ['Mapa entero', '4 barrios', 'Barro Duro'],
  'dash_note': 'Diferencias: fronteras entre regiones (Voronoi) y celdas unidas solo por la diagonal (Firma espacial).',
 },
}
ICONS = ['assinatura_espacial', 'monitoria_espacial', 'avaliacao_espacial', 'analises_voronoi',
         'combinacao_mapas', 'conversor_formatos', 'sequenciador_mapas']


def _save(fig, path):
    fig.savefig(path, dpi=200, bbox_inches='tight', pad_inches=0.15)
    plt.close(fig)


def _icons(folder):
    """Ícones SVG dos módulos rasterizados com o Qt do QGIS."""
    from qgis.PyQt.QtCore import QSize
    from qgis.PyQt.QtGui import QImage, QPainter
    from qgis.PyQt.QtSvg import QSvgRenderer
    from qgis.PyQt.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    paths = []
    names = sorted(os.listdir(os.path.join(ROOT, 'geosaga', 'icons', 'modulos')))
    for stem in ICONS:
        match = next((n for n in names if n.startswith(stem.split('_')[0])), None)
        out = os.path.join(folder, f'icon_{stem}.png')
        if match:
            renderer = QSvgRenderer(os.path.join(ROOT, 'geosaga', 'icons', 'modulos', match))
            image = QImage(QSize(256, 256), QImage.Format.Format_ARGB32)
            image.fill(0)
            painter = QPainter(image)
            renderer.render(painter)
            painter.end()
            image.save(out)
        paths.append(out if match else None)
    return paths


def overview(t, out, icons):
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.4)
    ax.axis('off')
    ax.text(5, 5.15, t['overview_title'], ha='center', va='center', fontsize=15, weight='bold', color=BRAND)
    for i, (name, q) in enumerate(zip(t['modules'], t['module_q'])):
        col, row = i % 4, i // 4
        x = 0.25 + col * 2.45 + (1.22 if row == 1 else 0)
        y = 2.65 - row * 2.45
        ax.add_patch(FancyBboxPatch((x, y), 2.2, 2.1, boxstyle='round,pad=0.02,rounding_size=0.12',
                                    fc='#f6f8fb', ec=GRID, lw=1.2))
        ax.add_patch(Rectangle((x, y + 2.02), 2.2, 0.08, color=SERIES[i % len(SERIES)], lw=0))
        if icons[i]:
            img = plt.imread(icons[i])
            ax.imshow(img, extent=(x + 0.8, x + 1.4, y + 1.25, y + 1.85), zorder=3)
        if len(name) > 16:  # nomes longos em duas linhas, para caber no cartão
            cut = name.rfind(' ', 0, len(name) // 2 + 4)
            name = name[:cut] + '\n' + name[cut + 1:]
        ax.text(x + 1.1, y + 0.98, name, ha='center', va='center', fontsize=10, weight='bold', color=INK,
                linespacing=1.1)
        ax.text(x + 1.1, y + 0.38, q, ha='center', va='center', fontsize=8.4, color=INK2, linespacing=1.2)
    _save(fig, out)


def flow(t, out):
    fig, ax = plt.subplots(figsize=(10, 2.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2.6)
    ax.axis('off')
    ax.text(5, 2.4, t['flow_title'], ha='center', fontsize=13, weight='bold', color=BRAND)
    for i, (title, sub) in enumerate(zip(t['flow'], t['flow_sub'])):
        x = 0.1 + i * 2.0
        ax.add_patch(FancyBboxPatch((x, 0.35), 1.7, 1.55, boxstyle='round,pad=0.02,rounding_size=0.1',
                                    fc='#f6f8fb', ec=SERIES[0] if i == 2 else GRID, lw=1.6 if i == 2 else 1.1))
        ax.text(x + 0.85, 1.55, title, ha='center', va='center', fontsize=10.5, weight='bold')
        ax.text(x + 0.85, 0.9, sub, ha='center', va='center', fontsize=8.3, color=INK2, linespacing=1.25)
        if i < 4:
            ax.add_patch(FancyArrowPatch((x + 1.72, 1.12), (x + 1.98, 1.12), arrowstyle='-|>',
                                         mutation_scale=14, color=MUTED, lw=1.4))
    _save(fig, out)


def _grid():
    yy, xx = np.mgrid[0:60, 0:80]
    return yy, xx


def signature(t, out):
    from geosaga.signature_model import raster_map_signature
    yy, xx = _grid()
    ref = (xx // 27) + 3 * (yy // 30) + 1                       # 6 bairros
    rng = np.random.default_rng(3)
    uso = 1 + ((xx // 16 + yy // 12) % 4)
    uso = np.where(rng.random(uso.shape) < 0.07, rng.integers(1, 5, uso.shape), uso)
    solos = 1 + (xx * 3 // 80)
    selected = np.isin(ref, [2, 4])
    totals = {c: int((uso == c).sum()) for c in range(1, 5)}
    inside = {c: int(((uso == c) & selected).sum()) for c in range(1, 5)}
    sig = raster_map_signature('uso', {i + 1: n for i, n in enumerate(t['sig_classes'])}, totals, inside, 0.01)
    fig = plt.figure(figsize=(11, 5.0))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.0, 0.34], width_ratios=[1, 1, 1, 1.25], hspace=0.3, wspace=0.6)
    fig.suptitle(t['sig_title'], fontsize=13, weight='bold', color=BRAND, y=0.99)
    cmap_ref = ListedColormap(['#d9dde3', '#c7ccd3', '#d2d6dc', '#cfd4da', '#c3c8cf', '#d6dade'])
    for k, (arr, title) in enumerate(((ref, t['sig_maps'][0]), (uso, t['sig_maps'][1]), (solos, t['sig_maps'][2]))):
        ax = fig.add_subplot(gs[0, k])
        if k == 0:
            ax.imshow(arr, cmap=cmap_ref, interpolation='nearest')
            ax.imshow(np.ma.masked_where(~selected, selected), cmap=ListedColormap([SERIES[0]]), alpha=0.75,
                      interpolation='nearest')
        else:
            cmap = ListedColormap(SERIES[:4] if k == 1 else [SERIES[4], SERIES[6], SERIES[2]])
            ax.imshow(arr, cmap=cmap, interpolation='nearest')
        ax.contour(selected, levels=[0.5], colors=[INK], linewidths=1.6)
        ax.set_title(title, fontsize=9.5, color=INK)
        ax.set_xticks([])
        ax.set_yticks([])
    ax = fig.add_subplot(gs[0, 3])
    values = [r.pct_area for r in sig.rows]
    bars = ax.barh(range(4), values, color=SERIES[:4], height=0.62)
    for bar, v in zip(bars, values):
        ax.text(v + 1, bar.get_y() + bar.get_height() / 2, f'{v:.1f}%', va='center', fontsize=9, color=INK)
    ax.set_yticks(range(4), t['sig_classes'], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, max(values) * 1.35)
    ax.set_title(t['sig_bar_title'], fontsize=9.5)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='x', labelsize=8)
    for k, text in enumerate((t['sig_f1'], t['sig_f2'])):
        ax = fig.add_subplot(gs[1, k * 2:(k + 1) * 2])
        ax.axis('off')
        ax.add_patch(FancyBboxPatch((0.01, 0.08), 0.98, 0.84, boxstyle='round,pad=0.02,rounding_size=0.04',
                                    fc='#f6f8fb', ec=SERIES[k * 1], lw=1.4, transform=ax.transAxes))
        ax.text(0.5, 0.5, text, ha='center', va='center', fontsize=9.2, transform=ax.transAxes, linespacing=1.4)
    _save(fig, out)


def voronoi(t, out):
    from geosaga.voronoi_core import Generator, assign_window
    from geosaga.voronoi_friction import assign_friction_window
    w, h, cell = 80, 60, 10.0
    gt = (0.0, cell, 0.0, h * cell, 0.0, -cell)
    pts = [(15, 15, 4.0), (60, 12, 1.0), (22, 45, 1.0), (62, 46, 2.0)]
    gens = [Generator(i + 1, c * cell + 5, (h - r) * cell - 5, m) for i, (c, r, m) in enumerate(pts)]
    friction = np.ones((h, w), dtype=float)
    friction[:, 38:42] = 8.0
    results = [assign_window(gens, gt, w, 0, h),
               assign_window(gens, gt, w, 0, h, mode='mass'),
               assign_friction_window(gens, friction, gt, 0, h),
               assign_friction_window(gens, friction, gt, 0, h, mass_weighted=True)]
    fig, axes = plt.subplots(1, 4, figsize=(11, 3.2))
    fig.subplots_adjust(top=0.80, wspace=0.12)
    fig.suptitle(t['vor_title'], fontsize=13, weight='bold', color=BRAND, y=0.99)
    cmap = ListedColormap(SERIES[:4])
    for k, (ax, labels, title) in enumerate(zip(axes, results, t['vor_modes'])):
        ax.imshow(labels, cmap=cmap, vmin=1, vmax=4, interpolation='nearest', alpha=0.85)
        if k >= 2:
            ax.imshow(np.ma.masked_where(friction < 2, friction), cmap=ListedColormap(['#3b3b3b']), alpha=0.35,
                      interpolation='nearest')
        for i, (c, r, m) in enumerate(pts):
            size = 40 + (m * 30 if k in (1, 3) else 0)
            ax.scatter([c], [h - 1 - (h - r)], s=size, c='white', edgecolors=INK, linewidths=1.2, zorder=3)
            if k in (1, 3):
                ax.text(c + 3, h - 1 - (h - r) - 2, f'M={m:g}', fontsize=7.5, color=INK, zorder=4)
        ax.set_title(title, fontsize=9.5)
        ax.set_xticks([])
        ax.set_yticks([])
    axes[2].text(40, 58, t['vor_river'], ha='center', fontsize=7.2, color=INK,
                 bbox=dict(fc='white', ec='none', alpha=0.8, pad=1.5))
    _save(fig, out)


def monitoring(t, out, classes):
    yy, xx = _grid()
    t1 = 1 + ((xx // 20 + yy // 20) % 4)
    t2 = t1.copy()
    t2[(xx > 40) & (yy < 30)] = 1
    t2[(xx < 20) & (yy > 40)] = 2
    change = (t1 != t2)
    fig = plt.figure(figsize=(11.5, 3.6))
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1.15], wspace=0.55)
    fig.subplots_adjust(top=0.82)
    fig.suptitle(t['mon_title'], fontsize=13, weight='bold', color=BRAND, y=0.99)
    cmap = ListedColormap(SERIES[:4])
    for k, (arr, title) in enumerate(((t1, t['mon_maps'][0]), (t2, t['mon_maps'][1]))):
        ax = fig.add_subplot(gs[0, k])
        ax.imshow(arr, cmap=cmap, vmin=1, vmax=4, interpolation='nearest')
        ax.set_title(title, fontsize=9.5)
        ax.set_xticks([])
        ax.set_yticks([])
    ax = fig.add_subplot(gs[0, 2])
    ax.imshow(change, cmap=ListedColormap(['#c9ced4', SERIES[1]]), interpolation='nearest')
    ax.set_title(t['mon_maps'][2], fontsize=9.5)
    ax.set_xticks([])
    ax.set_yticks([])
    for k, (color, label) in enumerate((('#c9ced4', t['mon_keep']), (SERIES[1], t['mon_change']))):
        ax.add_patch(Rectangle((0.02 + k * 0.55, -0.14), 0.07, 0.07, color=color, transform=ax.transAxes,
                               clip_on=False))
        ax.text(0.11 + k * 0.55, -0.105, label, fontsize=7.5, va='center', transform=ax.transAxes)
    matrix = np.zeros((4, 4), dtype=int)
    for a in range(4):
        for b in range(4):
            matrix[a, b] = int(((t1 == a + 1) & (t2 == b + 1)).sum())
    ax = fig.add_subplot(gs[0, 3])
    ax.imshow(np.log1p(matrix), cmap='Blues')
    for a in range(4):
        for b in range(4):
            ax.text(b, a, matrix[a, b], ha='center', va='center', fontsize=8,
                    color='white' if matrix[a, b] > matrix.max() * 0.5 else INK)
    ax.set_xticks(range(4), classes, fontsize=7.5, rotation=30, ha='right')
    ax.set_yticks(range(4), classes, fontsize=7.5)
    ax.set_xlabel(t['mon_axes'][0], fontsize=8.5)
    ax.set_ylabel(t['mon_axes'][1], fontsize=8.5)
    ax.set_title(t['mon_matrix'], fontsize=9.5)
    _save(fig, out)


def evaluation(t, out):
    yy, xx = _grid()
    a = 1 + ((xx // 20 + yy // 15) % 4)
    b = 1 + (xx * 3 // 80)
    score_a = {1: 2, 2: 9, 3: 5, 4: 7}
    score_b = {1: 8, 2: 4, 3: 6}
    sa = np.vectorize(score_a.get)(a)
    sb = np.vectorize(score_b.get)(b)
    result = 0.6 * sa + 0.4 * sb
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6))
    fig.subplots_adjust(top=0.84)
    fig.suptitle(t['aval_title'], fontsize=13, weight='bold', color=BRAND, y=0.99)
    seq = 'Greens'
    for ax, arr, title in zip(axes, (sa, sb, result), t['aval_maps']):
        im = ax.imshow(arr, cmap=seq, vmin=0, vmax=10, interpolation='nearest')
        ax.set_title(title, fontsize=9.5)
        ax.set_xticks([])
        ax.set_yticks([])
    cbar = fig.colorbar(im, ax=axes, orientation='horizontal', fraction=0.05, pad=0.06, aspect=50)
    cbar.set_ticks([0, 10], labels=[f'0 - {t["aval_low"]}', f'10 - {t["aval_high"]}'])
    cbar.ax.tick_params(labelsize=8)
    fig.text(0.5, -0.06, t['aval_formula'], ha='center', fontsize=10.5, color=INK,
             bbox=dict(fc='#f6f8fb', ec=GRID, boxstyle='round,pad=0.5'))
    _save(fig, out)


def combination(t, out):
    yy, xx = _grid()
    a = 1 + ((xx // 20 + yy // 20) % 3)
    b = 1 + (yy * 2 // 60)
    pairs = sorted(set(zip(a.ravel().tolist(), b.ravel().tolist())))
    code = np.zeros_like(a)
    for i, (p, q) in enumerate(pairs):
        code[(a == p) & (b == q)] = i + 1
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.1))
    fig.subplots_adjust(top=0.80)
    fig.suptitle(t['comb_title'], fontsize=13, weight='bold', color=BRAND, y=0.99)
    axes[0].imshow(a, cmap=ListedColormap(SERIES[:3]), interpolation='nearest')
    axes[1].imshow(b, cmap=ListedColormap([SERIES[4], SERIES[6]]), interpolation='nearest')
    axes[2].imshow(code, cmap=ListedColormap(SERIES[:len(pairs)]), interpolation='nearest')
    for ax, title in zip(axes, t['comb_maps']):
        ax.set_title(title, fontsize=9.5)
        ax.set_xticks([])
        ax.set_yticks([])
    for i, (p, q) in enumerate(pairs):
        axes[2].text(81, 4 + i * 8, f'{i + 1} = {p}×{q}', fontsize=7.8, va='center', color=INK)
    _save(fig, out)


def converter(t, out):
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    ax.text(5, 5.75, t['conv_title'], ha='center', fontsize=13, weight='bold', color=BRAND)
    nodes = {0: (5, 4.4), 1: (1.8, 1.1), 2: (8.2, 1.1)}
    for i, (x, y) in nodes.items():
        ax.add_patch(FancyBboxPatch((x - 1.05, y - 0.55), 2.1, 1.1, boxstyle='round,pad=0.02,rounding_size=0.15',
                                    fc='#f6f8fb', ec=SERIES[i], lw=2))
        ax.text(x, y, t['conv_nodes'][i], ha='center', va='center', fontsize=10.5, weight='bold')
    ops = t['conv_ops']
    links = [(0, 1, ops[0], ops[1]), (0, 2, ops[2], ops[3]), (1, 2, ops[4], ops[5])]
    for a, b, fwd, back in links:
        (x0, y0), (x1, y1) = nodes[a], nodes[b]
        dx, dy = x1 - x0, y1 - y0
        norm = (dx ** 2 + dy ** 2) ** 0.5
        ox, oy = -dy / norm * 0.18, dx / norm * 0.18
        s0, s1 = 0.3, 0.7
        for sign, label in ((1, fwd), (-1, back)):
            start = (x0 + dx * s0 + sign * ox, y0 + dy * s0 + sign * oy)
            end = (x0 + dx * s1 + sign * ox, y0 + dy * s1 + sign * oy)
            if sign < 0:
                start, end = end, start
            ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=14, color=INK2, lw=1.3))
            mx, my = (start[0] + end[0]) / 2 + sign * ox * 2.6, (start[1] + end[1]) / 2 + sign * oy * 2.6
            ax.text(mx, my, label, ha='center', va='center', fontsize=8.6, color=INK,
                    bbox=dict(fc='white', ec='none', pad=1))
    _save(fig, out)


def sequencer(t, out):
    yy, xx = _grid()
    fig, ax = plt.subplots(figsize=(10.5, 2.9))
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 2.9)
    ax.axis('off')
    ax.text(5.25, 2.7, t['seq_title'], ha='center', fontsize=13, weight='bold', color=BRAND)
    for i in range(4):
        grow = (xx - 40) ** 2 + (yy - 30) ** 2 < (8 + i * 7) ** 2
        frame = np.where(grow, 1, 2)
        x = 0.2 + i * 2.1
        ax.imshow(frame, cmap=ListedColormap([SERIES[1], SERIES[5]]), extent=(x, x + 1.8, 0.45, 1.8),
                  interpolation='nearest')
        ax.add_patch(Rectangle((x, 0.45), 1.8, 1.35, fill=False, ec=INK2, lw=1))
        ax.text(x + 0.9, 0.25, f'{t["seq_frame"]} {i + 1} - {2000 + i * 5}', ha='center', fontsize=8.5, color=INK2)
    ax.add_patch(FancyArrowPatch((8.6, 1.12), (9.05, 1.12), arrowstyle='-|>', mutation_scale=16, color=MUTED))
    ax.add_patch(FancyBboxPatch((9.1, 0.6), 1.25, 1.05, boxstyle='round,pad=0.02,rounding_size=0.1',
                                fc='#f6f8fb', ec=SERIES[0], lw=1.6))
    ax.text(9.72, 1.12, t['seq_gif'], ha='center', va='center', fontsize=9.5, weight='bold')
    _save(fig, out)


def dashboard(t, out):
    fig = plt.figure(figsize=(10.5, 6.2))
    gs = fig.add_gridspec(2, 4, height_ratios=[0.55, 1.4], hspace=0.55, wspace=0.35)
    fig.suptitle(t['dash_title'], fontsize=13, weight='bold', color=BRAND, y=0.99)
    for k, (value, label) in enumerate(t['kpis']):
        ax = fig.add_subplot(gs[0, k])
        ax.axis('off')
        ax.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle='round,pad=0.02,rounding_size=0.06',
                                    fc='#f6f8fb', ec=GRID, transform=ax.transAxes))
        ax.text(0.5, 0.62, value, ha='center', va='center', fontsize=24, weight='bold', color=BRAND,
                transform=ax.transAxes)
        ax.text(0.5, 0.22, label, ha='center', va='center', fontsize=9, color=INK2, transform=ax.transAxes)
    # Pontos (não barras): a escala ampliada perto de 100% não distorce a leitura, como faria uma barra
    # truncada (anti-padrão da skill de visualização).
    for slot, (cases, values, title, low) in enumerate((
            (t['dash_vor_cases'], [100.0, 100.0, 99.46, 99.42, 99.29, 99.06], t['dash_vor'], 98.8),
            (t['dash_sig_cases'], [100.0, 90.32, 87.50], t['dash_sig'], 84.0))):
        ax = fig.add_subplot(gs[1, slot * 2:(slot + 1) * 2])
        color = SERIES[0] if slot == 0 else SERIES[2]
        positions = range(len(values))
        ax.scatter(positions, values, s=90, color=color, edgecolors='white', linewidths=2, zorder=3)
        for x, v in zip(positions, values):
            ax.text(x, v + (100.4 - low) * 0.04, f'{v:.2f}'.rstrip('0').rstrip('.'), ha='center', fontsize=8.5)
        ax.set_ylim(low, 100 + (100 - low) * 0.12)
        ticks = sorted({round(v, 6) for v in ax.get_yticks() if low <= v <= 100} | {100.0})
        ax.set_yticks(ticks)  # sem marcas acima de 100%
        ax.set_xlim(-0.6, len(values) - 0.4)
        ax.set_xticks(list(positions), [c.replace('+', '+\n') for c in cases], fontsize=7.6)
        ax.set_title(title, fontsize=9.5)
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    fig.text(0.5, 0.01, t['dash_note'], ha='center', fontsize=8.5, color=INK2)
    _save(fig, out)


def main(target):
    common = os.path.join(target, 'comum')
    os.makedirs(common, exist_ok=True)
    icons = _icons(common)
    for lang, t in T.items():
        folder = os.path.join(target, lang, 'figuras')
        os.makedirs(folder, exist_ok=True)
        overview(t, os.path.join(folder, 'panorama.png'), icons)
        flow(t, os.path.join(folder, 'fluxo.png'))
        signature(t, os.path.join(folder, 'assinatura.png'))
        voronoi(t, os.path.join(folder, 'voronoi.png'))
        monitoring(t, os.path.join(folder, 'monitoria.png'), t['sig_classes'])
        evaluation(t, os.path.join(folder, 'avaliacao.png'))
        combination(t, os.path.join(folder, 'combinacao.png'))
        converter(t, os.path.join(folder, 'conversor.png'))
        sequencer(t, os.path.join(folder, 'sequenciador.png'))
        dashboard(t, os.path.join(folder, 'painel.png'))
        print(lang, 'ok')


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]))
