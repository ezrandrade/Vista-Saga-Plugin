"""Texto do manual do usuário em português do Brasil (Vista Saga Plugin 1.6.0).

Marcação simples: **negrito** dentro dos textos. As tabelas de campos vêm de campos.json (capturadas
nas janelas reais); as figuras, de build_figures.py e capture_windows.py.
"""

LANG = 'pt'
UI = {
    'doc_title': 'Manual do Usuário',
    'subtitle': 'Vista Saga Plugin 1.6.0 para QGIS 4',
    'tagline': 'Geoprocessamento inspirado no Vista SAGA/UFRJ, em sete módulos',
    'author': 'Esdras Andrade (IGDEMA/UFAL)',
    'date': 'Novembro de 2026',
    'toc': 'Sumário',
    'figure': 'Figura',
    'table': 'Tabela',
    'tip': 'Dica',
    'warning': 'Atenção',
    'note': 'Nota',
    'hidden': 'Dicas que só o manual conta',
    'fields_title': 'Campos e botões da janela',
    'fields_cols': ['Seção', 'Elemento', 'Tipo', 'O que faz'],
    'kinds': {'PushButton': 'botão', 'ToolButton': 'botão', 'CheckBox': 'caixa de marcar', 'LineEdit': 'campo de texto',
              'ComboBox': 'lista suspensa', 'MapLayerComboBox': 'camada do QGIS', 'SpinBox': 'campo numérico',
              'DoubleSpinBox': 'campo numérico', 'ListWidget': 'lista'},
    'close_label': 'Fechar (janela auxiliar)',
    'compare_cols': ['Rotina similar', 'O que muda no Vista Saga Plugin'],
    'results_cols': ['Arquivo ou saída', 'Conteúdo e leitura'],
    'routine': 'Rotina de uso correto',
    'concept': 'Para que serve',
    'compare': 'Em que difere de rotinas similares',
    'ease': 'Facilidade de uso',
    'window': 'A janela',
    'results': 'Resultados e como interpretá-los',
    'pitfalls': 'Erros comuns e como evitá-los',
    'footer': 'Vista Saga Plugin 1.6.0 - Manual do Usuário',
    'page': 'Página',
}

INTRO = {
    'title': 'Apresentação',
    'paras': [
        'O **Vista Saga Plugin** é um complemento independente para o **QGIS 4** que reúne, em sete módulos, '
        'procedimentos de análise geográfica inspirados no **Vista SAGA**, o sistema de análise ambiental criado no '
        'Laboratório de Geoprocessamento da UFRJ. O plugin não usa código do programa original: os métodos foram '
        'reimplementados e, nos módulos em que há resultado numérico comparável, **validados contra o Vista SAGA '
        'original**, célula a célula.',
        'O objetivo é permitir que o mesmo raciocínio de análise do Vista SAGA (assinaturas, monitorias, avaliações '
        'por pesos e notas, áreas de influência) seja feito dentro do QGIS, com os dados que você já usa, sem '
        'conversões manuais e com relatórios prontos para planilhas e textos técnicos.',
        'Este manual explica, para cada módulo, **para que ele serve**, **em que difere das rotinas parecidas** do '
        'QGIS e de outros complementos, **cada campo da janela**, a **rotina de uso correto**, **como ler os '
        'resultados** e as **dicas que não aparecem na tela**.',
    ],
    'audience_title': 'Para quem é este manual',
    'audience': [
        'Quem faz diagnóstico ambiental, planejamento urbano ou regional, estudos de bacia e de uso do solo.',
        'Quem já trabalhou com o Vista SAGA e quer reproduzir as mesmas análises no QGIS.',
        'Estudantes e professores de Geografia, Ecologia, Engenharia e áreas afins que precisam de análises '
        'geográficas explicáveis, com relatórios auditáveis.',
    ],
    'principles_title': 'Princípios do plugin',
    'principles': [
        '**Fidelidade de método:** quando há um modelo do Vista SAGA, o plugin o segue e mostra onde difere.',
        '**Nada é feito escondido:** o plugin não reprojeta mapas sem avisar, não supõe notas, não exclui classes '
        'sozinho e não altera os dados de entrada.',
        '**Relatórios auditáveis:** todo resultado vem com um TXT legível e um CSV para planilhas, sempre em '
        'português, independentemente do idioma da interface.',
        '**Uma só lógica de uso:** os sete módulos seguem o mesmo padrão de janela, de botões e de resultado.',
    ],
}

INSTALL = {
    'title': 'Instalação e primeiros passos',
    'steps_title': 'Instalação',
    'steps': [
        'Baixe o arquivo **Vista_Saga_Plugin_QGIS4_v1.6.0.zip** (o ZIP de instalação, não o código-fonte do GitHub).',
        'No QGIS 4, abra **Complementos > Gerenciar e instalar complementos > Instalar a partir de ZIP**.',
        'Escolha o ZIP, clique em **Instalar complemento** e reinicie o QGIS.',
        'O botão **Vista Saga Plugin** aparece na barra de ferramentas própria; ao clicar, abre-se o menu com os sete '
        'módulos. Os módulos também ficam em **Raster > Vista Saga Plugin**.',
    ],
    'warning': 'A pasta instalada chama-se **geosaga** de propósito. Não a renomeie: modelos e projetos antigos '
               'dependem desse nome e dos identificadores de processamento **geosaga:***.',
    'common_title': 'O que é igual em todos os módulos',
    'common': [
        '**Idioma:** a interface segue o idioma do QGIS (português, inglês ou espanhol; nos demais, inglês). Os '
        'relatórios CSV e TXT são sempre gravados em português.',
        '**Dicas:** pare o mouse sobre qualquer botão, campo, caixa de marcar ou lista para ver uma caixa amarela que '
        'explica o que ele faz.',
        '**Rodapé padrão:** **[Executar]** e **[Fechar]** em todas as janelas; a Avaliação tem também **[Validar]**.',
        '**Janela não modal:** a janela do módulo pode ficar aberta enquanto você trabalha no mapa do QGIS '
        '(selecionar feições, mudar estilos, abrir camadas).',
        '**Progresso:** durante a execução aparece uma janela de progresso com **Cancelar**; o desfecho (concluído, '
        'cancelado) aparece na barra de mensagens do QGIS.',
        '**Resultado temporário ou salvo:** o campo **Salvar em** vazio gera um resultado temporário, chamado '
        '"Módulo - operação" (por exemplo, "Análises Voronoi - Com Atrito"); preenchido, o resultado é salvo no '
        'arquivo escolhido e carregado com o nome desse arquivo.',
        '**Dados de entrada intactos:** nenhum módulo altera as camadas de entrada.',
    ],
    'temp_warning': 'Resultados temporários ficam na pasta temporária do QGIS e **somem quando o QGIS é fechado**. '
                    'Salve-os (botão direito na camada > Exportar) antes de encerrar, ou indique um arquivo em '
                    '**Salvar em** desde o início.',
    'tooltip_fig': 'As dicas (caixas amarelas) explicam cada elemento da janela',
}

CONCEPTS = {
    'title': 'Conceitos usados em todo o manual',
    'items': [
        ('Mapa categórico (temático)', 'Mapa em que cada célula ou polígono pertence a uma **classe** (uso do solo, '
         'tipo de solo, bairro). É o tipo de mapa que a maioria dos módulos usa. Valores contínuos (altitude, '
         'temperatura) precisam ser classificados antes.'),
        ('Classe, código e legenda', 'Cada classe tem um **código** (um número inteiro, no raster; um valor de campo, '
         'no vetor) e um **nome** (a legenda). O plugin lê os nomes do arquivo (legenda do RS2, nomes de categorias '
         'do GeoTIFF, arquivo .rs2.json) ou, na Assinatura, do estilo da camada no QGIS.'),
        ('FUNDO e NoData', 'O **FUNDO** é a classe de fundo do formato RS2 (em geral, código 0). O **NoData** é o '
         'valor "sem dado" de um GeoTIFF. Cada módulo diz como os trata; na Assinatura, por exemplo, ambos contam '
         'como classe, como no Vista SAGA.'),
        ('SRC (sistema de referência)', 'Define as coordenadas do mapa. Para medir áreas e distâncias, use um **SRC '
         'projetado em metros** (por exemplo, UTM SIRGAS 2000). O plugin **não reprojeta sem avisar**: mapas '
         'analisados em conjunto devem estar no mesmo SRC.'),
        ('Grade (raster)', 'Tamanho da célula, extensão e alinhamento de um raster. Módulos que comparam rasters '
         'célula a célula exigem **a mesma grade** em todos os mapas.'),
        ('RS2', 'Formato raster do Vista SAGA (um arquivo .rs2). Não guarda o SRC: o plugin o registra num arquivo '
         'ao lado (**.rs2.json**) ou pede que você o confirme. O Conversor de Formatos leva dados entre RS2, GeoTIFF '
         'e vetor.'),
        ('Lasca (sliver)', 'Sobreposição ou fresta muito fina entre polígonos vizinhos, causada por imprecisão de '
         'coordenadas. Na Combinação e na Assinatura vetoriais, lascas com **largura média menor que 1 cm** são '
         'toleradas e registradas no relatório.'),
    ],
}

MODULES = {}

MODULES['assinatura'] = {
    'title': 'Assinatura',
    'figure': ('assinatura', 'Assinatura: a seleção no mapa de referência recorta todos os mapas da lista'),
    'concept': [
        'A Assinatura responde à pergunta **"do que é feita esta área?"**. Você escolhe um **mapa de referência** '
        '(por exemplo, bairros), seleciona nele uma ou mais classes ou feições (por exemplo, dois bairros) e o plugin '
        'mede, **dentro desse limite**, quanto cada classe de cada mapa da lista ocupa: uso do solo, solos, '
        'escolaridade, declividade.',
        'É o modelo do Vista SAGA: a referência fica no topo da lista, a seleção nela define o limite e **todos os '
        'mapas são assinados, inclusive a referência**. O resultado sai da **união** da seleção e, se você quiser, '
        '**por feição** (um bloco para cada bairro selecionado).',
        'Para cada classe, o relatório traz a área no mapa inteiro, a área dentro do limite e duas porcentagens: a '
        '**% Área asn.** (do que o lugar é feito) e a **% Categoria** (quanto da classe se concentra ali).',
    ],
    'compare': [
        ('Estatísticas zonais e Histograma zonal (Processamento do QGIS)', 'Contam pixels de um raster por polígono. '
         'A Assinatura assina **vários mapas de uma vez**, usa a **seleção** no mapa de referência como limite, '
         'calcula a **união** e cada feição e entrega as duas porcentagens do Vista SAGA prontas.'),
        ('Interseção vetorial seguida de tabela dinâmica', 'Exige vários passos manuais e não resolve sobreposições. '
         'A guia Vetorial faz a interseção exata, **dissolve** polígonos da mesma classe, separa a **sobreposição** '
         'entre classes e mostra o que ficou **sem classe**.'),
        ('Assinatura do Vista SAGA original', 'Mesmas colunas e mesma lógica. A seleção é por **classe inteira** '
         '(o balde do Vista SAGA marca a região contínua); a área e os nomes das classes podem vir do QGIS; os '
         'relatórios saem em TXT e CSV.'),
    ],
    'ease': [
        'A ordem da lista diz tudo: **o primeiro mapa é a referência**.',
        'No raster, basta marcar as classes; "Marcar todas" equivale a "Assinar o mapa inteiro".',
        'No vetor, a seleção é a do próprio QGIS, com o botão **Selecionar no mapa**.',
        'A guia **Resultados** mostra a tabela e permite trocar entre a união e cada feição.',
    ],
    'windows': [('assinatura_raster', 'Assinatura, guia Raster: mapas, classes da referência, opções e resultado'),
                ('assinatura_vetorial', 'Assinatura, guia Vetorial: campos de classe e seleção feita no mapa do QGIS'),
                ('assinatura_resultados', 'Assinatura, guia Resultados: recorte (união ou feição) e tabela')],
    'routine': [
        'Escolha a guia **Raster** ou **Vetorial** (não se misturam formatos: raster só com raster, vetor só com vetor).',
        'Em **1. Mapas**, acrescente os mapas. O **primeiro da lista é a referência**; use **Mover para cima/baixo** '
        'para trocar a ordem. Todos devem estar no **mesmo SRC, projetado em metros**; no raster, também na **mesma '
        'grade**. Um RS2 sem .rs2.json pede o SRC ao ser acrescentado.',
        'No vetor, selecione cada mapa da lista e confira o **Campo de classe** e o **Campo da legenda**.',
        'Em **2. Seleção na referência**: no raster, marque as classes; no vetor, clique em **Selecionar no mapa** e '
        'clique nas feições no mapa do QGIS (Ctrl+clique acrescenta ou retira). O contador mostra quantas estão '
        'selecionadas.',
        'Em **3. Opções**, deixe **Resultado por feição** ligado se quiser um bloco para cada feição; no vetor, '
        'escolha o tratamento da sobreposição entre classes.',
        'Em **4. Resultado**, dê um título (opcional) e escolha onde salvar o CSV (o TXT vai ao lado). Clique em '
        '**Executar**.',
        'Confira a guia **Resultados** e abra o TXT para a leitura completa.',
    ],
    'results': [
        ('Relatório TXT', 'Cabeçalho com mapas, SRC, seleção, método e avisos; depois um bloco da **união da '
         'seleção** e um bloco para cada feição (ou classe, no raster). Cada bloco tem uma tabela por mapa.'),
        ('Relatório CSV', 'Uma linha por recorte, mapa e classe. Colunas: RECORTE (UNIAO ou FEICAO), ID_FEICAO, '
         'NOME_FEICAO, MAPA, CODIGO, CLASSE, TOTAL_PIXELS, TOTAL_HA, PIXELS_ASN, AREA_ASN_HA, PCT_AREA_ASN, '
         'PCT_CATEGORIA. Separador ";" e UTF-8: abre direto no Excel ou LibreOffice.'),
        ('% Área asn.', 'Área da classe no limite ÷ área do limite. **Caracteriza o lugar**; soma 100% em cada mapa.'),
        ('% Categoria', 'Área da classe no limite ÷ área da classe no mapa inteiro. **Mede concentração**; não soma '
         '100% e não deve ser somada.'),
        ('Linhas especiais', 'FUNDO e NoData contam como classe. No vetor: **Sem classe** (parte do limite sem '
         'polígono no mapa) e **Sobreposição excluída** (região com classes diferentes sobrepostas).'),
    ],
    'hidden': [
        'A tabela da própria referência sempre mostra 100% nas classes selecionadas: ela serve para **conferir o '
        'tamanho exato do limite**, que é a base de todos os outros mapas.',
        'Os nomes das classes de um raster vêm do **estilo da camada no QGIS** (simbologia Paletado/Valores únicos) '
        'quando o mapa foi acrescentado a partir do projeto: renomeie as classes na simbologia e rode de novo.',
        'Com muitas feições selecionadas, **desligue "Resultado por feição"**: o TXT fica enorme e a união continua '
        'disponível.',
        '**Não some os blocos por feição** para obter a união: se duas feições se sobrepõem, a união conta a área comum '
        'uma vez só. Use o bloco da união.',
        'No CSV, filtre a coluna **RECORTE** e monte tabelas dinâmicas por MAPA e CLASSE.',
        'A seção **Tolerância de lascas** do TXT (vetor) mostra frestas e sobreposições menores que 1 cm: servem para '
        'auditoria, não para interpretação.',
        'Raster e vetor dão números um pouco diferentes (célula × polígono exato). Para comparar lugares ou datas, use '
        'sempre o mesmo formato e a mesma grade.',
    ],
    'pitfalls': [
        '**"O mapa X está em outro SRC":** reprojete antes, no QGIS (o plugin não reprojeta).',
        '**"O mapa X não está na mesma grade":** alinhe os rasters antes (mesma célula, extensão e origem).',
        '**"Nenhuma feição selecionada":** use **Selecionar no mapa** e clique nas feições, ou **Selecionar todas**. '
        'A ferramenta de seleção do QGIS age sobre a camada ativa; o botão já torna a referência ativa.',
        'Classes aparecendo como "Classe 7": o arquivo não tem nomes gravados; dê nomes na simbologia do QGIS.',
    ],
}

MODULES['monitoria'] = {
    'title': 'Monitoria',
    'figure': ('monitoria', 'Monitoria: dois períodos, o mapa de transições e a matriz de transição'),
    'concept': [
        'A Monitoria responde à pergunta **"o que mudou entre dois períodos?"**. Ela compara um mapa inicial e um mapa '
        'final da mesma área e identifica, para cada célula (raster) ou porção de polígono (vetor), se a classe '
        '**permaneceu** ou **mudou** e para qual classe.',
        'O resultado é um **mapa de transições**, uma **tabela de transições** e uma **matriz de transição** (classe '
        'inicial nas linhas, classe final nas colunas), com áreas e porcentagens.',
    ],
    'compare': [
        ('Calculadora raster e tabelas cruzadas montadas à mão', 'Exigem codificar as transições e contar à parte. A '
         'Monitoria gera o mapa, a tabela e a matriz numa execução, com legenda descritiva ("Permaneceu", "Deixou de '
         'ser … → Tornou-se …").'),
        ('Ferramentas de mudança de complementos de classificação', 'Costumam trabalhar só com raster. A Monitoria tem '
         'também a guia **Vetorial**, que compara polígonos por sobreposição exata, em hectares.'),
        ('Monitoria do Vista SAGA', 'Mesmo raciocínio de mapa de transições e matriz; aqui com legenda em palavras '
         'ou por códigos, tabela copiável e resultado carregado no QGIS.'),
    ],
    'ease': [
        'Dois mapas, dois períodos, um botão: o mapa de transições é carregado já com cores e legenda.',
        'Permanências em cinza e mudanças em cores distintas, para leitura imediata.',
        'Tabelas da guia Resultados copiáveis para planilhas (Ctrl+A, Ctrl+C).',
    ],
    'windows': [('monitoria_raster', 'Monitoria, guia Raster: mapa inicial, mapa final e resultado'),
                ('monitoria_vetorial', 'Monitoria, guia Vetorial: camadas, campos de classe e período')],
    'routine': [
        'Escolha a guia **Raster** (mapas categóricos na mesma grade) ou **Vetorial** (camadas de polígonos).',
        'Indique o **mapa inicial** e o **mapa final** (camada do QGIS ou arquivo) e o nome de cada **período** '
        '(por exemplo, o ano).',
        'No vetor, escolha o **campo de classe** de cada período e, se houver, o **campo de legenda**.',
        'Dê um **título** e, se quiser, indique onde salvar. No raster, abra **Opções avançadas: legenda** para '
        'escolher legenda em palavras ou por códigos e, se quiser, uma tabela CSV com os nomes das classes.',
        'Clique em **Executar** e confira o mapa de transições e a guia **Resultados**.',
    ],
    'results': [
        ('Mapa de transições', 'GeoTIFF (raster) ou GeoPackage (vetor) com um código por transição, carregado com '
         'legenda: permanências em cinza, mudanças em cores.'),
        ('_transicoes.csv', 'Uma linha por transição: classe inicial, classe final, situação (permanência ou '
         'mudança), área (células ou ha) e porcentagem.'),
        ('_matriz.csv', 'Matriz de transição: linhas = classe inicial, colunas = classe final. A diagonal são as '
         'permanências; fora dela, as mudanças.'),
        ('_resumo.txt', 'Síntese: área total, área avaliada, permanências e mudanças principais.'),
    ],
    'hidden': [
        'Na guia Vetorial, **só a área comum às duas camadas** é comparada: confira se os dois períodos cobrem a mesma '
        'área e usam classes equivalentes.',
        'A tabela de nomes das classes (raster) usa o formato **PERIODO;CODIGO;CLASSE**: útil quando os rasters não '
        'têm nomes gravados ou quando as classes mudaram de nome entre os períodos.',
        'A leitura da matriz é mais rápida pelas **linhas**: cada linha mostra para onde foi cada classe do período '
        'inicial.',
        'Quando o campo de arquivo está preenchido, ele tem **prioridade** sobre a camada escolhida na lista.',
    ],
    'pitfalls': [
        'Rasters com grades diferentes: alinhe antes.',
        'Classes com códigos diferentes entre os períodos (por exemplo, 3 = Água num e 3 = Mata no outro) geram '
        'mudanças falsas: padronize a legenda antes.',
        'Mann–Kendall (tendência em séries longas) saiu da Monitoria e voltará como módulo próprio na versão 2.0.',
    ],
}

MODULES['avaliacao'] = {
    'title': 'Avaliação',
    'figure': ('avaliacao', 'Avaliação: notas por classe, pesos por critério e a média ponderada'),
    'concept': [
        'A Avaliação responde à pergunta **"onde é mais adequado (ou mais crítico)?"**. É a avaliação multicritério do '
        'Vista SAGA: cada mapa é um **critério** com um **peso** (em %), e cada classe recebe uma **nota** (de 0 a 10 '
        'ou de 0 a 100). O resultado é a **média ponderada** das notas em cada lugar.',
        'Há três guias com o mesmo leiaute: **Raster** (mapas categóricos na mesma grade), **Vetorial (Atributos)** '
        '(vários campos de uma mesma camada de polígonos) e **Vetorial (Sobreposição)** (várias camadas de polígonos '
        'cruzadas; só a área comum a todas é avaliada).',
    ],
    'compare': [
        ('Calculadora raster com reclassificação', 'Exige reclassificar cada mapa e escrever a fórmula à mão. A '
         'Avaliação monta a média ponderada com tabelas de notas e pesos, e **bloqueia a execução** enquanto houver '
         'classe sem nota.'),
        ('Sobreposição ponderada de outros programas', 'Normalmente só em raster. Aqui há guias vetoriais que '
         '**preservam a geometria** das feições (Atributos) ou cruzam camadas (Sobreposição).'),
        ('Avaliação do Vista SAGA', 'Mesmo método de pesos e notas, com arredondamento "meio para par" como no '
         'original; os pesos e as notas usados são gravados num arquivo de projeto reaproveitável.'),
    ],
    'ease': [
        'Classes sem nota ficam **destacadas** e contadas; **Validar** lista todas as pendências.',
        'A tecla **Tab** salta de peso em peso e de nota em nota.',
        'Clique no cabeçalho da tabela de classes para ordenar.',
        'Cada execução grava os pesos e as notas para reabrir depois.',
    ],
    'windows': [('avaliacao_raster', 'Avaliação, guia Raster: mapas e pesos, classes e notas, resultado'),
                ('avaliacao_atributos', 'Avaliação, guia Vetorial (Atributos): campos de uma camada como critérios'),
                ('avaliacao_sobreposicao', 'Avaliação, guia Vetorial (Sobreposição): camadas empilhadas')],
    'routine': [
        'Escolha a guia conforme os dados: **Raster**, **Vetorial (Atributos)** ou **Vetorial (Sobreposição)**.',
        'Escolha a **escala das notas** (0 a 10 ou 0 a 100).',
        'Acrescente os critérios (mapas, campos ou camadas) e digite o **peso** de cada um. Os pesos novos entram em '
        'branco; **Distribuir pesos igualmente** divide 100% entre todos.',
        'Selecione um critério e dê **nota** a cada classe. Para várias classes com a mesma nota, selecione-as e use '
        '**Aplicar**. Marque **Não avaliar** nas classes que devem ficar de fora.',
        'Clique em **Validar** para ver o que falta. Corrija até não haver pendências.',
        'Em **3. Resultado**, indique onde salvar (ou deixe temporário) e mantenha os relatórios CSV e TXT marcados. '
        'Clique em **Executar**.',
    ],
    'results': [
        ('Carta de avaliação', 'GeoTIFF (Raster) ou GeoPackage (vetoriais) com a nota final de cada lugar.'),
        ('_relatorio.csv', 'Combinações de classes encontradas, notas, nota final e áreas.'),
        ('_relatorio.txt', 'Relatório no modelo do Vista SAGA: critérios, pesos, notas e distribuição do resultado.'),
        ('*_pesos_notas.geosaga.json', 'Os pesos e as notas usados, para reabrir em **Abrir projeto…** e repetir ou '
         'ajustar a avaliação.'),
    ],
    'hidden': [
        'A nota **"—"** significa "sem nota" e **impede a execução**: o plugin nunca supõe nota 0 nem exclui classes '
        'sozinho.',
        '**Não avaliar** faz a classe virar NoData no resultado; use para áreas que não devem ser classificadas (por '
        'exemplo, corpos d\'água).',
        'Os pesos novos entram **em branco** de propósito: a divisão igual só acontece pelo botão.',
        'O arquivo de projeto guarda caminhos relativos à pasta dele: dá para mover a pasta inteira do estudo.',
        'Na guia Sobreposição, **só a área comum a todas as camadas** é avaliada; confira a cobertura antes.',
        'As tabelas aceitam Ctrl+A e Ctrl+C para copiar para planilhas, com o separador decimal do idioma.',
    ],
    'pitfalls': [
        'Pesos que não somam 100%: o rodapé da tabela mostra quanto falta.',
        'Rasters em grades diferentes não são aceitos na guia Raster.',
        'Notas pensadas em 0 a 100 digitadas com a escala 0 a 10: escolha a escala antes de dar as notas.',
    ],
}

MODULES['voronoi'] = {
    'title': 'Análises Voronoi',
    'figure': ('voronoi', 'Análises Voronoi: as quatro modalidades calculadas pelo próprio plugin'),
    'concept': [
        'As Análises Voronoi respondem à pergunta **"qual é a área de influência de cada ponto?"**. A partir de pontos '
        'geradores (escolas, postos de saúde, sedes), cada lugar é atribuído ao ponto que mais o "atrai".',
        'Há quatro modalidades, todas no modelo do Vista SAGA e validadas contra ele: **Simples** (menor distância), '
        '**Com Massa** (maior M/d², em que M é a massa do ponto), **Com Atrito** (menor custo acumulado pela reta '
        'entre o ponto e o lugar, numa superfície de atrito) e **Com Massa e Atrito** (menor custo ÷ M).',
        'O custo com atrito é a soma, nas células da reta entre o ponto e o lugar, de **distância ao ponto × nota de '
        'atrito × passo**. A nota é o próprio custo (nota 1 = custo basal). Não é caminho de custo mínimo: a reta não '
        'desvia de obstáculos, ela os "paga".',
    ],
    'compare': [
        ('Polígonos de Voronoi (Processamento do QGIS)', 'Fazem só a modalidade Simples, em vetor. O plugin tem '
         '**massa**, **atrito** (raster ou polígonos), combinação de várias superfícies e saída raster ou vetorial.'),
        ('Distância de custo (r.cost e similares)', 'Calculam o **caminho de menor custo**, que contorna obstáculos. '
         'O modelo do Vista SAGA usa a **reta** entre o ponto e o lugar; os resultados são diferentes e o plugin '
         'reproduz o do Vista SAGA.'),
        ('Voronoi do Vista SAGA', 'Mesmo método (Simples e Com Massa 100% iguais; atrito 99,4% a 99,7% das células). '
         'Acrescenta a superfície de atrito vetorial e a saída vetorial exata.'),
    ],
    'ease': [
        'Escolha a modalidade e o plugin mostra só os campos necessários.',
        'Guias Raster e Vetorial com os mesmos dados de entrada.',
        'Massa como M/d²: uma massa 9 alcança 3 vezes mais longe que uma massa 1, e não 9 vezes.',
    ],
    'windows': [('voronoi_raster', 'Análises Voronoi, guia Raster: modalidade, dados de entrada e resultado'),
                ('voronoi_vetorial', 'Análises Voronoi, guia Vetorial')],
    'routine': [
        'Escolha a guia **Raster** (grade de células) ou **Vetorial** (polígonos de fronteira exata).',
        'Escolha a **modalidade**.',
        'Indique a camada de **pontos geradores**, o campo de **identificação** e, nas modalidades com massa, o '
        '**campo de massa** (positivo).',
        'Com atrito, escolha o **tipo de superfície**: raster (nota em cada célula) ou polígonos (nota numa coluna); '
        'para várias superfícies, marque **Combinar múltiplas superfícies** e configure pesos e notas.',
        'Defina a **extensão da análise** (visível no QGIS, camada poligonal, manual, pontos + margem ou raster de '
        'referência) e, no raster, a **resolução**.',
        'Indique onde salvar (ou deixe temporário) e clique em **Executar**.',
    ],
    'results': [
        ('Mapa de regiões', 'Raster ou camada vetorial com a região de cada ponto, carregado com cores e o nome do '
         'ponto.'),
        ('_centros.csv', 'Uma linha por ponto: identificação, massa, células, área (m² e ha) e % da área avaliada.'),
        ('_resumo.txt', 'Modalidade, critério usado, tamanho da célula, recorte e a mesma tabela por ponto.'),
    ],
    'hidden': [
        'Empate entre pontos: vence o **primeiro da lista** (a ordem da camada), como no Vista SAGA.',
        '**Nota de atrito 0 é recusada**; para "quase sem atrito" use um valor pequeno, como 0,1.',
        'NoData no raster de atrito, área sem polígono e coluna vazia **não recebem resultado**, mas são '
        '**atravessados com nota 1** (custo basal).',
        'O **raster de referência** fixa a extensão, a resolução e o SRC da grade: use-o para casar o resultado com '
        'outros rasters do estudo.',
        'Com extensão de camada poligonal, só as células com o **centro dentro da área** recebem resultado.',
        'A guia Vetorial com atrito traça as fronteiras com tolerância de 0,5 m, sem rasterizar.',
    ],
    'pitfalls': [
        'SRC geográfico (graus): use SRC projetado em metros, porque distâncias e massas dependem de metros.',
        'Massas zero ou negativas são recusadas.',
        'Rasters de atrito antigos com valor 0 precisam ser revistos (nota 0 não é aceita).',
    ],
}

MODULES['combinacao'] = {
    'title': 'Combinação de Mapas',
    'figure': ('combinacao', 'Combinação de Mapas: cada associação de classes recebe um código'),
    'concept': [
        'A Combinação responde à pergunta **"que associações de classes existem e quanto ocupam?"**. Ela cruza dois '
        'ou mais mapas categóricos e dá um **código a cada associação observada** (por exemplo, "Agricultura sobre '
        'Argissolo"), sem pesos nem notas.',
        'O resultado é o **mapa combinado** e a **tabela de combinações**, com área e porcentagem de cada uma. É a '
        'base para descobrir padrões antes de uma avaliação.',
    ],
    'compare': [
        ('Interseção e União vetoriais (QGIS)', 'Cruzam geometrias, mas não codificam as associações nem resolvem '
         'lascas. A Combinação cria os campos **COD_nn/LEG_nn**, tolera lascas de menos de 1 cm e incorpora resíduos '
         'de cruzamento ao vizinho.'),
        ('r.cross (GRASS)', 'Cruza rasters, mas a legenda das combinações sai codificada. Aqui a tabela traz os nomes '
         'das classes de cada mapa e as áreas.'),
    ],
    'ease': [
        'A ordem da lista é a ordem da combinação, e os botões Mover para cima/baixo a ajustam.',
        'Resultado carregado no QGIS já com cores e legenda (até 75 combinações).',
        'Funciona com raster ou vetor.',
    ],
    'windows': [('combinacao_raster', 'Combinação de Mapas, guia Raster: mapas em ordem de combinação'),
                ('combinacao_vetorial', 'Combinação de Mapas, guia Vetorial: campo de classe e campo de legenda')],
    'routine': [
        'Escolha a guia **Raster** ou **Vetorial**.',
        'Acrescente **dois ou mais mapas** (camada selecionada, várias do QGIS ou arquivos).',
        'No vetor, selecione cada camada da lista e confira o **campo de classe** e o **campo da legenda**.',
        'Ajuste a ordem com **Mover para cima/baixo**: ela define a ordem das colunas na tabela.',
        'Indique onde salvar (ou deixe temporário) e clique em **Executar**.',
    ],
    'results': [
        ('Mapa combinado', 'GeoTIFF ou GeoPackage com um código por associação (vetor: campos COD_01/LEG_01, '
         'COD_02/LEG_02…).'),
        ('_combinacoes.csv', 'Uma linha por combinação: código, classes de cada mapa, área e porcentagem.'),
        ('_resumo.txt', 'Síntese, lascas toleradas e resíduos incorporados (vetor).'),
    ],
    'hidden': [
        'No vetor, sobreposições internas de uma mesma camada com **largura média abaixo de 1 cm** são toleradas e '
        'registradas no resumo; acima disso, a execução para e lista os pares.',
        'Resíduos de cruzamento finos (abaixo de 1 cm) são incorporados ao vizinho de **maior fronteira comum**, '
        'eliminando combinações falsas sem alterar a área total.',
        'Só a **área comum a todos os mapas** é combinada (vetor).',
    ],
    'pitfalls': [
        'Muitas classes em muitos mapas geram milhares de combinações: comece com poucos mapas.',
        'Rasters em grades diferentes não são combinados: alinhe antes.',
    ],
}

MODULES['conversor'] = {
    'title': 'Conversor de Formatos',
    'figure': ('conversor', 'Conversor de Formatos: seis conversões entre RS2, GeoTIFF e vetor'),
    'concept': [
        'O Conversor leva dados entre o formato **RS2** do Vista SAGA, o **GeoTIFF** e o **vetor** (GeoPackage, '
        'Shapefile, GeoJSON, FlatGeobuf), em seis operações: RS2 → GeoTIFF, GeoTIFF → RS2, RS2 → Vetor, GeoTIFF → '
        'Vetor, Vetor → GeoTIFF e Vetor → RS2.',
        'Ele preserva **códigos, nomes e cores** das classes, registra o SRC do RS2 no arquivo **.rs2.json** e '
        'permite converter **vários arquivos em lote**.',
    ],
    'compare': [
        ('Rasterizar, Poligonizar e Converter formato (QGIS/GDAL)', 'Não leem nem gravam RS2 e não levam a legenda das '
         'classes. O Conversor mantém códigos, nomes e paleta e grava um estilo **.qml** com as classes reais.'),
        ('Exportação do Vista SAGA', 'O RS2 não guarda SRC; o Conversor o registra no .rs2.json, para que os outros '
         'módulos o encontrem.'),
    ],
    'ease': [
        'Escolha a operação e a janela mostra só o que ela precisa.',
        '**Propriedades RS2…** mostra cabeçalho, legenda e grade antes de converter.',
        'Lote: mesma operação para muitos arquivos de uma vez.',
    ],
    'windows': [('conversor', 'Conversor de Formatos: operação Vetor → GeoTIFF'),
                ('conversor_rs2', 'Conversor de Formatos: operação RS2 → GeoTIFF, com o SRC do RS2')],
    'routine': [
        'Escolha a operação em **Converter**. Para vários arquivos, marque **Processar vários arquivos (lote)**.',
        'Indique o arquivo de entrada (ou uma camada do projeto). Num RS2, use **Propriedades RS2…** para conferir a '
        'legenda e a grade.',
        'Na rasterização (Vetor → GeoTIFF/RS2), escolha o **campo** e o **tamanho do pixel**; para alinhar um RS2 a '
        'outro, indique o **RS2 de referência** nas opções avançadas.',
        'Confirme o **SRC** quando a entrada ou a saída for RS2.',
        'Indique a saída (ou deixe **Resultado temporário** marcado) e clique em **Executar**.',
    ],
    'results': [
        ('GeoTIFF de classes', 'Códigos das classes, paleta, nomes (no .aux.xml) e um estilo **<nome>.qml** que o QGIS '
         'carrega sozinho, com só as classes reais na legenda.'),
        ('RS2 + .rs2.json', 'Arquivo do Vista SAGA e o arquivo ao lado com SRC, legenda e correspondência de códigos.'),
        ('Vetor', 'Polígonos com o código e o nome da classe (FUNDO opcional).'),
    ],
    'hidden': [
        'Ao copiar um GeoTIFF de classes para outra pasta, **leve junto o .aux.xml e o .qml**: é neles que ficam os '
        'nomes das classes e o estilo.',
        'O RS2 exige códigos de 0 (FUNDO) em diante; o modo **Códigos RS2** escolhe entre preservar e renumerar, e a '
        'correspondência fica no .rs2.json.',
        '**ALL_TOUCHED** marca toda célula tocada por uma feição; sem ele, só as células com o centro dentro dela.',
        'Na vetorização, **8 vizinhos** junta células ligadas pela diagonal; **4 vizinhos**, só pelos lados.',
        'Um TIFF RGB antigo do Vista SAGA pode ter as classes recuperadas com o **RS2 de referência**.',
    ],
    'pitfalls': [
        'SRC geográfico na rasterização: o tamanho do pixel fica em graus; use SRC projetado.',
        'Saída por cima de um arquivo existente: o Conversor substitui também os arquivos auxiliares do mesmo nome.',
    ],
}

MODULES['sequenciador'] = {
    'title': 'Sequenciador de Mapas',
    'figure': ('sequenciador', 'Sequenciador de Mapas: quadros em ordem viram um GIF animado'),
    'concept': [
        'O Sequenciador responde à pergunta **"como mostrar a evolução no tempo?"**. Ele monta uma animação **GIF** (e, '
        'se você quiser, os quadros em **PNG**) a partir de mapas em ordem, com data, nome e legenda sobre cada quadro.',
        'Há três guias: **Raster** (um raster por quadro), **Vetorial** (uma camada por quadro ou quadros gerados por '
        'um campo de data) e **Misto** (um vetor sobre um raster de fundo).',
    ],
    'compare': [
        ('Controlador temporal do QGIS', 'Exporta quadros, mas o GIF precisa ser montado fora. O Sequenciador gera o '
         'GIF direto, com rótulos e legenda, e aceita quadros mistos.'),
        ('Edição manual de imagens', 'Exige exportar cada mapa e montar a animação noutro programa. Aqui os quadros '
         'usam a simbologia do QGIS e a ordem pode ser ajustada por data.'),
    ],
    'ease': [
        'Os quadros usam a simbologia que você já definiu no QGIS.',
        'A ordem pode ser ajustada à mão ou por data, e a data pode ser editada.',
        'As camadas de origem não são alteradas.',
    ],
    'windows': [('sequenciador', 'Sequenciador de Mapas: sequência de quadros, dimensões e saídas')],
    'routine': [
        'Escolha a guia **Raster**, **Vetorial** ou **Misto** e acrescente os quadros.',
        'Confira a ordem; use **Editar data…** e **Ordenar por data** quando necessário.',
        'Em **2. Dimensões e composição**, ajuste largura, altura e duração de cada quadro, e o que escrever sobre o '
        'mapa (data, nome das camadas, legenda).',
        'Em **3. Saídas e prévia**, indique o GIF e, se quiser, os PNGs. Clique em **Executar**.',
    ],
    'results': [
        ('GIF animado', 'A animação com os quadros na ordem da lista; a prévia aparece na própria janela.'),
        ('PNGs (opcional)', 'Um PNG por quadro, com cores completas, numa pasta ao lado do GIF (ou na escolhida).'),
    ],
    'hidden': [
        'O GIF tem no máximo **256 cores**; cenas muito coloridas são quantizadas. Para cores exatas, use os **PNGs**.',
        'A legenda temática aparece até **10 categorias** por quadro.',
        'A opção **acumulativa** mostra, em cada quadro, as feições dos períodos anteriores: ideal para expansão '
        'urbana.',
        'Os quadros por campo temporal filtram a camada **sem alterar a camada original nem os filtros dela** no '
        'projeto.',
    ],
    'pitfalls': [
        'Quadros com extensões muito diferentes: deixe as camadas na mesma área antes.',
        'Duração muito curta deixa a animação ilegível; 800 a 1500 ms por quadro costuma funcionar.',
    ],
}

VALIDATION = {
    'title': 'Validação contra o Vista SAGA original',
    'paras': [
        'Os módulos com resultado numérico comparável foram validados contra o **Vista SAGA original**, executado em '
        'Windows 7 numa máquina virtual, com os mesmos dados de entrada.',
        '**Análises Voronoi:** Simples e Com Massa reproduziram **100% das células**; com atrito, **99,4% a 99,7%** na '
        'guia Raster e **99,1% a 99,6%** na guia Vetorial (versão contínua), com as diferenças concentradas na '
        'fronteira entre regiões.',
        '**Assinatura:** mapa inteiro com **100%** de coincidência; nas seleções parciais, as únicas diferenças são '
        'células da classe ligadas ao resto só pela diagonal (o balde do Vista SAGA as exclui; o plugin marca a classe '
        'inteira).',
        'Os scripts de comparação estão no repositório (**scripts/comparar_caso_bacia.py** e '
        '**scripts/comparar_assinatura_vista_saga.py**), para quem quiser repetir com os próprios dados.',
    ],
    'figure': ('painel', 'Painel de validação e qualidade do plugin'),
}

FAQ = {
    'title': 'Solução de problemas',
    'items': [
        ('Não encontro o plugin depois de instalar.', 'Reinicie o QGIS. Se o botão não aparecer, ative a barra em '
         'Exibir > Barras de ferramentas > Vista Saga Plugin, ou use Raster > Vista Saga Plugin.'),
        ('A mensagem diz que os mapas estão em SRC diferentes.', 'Reprojete as camadas para o mesmo SRC projetado '
         '(Vetor > Ferramentas de gerenciamento de dados > Reprojetar camada; Raster > Projeções > Reprojetar).'),
        ('A mensagem diz que os rasters não estão na mesma grade.', 'Use Raster > Alinhar rasters, com o mesmo tamanho '
         'de célula, extensão e origem.'),
        ('O resultado temporário sumiu.', 'Temporários somem ao fechar o QGIS. Indique um arquivo em Salvar em ou '
         'exporte a camada antes de fechar.'),
        ('As classes aparecem como "Classe 1", "Classe 2".', 'O arquivo não tem nomes gravados. Na Assinatura, dê '
         'nomes na simbologia da camada; no Conversor, mantenha o .aux.xml e o .qml junto do GeoTIFF.'),
        ('O QGIS ficou lento durante a execução.', 'Use Cancelar na janela de progresso, reduza a extensão ou aumente '
         'o tamanho da célula, e rode de novo.'),
        ('Onde vejo detalhes de um erro inesperado?', 'Em Exibir > Painéis > Mensagens de log, aba Vista Saga Plugin: '
         'o plugin registra lá o detalhe técnico.'),
    ],
}

GLOSSARY = {
    'title': 'Glossário',
    'items': [
        ('Área asn. (assinada)', 'Área de uma classe dentro do limite da Assinatura.'),
        ('Atrito', 'Resistência ao deslocamento usada no Voronoi; a nota é o custo por unidade de distância.'),
        ('Critério', 'Mapa ou campo usado na Avaliação, com um peso.'),
        ('Feição', 'Um polígono (ou ponto) de uma camada vetorial; no raster da Assinatura, uma classe marcada.'),
        ('FUNDO', 'Classe de fundo do formato RS2.'),
        ('Lasca', 'Sobreposição ou fresta finíssima entre polígonos; tolerada abaixo de 1 cm de largura média.'),
        ('Massa', 'Peso de um ponto gerador no Voronoi (M em M/d²).'),
        ('NoData', 'Valor "sem dado" de um raster.'),
        ('RS2', 'Formato raster do Vista SAGA.'),
        ('SRC', 'Sistema de referência de coordenadas.'),
        ('Transição', 'Par classe inicial → classe final na Monitoria.'),
    ],
}

QUICK = {
    'title': 'Referência rápida',
    'cols': ['Quero…', 'Módulo', 'Saída principal'],
    'rows': [
        ('saber do que é feita uma área', 'Assinatura', 'TXT e CSV com % Área asn. e % Categoria'),
        ('ver o que mudou entre duas datas', 'Monitoria', 'Mapa de transições e matriz'),
        ('achar as áreas mais adequadas', 'Avaliação', 'Carta com a média ponderada'),
        ('delimitar áreas de influência', 'Análises Voronoi', 'Mapa de regiões e _centros.csv'),
        ('descobrir associações de classes', 'Combinação de Mapas', 'Mapa combinado e _combinacoes.csv'),
        ('levar dados para o/do Vista SAGA', 'Conversor de Formatos', 'RS2, GeoTIFF ou vetor'),
        ('mostrar a evolução em animação', 'Sequenciador de Mapas', 'GIF animado e PNGs'),
    ],
}
