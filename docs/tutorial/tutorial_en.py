"""Step-by-step tutorial text (English). Figures come from numeros.json (executar_tutorial.py)."""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'docs', 'manual'))

import build_manual as bm  # noqa: E402

LANG = 'en'
USO_NAMES = ['Urban area', 'Native vegetation', 'Farming', 'Pasture', 'Water']  # as in gerar_dados.NAMES

UI = {
    'doc_title': 'Step-by-step tutorial', 'subtitle': 'Vista Saga Plugin 1.6.0 for QGIS 4',
    'tagline': 'Vila Serena: from data to diagnosis, through the seven modules', 'author': 'Esdras Andrade (IGDEMA/UFAL)',
    'date': 'November 2026', 'toc': 'Contents', 'figure': 'Figure', 'footer': 'Vista Saga Plugin 1.6.0 - Tutorial',
    'page': 'Page',
}


def f(value, places=2):
    """Number in English format (decimal point, comma thousands separator)."""
    return f'{value:,.{places}f}'


def build(work):
    n = json.load(open(os.path.join(work, 'numeros.json'), encoding='utf-8'))
    fig = lambda name: os.path.join(work, f'figuras_{LANG}', f'{name}.png')  # noqa: E731
    win = lambda name: os.path.join(work, f'janelas_{LANG}', f'{name}.png')  # noqa: E731
    B = []
    chapter = [0]

    def h1(text):
        chapter[0] += 1
        B.append({'type': 'h1', 'text': f'{chapter[0]}. {text}'})

    def h2(text): B.append({'type': 'h2', 'text': text})
    def p(*texts): B.extend({'type': 'p', 'text': t} for t in texts)
    def bullets(items): B.append({'type': 'bullets', 'items': items})
    def steps(items): B.append({'type': 'steps', 'items': items})
    def table(cols, rows, widths, header=True): B.append({'type': 'table', 'cols': cols, 'rows': rows,
                                                          'widths': widths, 'header': header})
    def tip(title, text=None, items=None, kind='tip'):
        B.append({'type': 'callout', 'kind': kind, 'title': title, 'text': text, 'items': items})
    def image(path, caption, width=6.3): B.append(bm.image(path, width, caption))
    def brk(): B.append({'type': 'pagebreak'})

    sig = n['assinatura']
    union, centro, beira = sig['uniao'], sig['2'], sig['1']   # codes: 1 Riverside, 2 Downtown
    mon = n['monitoria']
    ev = n['avaliacao']
    vor = n['voronoi']
    conv = n['conversor']

    B.append({'type': 'cover', 'title': UI['doc_title'], 'subtitle': UI['subtitle'], 'tagline': UI['tagline'],
              'author': UI['author'], 'date': UI['date'],
              'logo': os.path.join(ROOT, 'docs', 'assets', 'vista-saga-mark.png')})
    B.append({'type': 'toc', 'title': UI['toc']})
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Before you start')
    p('This tutorial is a **guided exercise**: from start to finish, you will carry out a complete territorial '
      'diagnosis of a fictitious town, **Vila Serena**, using the seven modules of the Vista Saga Plugin. Each step '
      'says what to click, what to fill in and **which result you should get**. If your number matches the one in the '
      'text, you did it right.',
      'The user manual explains every field and concept. This tutorial goes the other way round: it starts from a real '
      'question and shows how the modules link up to answer it.')
    h2('The Vila Serena question')
    p('Vila Serena is a town of 400 hectares (2 km × 2 km), crossed by a river from north to south, with hills to the '
      'east. Between 2000 and 2020 its urban area tripled. The town council wants to know:')
    steps(['**What are** the Downtown and Riverside districts **made of** today? (Signature)',
           '**What changed** between 2000 and 2020, and at the expense of what? (Monitoring)',
           '**Which associations** of land use and soil exist, and where is the city built on floodplain soil? '
           '(Map combination)',
           '**Where can the town grow** with the least conflict? (Evaluation)',
           '**Which school serves each part** of the town, given the size of the schools and the river? (Voronoi)',
           '**How to show** the growth as an animation at the public hearing? (Map sequencer)'])
    p('The Format converter comes first, because it prepares one of the maps and because it is the bridge to Vista SAGA.')
    h2('What you need')
    table(['Item', 'Details'], [
        ['QGIS', 'Version 4.x (Windows or Linux), interface in English (the plugin follows the QGIS language).'],
        ['Vista Saga Plugin', 'Version 1.6.0 installed (Plugins > Manage and Install Plugins > Install from ZIP).'],
        ['Tutorial data', '**dados_tutorial_vila_serena_en.zip** (synthetic data, free to use; class and district '
                          'names in English). Unzip it to a folder whose path has no accents, for example '
                          'C:\\VilaSerena\\dados.'],
        ['Time', 'About 2 hours in total; each lesson takes 10 to 20 minutes and can be done on its own.'],
    ], [0.25, 0.75])
    h2('What is in the data folder')
    p('File names are in Portuguese (the plugin was born in Brazil): **uso_solo** = land use, **solos** = soils, '
      '**declividade** = slope, **atrito** = friction, **bairros** = districts, **escolas** = schools, '
      '**MATRICULAS** = enrolment.')
    table(['File', 'Content'], [
        ['uso_solo_2000.tif, uso_solo_2010.tif, uso_solo_2020.tif', 'Land use on three dates: 1 Urban area, 2 Native '
                                                                    'vegetation, 3 Farming, 4 Pasture, 5 Water.'],
        ['solos.tif', '1 Argisol, 2 Latosol, 3 Fluvic neosol (floodplain soil, prone to flooding).'],
        ['declividade.tif', '1 Flat (0-3%), 2 Gently rolling (3-8%), 3 Rolling (8-20%), 4 Strongly rolling (> 20%).'],
        ['atrito.tif', 'Friction rating for Voronoi: urban area 1, pasture and farming 2, vegetation 4, water 10.'],
        ['bairros.gpkg', '6 districts (fields CODIGO and NOME).'],
        ['escolas.gpkg', '6 schools (fields NOME and MATRICULAS).'],
        ['aptidao_expansao.geosaga.json', 'Ready-made Evaluation project (weights and scores of lesson 5).'],
    ], [0.38, 0.62])
    p('All rasters share the **same grid**: 200 × 200 cells of 10 m, in the CRS **SIRGAS 2000 / UTM 25S '
      '(EPSG:31985)**. This is no accident: several modules compare maps cell by cell and require the same grid.')
    tip('The data are synthetic',
        'Vila Serena does not exist. The maps were generated by a script with a fixed seed '
        '(docs/tutorial/gerar_dados.py, in the repository), so everyone gets exactly the same numbers. The weights and '
        'scores used in the lessons are teaching choices, not method recommendations.', kind='warning')
    tip('Reports stay in Portuguese',
        'Whatever the interface language, the CSV and TXT reports, file suffixes (_transicoes, _combinacoes, '
        '_centros…) and column names are always written in Portuguese. This tutorial translates the columns it uses.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Preparing the project')
    steps(['Open QGIS 4 and create a new project (**Project > New**).',
           'Set the project CRS: **Project > Properties > CRS**, search for **31985** and choose '
           '**SIRGAS 2000 / UTM zone 25S**. Click **OK**.',
           'Drag the files of the **dados** folder into the Layers panel: the three **uso_solo**, **solos**, '
           '**declividade**, **atrito**, **bairros.gpkg** and **escolas.gpkg**.',
           'Rename the layers so they read like the screenshots (right-click > Rename Layer): **Land use 2000**, '
           '**Land use 2010**, **Land use 2020**, **Soils**, **Slope**, **Friction**, **Districts**, **Schools**.',
           'Check the legend of the categorical rasters: QGIS should show the **class names** (Urban area, Native '
           'vegetation…), because they are stored in the GeoTIFFs.',
           'Save the project in the tutorial folder (**Project > Save As…**, for example vila_serena.qgz).',
           'Create a **resultados** (results) folder next to the **dados** folder: all lesson results go there.'])
    image(fig('f01_dados'), 'The maps of Vila Serena: land use in 2000 and 2020, soils and slope')
    image(fig('f02_bairros_escolas'), 'Districts and schools (enrolment in brackets)', 4.2)
    tip('Why the CRS matters so much',
        'The plugin **never reprojects without telling you** and **never guesses the CRS** from coordinates. Maps in '
        'different CRSs are refused with a clear message. In real work, standardize the CRS (projected, in metres) '
        'before you start: it is the step that saves the most rework.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lesson 1 - Format converter: preparing and exchanging data')
    p('**Goal:** turn the districts (vector) into a raster on the same grid as the other maps, to use it as the '
      'reference in Signature; and export land use to RS2, the Vista SAGA format.')
    h2('1.1 Districts: from vector to GeoTIFF')
    steps(['Open **Vista Saga Plugin > Format converter**.',
           'In **Convert**, choose **Vector → GeoTIFF (rasterization)**.',
           'In **Project vector layer**, choose **Districts** and click **Select**.',
           'In **Field to rasterize**, choose **CODIGO**; in **Pixel size**, **10**.',
           'In **Output file**, enter resultados\\bairros.tif. Click **Run**.'])
    image(win('t01_conversor_vetor_geotiff'), 'Format converter: bairros.gpkg to GeoTIFF', 5.4)
    p(f"**Expected result:** bairros.tif with **{conv['bairros_tif'][0]} × {conv['bairros_tif'][1]} cells of "
      f"{f(conv['bairros_tif'][2], 0)} m**, exactly the grid of the other maps, because the districts cover the whole "
      'study area. The raster loads with a style (.qml) that shows only the real classes.')
    image(fig('f03_conversor'), 'The same map before (vector) and after (raster) the conversion')
    h2('1.2 Naming the raster classes')
    p('The new GeoTIFF stores the **codes** (1 to 6), and QGIS shows "Classe 1", "Classe 2"… Signature uses the names '
      'of the layer style in QGIS, so name the classes now:')
    steps(['Double-click the **bairros** raster layer and open **Symbology**.',
           'In the **Label** column, type: 1 Riverside, 2 Downtown, 3 Hilltop, 4 Harbour, 5 New Garden, 6 Green Village.',
           'Click **OK**. To keep the names with the file: **Style > Save as Default**.'])
    tip('A tip only the tutorial tells you',
        'The code → name table is in bairros.gpkg itself (fields CODIGO and NOME). Open the attribute table next to '
        'Symbology and copy the names; with maps of dozens of classes, this avoids mistakes.')
    h2('1.3 Land use 2020: from GeoTIFF to RS2 (and back)')
    steps(['In the converter, choose **GeoTIFF → RS2 (Vista SAGA format)**.',
           'In **Input file**, enter dados\\uso_solo_2020.tif; in **Output file**, resultados\\uso_solo_2020.rs2. '
           'Click **Run**.',
           'To check, go back: **RS2 → GeoTIFF (categorical raster)**, input uso_solo_2020.rs2, output '
           'uso_solo_2020_de_volta.tif. Check the CRS: the plugin reads it from the .rs2.json file written in the '
           'previous step (**EPSG:31985**).'])
    image(win('t02_conversor_geotiff_rs2'), 'Format converter: GeoTIFF to RS2', 5.4)
    p(f"**Expected result:** an RS2 file of {f(conv['rs2_bytes'], 0)} bytes, plus the sidecar file "
      '**uso_solo_2020.rs2.rs2.json**, which stores the CRS, the legend and the code mapping. The GeoTIFF that comes '
      f"back is **{'identical cell by cell' if conv['ida_e_volta_identico'] else 'different'}** to the original, with "
      'the same names and colours.')
    tip('Warning', 'RS2 **does not store the CRS**. When you move an RS2 to another folder or person, take the '
        '.rs2.json along; without it, the plugin will ask you to confirm the CRS.', kind='warning')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lesson 2 - Signature: what are Downtown and Riverside made of?')
    p('**Goal:** measure, inside the Downtown and Riverside districts, how much each class of land use, soil and slope '
      'occupies.')
    steps(['Open **Vista Saga Plugin > Signature**, **Raster** tab.',
           'In **1. Maps**, add the **bairros** raster **first** (it will be the reference), then **Land use 2020**, '
           '**Soils** and **Slope** (Layer in QGIS + **Add selected layer**).',
           'In **2. Selection on the reference**, tick **1 - Riverside** and **2 - Downtown**.',
           'In **3. Options**, keep **Per-feature result** on (one block per district, besides the union).',
           'In **4. Result**, type the title "Downtown and Riverside" and choose resultados\\assinatura.csv (the TXT is '
           'written next to it). Click **Run**.'])
    image(win('t03_assinatura_configuracao'), 'Signature: districts as the reference, Downtown and Riverside ticked', 5.2)
    image(win('t04_assinatura_resultados'), 'Signature, Results tab: the table of the union of the selection', 5.8)
    h2('Expected result')
    u_uso = union['uso_solo_2020.tif']
    p(f"The union of the two districts covers **{f(union['bairros.tif']['1'][0] + union['bairros.tif']['2'][0])} ha** "
      f"(Riverside {f(union['bairros.tif']['1'][0])} ha + Downtown {f(union['bairros.tif']['2'][0])} ha). For land use "
      'in 2020:')
    table(['Class', 'Signed area (ha)', '% signed area', '% category'],
          [[USO_NAMES[int(k) - 1], f(v[0]), f(v[1]), f(v[2])] for k, v in u_uso.items() if k != '0'],
          [0.34, 0.22, 0.22, 0.22])
    h2('How to read it')
    bullets([f"**% signed area** answers \"what is the place made of\": {f(u_uso['1'][1])}% of the two districts is "
             'urban. This column adds up to 100% in each map.',
             f"**% category** answers \"how much of the class is here\": {f(u_uso['1'][2])}% of all the urban area of "
             f"Vila Serena lies in these two districts, and {f(u_uso['5'][2])}% of the water. This column does **not** "
             'add up to 100%.',
             f"District by district, the contrast is sharp: Downtown is {f(centro['uso_solo_2020.tif']['1'][1])}% urban; "
             f"Riverside only {f(beira['uso_solo_2020.tif']['1'][1])}%, with {f(beira['uso_solo_2020.tif']['4'][1])}% "
             'pasture.',
             f"In Downtown, {f(centro['solos.tif']['3'][1])}% of the area is fluvic neosol, a floodplain soil: a clue that "
             'Map combination and Evaluation will confirm.'])
    image(fig('f04_assinatura'), 'Land use 2020 in each cut: Downtown, Riverside and the whole town')
    tip('Tips only the tutorial tells you', items=[
        'The table of the reference itself (districts) shows 100% for the ticked classes: it checks the exact size of '
        'the boundary. If it is not 100%, the selection is not what you think.',
        'Do not add up the per-district blocks to get the union: use the "Union of the selection" block.',
        'In the CSV, filter the RECORTE (cut) column (UNIAO or FEICAO) and build a pivot table by MAPA (map) and '
        'CLASSE (class).'])
    p('**Exercise:** sign the **New Garden** district on your own, the town\'s growth frontier. What is its % of urban '
      'area? And of native vegetation?')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lesson 3 - Monitoring: what changed between 2000 and 2020?')
    steps(['Open **Vista Saga Plugin > Monitoring**, **Raster** tab.',
           'In **Initial map**, choose **Land use 2000** and type **2000** in Period.',
           'In **Final map**, choose **Land use 2020** and type **2020** in Period.',
           'In **Study title**, "Land use 2000 - 2020"; in **Save to**, resultados\\transicoes_2000_2020.tif.',
           'Click **Run**.'])
    image(win('t05_monitoria'), 'Monitoring: the two periods and the result', 5.4)
    h2('Expected result')
    p(f"Of the {f(mon['validos'], 0)} cells ({f(mon['area_valida_ha'], 0)} ha), **{f(mon['pct_permanencia'])}% "
      f"persisted** in the same class ({f(mon['permanencias'] * 0.01)} ha) and **{f(mon['pct_mudanca'])}% changed** "
      f"({f(mon['mudancas'] * 0.01)} ha). The largest changes:")
    with open(os.path.join(work, 'resultados', 'transicoes_2000_2020_transicoes.csv'), encoding='utf-8-sig') as stream:
        changes = [r for r in csv.DictReader(stream, delimiter=';') if r['SITUACAO'] == 'Mudança']
    changes.sort(key=lambda r: -float(r['AREA_HA']))
    table(['Transition', 'Area (ha)', '% of the area'],
          [[f"{r['DEIXOU_DE_SER']} → {r['TORNOU_SE']}", f(float(r['AREA_HA'])), f(float(r['PCT_VALIDOS']))]
           for r in changes[:5]], [0.5, 0.25, 0.25])
    image(fig('f05_monitoria'), 'The transition map (persistence in grey) and the area of each class on both dates')
    h2('How to read it')
    bullets(['The urban area went from **32.49 ha to 109.70 ha** (3.4 times). Almost half of the growth came from '
             'pasture (46.98 ha) and a quarter from native vegetation (21.85 ha).',
             'Native vegetation fell from **120.52 ha to 52.34 ha** (-56.6%): it lost area to the city, to pasture and '
             'to farming.',
             'Water (12.80 ha) did not change: a good quality check. If the water "changed", distrust the maps.',
             'In the matrix (_matriz.csv), read **by row**: each row shows where each 2000 class went.'])
    tip('A tip only the tutorial tells you',
        'Open _transicoes.csv in Excel or LibreOffice and sort by the AREA_HA column: the first five change rows tell '
        'the story of the period. SITUACAO tells persistence (Permanência) from change (Mudança); DEIXOU_DE_SER and '
        'TORNOU_SE are the "from" and "to" classes.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lesson 4 - Map combination: city on floodplain soil?')
    steps(['Open **Vista Saga Plugin > Map combination**, **Raster** tab.',
           'Add **Land use 2020** and then **Soils** (the order sets the order of the columns in the table).',
           'In **Save to**, enter resultados\\uso2020_x_solos.tif and click **Run**.'])
    image(win('t06_combinacao'), 'Map combination: land use 2020 and soils', 5.4)
    h2('Expected result')
    p(f"**{n['combinacao']['combinacoes']} combinations** found, in {f(n['combinacao']['area_ha'], 0)} ha. The largest is "
      '**Pasture | Argisol** (98.07 ha, 24.52%). The one the council cares about is **Urban area | Fluvic neosol: '
      '17.89 ha (4.47%)**: city built on floodplain soil, prone to flooding.')
    image(fig('f06_combinacao'), 'Area of each combination of land use and soil')
    tip('A tip only the tutorial tells you',
        'In QGIS, use the **Identify Features** tool on the combined map: the cell value matches the ID_COMB of '
        '_combinacoes.csv. To highlight only urban areas on the floodplain, open Symbology and untick the other '
        'combinations.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lesson 5 - Evaluation: where can the town grow?')
    p('**Goal:** produce a suitability-for-urban-growth map as the weighted average of three criteria. The weights and '
      'scores below are **for teaching**: in a real study they must be justified (literature, expert consultation, '
      'legislation).')
    table(['Criterion (weight)', 'Scores (0 to 10)'], [
        ['Slope (40%)', 'Flat 10; Gently rolling 8; Rolling 4; Strongly rolling 1'],
        ['Soils (25%)', 'Argisol 7; Latosol 9; Fluvic neosol 2 (floodplain, floodable)'],
        ['Land use 2020 (35%)', 'Urban area 8; Native vegetation 1; Farming 6; Pasture 9; Water: Do not evaluate'],
    ], [0.3, 0.7])
    h2('Building it step by step')
    steps(['Open **Vista Saga Plugin > Evaluation**, **Raster** tab. Score scale: **0 to 10**.',
           'Add **Slope**, **Soils** and **Land use 2020**. Weights start blank, on purpose.',
           'Type the weights 40, 25 and 35 (the **Tab** key jumps from weight to weight). The line below the table '
           'should read "Weights: 100.00% - valid allocation".',
           'Select each map and type the class scores. For **Water**, tick **Do not evaluate**.',
           'Click **Validate**: no class may be left with the score "—".',
           'In **Save to**, enter resultados\\aptidao_expansao.tif, keep both reports ticked and click **Run**.'])
    tip('Shortcut', 'Instead of typing everything, click **Open project…** and choose '
        'dados\\aptidao_expansao.geosaga.json: the three maps, the weights and the scores load at once. That is how you '
        'reuse an evaluation.')
    image(win('t07_avaliacao'), 'Evaluation: weights, scores and Water set to "Do not evaluate"', 5.8)
    h2('Expected result')
    per = ev['area_por_nota_ha']
    p(f"**{f(ev['pixels_validos'], 0)} cells evaluated** ({f(ev['pixels_validos'] * 0.01, 1)} ha) and "
      f"{f(ev['pixels_sem_avaliacao'], 0)} not evaluated (the water, {f(ev['pixels_sem_avaliacao'] * 0.01, 1)} ha). "
      f"Minimum score **{f(ev['minimo'], 1)}**, maximum **{f(ev['maximo'], 1)}**, mean **{f(ev['media'])}**. Area per "
      'final score (as in the report):')
    table(['Final score'] + sorted(per, key=int), [['Area (ha)'] + [f(per[k]) for k in sorted(per, key=int)]],
          [0.2] + [0.8 / len(per)] * len(per))
    image(fig('f07_avaliacao'), 'Suitability-for-urban-growth map and area per final score')
    h2('How to read it')
    bullets([f"Scores **8 and 9** ({f(per.get('8', 0) + per.get('9', 0))} ha) are the most suitable areas: almost all "
             'on flat or gently rolling land, on argisol, under pasture or already urban.',
             f"Score **3** ({f(per.get('3', 0))} ha) brings together the worst of everything: native vegetation on steep "
             'slopes.',
             'A telling result: **latosol**, despite its score of 9, has the lowest mean score (5.51), because it lies on '
             'the hills, on steep slopes. Slope (40%) weighs more than soil (25%) and dominates. The floodplain (fluvic '
             'neosol, score 2) gets a mean of 6.18: it is flat, and the soil penalizes it only in part. If the council '
             'wants to exclude the floodplain altogether, a low score is not enough: set the class to **Do not '
             'evaluate**.'])
    tip('Tips only the tutorial tells you', items=[
        'The score "—" blocks the run: the plugin **never assumes a score of 0**. This is deliberate, so that no class '
        'enters the calculation without your decision.',
        'Each run writes *_pesos_notas.geosaga.json (weights and scores) next to the map: it is the exact record of what '
        'you used. Keep it with the study report.',
        'Test the sensitivity: change the weights to 50/20/30 and compare the maps. If the map changes a lot, the '
        'choice of weights is critical and needs a strong justification.'])
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lesson 6 - Voronoi analyses: which school serves each part of the town?')
    p('Three versions of the same question: by pure distance (**Simple**), by school size (**With mass**, enrolment) '
      'and by travel difficulty (**With Friction**: the river is expensive to cross).')
    h2('6.1 With mass')
    steps(['Open **Vista Saga Plugin > Voronoi analyses**, **Raster** tab.',
           'In **Mode**, choose **With mass**.',
           'In **Generating points**, **Schools**; in **Point identifier**, **NOME**; in **Mass field**, **MATRICULAS**.',
           'In **Analysis extent**, choose **Reference raster grid** and, in **Reference raster**, **Friction**: this '
           'way the result falls exactly on the grid of the other maps.',
           'In **Save to**, resultados\\voronoi_com_massa.tif. Click **Run**.'])
    image(win('t09_voronoi_massa'), 'Voronoi analyses, With mass: enrolment as mass, friction raster grid', 5.4)
    h2('6.2 With friction')
    steps(['Switch **Mode** to **With Friction**.',
           'In **Surface type**, **Raster**; in **Friction surface**, **Friction**.',
           'Keep the reference raster grid; in **Save to**, resultados\\voronoi_com_atrito.tif. Click **Run**.',
           'For comparison, also run the **Simple** mode (resultados\\voronoi_simples.tif).'])
    image(win('t08_voronoi_atrito'), 'Voronoi analyses, With Friction: raster friction surface', 5.4)
    h2('Expected result')
    names = list(vor['simples'])
    table(['School (enrolment)', 'Simple (ha)', 'With mass (ha)', 'With Friction (ha)'],
          [[f"{k} ({f(vor['simples'][k]['MASSA'], 0)})", f(vor['simples'][k]['AREA_HA']),
            f(vor['com_massa'][k]['AREA_HA']), f(vor['com_atrito'][k]['AREA_HA'])] for k in names],
          [0.4, 0.2, 0.2, 0.2])
    image(fig('f08_voronoi'), 'The areas of influence in the three modes (in With mass, the dot size is proportional '
          'to enrolment)')
    h2('How to read it')
    bullets([f"**With mass**, E. E. Darcy Ribeiro (1,200 pupils) grows from {f(vor['simples']['E. E. Darcy Ribeiro']['AREA_HA'])} "
             f"to **{f(vor['com_massa']['E. E. Darcy Ribeiro']['AREA_HA'])} ha**; E. M. Cora Coralina (250) drops from "
             f"{f(vor['simples']['E. M. Cora Coralina']['AREA_HA'])} to {f(vor['com_massa']['E. M. Cora Coralina']['AREA_HA'])} ha. "
             'The criterion is M/d²: a school with 4 times the mass reaches twice the distance, not four times.',
             f"**With Friction**, E. M. Monteiro Lobato, by the river, loses area ({f(vor['simples']['E. M. Monteiro Lobato']['AREA_HA'])} → "
             f"{f(vor['com_atrito']['E. M. Monteiro Lobato']['AREA_HA'])} ha): crossing the water costs 10 times more than "
             'walking in the city. E. E. Cecília Meireles gains '
             f"({f(vor['simples']['E. E. Cecília Meireles']['AREA_HA'])} → {f(vor['com_atrito']['E. E. Cecília Meireles']['AREA_HA'])} ha).",
             'The cost is measured along the **straight line** between the school and each place, as in Vista SAGA: it is '
             'not the least-cost path (GRASS r.cost). The line "pays" for the river; it does not go around it.'])
    tip('Tips only the tutorial tells you', items=[
        'A friction rating of 0 is refused; for "almost no friction", use 0.1.',
        'In an exact tie, the first point in the layer wins.',
        '_centros.csv gives the area (AREA_HA) and % (PCT_AREA) of each school: paste it next to the enrolment table and '
        'compute pupils per hectare served.'])
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lesson 7 - Map sequencer: the growth as an animation')
    steps(['Open **Vista Saga Plugin > Map sequencer**, **Raster** tab.',
           'Add, in this order, **Land use 2000**, **Land use 2010** and **Land use 2020** (the plugin reads the year '
           'from the name; use **Sort by date** if needed).',
           'In **2. Dimensions and composition**: width and height **600**, duration **1000 ms / frame**, **Show '
           'date/period on map** on.',
           'In **3. Outputs and preview**, enter resultados\\vila_serena_2000_2020.gif and tick **Also export individual '
           'PNG frames**. Click **Run**.'])
    image(win('t10_sequenciador'), 'Map sequencer: three frames, 600 × 600 pixels', 5.2)
    p('**Expected result:** a 3-frame GIF (2000, 2010, 2020) with the year in the corner, and a folder with the three '
      'PNGs (quadro_001_2000.png…). Frames use the symbology set in QGIS.')
    image(fig('f09_sequenciador'), 'The three frames created by the Map sequencer')
    tip('A tip only the tutorial tells you',
        'A GIF has at most 256 colours. For a slide presentation, use the PNGs: colours stay exact and you control the '
        'timing of each frame in the presentation software itself.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Wrap-up: the diagnosis of Vila Serena')
    p('Putting the lessons together, the answer to the council fits in five sentences:')
    steps([f"Downtown is already {f(centro['uso_solo_2020.tif']['1'][1], 1)}% urban, and a third of it lies on "
           'floodplain soil (Signature).',
           'In 20 years the town tripled, mainly over pasture, and native vegetation lost more than half of its area '
           '(Monitoring).',
           'There are 17.89 ha of city on fluvic neosol, a priority for drainage and flood control (Map combination).',
           f"The most suitable areas for growth (scores 8 and 9, {f(per.get('8', 0) + per.get('9', 0))} ha) lie on flat "
           'or gently rolling land, almost all outside the floodplain (Evaluation).',
           'The river redraws school catchments: taking the crossing into account changes the area served by most '
           'schools (Voronoi).'])
    h2('Checklist')
    table(['Lesson', 'Expected file in resultados', 'Key number'], [
        ['1', 'bairros.tif, uso_solo_2020.rs2 (+ .rs2.json)', '200 × 200 cells; identical round trip'],
        ['2', 'assinatura.csv, assinatura.txt', f"Urban area in the union: {f(u_uso['1'][0])} ha ({f(u_uso['1'][1])}%)"],
        ['3', 'transicoes_2000_2020.tif + _transicoes.csv, _matriz.csv, _resumo.txt', f"Change: {f(mon['pct_mudanca'])}%"],
        ['4', 'uso2020_x_solos.tif + _combinacoes.csv, _resumo.txt', f"{n['combinacao']['combinacoes']} combinations"],
        ['5', 'aptidao_expansao.tif + CSV and TXT reports + _pesos_notas.geosaga.json', f"Mean {f(ev['media'])}"],
        ['6', 'voronoi_*.tif + _centros.csv, _resumo.txt', f"Darcy Ribeiro With mass: {f(vor['com_massa']['E. E. Darcy Ribeiro']['AREA_HA'])} ha"],
        ['7', 'vila_serena_2000_2020.gif + PNG folder', '3 frames'],
    ], [0.1, 0.5, 0.4])
    h2('If your number did not match')
    bullets(['Check that you used the right maps (2000 and 2020, not 2010) and the right order in the list.',
             'Check the CRS of the project and of the layers (EPSG:31985).',
             'In Evaluation, check weights and scores against the ready-made project (aptidao_expansao.geosaga.json).',
             'In Voronoi, check the extent: with "Visible extent in QGIS", the total area changes with the zoom and the '
             'areas do not match; use the reference raster grid.'])
    h2('Next steps')
    bullets(['Repeat the lessons with your own data: the route is the same.',
             'See the **User Manual** for every field, advanced option and tip of each module.',
             'Watch the video of each module on the project channel (links on the official website).'])
    return {'lang': LANG, 'ui': UI, 'blocks': B}
