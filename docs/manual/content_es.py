"""Texto del manual del usuario en español (Vista Saga Plugin 1.6.0). Misma estructura que content_pt.py."""

LANG = 'es'
UI = {
    'doc_title': 'Manual del Usuario',
    'subtitle': 'Vista Saga Plugin 1.6.0 para QGIS 4',
    'tagline': 'Geoprocesamiento inspirado en el Vista SAGA/UFRJ, en siete módulos',
    'author': 'Esdras Andrade (IGDEMA/UFAL)',
    'date': 'Noviembre de 2026',
    'toc': 'Índice',
    'figure': 'Figura',
    'table': 'Tabla',
    'tip': 'Consejo',
    'warning': 'Atención',
    'note': 'Nota',
    'hidden': 'Consejos que solo cuenta el manual',
    'fields_title': 'Campos y botones de la ventana',
    'fields_cols': ['Sección', 'Elemento', 'Tipo', 'Qué hace'],
    'kinds': {'PushButton': 'botón', 'ToolButton': 'botón', 'CheckBox': 'casilla', 'LineEdit': 'campo de texto',
              'ComboBox': 'lista desplegable', 'MapLayerComboBox': 'capa de QGIS', 'SpinBox': 'campo numérico',
              'DoubleSpinBox': 'campo numérico', 'ListWidget': 'lista'},
    'close_label': 'Cerrar (ventana auxiliar)',
    'compare_cols': ['Rutina similar', 'Qué cambia en el Vista Saga Plugin'],
    'results_cols': ['Archivo o salida', 'Contenido y lectura'],
    'routine': 'Rutina de uso correcto',
    'concept': 'Para qué sirve',
    'compare': 'En qué se diferencia de rutinas similares',
    'ease': 'Facilidad de uso',
    'window': 'La ventana',
    'results': 'Resultados y cómo interpretarlos',
    'pitfalls': 'Errores comunes y cómo evitarlos',
    'footer': 'Vista Saga Plugin 1.6.0 - Manual del Usuario',
    'page': 'Página',
}

INTRO = {
    'title': 'Presentación',
    'paras': [
        'El **Vista Saga Plugin** es un complemento independiente para **QGIS 4** que reúne, en siete módulos, '
        'procedimientos de análisis geográfico inspirados en el **Vista SAGA**, el sistema de análisis ambiental creado '
        'en el Laboratorio de Geoprocesamiento de la UFRJ (Brasil). El complemento no usa código del programa original: '
        'los métodos se reimplementaron y, en los módulos con resultados numéricos comparables, se **validaron frente '
        'al Vista SAGA original**, celda por celda.',
        'El objetivo es seguir el mismo razonamiento del Vista SAGA (firmas, monitoreos, evaluaciones por pesos y notas, '
        'áreas de influencia) dentro de QGIS, con los datos que usted ya usa, sin conversiones manuales y con informes '
        'listos para hojas de cálculo y textos técnicos.',
        'Para cada módulo, este manual explica **para qué sirve**, **en qué se diferencia de las rutinas parecidas** de '
        'QGIS y de otros complementos, **cada campo de la ventana**, la **rutina de uso correcto**, **cómo leer los '
        'resultados** y los **consejos que no aparecen en pantalla**.',
    ],
    'audience_title': 'A quién se dirige este manual',
    'audience': [
        'Quien hace diagnóstico ambiental, planificación urbana o regional, estudios de cuencas y de uso del suelo.',
        'Quien ya trabajó con el Vista SAGA y quiere reproducir los mismos análisis en QGIS.',
        'Estudiantes y docentes de Geografía, Ecología, Ingeniería y áreas afines que necesitan análisis geográficos '
        'explicables, con informes auditables.',
    ],
    'principles_title': 'Principios del complemento',
    'principles': [
        '**Fidelidad de método:** cuando hay un modelo del Vista SAGA, el complemento lo sigue e indica dónde difiere.',
        '**Nada se hace a escondidas:** el complemento no reproyecta mapas sin avisar, no supone notas, no excluye '
        'clases por su cuenta y nunca altera los datos de entrada.',
        '**Informes auditables:** cada resultado viene con un TXT legible y un CSV para hojas de cálculo, siempre en '
        'portugués, sea cual sea el idioma de la interfaz.',
        '**Una sola lógica de uso:** los siete módulos siguen el mismo patrón de ventana, botones y resultado.',
    ],
}

INSTALL = {
    'title': 'Instalación y primeros pasos',
    'steps_title': 'Instalación',
    'steps': [
        'Descargue **Vista_Saga_Plugin_QGIS4_v1.6.0.zip** (el ZIP de instalación, no el código fuente de GitHub).',
        'En QGIS 4, abra **Complementos > Administrar e instalar complementos > Instalar a partir de ZIP**.',
        'Elija el ZIP, haga clic en **Instalar complemento** y reinicie QGIS.',
        'El botón **Vista Saga Plugin** aparece en su propia barra de herramientas; al hacer clic, se abre el menú con '
        'los siete módulos. También están en **Ráster > Vista Saga Plugin**.',
    ],
    'warning': 'La carpeta instalada se llama **geosaga** a propósito. No la renombre: modelos y proyectos antiguos '
               'dependen de ese nombre y de los identificadores de procesamiento **geosaga:***.',
    'common_title': 'Lo que es igual en todos los módulos',
    'common': [
        '**Idioma:** la interfaz sigue el idioma de QGIS (portugués, inglés o español; en los demás, inglés). Los '
        'informes CSV y TXT se graban siempre en portugués.',
        '**Ayudas:** detenga el ratón sobre cualquier botón, campo, casilla o lista para ver un recuadro amarillo que '
        'explica qué hace.',
        '**Pie estándar:** **[Ejecutar]** y **[Cerrar]** en todas las ventanas; la Evaluación tiene también '
        '**[Validar]**.',
        '**Ventana no modal:** la ventana del módulo puede quedar abierta mientras usted trabaja en el mapa de QGIS '
        '(seleccionar entidades, cambiar estilos, abrir capas).',
        '**Progreso:** durante la ejecución aparece una ventana de progreso con **Cancelar**; el desenlace (concluido, '
        'cancelado) aparece en la barra de mensajes de QGIS.',
        '**Resultado temporal o guardado:** el campo **Guardar en** vacío genera un resultado temporal, llamado '
        '"Módulo - operación" (por ejemplo, "Análises Voronoi - Com Atrito"); si se completa, el resultado se guarda en '
        'el archivo elegido y se carga con el nombre de ese archivo.',
        '**Datos de entrada intactos:** ningún módulo altera las capas de entrada.',
    ],
    'temp_warning': 'Los resultados temporales quedan en la carpeta temporal de QGIS y **desaparecen al cerrar QGIS**. '
                    'Guárdelos (clic derecho en la capa > Exportar) antes de salir, o indique un archivo en **Guardar '
                    'en** desde el principio.',
    'tooltip_fig': 'Las ayudas (recuadros amarillos) explican cada elemento de la ventana',
}

CONCEPTS = {
    'title': 'Conceptos usados en todo el manual',
    'items': [
        ('Mapa categórico (temático)', 'Mapa en el que cada celda o polígono pertenece a una **clase** (uso del suelo, '
         'tipo de suelo, barrio). Es el tipo de mapa que usa la mayoría de los módulos. Los valores continuos '
         '(altitud, temperatura) deben clasificarse antes.'),
        ('Clase, código y leyenda', 'Cada clase tiene un **código** (un entero en el ráster; un valor de campo en el '
         'vector) y un **nombre** (la leyenda). El complemento lee los nombres del archivo (leyenda del RS2, nombres '
         'de categorías del GeoTIFF, archivo .rs2.json) o, en la Firma espacial, del estilo de la capa en QGIS.'),
        ('FONDO (FUNDO) y NoData', 'El **FUNDO** es la clase de fondo del formato RS2 (en general, código 0). El '
         '**NoData** es el valor "sin dato" de un GeoTIFF. Cada módulo indica cómo los trata; en la Firma espacial, por '
         'ejemplo, ambos cuentan como clase, como en el Vista SAGA.'),
        ('SRC (sistema de referencia)', 'Define las coordenadas del mapa. Para medir áreas y distancias, use un **SRC '
         'proyectado en metros** (por ejemplo, UTM SIRGAS 2000). El complemento **no reproyecta sin avisar**: los mapas '
         'analizados en conjunto deben estar en el mismo SRC.'),
        ('Grilla (ráster)', 'Tamaño de celda, extensión y alineación de un ráster. Los módulos que comparan rásteres '
         'celda por celda exigen **la misma grilla** en todos los mapas.'),
        ('RS2', 'Formato ráster del Vista SAGA (un archivo .rs2). No guarda el SRC: el complemento lo registra en un '
         'archivo al lado (**.rs2.json**) o le pide que lo confirme. El Conversor de formatos lleva datos entre RS2, '
         'GeoTIFF y vector.'),
        ('Astilla (sliver)', 'Superposición o hueco muy fino entre polígonos vecinos, causado por imprecisión de '
         'coordenadas. En la Combinación y la Firma espacial vectoriales, las astillas con **ancho medio menor que '
         '1 cm** se toleran y se registran en el informe.'),
    ],
}

MODULES = {}

MODULES['assinatura'] = {
    'title': 'Firma espacial',
    'figure': ('assinatura', 'Firma espacial: la selección en el mapa de referencia recorta todos los mapas de la lista'),
    'concept': [
        'La Firma espacial responde a la pregunta **"¿de qué está hecha esta área?"**. Usted elige un **mapa de '
        'referencia** (por ejemplo, barrios), selecciona una o más de sus clases o entidades (por ejemplo, dos barrios) '
        'y el complemento mide, **dentro de ese límite**, cuánto ocupa cada clase de cada mapa de la lista: uso del '
        'suelo, suelos, escolaridad, pendiente.',
        'Es el modelo del Vista SAGA: la referencia queda arriba en la lista, su selección define el límite y **todos '
        'los mapas se firman, incluida la referencia**. El resultado sale de la **unión** de la selección y, si lo '
        'desea, **por entidad** (un bloque para cada barrio seleccionado).',
        'Para cada clase, el informe trae el área en el mapa entero, el área dentro del límite y dos porcentajes: el '
        '**% área firmada** (de qué está hecho el lugar) y el **% categoría** (cuánto de la clase se concentra allí).',
    ],
    'compare': [
        ('Estadísticas zonales e Histograma zonal (Procesamiento de QGIS)', 'Cuentan píxeles de un ráster por polígono. '
         'La Firma espacial firma **varios mapas a la vez**, usa la **selección** en el mapa de referencia como límite, '
         'calcula la **unión** y cada entidad y entrega listos los dos porcentajes del Vista SAGA.'),
        ('Intersección vectorial seguida de tabla dinámica', 'Exige varios pasos manuales y no resuelve superposiciones. '
         'La pestaña Vectorial hace la intersección exacta, **disuelve** polígonos de la misma clase, separa la '
         '**superposición** entre clases y muestra lo que quedó **sin clase**.'),
        ('Firma del Vista SAGA original', 'Mismas columnas y misma lógica. La selección es por **clase entera** (el '
         'balde del Vista SAGA marca una región continua); los nombres de las clases pueden venir de QGIS; los informes '
         'salen en TXT y CSV.'),
    ],
    'ease': [
        'El orden de la lista lo dice todo: **el primer mapa es la referencia**.',
        'En ráster, basta marcar las clases; "Marcar todas" equivale a "Firmar el mapa entero".',
        'En vector, la selección es la del propio QGIS, con el botón **Seleccionar en el mapa**.',
        'La pestaña **Resultados** muestra la tabla y permite alternar entre la unión y cada entidad.',
    ],
    'windows': [('assinatura_raster', 'Firma espacial, pestaña Ráster: mapas, clases de la referencia, opciones y '
                 'resultado'),
                ('assinatura_vetorial', 'Firma espacial, pestaña Vectorial: campos de clase y selección hecha en el '
                 'mapa de QGIS'),
                ('assinatura_resultados', 'Firma espacial, pestaña Resultados: recorte (unión o entidad) y tabla')],
    'routine': [
        'Elija la pestaña **Ráster** o **Vectorial** (no se mezclan formatos: ráster solo con ráster, vector solo con '
        'vector).',
        'En **1. Mapas**, agregue los mapas. **El primero de la lista es la referencia**; use **Mover hacia '
        'arriba/abajo** para cambiar el orden. Todos deben estar en el **mismo SRC, proyectado en metros**; en ráster, '
        'también en la **misma grilla**. Un RS2 sin .rs2.json pide su SRC al agregarse.',
        'En vector, seleccione cada mapa de la lista y verifique el **Campo de clase** y el **Campo de la leyenda**.',
        'En **2. Selección en la referencia**: en ráster, marque las clases; en vector, haga clic en **Seleccionar en '
        'el mapa** y haga clic en las entidades del mapa de QGIS (Ctrl+clic agrega o quita). El contador muestra '
        'cuántas están seleccionadas.',
        'En **3. Opciones**, deje activado **Resultado por entidad** si quiere un bloque para cada entidad; en vector, '
        'elija el tratamiento de la superposición entre clases.',
        'En **4. Resultado**, escriba un título (opcional) y elija dónde guardar el CSV (el TXT va al lado). Haga clic '
        'en **Ejecutar**.',
        'Revise la pestaña **Resultados** y abra el TXT para la lectura completa.',
    ],
    'results': [
        ('Informe TXT', 'Encabezado con mapas, SRC, selección, método y avisos; luego un bloque de la **unión de la '
         'selección** y un bloque para cada entidad (o clase, en ráster). Cada bloque tiene una tabla por mapa.'),
        ('Informe CSV', 'Una fila por recorte, mapa y clase. Columnas: RECORTE (UNIAO o FEICAO), ID_FEICAO, '
         'NOME_FEICAO, MAPA, CODIGO, CLASSE, TOTAL_PIXELS, TOTAL_HA, PIXELS_ASN, AREA_ASN_HA, PCT_AREA_ASN, '
         'PCT_CATEGORIA. Separador ";" y UTF-8: se abre directo en Excel o LibreOffice.'),
        ('% área firmada', 'Área de la clase en el límite ÷ área del límite. **Caracteriza el lugar**; suma 100% en cada '
         'mapa.'),
        ('% categoría', 'Área de la clase en el límite ÷ área de la clase en el mapa entero. **Mide concentración**; no '
         'suma 100% y no debe sumarse.'),
        ('Filas especiales', 'FONDO y NoData cuentan como clase. En vector: **Sin clase** (parte del límite sin polígono '
         'en el mapa) y **Superposición excluida** (región con clases diferentes superpuestas).'),
    ],
    'hidden': [
        'La tabla de la propia referencia siempre muestra 100% en las clases seleccionadas: sirve para **verificar el '
        'tamaño exacto del límite**, que es la base de todos los demás mapas.',
        'Los nombres de las clases de un ráster vienen del **estilo de la capa en QGIS** (simbología Paletizado/Valores '
        'únicos) cuando el mapa se agregó desde el proyecto: cambie los nombres en la simbología y ejecute de nuevo.',
        'Con muchas entidades seleccionadas, **desactive "Resultado por entidad"**: el TXT queda enorme y la unión sigue '
        'disponible.',
        '**No sume los bloques por entidad** para obtener la unión: si dos entidades se superponen, la unión cuenta el '
        'área común una sola vez. Use el bloque de la unión.',
        'En el CSV, filtre la columna **RECORTE** y arme tablas dinámicas por MAPA y CLASSE.',
        'La sección **Tolerancia de astillas** del TXT (vector) muestra huecos y superposiciones menores de 1 cm: sirve '
        'para auditoría, no para interpretación.',
        'Ráster y vector dan números un poco diferentes (celdas × polígono exacto). Para comparar lugares o fechas, use '
        'siempre el mismo formato y la misma grilla.',
    ],
    'pitfalls': [
        '**"El mapa X está en otro SRC":** reproyéctelo antes en QGIS (el complemento no reproyecta).',
        '**"El mapa X no está en la misma grilla":** alinee los rásteres antes (misma celda, extensión y origen).',
        '**"Ninguna entidad seleccionada":** use **Seleccionar en el mapa** y haga clic en las entidades, o '
        '**Seleccionar todas**. La herramienta de selección de QGIS actúa sobre la capa activa; el botón ya activa la '
        'referencia.',
        'Clases mostradas como "Clase 7": el archivo no tiene nombres grabados; póngales nombre en la simbología de QGIS.',
    ],
}

MODULES['monitoria'] = {
    'title': 'Monitoreo',
    'figure': ('monitoria', 'Monitoreo: dos períodos, el mapa de transiciones y la matriz de transición'),
    'concept': [
        'El Monitoreo responde a la pregunta **"¿qué cambió entre dos períodos?"**. Compara un mapa inicial y uno final '
        'de la misma área e identifica, para cada celda (ráster) o porción de polígono (vector), si la clase '
        '**permaneció** o **cambió**, y a cuál.',
        'El resultado es un **mapa de transiciones**, una **tabla de transiciones** y una **matriz de transición** '
        '(clase inicial en las filas, clase final en las columnas), con áreas y porcentajes.',
    ],
    'compare': [
        ('Calculadora ráster y tablas cruzadas hechas a mano', 'Exigen codificar las transiciones y contar aparte. El '
         'Monitoreo genera el mapa, la tabla y la matriz en una ejecución, con leyenda descriptiva ("Permaneció", '
         '"Dejó de ser … → Se convirtió en …").'),
        ('Herramientas de cambio de complementos de clasificación', 'Suelen trabajar solo con ráster. El Monitoreo tiene '
         'también la pestaña **Vectorial**, que compara polígonos por superposición exacta, en hectáreas.'),
        ('Monitoreo del Vista SAGA', 'Mismo razonamiento de mapa de transiciones y matriz; aquí con leyenda en palabras '
         'o por códigos, tabla copiable y resultado cargado en QGIS.'),
    ],
    'ease': [
        'Dos mapas, dos períodos, un botón: el mapa de transiciones se carga ya con colores y leyenda.',
        'Permanencias en gris y cambios en colores distintos, para lectura inmediata.',
        'Tablas de la pestaña Resultados copiables a hojas de cálculo (Ctrl+A, Ctrl+C).',
    ],
    'windows': [('monitoria_raster', 'Monitoreo, pestaña Ráster: mapa inicial, mapa final y resultado'),
                ('monitoria_vetorial', 'Monitoreo, pestaña Vectorial: capas, campos de clase y período')],
    'routine': [
        'Elija la pestaña **Ráster** (mapas categóricos en la misma grilla) o **Vectorial** (capas de polígonos).',
        'Indique el **mapa inicial** y el **mapa final** (capa de QGIS o archivo) y el nombre de cada **período** (por '
        'ejemplo, el año).',
        'En vector, elija el **campo de clase** de cada período y, si lo hay, el **campo de leyenda**.',
        'Escriba un **título** y, si quiere, indique dónde guardar. En ráster, abra **Opciones avanzadas: leyenda** para '
        'elegir leyenda en palabras o por códigos y, opcionalmente, una tabla CSV con los nombres de las clases.',
        'Haga clic en **Ejecutar** y revise el mapa de transiciones y la pestaña **Resultados**.',
    ],
    'results': [
        ('Mapa de transiciones', 'GeoTIFF (ráster) o GeoPackage (vector) con un código por transición, cargado con '
         'leyenda: permanencias en gris, cambios en colores.'),
        ('_transicoes.csv', 'Una fila por transición: clase inicial, clase final, situación (permanencia o cambio), '
         'área (celdas o ha) y porcentaje.'),
        ('_matriz.csv', 'Matriz de transición: filas = clase inicial, columnas = clase final. La diagonal son las '
         'permanencias; fuera de ella, los cambios.'),
        ('_resumo.txt', 'Síntesis: área total, área evaluada, permanencias y cambios principales.'),
    ],
    'hidden': [
        'En la pestaña Vectorial, **solo se compara el área común a las dos capas**: verifique que ambos períodos '
        'cubran la misma área y usen clases equivalentes.',
        'La tabla de nombres de clases (ráster) usa el formato **PERIODO;CODIGO;CLASSE**: útil cuando los rásteres no '
        'tienen nombres grabados o las clases cambiaron de nombre entre períodos.',
        'La matriz se lee más rápido por **filas**: cada fila muestra adónde fue cada clase del período inicial.',
        'Cuando el campo de archivo está completo, tiene **prioridad** sobre la capa elegida en la lista.',
    ],
    'pitfalls': [
        'Rásteres en grillas diferentes: alinéelos antes.',
        'Clases con códigos diferentes entre períodos (por ejemplo, 3 = Agua en uno y 3 = Bosque en el otro) generan '
        'cambios falsos: estandarice la leyenda antes.',
        'Mann–Kendall (tendencia en series largas) salió del Monitoreo y volverá como módulo propio en la versión 2.0.',
    ],
}

MODULES['avaliacao'] = {
    'title': 'Evaluación',
    'figure': ('avaliacao', 'Evaluación: notas por clase, pesos por criterio y la media ponderada'),
    'concept': [
        'La Evaluación responde a la pregunta **"¿dónde es más adecuado (o más crítico)?"**. Es la evaluación '
        'multicriterio del Vista SAGA: cada mapa es un **criterio** con un **peso** (en %), y cada clase recibe una '
        '**nota** (de 0 a 10 o de 0 a 100). El resultado es la **media ponderada** de las notas en cada lugar.',
        'Hay tres pestañas con el mismo diseño: **Ráster** (mapas categóricos en la misma grilla), **Vectorial '
        '(Atributos)** (varios campos de una misma capa de polígonos) y **Vectorial (Superposición)** (varias capas de '
        'polígonos cruzadas; solo se evalúa el área común a todas).',
    ],
    'compare': [
        ('Calculadora ráster con reclasificación', 'Exige reclasificar cada mapa y escribir la fórmula a mano. La '
         'Evaluación arma la media ponderada con tablas de notas y pesos, y **bloquea la ejecución** mientras haya una '
         'clase sin nota.'),
        ('Superposición ponderada de otros programas', 'Normalmente solo en ráster. Aquí hay pestañas vectoriales que '
         '**preservan la geometría** de las entidades (Atributos) o cruzan capas (Superposición).'),
        ('Evaluación del Vista SAGA', 'Mismo método de pesos y notas, con redondeo "mitad al par" como en el original; '
         'los pesos y notas usados se graban en un archivo de proyecto reutilizable.'),
    ],
    'ease': [
        'Las clases sin nota quedan **resaltadas** y contadas; **Validar** lista todos los pendientes.',
        'La tecla **Tab** salta de peso en peso y de nota en nota.',
        'Haga clic en el encabezado de la tabla de clases para ordenar.',
        'Cada ejecución graba los pesos y las notas para reabrirlos después.',
    ],
    'windows': [('avaliacao_raster', 'Evaluación, pestaña Ráster: mapas y pesos, clases y notas, resultado'),
                ('avaliacao_atributos', 'Evaluación, pestaña Vectorial (Atributos): campos de una capa como criterios'),
                ('avaliacao_sobreposicao', 'Evaluación, pestaña Vectorial (Superposición): capas apiladas')],
    'routine': [
        'Elija la pestaña según sus datos: **Ráster**, **Vectorial (Atributos)** o **Vectorial (Superposición)**.',
        'Elija la **escala de las notas** (0 a 10 o 0 a 100).',
        'Agregue los criterios (mapas, campos o capas) y escriba el **peso** de cada uno. Los pesos nuevos entran en '
        'blanco; **Distribuir pesos por igual** divide el 100% entre todos.',
        'Seleccione un criterio y dé **nota** a cada clase. Para varias clases con la misma nota, selecciónelas y use '
        '**Aplicar**. Marque **No evaluar** en las clases que deben quedar fuera.',
        'Haga clic en **Validar** para ver lo que falta. Corrija hasta que no haya pendientes.',
        'En **3. Resultado**, indique dónde guardar (o déjelo temporal) y mantenga marcados los informes CSV y TXT. '
        'Haga clic en **Ejecutar**.',
    ],
    'results': [
        ('Carta de evaluación', 'GeoTIFF (Ráster) o GeoPackage (pestañas vectoriales) con la nota final de cada lugar.'),
        ('_relatorio.csv', 'Combinaciones de clases encontradas, notas, nota final y áreas.'),
        ('_relatorio.txt', 'Informe con el modelo del Vista SAGA: criterios, pesos, notas y distribución del resultado.'),
        ('*_pesos_notas.geosaga.json', 'Los pesos y notas usados, para reabrir en **Abrir proyecto…** y repetir o ajustar '
         'la evaluación.'),
    ],
    'hidden': [
        'La nota **"—"** significa "sin nota" e **impide la ejecución**: el complemento nunca supone nota 0 ni excluye '
        'clases por su cuenta.',
        '**No evaluar** convierte la clase en NoData en el resultado; úselo para áreas que no deben clasificarse (por '
        'ejemplo, cuerpos de agua).',
        'Los pesos nuevos entran **en blanco** a propósito: la división igual solo ocurre con el botón.',
        'El archivo de proyecto guarda rutas relativas a su carpeta: se puede mover la carpeta entera del estudio.',
        'En la pestaña Superposición, **solo se evalúa el área común a todas las capas**; verifique la cobertura antes.',
        'Las tablas aceptan Ctrl+A y Ctrl+C para copiar a hojas de cálculo, con el separador decimal de su idioma.',
    ],
    'pitfalls': [
        'Pesos que no suman 100%: la línea debajo de la tabla muestra cuánto falta.',
        'Rásteres en grillas diferentes no se aceptan en la pestaña Ráster.',
        'Notas pensadas de 0 a 100 escritas con la escala de 0 a 10: elija la escala antes de poner las notas.',
    ],
}

MODULES['voronoi'] = {
    'title': 'Análisis de Voronoi',
    'figure': ('voronoi', 'Análisis de Voronoi: las cuatro modalidades calculadas por el propio complemento'),
    'concept': [
        'Los Análisis de Voronoi responden a la pregunta **"¿cuál es el área de influencia de cada punto?"**. A partir '
        'de puntos generadores (escuelas, centros de salud, sedes), cada lugar se asigna al punto que más lo "atrae".',
        'Hay cuatro modalidades, todas con el modelo del Vista SAGA y validadas frente a él: **Simple** (menor '
        'distancia), **Con masa** (mayor M/d², donde M es la masa del punto), **Con fricción** (menor costo acumulado '
        'por la recta entre el punto y el lugar, sobre una superficie de fricción) y **Con masa y fricción** (menor '
        'costo ÷ M).',
        'El costo con fricción es la suma, en las celdas de la recta entre el punto y el lugar, de **distancia al punto '
        '× nota de fricción × paso**. La nota es el propio costo (nota 1 = costo basal). No es un camino de costo '
        'mínimo: la recta no rodea los obstáculos, los "paga".',
    ],
    'compare': [
        ('Polígonos de Voronoi (Procesamiento de QGIS)', 'Solo hacen la modalidad Simple, en vector. El complemento '
         'agrega **masa**, **fricción** (ráster o polígonos), combinación de varias superficies y salida ráster o '
         'vectorial.'),
        ('Distancia de costo (r.cost y similares)', 'Calculan el **camino de menor costo**, que rodea obstáculos. El '
         'modelo del Vista SAGA usa la **recta** entre el punto y el lugar; los resultados son diferentes y el '
         'complemento reproduce el del Vista SAGA.'),
        ('Voronoi del Vista SAGA', 'Mismo método (Simple y Con masa 100% iguales; fricción 99,4% a 99,7% de las celdas). '
         'Agrega la superficie de fricción vectorial y la salida vectorial exacta.'),
    ],
    'ease': [
        'Elija la modalidad y el complemento muestra solo los campos necesarios.',
        'Pestañas Ráster y Vectorial con los mismos datos de entrada.',
        'Masa como M/d²: una masa 9 alcanza 3 veces más lejos que una masa 1, y no 9 veces.',
    ],
    'windows': [('voronoi_raster', 'Análisis de Voronoi, pestaña Ráster: modalidad, datos de entrada y resultado'),
                ('voronoi_vetorial', 'Análisis de Voronoi, pestaña Vectorial')],
    'routine': [
        'Elija la pestaña **Ráster** (grilla de celdas) o **Vectorial** (polígonos de frontera exacta).',
        'Elija la **modalidad**.',
        'Indique la capa de **puntos generadores**, el campo de **identificación** y, en las modalidades con masa, el '
        '**campo de masa** (positivo).',
        'Con fricción, elija el **tipo de superficie**: ráster (nota en cada celda) o polígonos (nota en una columna); '
        'para varias superficies, marque **Combinar varias superficies de fricción** y configure pesos y notas.',
        'Defina la **extensión del análisis** (visible en QGIS, capa poligonal, manual, puntos + margen o ráster de '
        'referencia) y, en ráster, la **resolución**.',
        'Indique dónde guardar (o déjelo temporal) y haga clic en **Ejecutar**.',
    ],
    'results': [
        ('Mapa de regiones', 'Ráster o capa vectorial con la región de cada punto, cargado con colores y el nombre del '
         'punto.'),
        ('_centros.csv', 'Una fila por punto: identificación, masa, celdas, área (m² y ha) y % del área evaluada.'),
        ('_resumo.txt', 'Modalidad, criterio usado, tamaño de celda, recorte y la misma tabla por punto.'),
    ],
    'hidden': [
        'Empate entre puntos: gana el **primero de la lista** (el orden de la capa), como en el Vista SAGA.',
        '**La nota de fricción 0 se rechaza**; para "casi sin fricción" use un valor pequeño, como 0,1.',
        'NoData en el ráster de fricción, áreas sin polígono y columna vacía **no reciben resultado**, pero se '
        '**atraviesan con nota 1** (costo basal).',
        'El **ráster de referencia** fija la extensión, la resolución y el SRC de la grilla: úselo para hacer coincidir '
        'el resultado con otros rásteres del estudio.',
        'Con extensión de capa poligonal, solo las celdas con el **centro dentro del área** reciben resultado.',
        'La pestaña Vectorial con fricción traza las fronteras con tolerancia de 0,5 m, sin rasterizar.',
    ],
    'pitfalls': [
        'SRC geográfico (grados): use un SRC proyectado en metros, porque distancias y masas dependen de metros.',
        'Masas cero o negativas se rechazan.',
        'Rásteres de fricción antiguos con valor 0 deben revisarse (no se acepta nota 0).',
    ],
}

MODULES['combinacao'] = {
    'title': 'Combinación de mapas',
    'figure': ('combinacao', 'Combinación de mapas: cada asociación de clases recibe un código'),
    'concept': [
        'La Combinación responde a la pregunta **"¿qué asociaciones de clases existen y cuánto ocupan?"**. Cruza dos o '
        'más mapas categóricos y da un **código a cada asociación observada** (por ejemplo, "Agricultura sobre '
        'Argisol"), sin pesos ni notas.',
        'El resultado es el **mapa combinado** y la **tabla de combinaciones**, con el área y el porcentaje de cada una. '
        'Es la base para descubrir patrones antes de una evaluación.',
    ],
    'compare': [
        ('Intersección y Unión vectoriales (QGIS)', 'Cruzan geometrías, pero no codifican las asociaciones ni resuelven '
         'astillas. La Combinación crea los campos **COD_nn/LEG_nn**, tolera astillas de menos de 1 cm e incorpora '
         'residuos de cruce al vecino.'),
        ('r.cross (GRASS)', 'Cruza rásteres, pero la leyenda de las combinaciones sale codificada. Aquí la tabla trae los '
         'nombres de las clases de cada mapa y las áreas.'),
    ],
    'ease': [
        'El orden de la lista es el orden de la combinación, ajustable con Mover hacia arriba/abajo.',
        'Resultado cargado en QGIS ya con colores y leyenda (hasta 75 combinaciones).',
        'Funciona con ráster o vector.',
    ],
    'windows': [('combinacao_raster', 'Combinación de mapas, pestaña Ráster: mapas en orden de combinación'),
                ('combinacao_vetorial', 'Combinación de mapas, pestaña Vectorial: campo de clase y campo de leyenda')],
    'routine': [
        'Elija la pestaña **Ráster** o **Vectorial**.',
        'Agregue **dos o más mapas** (capa seleccionada, varias de QGIS o archivos).',
        'En vector, seleccione cada capa de la lista y verifique el **campo de clase** y el **campo de la leyenda**.',
        'Ajuste el orden con **Mover hacia arriba/abajo**: define el orden de las columnas en la tabla.',
        'Indique dónde guardar (o déjelo temporal) y haga clic en **Ejecutar**.',
    ],
    'results': [
        ('Mapa combinado', 'GeoTIFF o GeoPackage con un código por asociación (vector: campos COD_01/LEG_01, '
         'COD_02/LEG_02…).'),
        ('_combinacoes.csv', 'Una fila por combinación: código, clases de cada mapa, área y porcentaje.'),
        ('_resumo.txt', 'Síntesis, astillas toleradas y residuos incorporados (vector).'),
    ],
    'hidden': [
        'En vector, las superposiciones internas de una misma capa con **ancho medio inferior a 1 cm** se toleran y se '
        'registran en el resumen; por encima de eso, la ejecución se detiene y lista los pares.',
        'Los residuos de cruce finos (menos de 1 cm) se incorporan al vecino de **mayor frontera común**, eliminando '
        'combinaciones falsas sin alterar el área total.',
        'Solo se combina el **área común a todos los mapas** (vector).',
    ],
    'pitfalls': [
        'Muchas clases en muchos mapas generan miles de combinaciones: empiece con pocos mapas.',
        'Rásteres en grillas diferentes no se combinan: alinéelos antes.',
    ],
}

MODULES['conversor'] = {
    'title': 'Conversor de formatos',
    'figure': ('conversor', 'Conversor de formatos: seis conversiones entre RS2, GeoTIFF y vector'),
    'concept': [
        'El Conversor lleva datos entre el formato **RS2** del Vista SAGA, el **GeoTIFF** y el **vector** (GeoPackage, '
        'Shapefile, GeoJSON, FlatGeobuf), en seis operaciones: RS2 → GeoTIFF, GeoTIFF → RS2, RS2 → Vector, GeoTIFF → '
        'Vector, Vector → GeoTIFF y Vector → RS2.',
        'Preserva **códigos, nombres y colores** de las clases, registra el SRC del RS2 en el archivo **.rs2.json** y '
        'permite convertir **varios archivos en lote**.',
    ],
    'compare': [
        ('Rasterizar, Poligonizar y Convertir formato (QGIS/GDAL)', 'No leen ni graban RS2 y no llevan la leyenda de las '
         'clases. El Conversor mantiene códigos, nombres y paleta y graba un estilo **.qml** con las clases reales.'),
        ('Exportación del Vista SAGA', 'El RS2 no guarda el SRC; el Conversor lo registra en el .rs2.json, para que los '
         'demás módulos lo encuentren.'),
    ],
    'ease': [
        'Elija la operación y la ventana muestra solo lo que necesita.',
        '**Propiedades del RS2…** muestra encabezado, leyenda y grilla antes de convertir.',
        'Lote: la misma operación para muchos archivos a la vez.',
    ],
    'windows': [('conversor', 'Conversor de formatos: operación Vector → GeoTIFF'),
                ('conversor_rs2', 'Conversor de formatos: operación RS2 → GeoTIFF, con el SRC del RS2')],
    'routine': [
        'Elija la operación en **Convertir**. Para varios archivos, marque **Procesar varios archivos (lote)**.',
        'Indique el archivo de entrada (o una capa del proyecto). En un RS2, use **Propiedades del RS2…** para verificar '
        'la leyenda y la grilla.',
        'Al rasterizar (Vector → GeoTIFF/RS2), elija el **campo** y el **tamaño del píxel**; para alinear un RS2 a otro, '
        'indique el **RS2 de referencia** en las opciones avanzadas.',
        'Confirme el **SRC** cuando la entrada o la salida sea RS2.',
        'Indique la salida (o deje marcado **Resultado temporal**) y haga clic en **Ejecutar**.',
    ],
    'results': [
        ('GeoTIFF de clases', 'Códigos de las clases, paleta, nombres (en el .aux.xml) y un estilo **<nombre>.qml** que '
         'QGIS carga solo, con únicamente las clases reales en la leyenda.'),
        ('RS2 + .rs2.json', 'Archivo del Vista SAGA y el archivo al lado con SRC, leyenda y correspondencia de códigos.'),
        ('Vector', 'Polígonos con el código y el nombre de la clase (FONDO opcional).'),
    ],
    'hidden': [
        'Al copiar un GeoTIFF de clases a otra carpeta, **lleve también el .aux.xml y el .qml**: allí están los nombres '
        'de las clases y el estilo.',
        'El RS2 exige códigos desde 0 (FONDO); la opción **Códigos del RS2** elige entre preservar y renumerar, y la '
        'correspondencia queda en el .rs2.json.',
        '**ALL_TOUCHED** marca toda celda tocada por una entidad; sin él, solo las celdas con el centro dentro de ella.',
        'Al vectorizar, **8 vecinos** une celdas conectadas por la diagonal; **4 vecinos**, solo por los lados.',
        'A un TIFF RGB antiguo del Vista SAGA se le pueden recuperar las clases con el **RS2 de referencia**.',
    ],
    'pitfalls': [
        'SRC geográfico al rasterizar: el tamaño del píxel queda en grados; use un SRC proyectado.',
        'Salida sobre un archivo existente: el Conversor reemplaza también los archivos auxiliares del mismo nombre.',
    ],
}

MODULES['sequenciador'] = {
    'title': 'Secuenciador de mapas',
    'figure': ('sequenciador', 'Secuenciador de mapas: cuadros en orden se convierten en un GIF animado'),
    'concept': [
        'El Secuenciador responde a la pregunta **"¿cómo mostrar la evolución en el tiempo?"**. Arma una animación '
        '**GIF** (y, si lo desea, los cuadros en **PNG**) a partir de mapas en orden, con fecha, nombre y leyenda sobre '
        'cada cuadro.',
        'Hay tres pestañas: **Ráster** (un ráster por cuadro), **Vectorial** (una capa por cuadro, o cuadros generados '
        'por un campo de fecha) y **Mixto** (un vector sobre un ráster de fondo).',
    ],
    'compare': [
        ('Controlador temporal de QGIS', 'Exporta cuadros, pero el GIF debe armarse aparte. El Secuenciador genera el GIF '
         'directo, con rótulos y leyenda, y acepta cuadros mixtos.'),
        ('Edición manual de imágenes', 'Exige exportar cada mapa y armar la animación en otro programa. Aquí los cuadros '
         'usan la simbología de QGIS y el orden puede ajustarse por fecha.'),
    ],
    'ease': [
        'Los cuadros usan la simbología que usted ya definió en QGIS.',
        'El orden puede ajustarse a mano o por fecha, y la fecha puede editarse.',
        'Las capas de origen no se modifican.',
    ],
    'windows': [('sequenciador', 'Secuenciador de mapas: secuencia de cuadros, dimensiones y salidas')],
    'routine': [
        'Elija la pestaña **Ráster**, **Vectorial** o **Mixto** y agregue los cuadros.',
        'Verifique el orden; use **Editar fecha…** y **Ordenar por fecha** cuando sea necesario.',
        'En **2. Dimensiones y composición**, ajuste el ancho, el alto y la duración de cada cuadro, y lo que se escribe '
        'sobre el mapa (fecha, nombre de las capas, leyenda).',
        'En **3. Salidas y vista previa**, indique el GIF y, si quiere, los PNG. Haga clic en **Ejecutar**.',
    ],
    'results': [
        ('GIF animado', 'La animación con los cuadros en el orden de la lista; la vista previa aparece en la propia '
         'ventana.'),
        ('PNG (opcional)', 'Un PNG por cuadro, a todo color, en una carpeta junto al GIF (o en la elegida).'),
    ],
    'hidden': [
        'El GIF tiene como máximo **256 colores**; las escenas muy coloridas se cuantizan. Para colores exactos, use los '
        '**PNG**.',
        'La leyenda temática aparece hasta con **10 categorías** por cuadro.',
        'La opción **acumulativa** muestra, en cada cuadro, las entidades de los períodos anteriores: ideal para la '
        'expansión urbana.',
        'Los cuadros por campo temporal filtran la capa **sin alterar la capa original ni sus filtros** en el proyecto.',
    ],
    'pitfalls': [
        'Cuadros con extensiones muy diferentes: deje las capas en la misma área antes.',
        'Una duración muy corta deja la animación ilegible; de 800 a 1500 ms por cuadro suele funcionar.',
    ],
}

VALIDATION = {
    'title': 'Validación frente al Vista SAGA original',
    'paras': [
        'Los módulos con resultados numéricos comparables se validaron frente al **Vista SAGA original**, ejecutado en '
        'Windows 7 en una máquina virtual, con los mismos datos de entrada.',
        '**Análisis de Voronoi:** Simple y Con masa reprodujeron el **100% de las celdas**; con fricción, del **99,4% al '
        '99,7%** en la pestaña Ráster y del **99,1% al 99,6%** en la pestaña Vectorial (versión continua), con las '
        'diferencias concentradas en la frontera entre regiones.',
        '**Firma espacial:** mapa entero con **100%** de coincidencia; en las selecciones parciales, las únicas '
        'diferencias son celdas de la clase unidas al resto solo por la diagonal (el balde del Vista SAGA las excluye; '
        'el complemento marca la clase entera).',
        'Los scripts de comparación están en el repositorio (**scripts/comparar_caso_bacia.py** y '
        '**scripts/comparar_assinatura_vista_saga.py**), para quien quiera repetirlos con sus propios datos.',
    ],
    'figure': ('painel', 'Panel de validación y calidad del complemento'),
}

FAQ = {
    'title': 'Solución de problemas',
    'items': [
        ('No encuentro el complemento después de instalarlo.', 'Reinicie QGIS. Si el botón no aparece, active la barra '
         'en Ver > Barras de herramientas > Vista Saga Plugin, o use Ráster > Vista Saga Plugin.'),
        ('El mensaje dice que los mapas están en SRC diferentes.', 'Reproyecte las capas al mismo SRC proyectado '
         '(Vectorial > Herramientas de gestión de datos > Reproyectar capa; Ráster > Proyecciones > Combar).'),
        ('El mensaje dice que los rásteres no están en la misma grilla.', 'Use Ráster > Alinear rásteres, con el mismo '
         'tamaño de celda, extensión y origen.'),
        ('El resultado temporal desapareció.', 'Los temporales desaparecen al cerrar QGIS. Indique un archivo en Guardar '
         'en o exporte la capa antes de cerrar.'),
        ('Las clases aparecen como "Clase 1", "Clase 2".', 'El archivo no tiene nombres grabados. En la Firma espacial, '
         'póngales nombre en la simbología de la capa; en el Conversor, mantenga el .aux.xml y el .qml junto al GeoTIFF.'),
        ('QGIS se volvió lento durante la ejecución.', 'Use Cancelar en la ventana de progreso, reduzca la extensión o '
         'aumente el tamaño de la celda, y ejecute de nuevo.'),
        ('¿Dónde veo detalles de un error inesperado?', 'En Ver > Paneles > Mensajes de registro, pestaña Vista Saga '
         'Plugin: el complemento registra allí el detalle técnico.'),
    ],
}

GLOSSARY = {
    'title': 'Glosario',
    'items': [
        ('Área firmada', 'Área de una clase dentro del límite de la Firma espacial.'),
        ('Fricción', 'Resistencia al desplazamiento usada en el Voronoi; la nota es el costo por unidad de distancia.'),
        ('Criterio', 'Mapa o campo usado en la Evaluación, con un peso.'),
        ('Entidad', 'Un polígono (o punto) de una capa vectorial; en el ráster de la Firma espacial, una clase marcada.'),
        ('FONDO (FUNDO)', 'Clase de fondo del formato RS2.'),
        ('Astilla', 'Superposición o hueco finísimo entre polígonos; tolerada por debajo de 1 cm de ancho medio.'),
        ('Masa', 'Peso de un punto generador en el Voronoi (M en M/d²).'),
        ('NoData', 'Valor "sin dato" de un ráster.'),
        ('RS2', 'Formato ráster del Vista SAGA.'),
        ('SRC', 'Sistema de referencia de coordenadas.'),
        ('Transición', 'Par clase inicial → clase final en el Monitoreo.'),
    ],
}

QUICK = {
    'title': 'Referencia rápida',
    'cols': ['Quiero…', 'Módulo', 'Salida principal'],
    'rows': [
        ('saber de qué está hecha un área', 'Firma espacial', 'TXT y CSV con % área firmada y % categoría'),
        ('ver qué cambió entre dos fechas', 'Monitoreo', 'Mapa de transiciones y matriz'),
        ('encontrar las áreas más adecuadas', 'Evaluación', 'Carta con la media ponderada'),
        ('delimitar áreas de influencia', 'Análisis de Voronoi', 'Mapa de regiones y _centros.csv'),
        ('descubrir asociaciones de clases', 'Combinación de mapas', 'Mapa combinado y _combinacoes.csv'),
        ('llevar datos al/del Vista SAGA', 'Conversor de formatos', 'RS2, GeoTIFF o vector'),
        ('mostrar la evolución en animación', 'Secuenciador de mapas', 'GIF animado y PNG'),
    ],
}
