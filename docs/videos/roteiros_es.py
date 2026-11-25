"""Guiones de video (YouTube), español. Un video por módulo, con los datos de Vila Serena."""

LANG = 'es'
UI = {
    'doc_title': 'Guiones de video', 'subtitle': 'Vista Saga Plugin 1.6.0 para QGIS 4',
    'tagline': 'Serie de videos instructivos - un video por módulo - español',
    'author': 'Esdras Andrade (IGDEMA/UFAL)', 'date': 'Noviembre de 2026', 'toc': 'Índice', 'figure': 'Figura',
    'footer': 'Vista Saga Plugin 1.6.0 - Guiones de video (es)', 'page': 'Página',
    'sheet': 'Ficha del video', 'scenes': 'Guion', 'youtube': 'Publicación en YouTube',
    'cols': ['Tiempo', 'En pantalla', 'Narración (locución)', 'Texto en pantalla'],
    'sheet_cols': ['Elemento', 'Contenido'],
    'fields': ['Título en YouTube', 'Duración estimada', 'Objetivo', 'Datos', 'Requisito previo', 'Miniatura (texto)'],
    'description': 'Descripción', 'chapters': 'Capítulos', 'tags': 'Etiquetas',
}

GUIDE = {
    'title': 'Cómo usar estos guiones',
    'paras': [
        'Cada módulo del Vista Saga Plugin tiene un video corto (4 a 6 minutos), grabado sobre los datos de la ciudad '
        'ficticia de **Vila Serena**, los mismos del tutorial paso a paso. Las cifras de la narración son las que el '
        'complemento realmente produce con esos datos: quien repita los pasos obtiene el mismo resultado.',
        'Cada guion tiene una **ficha** (título, duración, objetivo, texto de la miniatura), la **tabla de escenas** '
        '(tiempo, lo que aparece en pantalla, la narración y el texto superpuesto) y el material de **publicación** '
        '(descripción, capítulos y etiquetas de YouTube).',
    ],
    'production_title': 'Estándar de producción (para toda la serie)',
    'production': [
        '**Pantalla:** 1920 × 1080, QGIS 4 en **español** (el complemento sigue el idioma de QGIS), tema claro, fuente '
        'de la interfaz en tamaño normal. Cierre los paneles que no se usarán.',
        '**Datos:** paquete **dados_tutorial_vila_serena_es.zip** (nombres de clases y barrios en español), '
        'descomprimido en C:\\VilaSerena\\dados, con el proyecto abierto, SRC EPSG:31985 y las capas cargadas antes de '
        'grabar. Los nombres de archivo quedan en portugués (uso_solo = uso del suelo, solos = suelos, declividade = '
        'pendiente, atrito = fricción, bairros = barrios, escolas = escuelas); diga el significado la primera vez que '
        'aparezca cada uno.',
        '**Cursor:** resaltado de clic activado; mueva el ratón despacio y deténgase sobre el elemento mientras la '
        'narración lo nombra.',
        '**Zoom:** use zoom de edición (1,5× a 2×) cada vez que la narración cite un campo o una cifra.',
        '**Locución:** ritmo tranquilo, unas 150 palabras por minuto; grabe la narración aparte y sincronice en la '
        'edición.',
        '**Apertura estándar (5 s):** logotipo del Vista Saga Plugin + nombre del módulo. **Cierre estándar (10 s):** '
        '"Datos y tutorial en el sitio oficial: headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com" + pantallas finales al próximo video.',
        '**Subtítulos:** genérelos a partir de la columna Narración (es el texto final de la locución).',
        '**Texto en pantalla:** corto (hasta 8 palabras), en el tercio inferior, de 3 a 5 segundos.',
    ],
    'series_title': 'Orden de la serie',
    'series': ['1. Conversor de formatos', '2. Firma espacial', '3. Monitoreo', '4. Combinación de mapas',
               '5. Evaluación', '6. Análisis de Voronoi', '7. Secuenciador de mapas'],
    'series_note': 'El orden sigue el tutorial: el Conversor prepara el ráster de barrios que usa la Firma espacial. '
                   'Aun así, cada video se sostiene solo: cuando necesita un archivo de otro video, la narración lo avisa.',
}

VIDEOS = [
    {
        'title': '1. Conversor de formatos',
        'sheet': ['Conversor de formatos: vector, GeoTIFF y RS2 del Vista SAGA | Vista Saga Plugin para QGIS',
                  '5 min',
                  'Convertir un vector en GeoTIFF en la rejilla del estudio, nombrar las clases e intercambiar datos con '
                  'el formato RS2 del Vista SAGA.',
                  'bairros.gpkg (barrios), uso_solo_2020.tif (uso del suelo 2020)',
                  'Complemento instalado; proyecto de Vila Serena abierto.',
                  'DEL VECTOR AL RS2 EN UN CLIC'],
        'scenes': [
            ('0:00', 'Apertura estándar.', '', 'Conversor de formatos'),
            ('0:05', 'Proyecto de Vila Serena en QGIS; resaltar la capa de barrios (vector) y el uso del suelo 2020.',
             'En este video aprenderá a usar el Conversor de formatos del Vista Saga Plugin. Haremos dos cosas: '
             'convertir los barrios de Vila Serena, que son polígonos, en un ráster en la misma rejilla que los demás '
             'mapas; y llevar el uso del suelo al formato RS2, del Vista SAGA, y traerlo de vuelta.', ''),
            ('0:25', 'Menú Vista Saga Plugin abierto; clic en Conversor de formatos.',
             'Abra el menú del Vista Saga Plugin y elija Conversor de formatos.', ''),
            ('0:32', 'Lista Convertir abierta con las seis operaciones.',
             'Hay seis conversiones: de RS2 a GeoTIFF, de GeoTIFF a RS2, de RS2 o GeoTIFF a vector, y de vector a GeoTIFF '
             'o a RS2. La ventana muestra solo los campos de la operación elegida.', 'Seis conversiones'),
            ('0:48', 'Elegir Vector → GeoTIFF; Capa vectorial del proyecto: bairros; clic en Seleccionar.',
             'Elija Vector a GeoTIFF. En Capa vectorial del proyecto, elija la capa de barrios y haga clic en '
             'Seleccionar.', ''),
            ('1:00', 'Campo a rasterizar: CODIGO; Tamaño de píxel: 10 (zoom en los dos campos).',
             'En Campo a rasterizar, elija CODIGO, el código del barrio: es el valor que recibirá cada celda. Tamaño de '
             'píxel: diez. Como el SRC es UTM, la unidad es el metro.', 'Píxel de 10 m'),
            ('1:15', 'Archivo de salida: resultados\\bairros.tif; clic en Ejecutar; capa cargada.',
             'Indique el archivo de salida y haga clic en Ejecutar. El ráster se carga con un estilo que muestra solo '
             'las clases que existen.', ''),
            ('1:30', 'Propiedades de la capa > Información: 200 × 200, píxel 10.',
             'Fíjese: doscientas por doscientas celdas de diez metros. Exactamente la rejilla de los otros mapas, porque '
             'los barrios cubren toda el área de estudio. Esto será esencial en la Firma espacial.', '200 × 200 celdas'),
            ('1:48', 'Simbología del ráster: etiquetas "Classe 1…6"; cambiarlas por los nombres de los barrios; Aceptar.',
             'El GeoTIFF guarda los códigos, y QGIS muestra "Classe 1", "Classe 2". Ponga nombre a las clases en la '
             'Simbología: uno, Ribera; dos, Centro; y así sucesivamente. La Firma espacial usa esos nombres.',
             'Nombre las clases'),
            ('2:15', 'Tabla de atributos de los barrios junto a la Simbología (CODIGO y NOME).',
             'Consejo: la tabla de atributos del vector tiene la correspondencia entre código y nombre. Déjela abierta '
             'al lado y copie los nombres sin errores.', 'Consejo'),
            ('2:30', 'Volver al Conversor; elegir GeoTIFF → RS2; entrada uso_solo_2020.tif; salida uso_solo_2020.rs2.',
             'Ahora, el puente con el Vista SAGA. Elija GeoTIFF a RS2, indique el uso del suelo 2020 y un archivo de '
             'salida con extensión punto rs2.', 'GeoTIFF → RS2'),
            ('2:48', 'Clic en Ejecutar; explorador de archivos mostrando .rs2 y .rs2.json.',
             'Ejecute. Además del archivo RS2, el complemento graba un archivo lateral, punto rs2 punto json. El RS2 no '
             'guarda el sistema de coordenadas; ese archivo guarda el SRC, la leyenda y la correspondencia de códigos.',
             '.rs2.json = SRC'),
            ('3:10', 'Clic en Propiedades del RS2…: encabezado, leyenda y rejilla.',
             'El botón Propiedades del RS2 muestra el encabezado, la leyenda y la rejilla antes de cualquier conversión. '
             'Úselo para revisar archivos recibidos del Vista SAGA.', ''),
            ('3:25', 'Elegir RS2 → GeoTIFF; entrada uso_solo_2020.rs2; SRC completado (EPSG:31985); Ejecutar.',
             'Para comprobar, haga el camino de vuelta: RS2 a GeoTIFF. El SRC aparece completado, leído del archivo '
             'lateral. Ejecute.', ''),
            ('3:42', 'Lado a lado: uso_solo_2020.tif y uso_solo_2020_de_volta.tif, con la misma leyenda.',
             'El GeoTIFF que volvió es idéntico al original, celda por celda, con los mismos nombres y colores de las '
             'clases.', 'Ida y vuelta idéntica'),
            ('3:58', 'Lista de consejos en pantalla.',
             'Tres cuidados. Lleve siempre el punto rs2 punto json junto con el RS2. Al copiar un GeoTIFF de clases, '
             'lleve también el punto aux punto xml y el punto qml, que guardan nombres y estilo. Y para convertir muchos '
             'archivos a la vez, marque Procesar varios archivos.', 'Lleve .rs2.json, .aux.xml y .qml'),
            ('4:30', 'Cierre estándar; pantalla final al video de la Firma espacial.',
             'En el próximo video usaremos este ráster de barrios en la Firma espacial, para descubrir de qué está hecho '
             'cada barrio. Hasta pronto.', 'Próximo: Firma espacial'),
        ],
        'description': 'Aprenda a usar el Conversor de formatos del Vista Saga Plugin para QGIS 4: rasterizar un vector '
                       'en la rejilla de su estudio, nombrar las clases e intercambiar datos con el formato RS2 del Vista '
                       'SAGA, con ida y vuelta sin pérdidas. Datos del ejemplo (la ciudad ficticia de Vila Serena) y '
                       'tutorial completo en el sitio oficial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Apertura', '0:25 Las seis conversiones', '0:48 Vector a GeoTIFF', '1:48 Nombrar las clases',
                     '2:30 GeoTIFF a RS2', '3:25 RS2 de vuelta a GeoTIFF', '3:58 Cuidados', '4:30 Próximo video'],
        'tags': 'QGIS, QGIS 4, Vista SAGA, SAGA UFRJ, RS2, GeoTIFF, rasterización, conversión de formatos, SIG, Vista Saga Plugin',
    },
    {
        'title': '2. Firma espacial',
        'sheet': ['Firma espacial: ¿de qué está hecha esta área? | Vista Saga Plugin para QGIS',
                  '6 min',
                  'Medir la composición de un área (uso del suelo, suelos, pendiente) dentro de barrios seleccionados y '
                  'leer los dos porcentajes del Vista SAGA.',
                  'bairros.tif (del video 1, con las clases nombradas), uso_solo_2020.tif, solos.tif, declividade.tif',
                  'Ráster de barrios creado en el video del Conversor.',
                  '¿DE QUÉ ESTÁ HECHO ESTE BARRIO?'],
        'scenes': [
            ('0:00', 'Apertura estándar.', '', 'Firma espacial'),
            ('0:05', 'Mapa de Vila Serena con Centro y Ribera resaltados.',
             '¿De qué están hechos los barrios Centro y Ribera? ¿Cuánto es ciudad, vegetación, pastizal? ¿Qué suelos y '
             'qué pendientes tienen? Eso responde la Firma espacial, para varios mapas a la vez.', ''),
            ('0:22', 'Abrir Vista Saga Plugin > Firma espacial; pestaña Ráster.',
             'Abra la Firma espacial y quédese en la pestaña Ráster. Ráster y vector no se mezclan: cada pestaña trabaja '
             'con un tipo.', ''),
            ('0:32', 'Añadir primero el ráster de barrios, luego uso del suelo 2020, suelos y pendiente.',
             'En Mapas, añada primero el ráster de barrios. La regla es simple: el primero de la lista es la referencia, '
             'como el mapa de arriba en el Vista SAGA. Después, añada uso del suelo, suelos y pendiente.',
             'El 1.er mapa es la referencia'),
            ('0:55', 'Botones Mover hacia arriba y Mover hacia abajo (zoom).',
             'Si se equivoca de orden, use Mover hacia arriba. Todos los mapas deben tener el mismo SRC y la misma '
             'rejilla; si no, el complemento avisa y nunca reproyecta nada por su cuenta.', 'Mismo SRC, misma rejilla'),
            ('1:12', 'En Selección en la referencia, marcar 1 - Ribera y 2 - Centro.',
             'En Selección en la referencia aparecen las clases del primer mapa, con los nombres que dio en la '
             'Simbología. Marque Ribera y Centro. Esa selección es el límite del análisis.', ''),
            ('1:28', 'Opciones: Resultado por entidad activado; título y Guardar en assinatura.csv; Ejecutar.',
             'Deje activado Resultado por entidad: además de la unión de los dos barrios, sale un bloque para cada uno. '
             'Escriba un título, elija dónde guardar el CSV, y el TXT va con él. Ejecute.', ''),
            ('1:45', 'Pestaña Resultados con la tabla de la unión; zoom en las columnas.',
             'La pestaña Resultados muestra la tabla. La unión tiene ciento treinta hectáreas: setenta de Ribera y '
             'sesenta del Centro. La tabla del propio mapa de referencia muestra cien por ciento en las clases marcadas: '
             'es la comprobación del tamaño del límite.', '130 ha'),
            ('2:10', 'Resaltar las filas del uso del suelo; columna % área firmada.',
             'Ahora, el uso del suelo. La columna porcentaje del área firmada dice de qué está hecho el lugar: cuarenta '
             'y cinco coma cinco por ciento de los dos barrios es área urbana; veinticinco, pastizal. Esta columna suma '
             'cien.', '% área firmada = composición'),
            ('2:35', 'Resaltar la columna % categoría.',
             'La columna porcentaje de la categoría dice cuánto de la clase está allí: el cincuenta y cuatro por ciento '
             'de toda el área urbana de Vila Serena está en estos dos barrios, y la mitad del agua. Esta columna no suma '
             'cien, y no debe sumarse.', '% categoría = concentración'),
            ('3:00', 'Lista Recorte: cambiar de Unión de la selección a Centro y luego a Ribera.',
             'En la lista Recorte, vea cada barrio. El Centro es setenta por ciento urbano. Ribera, solo veinticuatro, '
             'con cuarenta y seis por ciento de pastizal. Y un tercio del Centro está sobre neosol flúvico, un suelo de '
             'llanura inundable.', 'Centro: 71 % urbano'),
            ('3:35', 'Abrir assinatura.txt y assinatura.csv en el editor y en la hoja de cálculo.',
             'El TXT es el informe completo, en el modelo del Vista SAGA. El CSV se abre directamente en la hoja de '
             'cálculo: filtre la columna RECORTE y arme una tabla dinámica por mapa y clase.', 'TXT + CSV'),
            ('4:00', 'Lista de consejos en pantalla.',
             'Dos consejos. No sume los bloques por barrio para obtener la unión: use el bloque de la unión. Y si las '
             'clases aparecen como Classe 1, Classe 2, el archivo no tiene nombres: póngalos en la Simbología y ejecute '
             'de nuevo.', 'Use el bloque de la unión'),
            ('4:25', 'Pestaña Vectorial (vista rápida): Seleccionar en el mapa y contador de entidades.',
             'Con datos vectoriales la lógica es la misma, en la pestaña Vectorial: usted selecciona las entidades en el '
             'mapa de QGIS con el botón Seleccionar en el mapa, y el complemento hace la intersección exacta.', ''),
            ('4:45', 'Cierre estándar; pantalla final al video del Monitoreo.',
             'En el próximo video, el Monitoreo: qué cambió en Vila Serena entre 2000 y 2020.', 'Próximo: Monitoreo'),
        ],
        'description': 'La Firma espacial del Vista Saga Plugin mide de qué está hecha un área: seleccione barrios (o '
                       'cualquier límite) en un mapa de referencia y obtenga, para varios mapas a la vez, el área y los dos '
                       'porcentajes del Vista SAGA (% del área firmada y % de la categoría). Ejemplo con la ciudad '
                       'ficticia de Vila Serena. Datos y tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Apertura', '0:22 La referencia es el primer mapa', '1:12 Selección en la referencia',
                     '1:45 Leer la tabla', '2:10 % área firmada', '2:35 % categoría', '3:00 Por barrio',
                     '3:35 TXT y CSV', '4:25 Pestaña Vectorial', '4:45 Próximo video'],
        'tags': 'QGIS, Vista SAGA, firma ambiental, uso del suelo, estadística zonal, SIG, planificación urbana, Vista Saga Plugin',
    },
    {
        'title': '3. Monitoreo',
        'sheet': ['Monitoreo: ¿qué cambió entre dos fechas? | Vista Saga Plugin para QGIS',
                  '5 min',
                  'Comparar el uso del suelo de 2000 y 2020, generar el mapa de transiciones y leer la matriz de '
                  'transición.',
                  'uso_solo_2000.tif, uso_solo_2020.tif',
                  'Proyecto de Vila Serena abierto.',
                  'LA CIUDAD SE TRIPLICÓ. ¿A COSTA DE QUÉ?'],
        'scenes': [
            ('0:00', 'Apertura estándar.', '', 'Monitoreo'),
            ('0:05', 'Uso del suelo 2000 y 2020 lado a lado.',
             'En veinte años, la mancha urbana de Vila Serena creció mucho. Pero ¿sobre qué creció? El Monitoreo '
             'compara dos mapas y muestra, lugar por lugar, qué permaneció y qué cambió.', ''),
            ('0:20', 'Abrir Monitoreo, pestaña Ráster; Mapa inicial: uso del suelo 2000; Período 2000.',
             'Abra el Monitoreo. En Mapa inicial, elija el uso del suelo 2000 y escriba el período: 2000.', ''),
            ('0:35', 'Mapa final: uso del suelo 2020; Período 2020; título; Guardar en; Ejecutar.',
             'En Mapa final, el de 2020, período 2020. Escriba un título, indique dónde guardar y ejecute. Los dos mapas '
             'deben estar en la misma rejilla.', ''),
            ('0:55', 'Mapa de transiciones cargado: permanencias en gris, cambios en colores.',
             'El mapa de transiciones llega listo: permanencias en gris, cambios en colores, con la leyenda en palabras. '
             'El anillo de color alrededor del centro es la expansión urbana.', ''),
            ('1:15', 'Pestaña Resultados: resumen con permanencia y cambio.',
             'En el resumen, el sesenta y nueve por ciento del área permaneció y el treinta y uno por ciento cambió: '
             'ciento veintitrés hectáreas.', 'Cambió el 31 %'),
            ('1:32', 'Tabla de transiciones ordenada por área; resaltar los cinco mayores cambios.',
             'Ordene las transiciones por área. El mayor cambio es pastizal que se volvió ciudad: cuarenta y siete '
             'hectáreas. Luego, vegetación nativa que pasó a pastizal, treinta hectáreas, y vegetación que pasó a ciudad, '
             'veintidós.', 'Pastizal → Área urbana: 47 ha'),
            ('2:05', 'Abrir _matriz.csv en la hoja de cálculo; resaltar la diagonal y una fila.',
             'La matriz de transición tiene la clase de 2000 en las filas y la de 2020 en las columnas. La diagonal es '
             'lo que permaneció. Léala por fila: la fila de la vegetación nativa muestra adónde fue.',
             'Lea la matriz por fila'),
            ('2:30', 'Resaltar: urbana 32,5 → 109,7 ha; vegetación 120,5 → 52,3 ha.',
             'Resultado: el área urbana pasó de treinta y dos a casi ciento diez hectáreas, tres veces y media. La '
             'vegetación nativa perdió más de la mitad de su área.', 'Vegetación: -57 %'),
            ('2:55', 'Resaltar el agua (12,8 ha en las dos fechas).',
             'Fíjese en el agua: doce coma ocho hectáreas en las dos fechas. Es un control de calidad. Si el río '
             '"cambiara", yo desconfiaría de los mapas, no de la realidad.', 'Agua = control'),
            ('3:15', 'Opciones avanzadas: leyenda (palabras o códigos; tabla de nombres).',
             'En Opciones avanzadas, elija la leyenda en palabras o por códigos, y opcionalmente una tabla con los '
             'nombres de las clases de cada período, útil cuando los rásteres no tienen nombres grabados.', ''),
            ('3:35', 'Pestaña Vectorial (vista rápida).',
             'Con polígonos, use la pestaña Vectorial: elija el campo de clase de cada fecha. Solo se compara el área '
             'común a las dos capas.', ''),
            ('3:50', 'Lista de consejos en pantalla.',
             'Cuidado con leyendas distintas entre fechas: si el código tres es agua en un mapa y bosque en el otro, '
             'aparecen cambios falsos. Estandarice la leyenda antes.', 'Estandarice la leyenda'),
            ('4:10', 'Cierre estándar; pantalla final al video de la Combinación.',
             'En el próximo video, la Combinación de mapas: qué asociaciones de uso del suelo y suelo existen en Vila '
             'Serena.', 'Próximo: Combinación'),
        ],
        'description': 'El Monitoreo del Vista Saga Plugin compara dos mapas de fechas distintas y entrega el mapa de '
                       'transiciones, la tabla de transiciones y la matriz, con áreas y porcentajes. Ejemplo: la expansión '
                       'urbana de Vila Serena entre 2000 y 2020. Datos y tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Apertura', '0:20 Mapas inicial y final', '0:55 Mapa de transiciones', '1:32 Mayores cambios',
                     '2:05 Matriz de transición', '2:55 Control de calidad', '3:15 Opciones y pestaña Vectorial',
                     '4:10 Próximo video'],
        'tags': 'QGIS, Vista SAGA, detección de cambios, uso y cobertura del suelo, matriz de transición, expansión urbana, Vista Saga Plugin',
    },
    {
        'title': '4. Combinación de mapas',
        'sheet': ['Combinación de mapas: ¿qué asociaciones existen y cuánto ocupan? | Vista Saga Plugin para QGIS',
                  '4 min',
                  'Cruzar uso del suelo y suelos, leer la tabla de combinaciones y encontrar la ciudad construida sobre '
                  'suelo inundable.',
                  'uso_solo_2020.tif, solos.tif',
                  'Proyecto de Vila Serena abierto.',
                  'CIUDAD SOBRE SUELO INUNDABLE: ¿DÓNDE?'],
        'scenes': [
            ('0:00', 'Apertura estándar.', '', 'Combinación de mapas'),
            ('0:05', 'Uso del suelo 2020 y suelos lado a lado.',
             '¿Dónde hay ciudad construida sobre suelo de llanura inundable? Para responder hay que cruzar dos mapas. La '
             'Combinación de mapas lo hace y da un código a cada asociación encontrada, sin pesos ni notas.', ''),
            ('0:22', 'Abrir Combinación de mapas, pestaña Ráster; añadir uso del suelo 2020 y suelos.',
             'Abra la Combinación de mapas, pestaña Ráster, y añada el uso del suelo 2020 y después los suelos. El orden '
             'de la lista es el orden de las columnas en la tabla.', ''),
            ('0:40', 'Guardar en; Ejecutar; mapa combinado cargado con colores y leyenda.',
             'Indique dónde guardar y ejecute. El mapa combinado se carga con colores y leyenda.', ''),
            ('0:55', 'Abrir _combinacoes.csv; ordenar por área.',
             'La tabla de combinaciones trae cada asociación con área y porcentaje. Son trece combinaciones en '
             'cuatrocientas hectáreas. La mayor es pastizal sobre argisol: noventa y ocho hectáreas.', '13 combinaciones'),
            ('1:25', 'Resaltar la fila Área urbana | Neosol flúvico.',
             'Y la que interesa al municipio: área urbana sobre neosol flúvico, diecisiete coma nueve hectáreas, cuatro '
             'y medio por ciento de la ciudad. Es ciudad en suelo inundable.', 'Ciudad en suelo inundable: 17,9 ha'),
            ('1:50', 'Simbología del mapa combinado: desmarcar todas las clases menos la 3.',
             'Para ver dónde está, abra la Simbología del mapa combinado y deje visible solo esa combinación.', ''),
            ('2:10', 'Herramienta Identificar sobre una celda; valor igual al ID_COMB del CSV.',
             'Con la herramienta Identificar, el valor de la celda es el código de la combinación, el mismo ID de la '
             'tabla.', 'Valor de la celda = ID_COMB'),
            ('2:25', 'Pestaña Vectorial: campos de clase y de leyenda; resumen con astillas.',
             'En la pestaña Vectorial, elija el campo de clase y el de leyenda de cada capa. El resultado trae los '
             'campos COD y LEG de cada mapa. Las astillas de cruce con menos de un centímetro de ancho medio se '
             'incorporan al vecino y se registran en el resumen.', 'Astillas < 1 cm'),
            ('2:55', 'Lista de consejos en pantalla.',
             'Empiece con pocos mapas: con muchas clases, las combinaciones se multiplican. Y use la Combinación para '
             'explorar antes de una Evaluación: muestra lo que existe, sin juzgar.', 'Explore antes de evaluar'),
            ('3:20', 'Cierre estándar; pantalla final al video de la Evaluación.',
             'En el próximo video, la Evaluación: dónde puede crecer Vila Serena.', 'Próximo: Evaluación'),
        ],
        'description': 'La Combinación de mapas del Vista Saga Plugin cruza dos o más mapas categóricos y da un código a '
                       'cada asociación de clases, con área y porcentaje. Ráster o vector. Ejemplo: uso del suelo y '
                       'suelos en Vila Serena. Datos y tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Apertura', '0:22 Armar la combinación', '0:55 Tabla de combinaciones',
                     '1:25 Ciudad en suelo inundable', '2:10 Identificar', '2:25 Pestaña Vectorial', '3:20 Próximo video'],
        'tags': 'QGIS, Vista SAGA, tabulación cruzada, superposición de mapas, suelos, uso del suelo, Vista Saga Plugin',
    },
    {
        'title': '5. Evaluación',
        'sheet': ['Evaluación multicriterio con pesos y notas | Vista Saga Plugin para QGIS',
                  '6 min',
                  'Armar una evaluación de aptitud para la expansión urbana (pendiente, suelos, uso del suelo), validar, '
                  'ejecutar e interpretar el mapa.',
                  'declividade.tif, solos.tif, uso_solo_2020.tif, aptidao_expansao.geosaga.json',
                  'Proyecto de Vila Serena abierto.',
                  '¿DÓNDE PUEDE CRECER LA CIUDAD?'],
        'scenes': [
            ('0:00', 'Apertura estándar.', '', 'Evaluación'),
            ('0:05', 'Mapas de pendiente, suelos y uso del suelo.',
             '¿Dónde puede crecer Vila Serena con menos conflicto? La Evaluación responde con una media ponderada: cada '
             'mapa es un criterio con un peso, y cada clase recibe una nota.', ''),
            ('0:20', 'Tabla en pantalla con pesos y notas.',
             'Usaremos tres criterios: pendiente, con cuarenta por ciento; suelos, veinticinco; uso del suelo, treinta y '
             'cinco. Los pesos y las notas de este ejemplo son didácticos: en un estudio real necesitan justificación.',
             'Pesos: 40 / 25 / 35'),
            ('0:42', 'Abrir Evaluación, pestaña Ráster; Escala de las notas 0 a 10; añadir los tres mapas.',
             'Abra la Evaluación, pestaña Ráster. Elija la escala de cero a diez y añada los tres mapas.', ''),
            ('0:58', 'Los pesos entran en blanco; escribir 40, 25, 35 con Tab.',
             'Los pesos entran en blanco, a propósito. Escriba los pesos; la tecla Tab salta de uno a otro. Abajo, el '
             'mensaje confirma: cien por ciento, distribución válida.', 'Tab salta entre pesos'),
            ('1:18', 'Seleccionar pendiente; notas 10, 8, 4, 1. Suelos: 7, 9, 2.',
             'Seleccione cada mapa y ponga nota a las clases. Pendiente: plano diez, suave ondulado ocho, ondulado '
             'cuatro, fuerte ondulado uno. Suelos: argisol siete, latosol nueve, neosol flúvico dos.', ''),
            ('1:45', 'Uso del suelo: 8, 1, 6, 9; Agua: marcar No evaluar.',
             'Uso del suelo: área urbana ocho, vegetación nativa uno, agricultura seis, pastizal nueve. Y en el agua, '
             'marque No evaluar: queda fuera del resultado.', 'Agua: No evaluar'),
            ('2:05', 'Una clase sin nota resaltada; clic en Validar; mensaje con lo pendiente.',
             'Si una clase queda sin nota, aparece resaltada, y el botón Validar lista lo que falta. El complemento nunca '
             'supone nota cero: ninguna clase entra en el cálculo sin su decisión.', 'Nunca supone nota 0'),
            ('2:30', 'Clic en Abrir proyecto… y elegir aptidao_expansao.geosaga.json; todo completado.',
             'Atajo: en Abrir proyecto, elija el archivo listo del tutorial. Mapas, pesos y notas se cargan de una vez. '
             'Así se repite o se ajusta una evaluación.', 'Abrir proyecto…'),
            ('2:50', 'Guardar en aptidao_expansao.tif; informes marcados; Ejecutar.',
             'Indique dónde guardar, mantenga marcados los informes CSV y TXT y ejecute.', ''),
            ('3:05', 'Mapa cargado; leyenda de 3 a 9.',
             'El mapa de aptitud llega a QGIS. Las notas van de tres a ocho coma nueve, con media de seis coma tres. El '
             'agua, sin evaluación, queda fuera.', 'Media 6,3'),
            ('3:25', 'Informe TXT: resumen por nota final; resaltar notas 8 y 9.',
             'En el informe, el resumen por nota final: las notas ocho y nueve suman noventa y ocho hectáreas, casi todas '
             'en relieve plano o suave, sobre argisol, en pastizal o en área ya urbana.', 'Notas 8-9: 98 ha'),
            ('3:50', 'Resaltar las combinaciones de la nota 3.',
             'La nota tres reúne lo peor de todo: vegetación nativa en pendiente fuerte. El informe muestra exactamente '
             'qué combinación de clases generó cada nota.', ''),
            ('4:10', 'Comparar: latosol en la sierra con nota media baja.',
             'Un detalle que enseña: el latosol tiene nota nueve, pero su media en el mapa es la más baja, porque está en '
             'la sierra. La pendiente pesa más y domina. Los pesos importan tanto como las notas.', 'El peso domina'),
            ('4:35', 'Archivo _pesos_notas.geosaga.json en la carpeta.',
             'Cada ejecución graba un archivo con los pesos y las notas usados. Guárdelo con el informe: es el registro '
             'de lo que usted decidió.', ''),
            ('4:50', 'Pestañas Vectorial (Atributos) y Vectorial (Superposición), vista rápida.',
             'Con datos vectoriales, use la pestaña Vectorial (Atributos), para campos de una misma capa, o Vectorial '
             '(Superposición), para cruzar capas. El diseño es el mismo.', ''),
            ('5:05', 'Cierre estándar; pantalla final al video de Voronoi.',
             'Pruebe la sensibilidad: cambie los pesos y compare los mapas. En el próximo video, el Análisis de Voronoi.',
             'Próximo: Voronoi'),
        ],
        'description': 'La Evaluación del Vista Saga Plugin hace análisis multicriterio por pesos y notas, en el modelo '
                       'del Vista SAGA: media ponderada, las clases sin nota bloquean la ejecución, informes CSV y TXT y '
                       'proyecto reutilizable. Ejemplo: aptitud para la expansión urbana en Vila Serena. Datos y '
                       'tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Apertura', '0:20 Criterios y pesos', '0:58 Escribir los pesos', '1:18 Notas de las clases',
                     '2:05 Validar', '2:30 Abrir proyecto', '3:05 El mapa de aptitud', '3:25 Informe por nota',
                     '4:10 El peso domina', '5:05 Próximo video'],
        'tags': 'QGIS, Vista SAGA, análisis multicriterio, media ponderada, aptitud, planificación urbana, Vista Saga Plugin',
    },
    {
        'title': '6. Análisis de Voronoi',
        'sheet': ['Áreas de influencia con Voronoi: simple, con masa y con fricción | Vista Saga Plugin para QGIS',
                  '6 min',
                  'Delimitar el área de influencia de escuelas por distancia, por tamaño (matrícula) y por dificultad de '
                  'desplazamiento (fricción del río).',
                  'escolas.gpkg (escuelas), atrito.tif (fricción)',
                  'Proyecto de Vila Serena abierto.',
                  'EL RÍO CAMBIA QUIÉN ATIENDE A QUIÉN'],
        'scenes': [
            ('0:00', 'Apertura estándar.', '', 'Análisis de Voronoi'),
            ('0:05', 'Mapa con las seis escuelas y el río.',
             '¿Qué escuela atiende cada parte de Vila Serena? Depende de la pregunta: por distancia, por el tamaño de la '
             'escuela o por la dificultad de llegar. El Análisis de Voronoi hace las tres versiones.', ''),
            ('0:22', 'Abrir Análisis de Voronoi, pestaña Ráster; lista Modo abierta.',
             'Abra el Análisis de Voronoi. Hay cuatro modos: Simple, Con masa, Con fricción y Con masa y fricción, todos '
             'validados frente al Vista SAGA original.', 'Validado frente al Vista SAGA'),
            ('0:38', 'Modo Simple; Puntos generadores: escolas; Identificador del punto: NOME.',
             'Empiece por el Simple. En Puntos generadores, las escuelas; en Identificador del punto, el campo NOME, el '
             'nombre de la escuela.', ''),
            ('0:50', 'Extensión del análisis: Rejilla del ráster de referencia; Ráster de referencia: atrito.',
             'En Extensión del análisis, elija Rejilla del ráster de referencia e indique el ráster de fricción. Así el '
             'resultado cae exactamente en la rejilla de los otros mapas. Ejecute.', 'Use la rejilla de referencia'),
            ('1:10', 'Resultado Simple cargado; tabla _centros.csv.',
             'Cada lugar queda con la escuela más cercana. La tabla de centros trae el área de cada región.', ''),
            ('1:22', 'Modo Con masa; Campo de masa: MATRICULAS; Ejecutar.',
             'Ahora, Con masa. En Campo de masa, elija MATRICULAS, la matrícula. El criterio es la masa dividida por la '
             'distancia al cuadrado, como en el Vista SAGA.', 'Criterio: M/d²'),
            ('1:40', 'Comparar Simple × Con masa; resaltar E. E. Darcy Ribeiro.',
             'La escuela Darcy Ribeiro, con mil doscientos alumnos, pasa de cuarenta a cien hectáreas. La Cora Coralina, '
             'con doscientos cincuenta, baja de cuarenta a veintitrés.', 'Darcy Ribeiro: 40 → 100 ha'),
            ('2:05', 'Texto explicativo en pantalla: 4× masa = 2× alcance.',
             'Un detalle importante: una escuela con cuatro veces más masa alcanza el doble de distancia, no el '
             'cuádruple. Es la raíz cuadrada de la razón de las masas.', '4× masa = 2× alcance'),
            ('2:25', 'Modo Con fricción; Tipo de superficie Ráster; Superficie de fricción: atrito; Ejecutar.',
             'Ahora, Con fricción. Elija el tipo de superficie ráster y el mapa de fricción. En él, andar por la ciudad '
             'cuesta uno, por el pastizal dos, por la vegetación cuatro, y cruzar el agua cuesta diez.', 'Agua: fricción 10'),
            ('2:50', 'Comparar Simple × Con fricción; resaltar E. M. Monteiro Lobato.',
             'La escuela Monteiro Lobato, junto al río, pierde área: de cincuenta y nueve a cincuenta hectáreas, porque '
             'cruzar el agua se volvió caro. La Cecília Meireles gana: de ochenta y seis a noventa y ocho.', ''),
            ('3:15', 'Diagrama en pantalla: recta escuela-lugar cruzando el río.',
             'Atención al modelo: el costo se mide en la recta entre la escuela y cada lugar, como en el Vista SAGA. No '
             'es el camino de menor costo de GRASS: la recta no rodea el río, paga por cruzarlo.',
             'Costo en la recta, no en el camino mínimo'),
            ('3:40', 'Pestaña Vectorial: Simple y Con masa con fronteras exactas.',
             'En la pestaña Vectorial, el resultado sale en polígonos, con fronteras exactas en el Simple y en el Con '
             'masa, y trazadas sin rasterizar en los modos con fricción.', ''),
            ('3:58', 'Casilla Combinar varias superficies de fricción (vista rápida).',
             'Y si la fricción viene de varios mapas, como relieve y uso del suelo, marque Combinar varias superficies '
             'de fricción y defina pesos y notas, como en la Evaluación.', ''),
            ('4:15', 'Lista de consejos en pantalla.',
             'Tres consejos. La nota de fricción cero se rechaza: para casi sin fricción, use cero coma uno. En caso de '
             'empate, gana el primer punto de la capa. Y use siempre un SRC en metros.', 'Fricción 0 se rechaza'),
            ('4:40', 'Cierre estándar; pantalla final al video del Secuenciador.',
             'En el último video de la serie, el Secuenciador de mapas: la expansión de Vila Serena en animación.',
             'Próximo: Secuenciador'),
        ],
        'description': 'El Análisis de Voronoi del Vista Saga Plugin delimita áreas de influencia en cuatro modos (Simple, '
                       'Con masa, Con fricción, Con masa y fricción), en el modelo del Vista SAGA y validados frente a él. '
                       'Ráster o vector, con superficie de fricción ráster o poligonal. Ejemplo: las escuelas de Vila '
                       'Serena y el río. Datos y tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Apertura', '0:22 Los cuatro modos', '0:38 Simple', '1:22 Con masa (M/d²)',
                     '2:25 Con fricción', '3:15 Costo en la recta', '3:40 Pestaña Vectorial', '4:15 Consejos',
                     '4:40 Próximo video'],
        'tags': 'QGIS, Vista SAGA, Voronoi, polígonos de Thiessen, área de influencia, superficie de fricción, modelo gravitacional, Vista Saga Plugin',
    },
    {
        'title': '7. Secuenciador de mapas',
        'sheet': ['Secuenciador de mapas: GIF animado de la evolución en el tiempo | Vista Saga Plugin para QGIS',
                  '4 min',
                  'Armar una animación GIF (y cuadros PNG) con el uso del suelo de 2000, 2010 y 2020.',
                  'uso_solo_2000.tif, uso_solo_2010.tif, uso_solo_2020.tif',
                  'Proyecto de Vila Serena abierto, con la simbología final de las capas.',
                  '20 AÑOS EN 3 SEGUNDOS'],
        'scenes': [
            ('0:00', 'Apertura estándar.', '', 'Secuenciador de mapas'),
            ('0:05', 'El GIF final en pantalla completa.',
             'Veinte años de expansión urbana en tres segundos. Para presentar cambios en el tiempo, una animación '
             'comunica mejor que tres mapas lado a lado. El Secuenciador de mapas lo hace directamente desde QGIS.', ''),
            ('0:22', 'Abrir Secuenciador, pestaña Ráster; añadir 2000, 2010 y 2020.',
             'Abra el Secuenciador, pestaña Ráster, y añada los tres mapas de uso del suelo. El complemento lee el año en '
             'el nombre de la capa y lo muestra en la lista.', ''),
            ('0:40', 'Botones Editar fecha… y Ordenar por fecha.',
             'Si hace falta, edite la fecha de un cuadro o use Ordenar por fecha. Mover hacia arriba y hacia abajo '
             'ajustan el orden a mano.', ''),
            ('0:55', 'Dimensiones: 600 × 600; Duración 1000 ms; Mostrar la fecha activado; leyenda temática.',
             'En Dimensiones y composición, use seiscientos por seiscientos píxeles y un segundo por cuadro. Active la '
             'fecha sobre el mapa y, si quiere, la leyenda temática, con hasta diez categorías.', '1 s por cuadro'),
            ('1:15', 'Salidas: archivo .gif; marcar cuadros PNG; Ejecutar; vista previa en la ventana.',
             'Indique el archivo GIF y marque Exportar también los cuadros PNG individuales. Ejecute. La vista previa '
             'aparece en la propia ventana.', ''),
            ('1:35', 'Carpeta con quadro_001_2000.png, quadro_002_2010.png, quadro_003_2020.png.',
             'En la carpeta, además del GIF, los tres cuadros en PNG, con colores exactos.', ''),
            ('1:48', 'Pestañas Vectorial y Mixto (vista rápida); opción acumulativa.',
             'En las pestañas Vectorial y Mixto se animan capas vectoriales, incluso por un campo de fecha, y se pueden '
             'superponer vectores a un ráster de fondo. La opción acumulativa mantiene las entidades de los períodos '
             'anteriores: ideal para mostrar crecimiento.', 'Acumulativo = crecimiento'),
            ('2:15', 'Lista de consejos en pantalla.',
             'Dos consejos. El GIF tiene como máximo doscientos cincuenta y seis colores; para diapositivas, use los PNG. '
             'Y los cuadros usan la simbología de QGIS: ajuste colores y leyenda antes de exportar.',
             'Ajuste la simbología antes'),
            ('2:35', 'Cierre de la serie: los siete módulos en mosaico; sitio oficial.',
             'Con este video, conoció los siete módulos del Vista Saga Plugin. El tutorial completo, el manual y los '
             'datos de Vila Serena están en el sitio oficial. ¡Buen trabajo!', 'headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com'),
        ],
        'description': 'El Secuenciador de mapas del Vista Saga Plugin genera un GIF animado (y cuadros PNG) a partir de '
                       'mapas en orden, con fecha, nombres y leyenda en cada cuadro, usando la simbología de QGIS. '
                       'Ejemplo: la expansión urbana de Vila Serena de 2000 a 2020. Datos y tutorial: '
                       'https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Apertura', '0:22 Añadir cuadros', '0:55 Dimensiones y composición', '1:15 Generar el GIF',
                     '1:48 Vectorial, Mixto y acumulativo', '2:15 Consejos', '2:35 Cierre de la serie'],
        'tags': 'QGIS, Vista SAGA, GIF animado, serie temporal, animación de mapas, expansión urbana, Vista Saga Plugin',
    },
]
