"""Texto del tutorial paso a paso (español). Las cifras vienen de numeros.json (executar_tutorial.py)."""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'docs', 'manual'))

import build_manual as bm  # noqa: E402

LANG = 'es'
USO_NAMES = ['Área urbana', 'Vegetación nativa', 'Agricultura', 'Pastizal', 'Agua']  # como en gerar_dados.NAMES

UI = {
    'doc_title': 'Tutorial paso a paso', 'subtitle': 'Vista Saga Plugin 1.6.0 para QGIS 4',
    'tagline': 'Vila Serena: del dato al diagnóstico, en los siete módulos', 'author': 'Esdras Andrade (IGDEMA/UFAL)',
    'date': 'Noviembre de 2026', 'toc': 'Índice', 'figure': 'Figura', 'footer': 'Vista Saga Plugin 1.6.0 - Tutorial',
    'page': 'Página',
}


def f(value, places=2):
    """Número con coma decimal y punto de millar."""
    text = f'{value:,.{places}f}'
    return text.replace(',', 'X').replace('.', ',').replace('X', '.')


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
    union, centro, beira = sig['uniao'], sig['2'], sig['1']   # códigos: 1 Ribera, 2 Centro
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
    h1('Antes de empezar')
    p('Este tutorial es un **ejercicio guiado**: hará, de principio a fin, un diagnóstico territorial completo de una '
      'ciudad ficticia, **Vila Serena**, con los siete módulos del Vista Saga Plugin. Cada paso dice qué pulsar, qué '
      'completar y **qué resultado debe obtener**. Si su cifra coincide con la del texto, lo hizo bien.',
      'El manual del usuario explica cada campo y cada concepto. Este tutorial hace el camino inverso: parte de una '
      'pregunta real y muestra cómo se encadenan los módulos para responderla.')
    h2('La pregunta de Vila Serena')
    p('Vila Serena es una ciudad de 400 hectáreas (2 km × 2 km), atravesada por un río de norte a sur, con una sierra '
      'al este. Entre 2000 y 2020, la mancha urbana se triplicó. El municipio quiere saber:')
    steps(['¿**De qué están hechos** hoy los barrios Centro y Ribera? (Firma espacial)',
           '¿**Qué cambió** entre 2000 y 2020, y a costa de qué? (Monitoreo)',
           '¿**Qué asociaciones** de uso del suelo y suelo existen, y dónde hay ciudad sobre suelo inundable? '
           '(Combinación de mapas)',
           '¿**Dónde puede crecer la ciudad** con menos conflicto? (Evaluación)',
           '¿**Qué escuela atiende cada parte** de la ciudad, considerando el tamaño de las escuelas y el río? (Voronoi)',
           '¿**Cómo mostrar** la expansión en una animación para la audiencia pública? (Secuenciador de mapas)'])
    p('El Conversor de formatos va primero, porque prepara uno de los mapas y porque es el puente con el Vista SAGA.')
    h2('Qué necesita')
    table(['Elemento', 'Detalle'], [
        ['QGIS', 'Versión 4.x (Windows o Linux), interfaz en español (el complemento sigue el idioma de QGIS).'],
        ['Vista Saga Plugin', 'Versión 1.6.0 instalada (Complementos > Administrar e instalar complementos > Instalar a '
                              'partir de ZIP).'],
        ['Datos del tutorial', '**dados_tutorial_vila_serena_es.zip** (datos sintéticos, de libre uso; nombres de clases '
                               'y barrios en español). Descomprímalo en una carpeta sin tildes en la ruta, por ejemplo '
                               'C:\\VilaSerena\\dados.'],
        ['Tiempo', 'Unas 2 horas en total; cada lección lleva de 10 a 20 minutos y puede hacerse por separado.'],
    ], [0.25, 0.75])
    h2('Qué hay en la carpeta de datos')
    p('Los nombres de archivo están en portugués (el complemento nació en Brasil): **uso_solo** = uso del suelo, '
      '**solos** = suelos, **declividade** = pendiente, **atrito** = fricción, **bairros** = barrios, **escolas** = '
      'escuelas, **MATRICULAS** = matrícula.')
    table(['Archivo', 'Contenido'], [
        ['uso_solo_2000.tif, uso_solo_2010.tif, uso_solo_2020.tif', 'Uso del suelo en tres fechas: 1 Área urbana, '
                                                                    '2 Vegetación nativa, 3 Agricultura, 4 Pastizal, 5 Agua.'],
        ['solos.tif', '1 Argisol, 2 Latosol, 3 Neosol flúvico (suelo de llanura inundable).'],
        ['declividade.tif', '1 Plano (0-3%), 2 Suave ondulado (3-8%), 3 Ondulado (8-20%), 4 Fuerte ondulado (> 20%).'],
        ['atrito.tif', 'Nota de fricción para Voronoi: área urbana 1, pastizal y agricultura 2, vegetación 4, agua 10.'],
        ['bairros.gpkg', '6 barrios (campos CODIGO y NOME).'],
        ['escolas.gpkg', '6 escuelas (campos NOME y MATRICULAS).'],
        ['aptidao_expansao.geosaga.json', 'Proyecto listo de la Evaluación (pesos y notas de la lección 5).'],
    ], [0.38, 0.62])
    p('Todos los rásteres tienen la **misma rejilla**: 200 × 200 celdas de 10 m, en el SRC **SIRGAS 2000 / UTM 25S '
      '(EPSG:31985)**. No es casualidad: varios módulos comparan mapas celda por celda y exigen la misma rejilla.')
    tip('Los datos son sintéticos',
        'Vila Serena no existe. Los mapas se generaron con un script de semilla fija (docs/tutorial/gerar_dados.py, en '
        'el repositorio), de modo que todos obtienen exactamente las mismas cifras. Los pesos y las notas de las '
        'lecciones son elecciones didácticas, no recomendaciones de método.', kind='warning')
    tip('Los informes quedan en portugués',
        'Sea cual sea el idioma de la interfaz, los informes CSV y TXT, los sufijos de archivo (_transicoes, '
        '_combinacoes, _centros…) y los nombres de las columnas se graban siempre en portugués. Este tutorial traduce '
        'las columnas que usa.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Preparación del proyecto')
    steps(['Abra QGIS 4 y cree un proyecto nuevo (**Proyecto > Nuevo**).',
           'Defina el SRC del proyecto: **Proyecto > Propiedades > SRC**, busque **31985** y elija '
           '**SIRGAS 2000 / UTM zone 25S**. Pulse **Aceptar**.',
           'Arrastre al panel de capas los archivos de la carpeta **dados**: los tres **uso_solo**, **solos**, '
           '**declividade**, **atrito**, **bairros.gpkg** y **escolas.gpkg**.',
           'Cambie el nombre de las capas para que coincidan con las capturas (clic derecho > Cambiar nombre de capa): '
           '**Uso del suelo 2000**, **Uso del suelo 2010**, **Uso del suelo 2020**, **Suelos**, **Pendiente**, '
           '**Fricción**, **Barrios**, **Escuelas**.',
           'Revise la leyenda de los rásteres categóricos: QGIS debe mostrar los **nombres de las clases** (Área urbana, '
           'Vegetación nativa…), porque están grabados en los GeoTIFF.',
           'Guarde el proyecto en la carpeta del tutorial (**Proyecto > Guardar como…**, por ejemplo vila_serena.qgz).',
           'Cree una carpeta **resultados** junto a la carpeta **dados**: todos los resultados de las lecciones van allí.'])
    image(fig('f01_dados'), 'Los mapas de Vila Serena: uso del suelo en 2000 y 2020, suelos y pendiente')
    image(fig('f02_bairros_escolas'), 'Barrios y escuelas (entre paréntesis, la matrícula)', 4.2)
    tip('Por qué el SRC importa tanto',
        'El complemento **nunca reproyecta sin avisar** y **nunca adivina el SRC** a partir de las coordenadas. Los mapas '
        'en SRC distintos se rechazan con un mensaje claro. En trabajos reales, estandarice el SRC (proyectado, en '
        'metros) antes de empezar: es el paso que más retrabajo evita.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lección 1 - Conversor de formatos: preparar e intercambiar datos')
    p('**Objetivo:** convertir los barrios (vector) en un ráster en la misma rejilla que los demás mapas, para usarlo '
      'como referencia en la Firma espacial; y exportar el uso del suelo al formato RS2, del Vista SAGA.')
    h2('1.1 Barrios: de vector a GeoTIFF')
    steps(['Abra **Vista Saga Plugin > Conversor de formatos**.',
           'En **Convertir**, elija **Vector → GeoTIFF (rasterización)**.',
           'En **Capa vectorial del proyecto**, elija **Barrios** y pulse **Seleccionar**.',
           'En **Campo a rasterizar**, elija **CODIGO**; en **Tamaño de píxel**, **10**.',
           'En **Archivo de salida**, indique resultados\\bairros.tif. Pulse **Ejecutar**.'])
    image(win('t01_conversor_vetor_geotiff'), 'Conversor de formatos: bairros.gpkg a GeoTIFF', 5.4)
    p(f"**Resultado esperado:** bairros.tif con **{conv['bairros_tif'][0]} × {conv['bairros_tif'][1]} celdas de "
      f"{f(conv['bairros_tif'][2], 0)} m**, exactamente la rejilla de los otros mapas, porque los barrios cubren toda el "
      'área de estudio. El ráster se carga con un estilo (.qml) que muestra solo las clases reales.')
    image(fig('f03_conversor'), 'El mismo mapa antes (vector) y después (ráster) de la conversión')
    h2('1.2 Poner nombre a las clases del ráster')
    p('El GeoTIFF generado guarda los **códigos** (1 a 6), y QGIS muestra "Classe 1", "Classe 2"… La Firma espacial usa '
      'los nombres del estilo de la capa en QGIS; así que ponga nombre a las clases ahora:')
    steps(['Haga doble clic en la capa ráster **bairros** y abra **Simbología**.',
           'En la columna **Etiqueta**, escriba: 1 Ribera, 2 Centro, 3 Alto de la Sierra, 4 Puerto, 5 Jardín Nuevo, '
           '6 Villa Verde.',
           'Pulse **Aceptar**. Para guardar los nombres junto al archivo: **Estilo > Guardar como predeterminado**.'])
    tip('Un consejo que solo cuenta el tutorial',
        'La tabla de correspondencia código → nombre está en el propio bairros.gpkg (campos CODIGO y NOME). Abra la tabla '
        'de atributos junto a la Simbología y copie los nombres; en mapas con decenas de clases, evita errores.')
    h2('1.3 Uso del suelo 2020: de GeoTIFF a RS2 (y de vuelta)')
    steps(['En el Conversor, elija **GeoTIFF → RS2 (formato Vista SAGA)**.',
           'En **Archivo de entrada**, indique dados\\uso_solo_2020.tif; en **Archivo de salida**, '
           'resultados\\uso_solo_2020.rs2. Pulse **Ejecutar**.',
           'Para comprobar, haga el camino de vuelta: **RS2 → GeoTIFF (ráster categórico)**, entrada uso_solo_2020.rs2, '
           'salida uso_solo_2020_de_volta.tif. Revise el SRC: el complemento lo lee del archivo .rs2.json grabado en el '
           'paso anterior (**EPSG:31985**).'])
    image(win('t02_conversor_geotiff_rs2'), 'Conversor de formatos: GeoTIFF a RS2', 5.4)
    p(f"**Resultado esperado:** un archivo RS2 de {f(conv['rs2_bytes'], 0)} bytes, más el archivo lateral "
      '**uso_solo_2020.rs2.rs2.json**, que guarda el SRC, la leyenda y la correspondencia de códigos. El GeoTIFF de '
      f"vuelta es **{'idéntico celda por celda' if conv['ida_e_volta_identico'] else 'distinto'}** al original, con los "
      'mismos nombres y colores.')
    tip('Atención', 'El RS2 **no guarda el SRC**. Al llevar un RS2 a otra carpeta o a otra persona, lleve también el '
        '.rs2.json; sin él, el complemento le pedirá que confirme el SRC.', kind='warning')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lección 2 - Firma espacial: ¿de qué están hechos Centro y Ribera?')
    p('**Objetivo:** medir, dentro de los barrios Centro y Ribera, cuánto ocupa cada clase de uso del suelo, de suelo y '
      'de pendiente.')
    steps(['Abra **Vista Saga Plugin > Firma espacial**, pestaña **Ráster**.',
           'En **1. Mapas**, añada **primero** el ráster **bairros** (será la referencia) y después **Uso del suelo '
           '2020**, **Suelos** y **Pendiente** (Capa en QGIS + **Añadir capa seleccionada**).',
           'En **2. Selección en la referencia**, marque **1 - Ribera** y **2 - Centro**.',
           'En **3. Opciones**, deje activado **Resultado por entidad** (un bloque por barrio, además de la unión).',
           'En **4. Resultado**, escriba el título "Centro y Ribera" y elija resultados\\assinatura.csv (el TXT se graba '
           'al lado). Pulse **Ejecutar**.'])
    image(win('t03_assinatura_configuracao'), 'Firma espacial: barrios como referencia, Centro y Ribera marcados', 5.2)
    image(win('t04_assinatura_resultados'), 'Firma espacial, pestaña Resultados: la tabla de la unión de la selección', 5.8)
    h2('Resultado esperado')
    u_uso = union['uso_solo_2020.tif']
    p(f"La unión de los dos barrios tiene **{f(union['bairros.tif']['1'][0] + union['bairros.tif']['2'][0])} ha** "
      f"(Ribera {f(union['bairros.tif']['1'][0])} ha + Centro {f(union['bairros.tif']['2'][0])} ha). Para el uso del "
      'suelo de 2020:')
    table(['Clase', 'Área firmada (ha)', '% área firmada', '% categoría'],
          [[USO_NAMES[int(k) - 1], f(v[0]), f(v[1]), f(v[2])] for k, v in u_uso.items() if k != '0'],
          [0.34, 0.22, 0.22, 0.22])
    h2('Cómo leerlo')
    bullets([f"**% área firmada** responde \"de qué está hecho el lugar\": el {f(u_uso['1'][1])} % de los dos barrios es "
             'urbano. Esta columna suma 100 % en cada mapa.',
             f"**% categoría** responde \"cuánto de la clase está aquí\": el {f(u_uso['1'][2])} % de toda el área urbana "
             f"de Vila Serena está en estos dos barrios, y el {f(u_uso['5'][2])} % del agua. Esta columna **no** suma 100 %.",
             f"Por barrio, el contraste es fuerte: el Centro es {f(centro['uso_solo_2020.tif']['1'][1])} % urbano; Ribera, "
             f"solo {f(beira['uso_solo_2020.tif']['1'][1])} %, con {f(beira['uso_solo_2020.tif']['4'][1])} % de pastizal.",
             f"En el Centro, el {f(centro['solos.tif']['3'][1])} % del área es neosol flúvico, suelo de llanura inundable: "
             'una pista que la Combinación y la Evaluación confirmarán.'])
    image(fig('f04_assinatura'), 'Uso del suelo 2020 en cada recorte: Centro, Ribera y la ciudad entera')
    tip('Consejos que solo cuenta el tutorial', items=[
        'La tabla de la propia referencia (barrios) muestra 100 % en las clases marcadas: es la comprobación del tamaño '
        'exacto del límite. Si no da 100 %, la selección no es la que usted cree.',
        'No sume los bloques por barrio para obtener la unión: use el bloque "Unión de la selección".',
        'En el CSV, filtre la columna RECORTE (UNIAO o FEICAO) y arme una tabla dinámica por MAPA y CLASSE (clase).'])
    p('**Ejercicio:** firme usted solo el barrio **Jardín Nuevo**, la frontera de expansión de la ciudad. ¿Qué % de área '
      'urbana tiene? ¿Y de vegetación nativa?')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lección 3 - Monitoreo: ¿qué cambió entre 2000 y 2020?')
    steps(['Abra **Vista Saga Plugin > Monitoreo**, pestaña **Ráster**.',
           'En **Mapa inicial**, elija **Uso del suelo 2000** y escriba **2000** en Período.',
           'En **Mapa final**, elija **Uso del suelo 2020** y escriba **2020** en Período.',
           'En **Título del estudio**, "Uso del suelo 2000 - 2020"; en **Guardar en**, '
           'resultados\\transicoes_2000_2020.tif.',
           'Pulse **Ejecutar**.'])
    image(win('t05_monitoria'), 'Monitoreo: los dos períodos y el resultado', 5.4)
    h2('Resultado esperado')
    p(f"De las {f(mon['validos'], 0)} celdas ({f(mon['area_valida_ha'], 0)} ha), el **{f(mon['pct_permanencia'])} % "
      f"permaneció** en la misma clase ({f(mon['permanencias'] * 0.01)} ha) y el **{f(mon['pct_mudanca'])} % cambió** "
      f"({f(mon['mudancas'] * 0.01)} ha). Los mayores cambios:")
    with open(os.path.join(work, 'resultados', 'transicoes_2000_2020_transicoes.csv'), encoding='utf-8-sig') as stream:
        changes = [r for r in csv.DictReader(stream, delimiter=';') if r['SITUACAO'] == 'Mudança']
    changes.sort(key=lambda r: -float(r['AREA_HA']))
    table(['Transición', 'Área (ha)', '% del área'],
          [[f"{r['DEIXOU_DE_SER']} → {r['TORNOU_SE']}", f(float(r['AREA_HA'])), f(float(r['PCT_VALIDOS']))]
           for r in changes[:5]], [0.5, 0.25, 0.25])
    image(fig('f05_monitoria'), 'El mapa de transiciones (permanencia en gris) y el área de cada clase en las dos fechas')
    h2('Cómo leerlo')
    bullets(['El área urbana pasó de **32,49 ha a 109,70 ha** (3,4 veces). Casi la mitad del crecimiento vino del '
             'pastizal (46,98 ha) y un cuarto, de la vegetación nativa (21,85 ha).',
             'La vegetación nativa cayó de **120,52 ha a 52,34 ha** (-56,6 %): perdió área frente a la ciudad, el '
             'pastizal y la agricultura.',
             'El agua (12,80 ha) no cambió: es un buen control de calidad. Si el agua "cambiara", desconfíe de los mapas.',
             'En la matriz (_matriz.csv), lea **por fila**: cada fila muestra adónde fue cada clase de 2000.'])
    tip('Un consejo que solo cuenta el tutorial',
        'Abra _transicoes.csv en Excel o LibreOffice y ordene por la columna AREA_HA: las cinco primeras filas de cambio '
        'cuentan la historia del período. SITUACAO distingue permanencia (Permanência) de cambio (Mudança); '
        'DEIXOU_DE_SER y TORNOU_SE son las clases "de" y "a".')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lección 4 - Combinación de mapas: ¿ciudad sobre suelo inundable?')
    steps(['Abra **Vista Saga Plugin > Combinación de mapas**, pestaña **Ráster**.',
           'Añada **Uso del suelo 2020** y después **Suelos** (el orden define el orden de las columnas en la tabla).',
           'En **Guardar en**, indique resultados\\uso2020_x_solos.tif y pulse **Ejecutar**.'])
    image(win('t06_combinacao'), 'Combinación de mapas: uso del suelo 2020 y suelos', 5.4)
    h2('Resultado esperado')
    p(f"**{n['combinacao']['combinacoes']} combinaciones** encontradas, en {f(n['combinacao']['area_ha'], 0)} ha. La "
      'mayor es **Pastizal | Argisol** (98,07 ha, 24,52 %). La que interesa al municipio es **Área urbana | Neosol '
      'flúvico: 17,89 ha (4,47 %)**: ciudad construida sobre suelo inundable.')
    image(fig('f06_combinacao'), 'Área de cada combinación de uso del suelo y suelo')
    tip('Un consejo que solo cuenta el tutorial',
        'En QGIS, use la herramienta **Identificar objetos** sobre el mapa combinado: el valor de la celda corresponde al '
        'ID_COMB de _combinacoes.csv. Para resaltar solo las áreas urbanas en suelo inundable, abra la Simbología y '
        'desmarque las demás combinaciones.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lección 5 - Evaluación: ¿dónde puede crecer la ciudad?')
    p('**Objetivo:** producir un mapa de aptitud para la expansión urbana como media ponderada de tres criterios. Los '
      'pesos y las notas de abajo son **didácticos**: en un estudio real deben justificarse (literatura, consulta a '
      'especialistas, legislación).')
    table(['Criterio (peso)', 'Notas (0 a 10)'], [
        ['Pendiente (40 %)', 'Plano 10; Suave ondulado 8; Ondulado 4; Fuerte ondulado 1'],
        ['Suelos (25 %)', 'Argisol 7; Latosol 9; Neosol flúvico 2 (llanura inundable)'],
        ['Uso del suelo 2020 (35 %)', 'Área urbana 8; Vegetación nativa 1; Agricultura 6; Pastizal 9; Agua: No evaluar'],
    ], [0.3, 0.7])
    h2('Armado paso a paso')
    steps(['Abra **Vista Saga Plugin > Evaluación**, pestaña **Ráster**. Escala de las notas: **0 a 10**.',
           'Añada **Pendiente**, **Suelos** y **Uso del suelo 2020**. Los pesos entran en blanco, a propósito.',
           'Escriba los pesos 40, 25 y 35 (la tecla **Tab** salta de peso en peso). La línea bajo la tabla debe decir '
           '"Pesos: 100,00% - distribución válida".',
           'Seleccione cada mapa y escriba las notas de las clases. En **Agua**, marque **No evaluar**.',
           'Pulse **Validar**: no puede quedar ninguna clase con nota "—".',
           'En **Guardar en**, indique resultados\\aptidao_expansao.tif, mantenga marcados los dos informes y pulse '
           '**Ejecutar**.'])
    tip('Atajo', 'En lugar de escribirlo todo, pulse **Abrir proyecto…** y elija dados\\aptidao_expansao.geosaga.json: '
        'los tres mapas, los pesos y las notas se cargan de una vez. Así se reutiliza una evaluación.')
    image(win('t07_avaliacao'), 'Evaluación: pesos, notas y Agua en "No evaluar"', 5.8)
    h2('Resultado esperado')
    per = ev['area_por_nota_ha']
    p(f"**{f(ev['pixels_validos'], 0)} celdas evaluadas** ({f(ev['pixels_validos'] * 0.01, 1)} ha) y "
      f"{f(ev['pixels_sem_avaliacao'], 0)} sin evaluar (el agua, {f(ev['pixels_sem_avaliacao'] * 0.01, 1)} ha). Nota "
      f"mínima **{f(ev['minimo'], 1)}**, máxima **{f(ev['maximo'], 1)}**, media **{f(ev['media'])}**. Área por nota "
      'final (como en el informe):')
    table(['Nota final'] + sorted(per, key=int), [['Área (ha)'] + [f(per[k]) for k in sorted(per, key=int)]],
          [0.2] + [0.8 / len(per)] * len(per))
    image(fig('f07_avaliacao'), 'Mapa de aptitud para la expansión urbana y área por nota final')
    h2('Cómo leerlo')
    bullets([f"Las notas **8 y 9** ({f(per.get('8', 0) + per.get('9', 0))} ha) son las áreas más aptas: casi todas en "
             'relieve plano o suave ondulado, sobre argisol, ocupadas por pastizal o ya urbanas.',
             f"La nota **3** ({f(per.get('3', 0))} ha) reúne lo peor de todo: vegetación nativa en pendiente fuerte.",
             'Un resultado que enseña: el **latosol**, pese a su nota 9, tiene la menor nota media (5,51), porque está en '
             'la sierra, en pendiente alta. La pendiente (40 %) pesa más que el suelo (25 %) y domina. La llanura '
             'inundable (neosol flúvico, nota 2) queda con media 6,18: es plana, y el suelo solo la penaliza en parte. '
             'Si el municipio quiere excluir del todo la llanura inundable, no basta una nota baja: marque la clase como '
             '**No evaluar**.'])
    tip('Consejos que solo cuenta el tutorial', items=[
        'La nota "—" bloquea la ejecución: el complemento **nunca supone nota 0**. Es a propósito, para que ninguna clase '
        'entre en el cálculo sin su decisión.',
        'Cada ejecución graba *_pesos_notas.geosaga.json (pesos y notas) junto al mapa: es el registro exacto de lo que '
        'usó. Guárdelo con el informe del estudio.',
        'Pruebe la sensibilidad: cambie los pesos a 50/20/30 y compare los mapas. Si el mapa cambia mucho, la elección de '
        'los pesos es crítica y necesita una justificación sólida.'])
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lección 6 - Análisis de Voronoi: ¿qué escuela atiende cada parte de la ciudad?')
    p('Tres versiones de la misma pregunta: por la distancia pura (**Simple**), por el tamaño de la escuela (**Con '
      'masa**, matrícula) y por la dificultad de desplazamiento (**Con fricción**: cruzar el río sale caro).')
    h2('6.1 Con masa')
    steps(['Abra **Vista Saga Plugin > Análisis de Voronoi**, pestaña **Ráster**.',
           'En **Modo**, elija **Con masa**.',
           'En **Puntos generadores**, **Escuelas**; en **Identificador del punto**, **NOME**; en **Campo de masa**, '
           '**MATRICULAS**.',
           'En **Extensión del análisis**, elija **Rejilla del ráster de referencia** y, en **Ráster de referencia**, '
           '**Fricción**: así el resultado cae exactamente en la rejilla de los otros mapas.',
           'En **Guardar en**, resultados\\voronoi_com_massa.tif. Pulse **Ejecutar**.'])
    image(win('t09_voronoi_massa'), 'Análisis de Voronoi, Con masa: matrícula como masa, rejilla del ráster de fricción', 5.4)
    h2('6.2 Con fricción')
    steps(['Cambie el **Modo** a **Con fricción**.',
           'En **Tipo de superficie**, **Ráster**; en **Superficie de fricción**, **Fricción**.',
           'Mantenga la rejilla del ráster de referencia; en **Guardar en**, resultados\\voronoi_com_atrito.tif. Pulse '
           '**Ejecutar**.',
           'Para comparar, ejecute también el modo **Simple** (resultados\\voronoi_simples.tif).'])
    image(win('t08_voronoi_atrito'), 'Análisis de Voronoi, Con fricción: superficie de fricción ráster', 5.4)
    h2('Resultado esperado')
    names = list(vor['simples'])
    table(['Escuela (matrícula)', 'Simple (ha)', 'Con masa (ha)', 'Con fricción (ha)'],
          [[f"{k} ({f(vor['simples'][k]['MASSA'], 0)})", f(vor['simples'][k]['AREA_HA']),
            f(vor['com_massa'][k]['AREA_HA']), f(vor['com_atrito'][k]['AREA_HA'])] for k in names],
          [0.4, 0.2, 0.2, 0.2])
    image(fig('f08_voronoi'), 'Las áreas de influencia en los tres modos (en Con masa, el tamaño del punto es '
          'proporcional a la matrícula)')
    h2('Cómo leerlo')
    bullets([f"**Con masa**, la E. E. Darcy Ribeiro (1.200 alumnos) pasa de {f(vor['simples']['E. E. Darcy Ribeiro']['AREA_HA'])} "
             f"a **{f(vor['com_massa']['E. E. Darcy Ribeiro']['AREA_HA'])} ha**; la E. M. Cora Coralina (250) baja de "
             f"{f(vor['simples']['E. M. Cora Coralina']['AREA_HA'])} a {f(vor['com_massa']['E. M. Cora Coralina']['AREA_HA'])} ha. "
             'El criterio es M/d²: una escuela con 4 veces más masa alcanza el doble de distancia, no el cuádruple.',
             f"**Con fricción**, la E. M. Monteiro Lobato, junto al río, pierde área ({f(vor['simples']['E. M. Monteiro Lobato']['AREA_HA'])} → "
             f"{f(vor['com_atrito']['E. M. Monteiro Lobato']['AREA_HA'])} ha): cruzar el agua cuesta 10 veces más que andar "
             'por la ciudad. La E. E. Cecília Meireles gana '
             f"({f(vor['simples']['E. E. Cecília Meireles']['AREA_HA'])} → {f(vor['com_atrito']['E. E. Cecília Meireles']['AREA_HA'])} ha).",
             'El costo se mide en la **recta** entre la escuela y cada lugar, como en el Vista SAGA: no es el camino de '
             'menor costo (r.cost de GRASS). La recta "paga" el río; no lo rodea.'])
    tip('Consejos que solo cuenta el tutorial', items=[
        'La nota de fricción 0 se rechaza; para "casi sin fricción", use 0,1.',
        'En caso de empate exacto, gana el primer punto de la capa.',
        '_centros.csv trae el área (AREA_HA) y el % (PCT_AREA) de cada escuela: péguelo junto a la tabla de matrícula y '
        'calcule alumnos por hectárea atendida.'])
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lección 7 - Secuenciador de mapas: la expansión en animación')
    steps(['Abra **Vista Saga Plugin > Secuenciador de mapas**, pestaña **Ráster**.',
           'Añada, en este orden, **Uso del suelo 2000**, **Uso del suelo 2010** y **Uso del suelo 2020** (el complemento '
           'lee el año en el nombre; use **Ordenar por fecha** si hace falta).',
           'En **2. Dimensiones y composición**: ancho y altura **600**, duración **1000 ms / cuadro**, **Mostrar la '
           'fecha o el período en el mapa** activado.',
           'En **3. Salidas y vista previa**, indique resultados\\vila_serena_2000_2020.gif y marque **Exportar también '
           'los cuadros PNG individuales**. Pulse **Ejecutar**.'])
    image(win('t10_sequenciador'), 'Secuenciador de mapas: tres cuadros, 600 × 600 píxeles', 5.2)
    p('**Resultado esperado:** un GIF de 3 cuadros (2000, 2010, 2020) con el año en la esquina, y una carpeta con los '
      'tres PNG (quadro_001_2000.png…). Los cuadros usan la simbología definida en QGIS.')
    image(fig('f09_sequenciador'), 'Los tres cuadros generados por el Secuenciador')
    tip('Un consejo que solo cuenta el tutorial',
        'El GIF tiene como máximo 256 colores. Para una presentación de diapositivas, use los PNG: los colores quedan '
        'exactos y usted controla el tiempo de cada cuadro en el propio programa de presentación.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Cierre: el diagnóstico de Vila Serena')
    p('Juntando las lecciones, la respuesta al municipio cabe en cinco frases:')
    steps([f"El Centro ya es {f(centro['uso_solo_2020.tif']['1'][1], 1)} % urbano, y un tercio de él está sobre suelo "
           'inundable (Firma espacial).',
           'En 20 años la ciudad se triplicó, sobre todo sobre pastizal, y la vegetación nativa perdió más de la mitad de '
           'su área (Monitoreo).',
           'Hay 17,89 ha de ciudad sobre neosol flúvico, prioridad para drenaje y control de crecidas (Combinación de '
           'mapas).',
           f"Las áreas más aptas para crecer (notas 8 y 9, {f(per.get('8', 0) + per.get('9', 0))} ha) están en relieve "
           'plano o suave, casi todas fuera de la llanura inundable (Evaluación).',
           'El río redibuja la atención escolar: tener en cuenta el cruce cambia el área atendida de la mayoría de las '
           'escuelas (Voronoi).'])
    h2('Lista de comprobación')
    table(['Lección', 'Archivo esperado en resultados', 'Cifra clave'], [
        ['1', 'bairros.tif, uso_solo_2020.rs2 (+ .rs2.json)', '200 × 200 celdas; ida y vuelta idéntica'],
        ['2', 'assinatura.csv, assinatura.txt', f"Área urbana en la unión: {f(u_uso['1'][0])} ha ({f(u_uso['1'][1])} %)"],
        ['3', 'transicoes_2000_2020.tif + _transicoes.csv, _matriz.csv, _resumo.txt', f"Cambio: {f(mon['pct_mudanca'])} %"],
        ['4', 'uso2020_x_solos.tif + _combinacoes.csv, _resumo.txt', f"{n['combinacao']['combinacoes']} combinaciones"],
        ['5', 'aptidao_expansao.tif + informes CSV y TXT + _pesos_notas.geosaga.json', f"Media {f(ev['media'])}"],
        ['6', 'voronoi_*.tif + _centros.csv, _resumo.txt', f"Darcy Ribeiro Con masa: {f(vor['com_massa']['E. E. Darcy Ribeiro']['AREA_HA'])} ha"],
        ['7', 'vila_serena_2000_2020.gif + carpeta de PNG', '3 cuadros'],
    ], [0.1, 0.5, 0.4])
    h2('Si su cifra no coincidió')
    bullets(['Compruebe que usó los mapas correctos (2000 y 2020, no 2010) y el orden correcto en la lista.',
             'Compruebe el SRC del proyecto y de las capas (EPSG:31985).',
             'En la Evaluación, compare pesos y notas con el proyecto listo (aptidao_expansao.geosaga.json).',
             'En Voronoi, revise la extensión: con "Extensión visible en QGIS", el área total cambia con el zoom y las '
             'áreas no coinciden; use la rejilla del ráster de referencia.'])
    h2('Próximos pasos')
    bullets(['Repita las lecciones con sus datos: el recorrido es el mismo.',
             'Consulte el **Manual del Usuario** para todos los campos, opciones avanzadas y consejos de cada módulo.',
             'Vea los videos de cada módulo en el canal del proyecto (enlaces en el sitio oficial).'])
    return {'lang': LANG, 'ui': UI, 'blocks': B}
