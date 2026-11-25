"""Video scripts (YouTube), English. One video per module, using the Vila Serena data."""

LANG = 'en'
UI = {
    'doc_title': 'Video scripts', 'subtitle': 'Vista Saga Plugin 1.6.0 for QGIS 4',
    'tagline': 'Instructional video series - one video per module - English',
    'author': 'Esdras Andrade (IGDEMA/UFAL)', 'date': 'November 2026', 'toc': 'Contents', 'figure': 'Figure',
    'footer': 'Vista Saga Plugin 1.6.0 - Video scripts (en)', 'page': 'Page',
    'sheet': 'Video sheet', 'scenes': 'Script', 'youtube': 'Publishing on YouTube',
    'cols': ['Time', 'On screen', 'Narration (voice-over)', 'On-screen text'],
    'sheet_cols': ['Item', 'Content'],
    'fields': ['YouTube title', 'Estimated length', 'Goal', 'Data', 'Prerequisite', 'Thumbnail (text)'],
    'description': 'Description', 'chapters': 'Chapters', 'tags': 'Tags',
}

GUIDE = {
    'title': 'How to use these scripts',
    'paras': [
        'Each module of the Vista Saga Plugin gets a short video (4 to 6 minutes), recorded on the data of the '
        'fictitious town of **Vila Serena**, the same as in the step-by-step tutorial. The figures in the narration are '
        'the ones the plugin really produces with these data: viewers who repeat the steps get the same results.',
        'Each script has a **sheet** (title, length, goal, thumbnail text), the **scene table** (time, what is on '
        'screen, the narration and the overlay text) and the **publishing** material (YouTube description, chapters '
        'and tags).',
    ],
    'production_title': 'Production standard (for the whole series)',
    'production': [
        '**Screen:** 1920 × 1080, QGIS 4 in **English** (the plugin follows the QGIS language), light theme, normal '
        'interface font size. Close panels that will not be used.',
        '**Data:** package **dados_tutorial_vila_serena_en.zip** (class and district names in English), unzipped to '
        'C:\\VilaSerena\\dados, with the project already open, CRS EPSG:31985 and the layers loaded before recording. '
        'File names stay in Portuguese (uso_solo = land use, solos = soils, declividade = slope, atrito = friction, '
        'bairros = districts, escolas = schools); say the English meaning the first time each one appears.',
        '**Cursor:** click highlight on; move the mouse slowly and rest on the element while the narration names it.',
        '**Zoom:** use editing zoom (1.5× to 2×) whenever the narration mentions a field or a number.',
        '**Voice-over:** calm pace, about 150 words per minute; record the narration separately and sync in editing.',
        '**Standard opening (5 s):** Vista Saga Plugin logo + module name. **Standard closing (10 s):** "Data and '
        'tutorial on the official website: headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com" + end cards to the next video.',
        '**Captions:** build them from the Narration column (it is the final voice-over text).',
        '**On-screen text:** short (up to 8 words), lower third, for 3 to 5 seconds.',
    ],
    'series_title': 'Series order',
    'series': ['1. Format converter', '2. Signature', '3. Monitoring', '4. Map combination', '5. Evaluation',
               '6. Voronoi analyses', '7. Map sequencer'],
    'series_note': 'The order follows the tutorial: the Format converter prepares the district raster used in '
                   'Signature. Each video still stands on its own: when it needs a file from another video, the '
                   'narration says so.',
}

VIDEOS = [
    {
        'title': '1. Format converter',
        'sheet': ['Format converter: vector, GeoTIFF and Vista SAGA RS2 | Vista Saga Plugin for QGIS',
                  '5 min',
                  'Convert a vector to GeoTIFF on the study grid, name the classes and exchange data with the Vista '
                  'SAGA RS2 format.',
                  'bairros.gpkg (districts), uso_solo_2020.tif (land use 2020)',
                  'Plugin installed; Vila Serena project open.',
                  'FROM VECTOR TO RS2 IN ONE CLICK'],
        'scenes': [
            ('0:00', 'Standard opening.', '', 'Format converter'),
            ('0:05', 'Vila Serena project in QGIS; highlight the districts layer (vector) and land use 2020.',
             'In this video you will learn to use the Format converter of the Vista Saga Plugin. We will do two things: '
             'turn the districts of Vila Serena, which are polygons, into a raster on the same grid as the other maps; '
             'and take the land use map to RS2, the Vista SAGA format, and bring it back.', ''),
            ('0:25', 'Vista Saga Plugin menu open; click Format converter.',
             'Open the Vista Saga Plugin menu and choose Format converter.', ''),
            ('0:32', 'Convert list open, showing the six operations.',
             'There are six conversions: RS2 to GeoTIFF, GeoTIFF to RS2, RS2 or GeoTIFF to vector, and vector to '
             'GeoTIFF or to RS2. The window only shows the fields of the chosen operation.', 'Six conversions'),
            ('0:48', 'Choose Vector → GeoTIFF; Project vector layer: bairros; click Select.',
             'Choose Vector to GeoTIFF. In Project vector layer, choose the districts layer and click Select.', ''),
            ('1:00', 'Field to rasterize: CODIGO; Pixel size: 10 (zoom on both fields).',
             'In Field to rasterize, choose CODIGO, the district code: it is the value each cell will get. Pixel size: '
             'ten. Since the CRS is UTM, the unit is the metre.', '10 m pixel'),
            ('1:15', 'Output file: resultados\\bairros.tif; click Run; layer loaded.',
             'Set the output file and click Run. The raster is loaded with a style that shows only the classes that '
             'actually exist.', ''),
            ('1:30', 'Layer properties > Information: 200 × 200, pixel 10.',
             'Look: two hundred by two hundred cells of ten metres. Exactly the grid of the other maps, because the '
             'districts cover the whole study area. This will be essential in Signature.', '200 × 200 cells'),
            ('1:48', 'Raster symbology: labels "Classe 1…6"; edit them to the district names; OK.',
             'The GeoTIFF stores the codes, and QGIS shows "Classe 1", "Classe 2". Name the classes in Symbology: one, '
             'Riverside; two, Downtown; and so on. Signature uses these names.', 'Name the classes'),
            ('2:15', 'Attribute table of the districts next to Symbology (CODIGO and NOME).',
             'Tip: the attribute table of the vector holds the code-to-name correspondence. Keep it open next to '
             'Symbology and copy the names without mistakes.', 'Tip'),
            ('2:30', 'Back to the converter; choose GeoTIFF → RS2; input uso_solo_2020.tif; output uso_solo_2020.rs2.',
             'Now, the bridge to Vista SAGA. Choose GeoTIFF to RS2, select land use 2020 and an output file ending in '
             'dot rs2.', 'GeoTIFF → RS2'),
            ('2:48', 'Click Run; file manager showing .rs2 and .rs2.json.',
             'Run. Besides the RS2 file, the plugin writes a sidecar file, dot rs2 dot json. RS2 does not store the '
             'coordinate system; this file stores the CRS, the legend and the code mapping.', '.rs2.json = CRS'),
            ('3:10', 'Click RS2 properties…: header, legend and grid.',
             'The RS2 properties button shows the header, the legend and the grid before any conversion. Use it to '
             'check files you receive from Vista SAGA.', ''),
            ('3:25', 'Choose RS2 → GeoTIFF; input uso_solo_2020.rs2; CRS filled in (EPSG:31985); Run.',
             'To check, go back: RS2 to GeoTIFF. The CRS is already filled in, read from the sidecar file. Run.', ''),
            ('3:42', 'Side by side: uso_solo_2020.tif and uso_solo_2020_de_volta.tif, same legend.',
             'The GeoTIFF that came back is identical to the original, cell by cell, with the same class names and '
             'colours.', 'Round trip: identical'),
            ('3:58', 'Tips on screen.',
             'Three precautions. Always carry the dot rs2 dot json file with the RS2. When copying a class GeoTIFF, '
             'take the dot aux dot xml and the dot qml files too: they hold names and style. And to convert many files '
             'at once, tick Process multiple files.', 'Carry .rs2.json, .aux.xml, .qml'),
            ('4:30', 'Standard closing; end card to the Signature video.',
             'In the next video, we will use this district raster in Signature, to find out what each district is made '
             'of. See you there.', 'Next: Signature'),
        ],
        'description': 'Learn to use the Format converter of the Vista Saga Plugin for QGIS 4: rasterize a vector on '
                       'your study grid, name the classes and exchange data with the Vista SAGA RS2 format, with a '
                       'lossless round trip. Example data (the fictitious town of Vila Serena) and full tutorial on the '
                       'official website: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Opening', '0:25 The six conversions', '0:48 Vector to GeoTIFF', '1:48 Naming the classes',
                     '2:30 GeoTIFF to RS2', '3:25 RS2 back to GeoTIFF', '3:58 Precautions', '4:30 Next video'],
        'tags': 'QGIS, QGIS 4, Vista SAGA, SAGA UFRJ, RS2, GeoTIFF, rasterization, format conversion, GIS, Vista Saga Plugin',
    },
    {
        'title': '2. Signature',
        'sheet': ['Signature: what is this area made of? | Vista Saga Plugin for QGIS',
                  '6 min',
                  'Measure the make-up of an area (land use, soils, slope) inside selected districts and read the two '
                  'Vista SAGA percentages.',
                  'bairros.tif (from video 1, classes named), uso_solo_2020.tif, solos.tif, declividade.tif',
                  'District raster created in the Format converter video.',
                  'WHAT IS THIS DISTRICT MADE OF?'],
        'scenes': [
            ('0:00', 'Standard opening.', '', 'Signature'),
            ('0:05', 'Map of Vila Serena with Downtown and Riverside highlighted.',
             'What are Downtown and Riverside made of? How much of them is city, vegetation, pasture? Which soils and '
             'which slopes do they have? Signature answers this, for several maps at once.', ''),
            ('0:22', 'Open Vista Saga Plugin > Signature; Raster tab.',
             'Open Signature and stay on the Raster tab. Raster and vector do not mix: each tab works with one kind.', ''),
            ('0:32', 'Add the district raster first, then land use 2020, soils, slope.',
             'In Maps, add the district raster first. The rule is simple: the first map in the list is the reference, '
             'like the top map in Vista SAGA. Then add land use, soils and slope.', 'The 1st map is the reference'),
            ('0:55', 'Move up and Move down buttons (zoom).',
             'If the order is wrong, use Move up. All maps must share the same CRS and the same grid; if they do not, '
             'the plugin warns you and never reprojects anything on its own.', 'Same CRS, same grid'),
            ('1:12', 'In Selection on the reference, tick 1 - Riverside and 2 - Downtown.',
             'Selection on the reference lists the classes of the first map, with the names you gave in Symbology. '
             'Tick Riverside and Downtown. This selection is the boundary of the analysis.', ''),
            ('1:28', 'Options: Per-feature result on; title and Save to assinatura.csv; Run.',
             'Keep Per-feature result on: besides the union of both districts, you get one block for each. Type a '
             'title, choose where to save the CSV, and the TXT goes with it. Run.', ''),
            ('1:45', 'Results tab with the union table; zoom on the columns.',
             'The Results tab shows the table. The union covers one hundred and thirty hectares: seventy from '
             'Riverside and sixty from Downtown. The table of the reference map itself shows one hundred percent for '
             'the ticked classes: that is your check on the size of the boundary.', '130 ha'),
            ('2:10', 'Highlight the land use rows; % signed area column.',
             'Now land use. The percent of signed area column tells you what the place is made of: forty-five point '
             'five percent of the two districts is urban; twenty-five, pasture. This column adds up to one hundred.',
             '% signed area = make-up'),
            ('2:35', 'Highlight the % category column.',
             'The percent of category column tells you how much of the class is there: fifty-four percent of all urban '
             'area in Vila Serena lies in these two districts, and half of the water. This column does not add up to '
             'one hundred, and must not be added up.', '% category = concentration'),
            ('3:00', 'Cut list: switch from Union of the selection to Downtown, then Riverside.',
             'In the Cut list, look at each district. Downtown is seventy percent urban. Riverside only twenty-four, '
             'with forty-six percent pasture. And a third of Downtown lies on fluvic neosol, a floodplain soil.',
             'Downtown: 71% urban'),
            ('3:35', 'Open assinatura.txt and assinatura.csv in the editor and the spreadsheet.',
             'The TXT is the full report, in the Vista SAGA layout. The CSV opens straight in a spreadsheet: filter the '
             'RECORTE column and build a pivot table by map and class.', 'TXT + CSV'),
            ('4:00', 'Tips on screen.',
             'Two tips. Do not add up the per-district blocks to get the union: use the union block. And if classes '
             'show up as Classe 1, Classe 2, the file has no names: name them in Symbology and run again.',
             'Use the union block'),
            ('4:25', 'Vector tab (quick look): Select on map and feature counter.',
             'With vector data the logic is the same, on the Vector tab: you select features on the QGIS map with the '
             'Select on map button, and the plugin computes the exact intersection.', ''),
            ('4:45', 'Standard closing; end card to the Monitoring video.',
             'In the next video, Monitoring: what changed in Vila Serena between 2000 and 2020.', 'Next: Monitoring'),
        ],
        'description': 'Signature, in the Vista Saga Plugin, measures what an area is made of: select districts (or any '
                       'boundary) on a reference map and get, for several maps at once, the area and the two Vista SAGA '
                       'percentages (% signed area and % category). Example with the fictitious town of Vila Serena. '
                       'Data and tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Opening', '0:22 The first map is the reference', '1:12 Selection on the reference',
                     '1:45 Reading the table', '2:10 % signed area', '2:35 % category', '3:00 Per district',
                     '3:35 TXT and CSV', '4:25 Vector tab', '4:45 Next video'],
        'tags': 'QGIS, Vista SAGA, environmental signature, land use, zonal statistics, GIS, urban planning, Vista Saga Plugin',
    },
    {
        'title': '3. Monitoring',
        'sheet': ['Monitoring: what changed between two dates? | Vista Saga Plugin for QGIS',
                  '5 min',
                  'Compare land use in 2000 and 2020, create the transition map and read the transition matrix.',
                  'uso_solo_2000.tif, uso_solo_2020.tif',
                  'Vila Serena project open.',
                  'THE TOWN TRIPLED. AT WHAT COST?'],
        'scenes': [
            ('0:00', 'Standard opening.', '', 'Monitoring'),
            ('0:05', 'Land use 2000 and 2020 side by side.',
             'In twenty years, the urban area of Vila Serena grew a lot. But it grew over what? Monitoring compares two '
             'maps and shows, place by place, what stayed and what changed.', ''),
            ('0:20', 'Open Monitoring, Raster tab; Initial map: land use 2000; Period 2000.',
             'Open Monitoring. In Initial map, choose land use 2000 and type the period: 2000.', ''),
            ('0:35', 'Final map: land use 2020; Period 2020; title; Save to; Run.',
             'In Final map, the 2020 one, period 2020. Type a title, choose where to save and run. Both maps must share '
             'the same grid.', ''),
            ('0:55', 'Transition map loaded: persistence in grey, changes in colours.',
             'The transition map arrives ready: persistence in grey, changes in colours, with a legend in words. The '
             'coloured ring around the centre is urban growth.', ''),
            ('1:15', 'Results tab: summary with persistence and change.',
             'In the summary, sixty-nine percent of the area persisted and thirty-one percent changed: one hundred and '
             'twenty-three hectares.', '31% changed'),
            ('1:32', 'Transitions table sorted by area; highlight the five largest changes.',
             'Sort the transitions by area. The largest change is pasture that became city: forty-seven hectares. Then '
             'native vegetation that became pasture, thirty hectares, and vegetation that became city, twenty-two.',
             'Pasture → Urban: 47 ha'),
            ('2:05', 'Open _matriz.csv in the spreadsheet; highlight the diagonal and one row.',
             'The transition matrix has the 2000 class in the rows and the 2020 class in the columns. The diagonal is '
             'what persisted. Read it by row: the native vegetation row shows where it went.', 'Read the matrix by row'),
            ('2:30', 'Highlight: urban 32.5 → 109.7 ha; vegetation 120.5 → 52.3 ha.',
             'Result: the urban area went from thirty-two to almost one hundred and ten hectares, three and a half '
             'times. Native vegetation lost more than half of its area.', 'Vegetation: -57%'),
            ('2:55', 'Highlight water (12.8 ha on both dates).',
             'Look at the water: twelve point eight hectares on both dates. It is a quality check. If the river '
             '"changed", I would distrust the maps, not reality.', 'Water = quality check'),
            ('3:15', 'Advanced options: legend (words or codes; class name table).',
             'Under Advanced options, choose a legend in words or by codes, and optionally a table with the class names '
             'of each period, useful when the rasters have no stored names.', ''),
            ('3:35', 'Vector tab (quick look).',
             'With polygons, use the Vector tab: choose the class field for each date. Only the area shared by both '
             'layers is compared.', ''),
            ('3:50', 'Tips on screen.',
             'Watch out for different legends between dates: if code three is water on one map and forest on the other, '
             'you get false changes. Harmonize the legend first.', 'Harmonize the legend'),
            ('4:10', 'Standard closing; end card to the Map combination video.',
             'In the next video, Map combination: which associations of land use and soil exist in Vila Serena.',
             'Next: Map combination'),
        ],
        'description': 'Monitoring, in the Vista Saga Plugin, compares two maps from different dates and delivers the '
                       'transition map, the transition table and the matrix, with areas and percentages. Example: urban '
                       'growth in Vila Serena from 2000 to 2020. Data and tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Opening', '0:20 Initial and final maps', '0:55 Transition map', '1:32 Largest changes',
                     '2:05 Transition matrix', '2:55 Quality check', '3:15 Options and Vector tab', '4:10 Next video'],
        'tags': 'QGIS, Vista SAGA, change detection, land use land cover, transition matrix, urban growth, Vista Saga Plugin',
    },
    {
        'title': '4. Map combination',
        'sheet': ['Map combination: which associations exist and how much area? | Vista Saga Plugin for QGIS',
                  '4 min',
                  'Cross land use and soils, read the combination table and find the city built on floodplain soil.',
                  'uso_solo_2020.tif, solos.tif',
                  'Vila Serena project open.',
                  'CITY ON THE FLOODPLAIN: WHERE?'],
        'scenes': [
            ('0:00', 'Standard opening.', '', 'Map combination'),
            ('0:05', 'Land use 2020 and soils side by side.',
             'Where is the city built on floodplain soil, prone to flooding? To answer, you must cross two maps. Map '
             'combination does it and gives a code to each association it finds, with no weights or scores.', ''),
            ('0:22', 'Open Map combination, Raster tab; add land use 2020 and soils.',
             'Open Map combination, Raster tab, and add land use 2020, then soils. The order of the list is the order of '
             'the columns in the table.', ''),
            ('0:40', 'Save to; Run; combined map loaded with colours and legend.',
             'Choose where to save and run. The combined map loads with colours and a legend.', ''),
            ('0:55', 'Open _combinacoes.csv; sort by area.',
             'The combination table lists each association with area and percentage. There are thirteen combinations '
             'in four hundred hectares. The largest is pasture on argisol: ninety-eight hectares.', '13 combinations'),
            ('1:25', 'Highlight the row Urban area | Fluvic neosol.',
             'And the one the town council cares about: urban area on fluvic neosol, seventeen point nine hectares, '
             'four and a half percent of the town. That is city on floodplain soil.', 'City on floodplain: 17.9 ha'),
            ('1:50', 'Symbology of the combined map: untick every class except 3.',
             'To see where it is, open the Symbology of the combined map and leave only that combination visible.', ''),
            ('2:10', 'Identify tool on a cell; value equal to ID_COMB in the CSV.',
             'With the Identify tool, the cell value is the combination code, the same ID as in the table.',
             'Cell value = ID_COMB'),
            ('2:25', 'Vector tab: class and legend fields; summary with slivers.',
             'On the Vector tab, choose the class field and the legend field of each layer. The result has COD and LEG '
             'fields for each map. Crossing slivers thinner than one centimetre on average are merged into the '
             'neighbour and reported in the summary.', 'Slivers < 1 cm'),
            ('2:55', 'Tips on screen.',
             'Start with few maps: with many classes, combinations multiply. And use Map combination to explore before '
             'an Evaluation: it shows what exists, without judging.', 'Explore before evaluating'),
            ('3:20', 'Standard closing; end card to the Evaluation video.',
             'In the next video, Evaluation: where Vila Serena can grow.', 'Next: Evaluation'),
        ],
        'description': 'Map combination, in the Vista Saga Plugin, crosses two or more categorical maps and gives a code '
                       'to each association of classes, with area and percentage. Raster or vector. Example: land use and '
                       'soils in Vila Serena. Data and tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Opening', '0:22 Setting up the combination', '0:55 Combination table',
                     '1:25 City on the floodplain', '2:10 Identify', '2:25 Vector tab', '3:20 Next video'],
        'tags': 'QGIS, Vista SAGA, cross tabulation, map overlay, soils, land use, Vista Saga Plugin',
    },
    {
        'title': '5. Evaluation',
        'sheet': ['Multi-criteria evaluation with weights and scores | Vista Saga Plugin for QGIS',
                  '6 min',
                  'Build a suitability-for-urban-growth evaluation (slope, soils, land use), validate, run and interpret '
                  'the map.',
                  'declividade.tif, solos.tif, uso_solo_2020.tif, aptidao_expansao.geosaga.json',
                  'Vila Serena project open.',
                  'WHERE CAN THE TOWN GROW?'],
        'scenes': [
            ('0:00', 'Standard opening.', '', 'Evaluation'),
            ('0:05', 'Slope, soils and land use maps.',
             'Where can Vila Serena grow with the least conflict? Evaluation answers with a weighted average: each map '
             'is a criterion with a weight, and each class gets a score.', ''),
            ('0:20', 'On-screen table with weights and scores.',
             'We will use three criteria: slope, with forty percent; soils, twenty-five; land use, thirty-five. The '
             'weights and scores in this example are for teaching: in a real study they need a justification.',
             'Weights: 40 / 25 / 35'),
            ('0:42', 'Open Evaluation, Raster tab; Score scale 0 to 10; add the three maps.',
             'Open Evaluation, Raster tab. Choose the zero to ten scale and add the three maps.', ''),
            ('0:58', 'Weights start blank; type 40, 25, 35 using Tab.',
             'Weights start blank, on purpose. Type the weights; the Tab key jumps from one to the next. Below, the '
             'message confirms: one hundred percent, valid distribution.', 'Tab jumps between weights'),
            ('1:18', 'Select slope; scores 10, 8, 4, 1. Soils: 7, 9, 2.',
             'Select each map and score its classes. Slope: flat ten, gently rolling eight, rolling four, strongly '
             'rolling one. Soils: argisol seven, latosol nine, fluvic neosol two.', ''),
            ('1:45', 'Land use: 8, 1, 6, 9; Water: tick Do not evaluate.',
             'Land use: urban eight, native vegetation one, farming six, pasture nine. For water, tick Do not evaluate: '
             'it stays out of the result.', 'Water: Do not evaluate'),
            ('2:05', 'A class without a score highlighted; click Validate; message listing what is missing.',
             'If a class is left without a score, it is highlighted, and the Validate button lists what is missing. The '
             'plugin never assumes a score of zero: no class enters the calculation without your decision.',
             'Never assumes score 0'),
            ('2:30', 'Click Open project… and choose aptidao_expansao.geosaga.json; everything filled in.',
             'Shortcut: in Open project, choose the ready-made file from the tutorial. Maps, weights and scores load at '
             'once. That is how you repeat or tweak an evaluation.', 'Open project…'),
            ('2:50', 'Save to aptidao_expansao.tif; reports ticked; Run.',
             'Choose where to save, keep the CSV and TXT reports ticked and run.', ''),
            ('3:05', 'Map loaded; legend from 3 to 9.',
             'The suitability map arrives in QGIS. Scores go from three to eight point nine, with a mean of six point '
             'three. Water, not evaluated, stays out.', 'Mean 6.3'),
            ('3:25', 'TXT report: summary by final score; highlight scores 8 and 9.',
             'In the report, the summary by final score: scores eight and nine add up to ninety-eight hectares, almost '
             'all on flat or gently rolling land, on argisol, under pasture or already urban.', 'Scores 8-9: 98 ha'),
            ('3:50', 'Highlight the combinations of score 3.',
             'Score three brings together the worst of everything: native vegetation on steep slopes. The report shows '
             'exactly which combination of classes produced each score.', ''),
            ('4:10', 'Compare: latosol on the hills with a low mean score.',
             'A telling detail: latosol has a score of nine, yet its mean on the map is the lowest, because it lies on '
             'the hills. Slope weighs more and dominates. Weights matter as much as scores.', 'Weight beats score'),
            ('4:35', 'File _pesos_notas.geosaga.json in the folder.',
             'Each run writes a file with the weights and scores used. Keep it with the report: it is the record of '
             'what you decided.', ''),
            ('4:50', 'Vector (Attributes) and Vector (Overlay) tabs, quick look.',
             'With vector data, use the Vector (Attributes) tab for fields of one layer, or Vector (Overlay) to cross '
             'layers. The layout is the same.', ''),
            ('5:05', 'Standard closing; end card to the Voronoi video.',
             'Test the sensitivity: change the weights and compare the maps. In the next video, Voronoi analyses.',
             'Next: Voronoi'),
        ],
        'description': 'Evaluation, in the Vista Saga Plugin, performs multi-criteria analysis with weights and scores, '
                       'following Vista SAGA: weighted average, classes without a score block the run, CSV and TXT '
                       'reports and a reusable project. Example: suitability for urban growth in Vila Serena. Data and '
                       'tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Opening', '0:20 Criteria and weights', '0:58 Typing weights', '1:18 Class scores',
                     '2:05 Validate', '2:30 Open project', '3:05 The suitability map', '3:25 Report by score',
                     '4:10 Weight beats score', '5:05 Next video'],
        'tags': 'QGIS, Vista SAGA, multi-criteria analysis, weighted overlay, suitability, urban planning, Vista Saga Plugin',
    },
    {
        'title': '6. Voronoi analyses',
        'sheet': ['Areas of influence with Voronoi: simple, with mass and with friction | Vista Saga Plugin for QGIS',
                  '6 min',
                  'Delimit the area of influence of schools by distance, by size (enrolment) and by travel difficulty '
                  '(river friction).',
                  'escolas.gpkg (schools), atrito.tif (friction)',
                  'Vila Serena project open.',
                  'THE RIVER CHANGES WHO SERVES WHOM'],
        'scenes': [
            ('0:00', 'Standard opening.', '', 'Voronoi analyses'),
            ('0:05', 'Map with the six schools and the river.',
             'Which school serves each part of Vila Serena? It depends on the question: by distance, by the size of the '
             'school or by how hard it is to get there. Voronoi analyses do all three.', ''),
            ('0:22', 'Open Voronoi analyses, Raster tab; Mode list open.',
             'Open Voronoi analyses. There are four modes: Simple, With mass, With friction and With mass and friction, '
             'all validated against the original Vista SAGA.', 'Validated against Vista SAGA'),
            ('0:38', 'Mode Simple; Generating points: escolas; Point identifier: NOME.',
             'Start with Simple. In Generating points, the schools; in Point identifier, the NOME field, the school '
             'name.', ''),
            ('0:50', 'Analysis extent: Reference raster grid; Reference raster: atrito.',
             'In Analysis extent, choose Reference raster grid and pick the friction raster. That way the result falls '
             'exactly on the grid of the other maps. Run.', 'Use the reference grid'),
            ('1:10', 'Simple result loaded; _centros.csv table.',
             'Each place goes to the nearest school. The centres table gives the area of each region.', ''),
            ('1:22', 'Mode With mass; Mass field: MATRICULAS; Run.',
             'Now With mass. In Mass field, choose MATRICULAS, the enrolment. The criterion is mass divided by distance '
             'squared, as in Vista SAGA.', 'Criterion: M/d²'),
            ('1:40', 'Compare Simple × With mass; highlight E. E. Darcy Ribeiro.',
             'Darcy Ribeiro school, with one thousand two hundred pupils, grows from forty to one hundred hectares. '
             'Cora Coralina, with two hundred and fifty, drops from forty to twenty-three.', 'Darcy Ribeiro: 40 → 100 ha'),
            ('2:05', 'Explanatory text on screen: 4× mass = 2× reach.',
             'An important detail: a school with four times the mass reaches twice the distance, not four times. It is '
             'the square root of the mass ratio.', '4× mass = 2× reach'),
            ('2:25', 'Mode With friction; Surface type Raster; Friction surface: atrito; Run.',
             'Now With friction. Choose the raster surface type and the friction map. In it, walking in the city costs '
             'one, pasture two, vegetation four, and crossing the water costs ten.', 'Water: friction 10'),
            ('2:50', 'Compare Simple × With friction; highlight E. M. Monteiro Lobato.',
             'Monteiro Lobato school, by the river, loses area: from fifty-nine to fifty hectares, because crossing the '
             'water became expensive. Cecília Meireles gains: from eighty-six to ninety-eight.', ''),
            ('3:15', 'Diagram on screen: straight line from school to place crossing the river.',
             'Mind the model: the cost is measured along the straight line between the school and each place, as in '
             'Vista SAGA. It is not the least-cost path of GRASS: the line does not go around the river, it pays for '
             'the crossing.', 'Cost on the straight line'),
            ('3:40', 'Vector tab: Simple and With mass with exact boundaries.',
             'On the Vector tab, the result comes as polygons, with exact boundaries for Simple and With mass, and '
             'traced without rasterizing in the friction modes.', ''),
            ('3:58', 'Combine multiple friction surfaces button (quick look).',
             'And if friction comes from several maps, such as relief and land use, tick Combine multiple friction '
             'surfaces and set weights and scores, as in Evaluation.', ''),
            ('4:15', 'Tips on screen.',
             'Three tips. A friction rating of zero is refused: for almost no friction, use zero point one. In a tie, '
             'the first point in the layer wins. And always use a CRS in metres.', 'Friction 0 is refused'),
            ('4:40', 'Standard closing; end card to the Map sequencer video.',
             'In the last video of the series, the Map sequencer: Vila Serena\'s growth as an animation.',
             'Next: Map sequencer'),
        ],
        'description': 'Voronoi analyses, in the Vista Saga Plugin, delimit areas of influence in four modes (Simple, '
                       'With mass, With friction, With mass and friction), following Vista SAGA and validated against it. '
                       'Raster or vector, with a raster or polygon friction surface. Example: the schools of Vila Serena '
                       'and the river. Data and tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Opening', '0:22 The four modes', '0:38 Simple', '1:22 With mass (M/d²)',
                     '2:25 With friction', '3:15 Cost on the straight line', '3:40 Vector tab', '4:15 Tips',
                     '4:40 Next video'],
        'tags': 'QGIS, Vista SAGA, Voronoi, Thiessen polygons, area of influence, friction surface, gravity model, Vista Saga Plugin',
    },
    {
        'title': '7. Map sequencer',
        'sheet': ['Map sequencer: animated GIF of change over time | Vista Saga Plugin for QGIS',
                  '4 min',
                  'Build a GIF animation (and PNG frames) with land use in 2000, 2010 and 2020.',
                  'uso_solo_2000.tif, uso_solo_2010.tif, uso_solo_2020.tif',
                  'Vila Serena project open, with the final symbology of the layers.',
                  '20 YEARS IN 3 SECONDS'],
        'scenes': [
            ('0:00', 'Standard opening.', '', 'Map sequencer'),
            ('0:05', 'The final GIF playing full screen.',
             'Twenty years of urban growth in three seconds. To present change over time, an animation communicates '
             'better than three maps side by side. The Map sequencer does it straight from QGIS.', ''),
            ('0:22', 'Open Map sequencer, Raster tab; add 2000, 2010 and 2020.',
             'Open the Map sequencer, Raster tab, and add the three land use maps. The plugin reads the year from the '
             'layer name and shows it in the list.', ''),
            ('0:40', 'Edit date… and Sort by date buttons.',
             'If needed, edit the date of a frame or use Sort by date. Move up and Move down adjust the order by hand.', ''),
            ('0:55', 'Dimensions: 600 × 600; Duration 1000 ms; Show date on; thematic legend.',
             'In Dimensions and composition, use six hundred by six hundred pixels and one second per frame. Turn on the '
             'date on the map and, if you like, the thematic legend, with up to ten categories.', '1 s per frame'),
            ('1:15', 'Outputs: .gif file; tick PNG frames; Run; preview in the window.',
             'Set the GIF file and tick Also export individual PNG frames. Run. The preview appears in the window '
             'itself.', ''),
            ('1:35', 'Folder with quadro_001_2000.png, quadro_002_2010.png, quadro_003_2020.png.',
             'In the folder, besides the GIF, the three frames as PNG, in exact colours.', ''),
            ('1:48', 'Vector and Mixed tabs (quick look); cumulative option.',
             'On the Vector and Mixed tabs you animate vector layers, including by a date field, and can overlay vectors '
             'on a raster background. The cumulative option keeps features from earlier periods: great to show growth.',
             'Cumulative = growth'),
            ('2:15', 'Tips on screen.',
             'Two tips. A GIF has at most two hundred and fifty-six colours; for slides, use the PNGs. And frames use the '
             'QGIS symbology: adjust colours and legend before exporting.', 'Adjust the symbology first'),
            ('2:35', 'Series closing: the seven modules in a mosaic; official website.',
             'With this video, you have met the seven modules of the Vista Saga Plugin. The full tutorial, the manual '
             'and the Vila Serena data are on the official website. Enjoy your work!', 'headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com'),
        ],
        'description': 'The Map sequencer of the Vista Saga Plugin creates an animated GIF (and PNG frames) from ordered '
                       'maps, with date, names and legend on each frame, using the QGIS symbology. Example: urban growth '
                       'in Vila Serena from 2000 to 2020. Data and tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Opening', '0:22 Adding frames', '0:55 Dimensions and composition', '1:15 Creating the GIF',
                     '1:48 Vector, Mixed and cumulative', '2:15 Tips', '2:35 Series closing'],
        'tags': 'QGIS, Vista SAGA, animated GIF, time series, map animation, urban growth, Vista Saga Plugin',
    },
]
