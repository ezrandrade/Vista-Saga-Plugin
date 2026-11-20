"""User manual text in English (Vista Saga Plugin 1.6.0). Same structure as content_pt.py."""

LANG = 'en'
UI = {
    'doc_title': 'User Manual',
    'subtitle': 'Vista Saga Plugin 1.6.0 for QGIS 4',
    'tagline': 'Geoprocessing inspired by Vista SAGA/UFRJ, in seven modules',
    'author': 'Esdras Andrade (IGDEMA/UFAL)',
    'date': 'November 2026',
    'toc': 'Contents',
    'figure': 'Figure',
    'table': 'Table',
    'tip': 'Tip',
    'warning': 'Warning',
    'note': 'Note',
    'hidden': 'Tips only the manual tells you',
    'fields_title': 'Window fields and buttons',
    'fields_cols': ['Section', 'Element', 'Type', 'What it does'],
    'kinds': {'PushButton': 'button', 'ToolButton': 'button', 'CheckBox': 'check box', 'LineEdit': 'text field',
              'ComboBox': 'drop-down list', 'MapLayerComboBox': 'QGIS layer', 'SpinBox': 'number field',
              'DoubleSpinBox': 'number field', 'ListWidget': 'list'},
    'close_label': 'Close (auxiliary window)',
    'compare_cols': ['Similar routine', 'What changes in Vista Saga Plugin'],
    'results_cols': ['File or output', 'Content and how to read it'],
    'routine': 'Correct way to use it',
    'concept': 'What it is for',
    'compare': 'How it differs from similar routines',
    'ease': 'Ease of use',
    'window': 'The window',
    'results': 'Results and how to interpret them',
    'pitfalls': 'Common mistakes and how to avoid them',
    'footer': 'Vista Saga Plugin 1.6.0 - User Manual',
    'page': 'Page',
}

INTRO = {
    'title': 'Introduction',
    'paras': [
        '**Vista Saga Plugin** is an independent plugin for **QGIS 4** that brings together, in seven modules, '
        'geographic analysis procedures inspired by **Vista SAGA**, the environmental analysis system created at the '
        'Geoprocessing Laboratory of UFRJ (Brazil). The plugin uses no code from the original program: the methods '
        'were reimplemented and, in the modules that produce comparable numbers, **validated against the original '
        'Vista SAGA**, cell by cell.',
        'The goal is to let you follow the same reasoning as Vista SAGA (signatures, monitoring, evaluation by weights '
        'and scores, influence areas) inside QGIS, with the data you already use, without manual conversions and with '
        'reports ready for spreadsheets and technical texts.',
        'For each module, this manual explains **what it is for**, **how it differs from similar routines** in QGIS '
        'and other plugins, **every field of the window**, the **correct way to use it**, **how to read the results** '
        'and the **tips that do not show on screen**.',
    ],
    'audience_title': 'Who this manual is for',
    'audience': [
        'People working on environmental diagnosis, urban or regional planning, watershed and land-use studies.',
        'Former Vista SAGA users who want to reproduce the same analyses in QGIS.',
        'Students and teachers of Geography, Ecology, Engineering and related fields who need explainable geographic '
        'analyses with auditable reports.',
    ],
    'principles_title': 'Plugin principles',
    'principles': [
        '**Method fidelity:** when there is a Vista SAGA model, the plugin follows it and states where it differs.',
        '**Nothing is done behind your back:** the plugin does not reproject maps silently, does not assume scores, '
        'does not drop classes on its own and never changes the input data.',
        '**Auditable reports:** every result comes with a readable TXT and a CSV for spreadsheets, always in '
        'Portuguese, whatever the interface language.',
        '**One way of working:** the seven modules share the same window layout, buttons and results.',
    ],
}

INSTALL = {
    'title': 'Installation and first steps',
    'steps_title': 'Installation',
    'steps': [
        'Download **Vista_Saga_Plugin_QGIS4_v1.6.0.zip** (the installation ZIP, not the GitHub source code).',
        'In QGIS 4, open **Plugins > Manage and Install Plugins > Install from ZIP**.',
        'Choose the ZIP, click **Install Plugin** and restart QGIS.',
        'The **Vista Saga Plugin** button appears on its own toolbar; clicking it opens the menu with the seven '
        'modules. They are also under **Raster > Vista Saga Plugin**.',
    ],
    'warning': 'The installed folder is called **geosaga** on purpose. Do not rename it: older models and projects '
               'depend on that name and on the **geosaga:*** processing identifiers.',
    'common_title': 'What is the same in every module',
    'common': [
        '**Language:** the interface follows the QGIS language (Portuguese, English or Spanish; English for the '
        'others). CSV and TXT reports are always written in Portuguese.',
        '**Tooltips:** hover over any button, field, check box or list to see a yellow box explaining what it does.',
        '**Standard footer:** **[Run]** and **[Close]** in every window; Evaluation also has **[Validate]**.',
        '**Non-modal window:** the module window can stay open while you work on the QGIS map (select features, '
        'change styles, open layers).',
        '**Progress:** while running, a progress window with **Cancel** appears; the outcome (finished, cancelled) is '
        'shown in the QGIS message bar.',
        '**Temporary or saved result:** an empty **Save to** field gives a temporary result named '
        '"Module - operation" (for example, "Análises Voronoi - Com Atrito"); when filled in, the result is saved to '
        'the chosen file and loaded with that file name.',
        '**Input data untouched:** no module changes the input layers.',
    ],
    'temp_warning': 'Temporary results live in the QGIS temporary folder and **disappear when QGIS closes**. Save them '
                    '(right-click the layer > Export) before quitting, or fill in **Save to** from the start.',
    'tooltip_fig': 'Tooltips (yellow boxes) explain every element of the window',
}

CONCEPTS = {
    'title': 'Concepts used throughout this manual',
    'items': [
        ('Categorical (thematic) map', 'A map in which each cell or polygon belongs to a **class** (land use, soil '
         'type, district). Most modules use this kind of map. Continuous values (elevation, temperature) must be '
         'classified first.'),
        ('Class, code and label', 'Each class has a **code** (an integer in rasters; a field value in vectors) and a '
         '**name** (the label). The plugin reads names from the file (RS2 legend, GeoTIFF category names, .rs2.json '
         'file) or, in Signature, from the layer style in QGIS.'),
        ('BACKGROUND (FUNDO) and NoData', '**FUNDO** is the background class of the RS2 format (usually code 0). '
         '**NoData** is the "no data" value of a GeoTIFF. Each module states how it handles them; in Signature, for '
         'example, both count as a class, as in Vista SAGA.'),
        ('CRS (reference system)', 'Defines the map coordinates. To measure areas and distances, use a **projected CRS '
         'in meters** (for example, UTM SIRGAS 2000). The plugin **does not reproject silently**: maps analysed '
         'together must share the same CRS.'),
        ('Grid (raster)', 'Cell size, extent and alignment of a raster. Modules that compare rasters cell by cell '
         'require **the same grid** for all maps.'),
        ('RS2', 'The Vista SAGA raster format (a .rs2 file). It does not store the CRS: the plugin records it in a '
         'side file (**.rs2.json**) or asks you to confirm it. The Format Converter moves data between RS2, GeoTIFF '
         'and vector.'),
        ('Sliver', 'A very thin overlap or gap between neighbouring polygons, caused by coordinate imprecision. In '
         'vector Combination and Signature, slivers with a **mean width below 1 cm** are tolerated and recorded in '
         'the report.'),
    ],
}

MODULES = {}

MODULES['assinatura'] = {
    'title': 'Signature',
    'figure': ('assinatura', 'Signature: the selection on the reference map cuts every map in the list'),
    'concept': [
        'Signature answers the question **"what is this area made of?"**. You choose a **reference map** (for '
        'example, districts), select one or more of its classes or features (for example, two districts) and the '
        'plugin measures, **within that boundary**, how much each class of each map in the list occupies: land use, '
        'soils, education level, slope.',
        'It is the Vista SAGA model: the reference is at the top of the list, its selection sets the boundary and '
        '**every map is signed, including the reference**. The result comes for the **union** of the selection and, '
        'if you want, **per feature** (one block for each selected district).',
        'For each class, the report gives the area in the whole map, the area within the boundary and two '
        'percentages: **% signed area** (what the place is made of) and **% category** (how much of the class is '
        'concentrated there).',
    ],
    'compare': [
        ('Zonal statistics and Zonal histogram (QGIS Processing)', 'They count raster pixels per polygon. Signature '
         'signs **several maps at once**, uses the **selection** on the reference map as the boundary, computes the '
         '**union** and each feature, and delivers the two Vista SAGA percentages ready to use.'),
        ('Vector intersection followed by a pivot table', 'Several manual steps that do not handle overlaps. The '
         'Vector tab performs an exact intersection, **dissolves** polygons of the same class, separates the '
         '**overlap** between classes and shows what was left **without class**.'),
        ('Original Vista SAGA Signature', 'Same columns and logic. Selection is by **whole class** (Vista SAGA\'s '
         'bucket marks a contiguous region); class names may come from QGIS; reports are written as TXT and CSV.'),
    ],
    'ease': [
        'The order of the list says it all: **the first map is the reference**.',
        'In raster, just check the classes; "Check all" equals "Sign the whole map".',
        'In vector, selection is done with QGIS itself, through the **Select on map** button.',
        'The **Results** tab shows the table and lets you switch between the union and each feature.',
    ],
    'windows': [('assinatura_raster', 'Signature, Raster tab: maps, reference classes, options and result'),
                ('assinatura_vetorial', 'Signature, Vector tab: class fields and selection made on the QGIS map'),
                ('assinatura_resultados', 'Signature, Results tab: cut (union or feature) and table')],
    'routine': [
        'Choose the **Raster** or **Vector** tab (formats are not mixed: raster only with raster, vector only with '
        'vector).',
        'In **1. Maps**, add the maps. **The first one in the list is the reference**; use **Move up/down** to change '
        'the order. All of them must share the **same projected CRS in meters**; in raster, also the **same grid**. '
        'An RS2 without .rs2.json asks for its CRS when added.',
        'In vector, select each map in the list and check the **Class field** and the **Legend field**.',
        'In **2. Selection on the reference**: in raster, check the classes; in vector, click **Select on map** and '
        'click the features on the QGIS map (Ctrl+click adds or removes). The counter shows how many are selected.',
        'In **3. Options**, keep **Per-feature result** on if you want a block for each feature; in vector, choose '
        'how to treat overlaps between classes.',
        'In **4. Result**, enter a title (optional) and choose where to save the CSV (the TXT goes next to it). Click '
        '**Run**.',
        'Check the **Results** tab and open the TXT for the full reading.',
    ],
    'results': [
        ('TXT report', 'A header with maps, CRS, selection, method and warnings; then a block for the **union of the '
         'selection** and one block for each feature (or class, in raster). Each block has one table per map.'),
        ('CSV report', 'One row per cut, map and class. Columns: RECORTE (UNIAO or FEICAO), ID_FEICAO, NOME_FEICAO, '
         'MAPA, CODIGO, CLASSE, TOTAL_PIXELS, TOTAL_HA, PIXELS_ASN, AREA_ASN_HA, PCT_AREA_ASN, PCT_CATEGORIA. '
         '";" separator and UTF-8: opens directly in Excel or LibreOffice.'),
        ('% signed area', 'Class area in the boundary ÷ boundary area. **Characterizes the place**; adds up to 100% in '
         'each map.'),
        ('% category', 'Class area in the boundary ÷ class area in the whole map. **Measures concentration**; does not '
         'add up to 100% and must not be summed.'),
        ('Special rows', 'BACKGROUND and NoData count as classes. In vector: **No class** (part of the boundary without '
         'a polygon in the map) and **Excluded overlap** (region where different classes overlap).'),
    ],
    'hidden': [
        'The table of the reference itself always shows 100% for the selected classes: it is there to **check the '
        'exact size of the boundary**, which is the base of all other maps.',
        'Raster class names come from the **layer style in QGIS** (Paletted/Unique values symbology) when the map was '
        'added from the project: rename the classes in the symbology and run again.',
        'With many selected features, **turn off "Per-feature result"**: the TXT gets huge and the union is still '
        'there.',
        '**Do not add up the per-feature blocks** to get the union: if two features overlap, the union counts the '
        'common area only once. Use the union block.',
        'In the CSV, filter the **RECORTE** column and build pivot tables by MAPA and CLASSE.',
        'The **Sliver tolerance** section of the TXT (vector) lists gaps and overlaps thinner than 1 cm: it is for '
        'auditing, not for interpretation.',
        'Raster and vector give slightly different numbers (cells × exact polygon). To compare places or dates, always '
        'use the same format and the same grid.',
    ],
    'pitfalls': [
        '**"Map X is in a different CRS":** reproject it beforehand in QGIS (the plugin does not reproject).',
        '**"Map X is not on the same grid":** align the rasters first (same cell size, extent and origin).',
        '**"No feature selected":** use **Select on map** and click the features, or **Select all**. The QGIS '
        'selection tool acts on the active layer; the button makes the reference active for you.',
        'Classes shown as "Class 7": the file has no stored names; name them in the QGIS symbology.',
    ],
}

MODULES['monitoria'] = {
    'title': 'Monitoring',
    'figure': ('monitoria', 'Monitoring: two periods, the transition map and the transition matrix'),
    'concept': [
        'Monitoring answers the question **"what changed between two periods?"**. It compares an initial and a final '
        'map of the same area and finds, for each cell (raster) or piece of polygon (vector), whether the class '
        '**stayed the same** or **changed** and into which class.',
        'The result is a **transition map**, a **transition table** and a **transition matrix** (initial class in '
        'rows, final class in columns), with areas and percentages.',
    ],
    'compare': [
        ('Raster calculator and hand-made cross tabulation', 'They require coding the transitions and counting '
         'separately. Monitoring produces the map, the table and the matrix in one run, with a descriptive legend '
         '("Remained", "Ceased to be … → Became …").'),
        ('Change tools of classification plugins', 'Usually raster only. Monitoring also has a **Vector** tab that '
         'compares polygons by exact overlay, in hectares.'),
        ('Vista SAGA Monitoring', 'Same reasoning of transition map and matrix; here with a legend in words or codes, '
         'a copyable table and the result loaded in QGIS.'),
    ],
    'ease': [
        'Two maps, two periods, one button: the transition map is loaded with colours and legend.',
        'Persistence in grey and changes in distinct colours, for immediate reading.',
        'Results tables copyable to spreadsheets (Ctrl+A, Ctrl+C).',
    ],
    'windows': [('monitoria_raster', 'Monitoring, Raster tab: initial map, final map and result'),
                ('monitoria_vetorial', 'Monitoring, Vector tab: layers, class fields and period')],
    'routine': [
        'Choose the **Raster** tab (categorical maps on the same grid) or **Vector** (polygon layers).',
        'Set the **initial map** and the **final map** (QGIS layer or file) and the name of each **period** (for '
        'example, the year).',
        'In vector, choose the **class field** of each period and, if available, the **legend field**.',
        'Enter a **title** and, if you wish, where to save. In raster, open **Advanced options: legend** to choose a '
        'legend in words or codes and, optionally, a CSV table with the class names.',
        'Click **Run** and check the transition map and the **Results** tab.',
    ],
    'results': [
        ('Transition map', 'GeoTIFF (raster) or GeoPackage (vector) with one code per transition, loaded with a '
         'legend: persistence in grey, changes in colours.'),
        ('_transicoes.csv', 'One row per transition: initial class, final class, situation (persistence or change), '
         'area (cells or ha) and percentage.'),
        ('_matriz.csv', 'Transition matrix: rows = initial class, columns = final class. The diagonal is persistence; '
         'off the diagonal, change.'),
        ('_resumo.txt', 'Summary: total area, evaluated area, main persistence and changes.'),
    ],
    'hidden': [
        'In the Vector tab, **only the area common to both layers** is compared: check that both periods cover the '
        'same area and use equivalent classes.',
        'The class-name table (raster) uses the **PERIODO;CODIGO;CLASSE** format: useful when rasters have no stored '
        'names or classes were renamed between periods.',
        'The matrix is quicker to read by **rows**: each row shows where each class of the initial period went.',
        'When the file field is filled in, it takes **priority** over the layer chosen in the list.',
    ],
    'pitfalls': [
        'Rasters on different grids: align them first.',
        'Classes with different codes between periods (for example, 3 = Water in one and 3 = Forest in the other) '
        'produce false changes: standardize the legend first.',
        'Mann–Kendall (trend in long series) was removed from Monitoring and will return as a module of its own in '
        'version 2.0.',
    ],
}

MODULES['avaliacao'] = {
    'title': 'Evaluation',
    'figure': ('avaliacao', 'Evaluation: scores by class, weights by criterion and the weighted mean'),
    'concept': [
        'Evaluation answers the question **"where is it most suitable (or most critical)?"**. It is Vista SAGA\'s '
        'multicriteria evaluation: each map is a **criterion** with a **weight** (in %), and each class gets a '
        '**score** (0 to 10 or 0 to 100). The result is the **weighted mean** of the scores at each place.',
        'There are three tabs with the same layout: **Raster** (categorical maps on the same grid), **Vector '
        '(Attributes)** (several fields of one polygon layer) and **Vector (Overlay)** (several polygon layers '
        'overlaid; only the area common to all of them is evaluated).',
    ],
    'compare': [
        ('Raster calculator with reclassification', 'You must reclassify each map and type the formula. Evaluation '
         'builds the weighted mean from tables of scores and weights, and **blocks the run** while any class has no '
         'score.'),
        ('Weighted overlay in other programs', 'Usually raster only. Here, vector tabs **preserve the geometry** of the '
         'features (Attributes) or overlay layers (Overlay).'),
        ('Vista SAGA Evaluation', 'Same method of weights and scores, with "round half to even" as in the original; '
         'the weights and scores used are saved in a reusable project file.'),
    ],
    'ease': [
        'Classes without a score are **highlighted** and counted; **Validate** lists every pending item.',
        'The **Tab** key jumps from weight to weight and from score to score.',
        'Click the header of the class table to sort.',
        'Each run saves the weights and scores so you can reopen them later.',
    ],
    'windows': [('avaliacao_raster', 'Evaluation, Raster tab: maps and weights, classes and scores, result'),
                ('avaliacao_atributos', 'Evaluation, Vector (Attributes) tab: fields of one layer as criteria'),
                ('avaliacao_sobreposicao', 'Evaluation, Vector (Overlay) tab: stacked layers')],
    'routine': [
        'Choose the tab according to your data: **Raster**, **Vector (Attributes)** or **Vector (Overlay)**.',
        'Choose the **score scale** (0 to 10 or 0 to 100).',
        'Add the criteria (maps, fields or layers) and type each **weight**. New weights start blank; **Distribute weights '
        'equally** divides 100% among all of them.',
        'Select a criterion and give a **score** to each class. For several classes with the same score, select them '
        'and use **Apply**. Check **Do not evaluate** for classes that must be left out.',
        'Click **Validate** to see what is missing. Fix it until nothing is pending.',
        'In **3. Result**, choose where to save (or keep it temporary) and keep the CSV and TXT reports checked. Click '
        '**Run**.',
    ],
    'results': [
        ('Evaluation map', 'GeoTIFF (Raster) or GeoPackage (vector tabs) with the final score of each place.'),
        ('_relatorio.csv', 'Class combinations found, scores, final score and areas.'),
        ('_relatorio.txt', 'Report in the Vista SAGA template: criteria, weights, scores and result distribution.'),
        ('*_pesos_notas.geosaga.json', 'The weights and scores used, to reopen with **Open project…** and repeat or '
         'adjust the evaluation.'),
    ],
    'hidden': [
        'The score **"—"** means "no score" and **prevents the run**: the plugin never assumes a score of 0 nor drops '
        'classes on its own.',
        '**Do not evaluate** turns the class into NoData in the result; use it for areas that should not be classified '
        '(for example, water bodies).',
        'New weights start **blank** on purpose: the equal split only happens through the button.',
        'The project file stores paths relative to its own folder: you can move the whole study folder.',
        'In the Overlay tab, **only the area common to all layers** is evaluated; check coverage first.',
        'Tables accept Ctrl+A and Ctrl+C to copy to spreadsheets, with the decimal separator of your language.',
    ],
    'pitfalls': [
        'Weights not adding up to 100%: the line below the table shows how much is missing.',
        'Rasters on different grids are not accepted in the Raster tab.',
        'Scores planned on 0 to 100 typed with the 0 to 10 scale: choose the scale before scoring.',
    ],
}

MODULES['voronoi'] = {
    'title': 'Voronoi Analyses',
    'figure': ('voronoi', 'Voronoi analyses: the four modes computed by the plugin itself'),
    'concept': [
        'Voronoi analyses answer the question **"what is the influence area of each point?"**. From generating points '
        '(schools, health centres, offices), each place is assigned to the point that "attracts" it the most.',
        'There are four modes, all following the Vista SAGA model and validated against it: **Simple** (shortest '
        'distance), **With mass** (largest M/d², where M is the mass of the point), **With friction** (lowest cost '
        'accumulated along the straight line between the point and the place, over a friction surface) and **Mass '
        'and friction** (lowest cost ÷ M).',
        'The friction cost is the sum, over the cells of the line between the point and the place, of **distance to '
        'the point × friction rating × step**. The rating is the cost itself (rating 1 = base cost). It is not a '
        'least-cost path: the line does not detour around obstacles, it "pays" for them.',
    ],
    'compare': [
        ('Voronoi polygons (QGIS Processing)', 'Only the Simple mode, in vector. The plugin adds **mass**, **friction** '
         '(raster or polygons), combination of several surfaces and raster or vector output.'),
        ('Cost distance (r.cost and similar)', 'They compute the **least-cost path**, which goes around obstacles. The '
         'Vista SAGA model uses the **straight line** between the point and the place; the results differ and the '
         'plugin reproduces Vista SAGA\'s.'),
        ('Vista SAGA Voronoi', 'Same method (Simple and Mass 100% identical; friction 99.4% to 99.7% of cells). Adds '
         'the vector friction surface and exact vector output.'),
    ],
    'ease': [
        'Choose the mode and the plugin shows only the fields it needs.',
        'Raster and Vector tabs share the same input data.',
        'Mass as M/d²: a mass of 9 reaches 3 times farther than a mass of 1, not 9 times.',
    ],
    'windows': [('voronoi_raster', 'Voronoi analyses, Raster tab: mode, input data and result'),
                ('voronoi_vetorial', 'Voronoi analyses, Vector tab')],
    'routine': [
        'Choose the **Raster** tab (cell grid) or **Vector** (polygons with exact boundaries).',
        'Choose the **mode**.',
        'Set the **generating points** layer, the **identifier** field and, in the mass modes, the **mass field** '
        '(positive).',
        'With friction, choose the **surface type**: raster (rating in each cell) or polygons (rating in a column); '
        'for several surfaces, check **Combine multiple friction surfaces** and set weights and ratings.',
        'Set the **analysis extent** (visible in QGIS, polygon layer, manual, points + margin or reference raster) '
        'and, in raster, the **resolution**.',
        'Choose where to save (or keep it temporary) and click **Run**.',
    ],
    'results': [
        ('Region map', 'Raster or vector layer with the region of each point, loaded with colours and the point name.'),
        ('_centros.csv', 'One row per point: identifier, mass, cells, area (m² and ha) and % of the evaluated area.'),
        ('_resumo.txt', 'Mode, criterion used, cell size, clipping and the same table per point.'),
    ],
    'hidden': [
        'Ties between points: the **first one in the list** (the layer order) wins, as in Vista SAGA.',
        '**A friction rating of 0 is refused**; for "almost no friction" use a small value, such as 0.1.',
        'NoData in the friction raster, areas without polygons and empty column values **get no result** but are '
        '**crossed with rating 1** (base cost).',
        'The **reference raster** fixes the extent, resolution and CRS of the grid: use it to match the result to '
        'other rasters of the study.',
        'With a polygon-layer extent, only cells whose **centre lies inside the area** get a result.',
        'The Vector tab with friction traces boundaries with a 0.5 m tolerance, without rasterizing.',
    ],
    'pitfalls': [
        'Geographic CRS (degrees): use a projected CRS in meters, because distances and masses depend on meters.',
        'Zero or negative masses are refused.',
        'Old friction rasters containing 0 must be revised (rating 0 is not accepted).',
    ],
}

MODULES['combinacao'] = {
    'title': 'Map Combination',
    'figure': ('combinacao', 'Map Combination: each association of classes gets a code'),
    'concept': [
        'Combination answers the question **"which class associations exist and how much do they occupy?"**. It '
        'overlays two or more categorical maps and gives a **code to each observed association** (for example, '
        '"Agriculture on Argisol"), without weights or scores.',
        'The result is the **combined map** and the **combination table**, with the area and percentage of each one. '
        'It is the basis for discovering patterns before an evaluation.',
    ],
    'compare': [
        ('Vector Intersection and Union (QGIS)', 'They overlay geometries but do not code the associations nor handle '
         'slivers. Combination creates the **COD_nn/LEG_nn** fields, tolerates slivers thinner than 1 cm and merges '
         'crossing residues into the neighbour.'),
        ('r.cross (GRASS)', 'Overlays rasters, but the combination legend is coded. Here the table brings the class '
         'names of each map and the areas.'),
    ],
    'ease': [
        'The list order is the combination order, adjusted with Move up/down.',
        'Result loaded in QGIS with colours and legend (up to 75 combinations).',
        'Works with raster or vector.',
    ],
    'windows': [('combinacao_raster', 'Map Combination, Raster tab: maps in combination order'),
                ('combinacao_vetorial', 'Map Combination, Vector tab: class field and legend field')],
    'routine': [
        'Choose the **Raster** or **Vector** tab.',
        'Add **two or more maps** (selected layer, several from QGIS or files).',
        'In vector, select each layer in the list and check the **class field** and the **legend field**.',
        'Adjust the order with **Move up/down**: it sets the order of the columns in the table.',
        'Choose where to save (or keep it temporary) and click **Run**.',
    ],
    'results': [
        ('Combined map', 'GeoTIFF or GeoPackage with one code per association (vector: fields COD_01/LEG_01, '
         'COD_02/LEG_02…).'),
        ('_combinacoes.csv', 'One row per combination: code, classes of each map, area and percentage.'),
        ('_resumo.txt', 'Summary, tolerated slivers and merged residues (vector).'),
    ],
    'hidden': [
        'In vector, overlaps within the same layer with a **mean width below 1 cm** are tolerated and recorded in the '
        'summary; above that, the run stops and lists the pairs.',
        'Thin crossing residues (below 1 cm) are merged into the neighbour with the **longest common boundary**, '
        'removing false combinations without changing the total area.',
        'Only the **area common to all maps** is combined (vector).',
    ],
    'pitfalls': [
        'Many classes in many maps produce thousands of combinations: start with few maps.',
        'Rasters on different grids are not combined: align them first.',
    ],
}

MODULES['conversor'] = {
    'title': 'Format Converter',
    'figure': ('conversor', 'Format Converter: six conversions between RS2, GeoTIFF and vector'),
    'concept': [
        'The Converter moves data between Vista SAGA\'s **RS2** format, **GeoTIFF** and **vector** (GeoPackage, '
        'Shapefile, GeoJSON, FlatGeobuf), in six operations: RS2 → GeoTIFF, GeoTIFF → RS2, RS2 → Vector, GeoTIFF → '
        'Vector, Vector → GeoTIFF and Vector → RS2.',
        'It preserves class **codes, names and colours**, records the RS2 CRS in the **.rs2.json** file and can '
        'convert **many files in batch**.',
    ],
    'compare': [
        ('Rasterize, Polygonize and Translate (QGIS/GDAL)', 'They neither read nor write RS2 and do not carry the class '
         'legend. The Converter keeps codes, names and palette and writes a **.qml** style with the real classes.'),
        ('Vista SAGA export', 'RS2 does not store a CRS; the Converter records it in .rs2.json, so the other modules '
         'can find it.'),
    ],
    'ease': [
        'Choose the operation and the window shows only what it needs.',
        '**RS2 properties…** shows header, legend and grid before converting.',
        'Batch: the same operation for many files at once.',
    ],
    'windows': [('conversor', 'Format Converter: Vector → GeoTIFF operation'),
                ('conversor_rs2', 'Format Converter: RS2 → GeoTIFF operation, with the RS2 CRS')],
    'routine': [
        'Choose the operation in **Convert**. For several files, check **Process multiple files (batch)**.',
        'Set the input file (or a project layer). For an RS2, use **RS2 properties…** to check the legend and grid.',
        'When rasterizing (Vector → GeoTIFF/RS2), choose the **field** and the **pixel size**; to align an RS2 with '
        'another, set the **reference RS2** in the advanced options.',
        'Confirm the **CRS** when the input or output is RS2.',
        'Set the output (or keep **Temporary result** checked) and click **Run**.',
    ],
    'results': [
        ('Class GeoTIFF', 'Class codes, palette, names (in .aux.xml) and a **<name>.qml** style that QGIS loads by '
         'itself, with only the real classes in the legend.'),
        ('RS2 + .rs2.json', 'The Vista SAGA file and the side file with CRS, legend and code mapping.'),
        ('Vector', 'Polygons with the class code and name (BACKGROUND optional).'),
    ],
    'hidden': [
        'When copying a class GeoTIFF to another folder, **take the .aux.xml and the .qml along**: they hold the '
        'class names and the style.',
        'RS2 requires codes from 0 (BACKGROUND) upwards; the **RS2 codes** option chooses between preserving and '
        'renumbering, and the mapping is kept in .rs2.json.',
        '**ALL_TOUCHED** marks every cell touched by a feature; without it, only cells whose centre lies inside it.',
        'When vectorizing, **8 neighbours** joins cells connected diagonally; **4 neighbours**, only by their sides.',
        'An old Vista SAGA RGB TIFF can have its classes recovered with the **reference RS2**.',
    ],
    'pitfalls': [
        'Geographic CRS when rasterizing: the pixel size ends up in degrees; use a projected CRS.',
        'Output over an existing file: the Converter also replaces the auxiliary files with the same name.',
    ],
}

MODULES['sequenciador'] = {
    'title': 'Map Sequencer',
    'figure': ('sequenciador', 'Map Sequencer: ordered frames become an animated GIF'),
    'concept': [
        'The Sequencer answers the question **"how do I show change over time?"**. It builds an animated **GIF** (and, '
        'if you want, the frames as **PNG**) from maps in order, with date, name and legend on each frame.',
        'There are three tabs: **Raster** (one raster per frame), **Vector** (one layer per frame, or frames generated '
        'from a date field) and **Mixed** (a vector over a background raster).',
    ],
    'compare': [
        ('QGIS Temporal Controller', 'Exports frames, but the GIF must be assembled elsewhere. The Sequencer builds the '
         'GIF directly, with labels and legend, and accepts mixed frames.'),
        ('Manual image editing', 'Requires exporting each map and building the animation in another program. Here the '
         'frames use the QGIS symbology and the order can be adjusted by date.'),
    ],
    'ease': [
        'Frames use the symbology you already set in QGIS.',
        'The order can be set by hand or by date, and dates can be edited.',
        'The source layers are not changed.',
    ],
    'windows': [('sequenciador', 'Map Sequencer: frame sequence, dimensions and outputs')],
    'routine': [
        'Choose the **Raster**, **Vector** or **Mixed** tab and add the frames.',
        'Check the order; use **Edit date…** and **Sort by date** when needed.',
        'In **2. Dimensions and composition**, set the width, height and duration of each frame, and what to write on '
        'the map (date, layer names, legend).',
        'In **3. Outputs and preview**, set the GIF and, if you wish, the PNGs. Click **Run**.',
    ],
    'results': [
        ('Animated GIF', 'The animation with frames in list order; a preview appears in the window itself.'),
        ('PNGs (optional)', 'One full-colour PNG per frame, in a folder next to the GIF (or the chosen one).'),
    ],
    'hidden': [
        'A GIF has at most **256 colours**; very colourful scenes are quantized. For exact colours, use the **PNGs**.',
        'The thematic legend shows up to **10 categories** per frame.',
        'The **cumulative** option shows, in each frame, the features of earlier periods: ideal for urban growth.',
        'Frames from a temporal field filter the layer **without changing the original layer or its filters** in the '
        'project.',
    ],
    'pitfalls': [
        'Frames with very different extents: put the layers on the same area first.',
        'A very short duration makes the animation unreadable; 800 to 1500 ms per frame usually works.',
    ],
}

VALIDATION = {
    'title': 'Validation against the original Vista SAGA',
    'paras': [
        'The modules with comparable numerical results were validated against the **original Vista SAGA**, run on '
        'Windows 7 in a virtual machine, with the same input data.',
        '**Voronoi analyses:** Simple and Mass reproduced **100% of the cells**; with friction, **99.4% to 99.7%** in '
        'the Raster tab and **99.1% to 99.6%** in the Vector tab (continuous version), with the differences '
        'concentrated on the boundaries between regions.',
        '**Signature:** whole map with **100%** agreement; in partial selections, the only differences are class cells '
        'joined to the rest only diagonally (Vista SAGA\'s bucket excludes them; the plugin marks the whole class).',
        'The comparison scripts are in the repository (**scripts/comparar_caso_bacia.py** and '
        '**scripts/comparar_assinatura_vista_saga.py**), for anyone who wants to repeat them with their own data.',
    ],
    'figure': ('painel', 'Validation and quality dashboard of the plugin'),
}

FAQ = {
    'title': 'Troubleshooting',
    'items': [
        ('I cannot find the plugin after installing it.', 'Restart QGIS. If the button does not appear, enable the '
         'toolbar in View > Toolbars > Vista Saga Plugin, or use Raster > Vista Saga Plugin.'),
        ('The message says the maps are in different CRSs.', 'Reproject the layers to the same projected CRS (Vector > '
         'Data Management Tools > Reproject Layer; Raster > Projections > Warp).'),
        ('The message says the rasters are not on the same grid.', 'Use Raster > Align Rasters with the same cell size, '
         'extent and origin.'),
        ('The temporary result disappeared.', 'Temporary results vanish when QGIS closes. Fill in Save to or export the '
         'layer before closing.'),
        ('Classes show up as "Class 1", "Class 2".', 'The file has no stored names. In Signature, name them in the '
         'layer symbology; in the Converter, keep the .aux.xml and the .qml next to the GeoTIFF.'),
        ('QGIS became slow during the run.', 'Use Cancel in the progress window, reduce the extent or increase the cell '
         'size, and run again.'),
        ('Where do I see details of an unexpected error?', 'In View > Panels > Log Messages, Vista Saga Plugin tab: the '
         'plugin records the technical details there.'),
    ],
}

GLOSSARY = {
    'title': 'Glossary',
    'items': [
        ('Signed area', 'Area of a class within the Signature boundary.'),
        ('Friction', 'Resistance to movement used in Voronoi; the rating is the cost per unit of distance.'),
        ('Criterion', 'Map or field used in Evaluation, with a weight.'),
        ('Feature', 'A polygon (or point) of a vector layer; in Signature raster, a checked class.'),
        ('BACKGROUND (FUNDO)', 'Background class of the RS2 format.'),
        ('Sliver', 'A very thin overlap or gap between polygons; tolerated below a 1 cm mean width.'),
        ('Mass', 'Weight of a generating point in Voronoi (M in M/d²).'),
        ('NoData', '"No data" value of a raster.'),
        ('RS2', 'Vista SAGA raster format.'),
        ('CRS', 'Coordinate reference system.'),
        ('Transition', 'Initial class → final class pair in Monitoring.'),
    ],
}

QUICK = {
    'title': 'Quick reference',
    'cols': ['I want to…', 'Module', 'Main output'],
    'rows': [
        ('know what an area is made of', 'Signature', 'TXT and CSV with % signed area and % category'),
        ('see what changed between two dates', 'Monitoring', 'Transition map and matrix'),
        ('find the most suitable areas', 'Evaluation', 'Map with the weighted mean'),
        ('outline influence areas', 'Voronoi Analyses', 'Region map and _centros.csv'),
        ('discover class associations', 'Map Combination', 'Combined map and _combinacoes.csv'),
        ('move data to/from Vista SAGA', 'Format Converter', 'RS2, GeoTIFF or vector'),
        ('show change as an animation', 'Map Sequencer', 'Animated GIF and PNGs'),
    ],
}
