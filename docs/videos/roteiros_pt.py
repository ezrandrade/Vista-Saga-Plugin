"""Roteiros dos vídeos instrucionais (YouTube), português do Brasil. Um vídeo por módulo, com os dados de Vila Serena."""

LANG = 'pt'
UI = {
    'doc_title': 'Roteiros de vídeo', 'subtitle': 'Vista Saga Plugin 1.6.0 para QGIS 4',
    'tagline': 'Série de vídeos instrucionais - um vídeo por módulo - português do Brasil',
    'author': 'Esdras Andrade (IGDEMA/UFAL)', 'date': 'Novembro de 2026', 'toc': 'Sumário', 'figure': 'Figura',
    'footer': 'Vista Saga Plugin 1.6.0 - Roteiros de vídeo (pt-BR)', 'page': 'Página',
    'sheet': 'Ficha do vídeo', 'scenes': 'Roteiro', 'youtube': 'Publicação no YouTube',
    'cols': ['Tempo', 'Na tela', 'Narração (locução)', 'Texto na tela'],
    'sheet_cols': ['Item', 'Conteúdo'],
    'fields': ['Título no YouTube', 'Duração estimada', 'Objetivo', 'Dados', 'Pré-requisito', 'Miniatura (texto)'],
    'description': 'Descrição', 'chapters': 'Capítulos', 'tags': 'Tags',
}

GUIDE = {
    'title': 'Como usar estes roteiros',
    'paras': [
        'Cada módulo do Vista Saga Plugin tem um vídeo curto (4 a 6 minutos), gravado sobre os dados da cidade '
        'fictícia **Vila Serena**, os mesmos do tutorial passo a passo. Os números ditos na narração são os que o '
        'plugin realmente produz com esses dados: quem assistir e repetir obtém o mesmo resultado.',
        'Cada roteiro tem uma **ficha** (título, duração, objetivo, texto da miniatura), a **tabela de cenas** (tempo, '
        'o que aparece na tela, a narração e o texto sobreposto) e o material de **publicação** (descrição, capítulos '
        'e tags do YouTube).',
    ],
    'production_title': 'Padrão de produção (vale para toda a série)',
    'production': [
        '**Tela:** 1920 × 1080, QGIS 4 em **português** (o plugin segue o idioma do QGIS), tema claro, fonte da '
        'interface em tamanho normal. Feche painéis que não serão usados.',
        '**Dados:** pacote **dados_tutorial_vila_serena_pt.zip**, descompactado em C:\\VilaSerena\\dados, com o '
        'projeto já aberto, SRC EPSG:31985 e as camadas carregadas antes de gravar.',
        '**Cursor:** destaque de clique ligado; mova o mouse devagar e pare sobre o elemento enquanto a narração o cita.',
        '**Ampliação:** use zoom de edição (1,5× a 2×) sempre que a narração citar um campo ou um número.',
        '**Locução:** ritmo calmo, cerca de 140 palavras por minuto; grave a narração separada e sincronize na edição.',
        '**Abertura padrão (5 s):** logotipo do Vista Saga Plugin + nome do módulo. **Encerramento padrão (10 s):** '
        '"Dados e tutorial no site oficial: headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com" + cartões para o próximo vídeo.',
        '**Legendas:** gere as legendas a partir da coluna Narração (ela é o texto final da locução).',
        '**Texto na tela:** curto (até 8 palavras), no terço inferior, por 3 a 5 segundos.',
    ],
    'series_title': 'Ordem da série',
    'series': ['1. Conversor de Formatos', '2. Assinatura', '3. Monitoria', '4. Combinação de Mapas', '5. Avaliação',
               '6. Análises Voronoi', '7. Sequenciador de Mapas'],
    'series_note': 'A ordem segue o tutorial: o Conversor prepara o raster dos bairros usado na Assinatura. Cada vídeo, '
                   'porém, se sustenta sozinho: quando depende de um arquivo de outro vídeo, a narração avisa.',
}

VIDEOS = [
    {
        'title': '1. Conversor de Formatos',
        'sheet': ['Conversor de Formatos: vetor, GeoTIFF e RS2 do Vista SAGA | Vista Saga Plugin para QGIS',
                  '5 min',
                  'Converter um vetor em GeoTIFF na grade do estudo, nomear as classes e trocar dados com o formato RS2 '
                  'do Vista SAGA.',
                  'bairros.gpkg, uso_solo_2020.tif',
                  'Plugin instalado; projeto de Vila Serena aberto.',
                  'DO VETOR AO RS2 EM 1 CLIQUE'],
        'scenes': [
            ('0:00', 'Abertura padrão.', '', 'Conversor de Formatos'),
            ('0:05', 'Projeto de Vila Serena no QGIS; destaque nas camadas Bairros (vetor) e Uso do solo 2020.',
             'Neste vídeo você vai aprender a usar o Conversor de Formatos do Vista Saga Plugin. Vamos fazer duas '
             'coisas: transformar os bairros de Vila Serena, que são polígonos, num raster na mesma grade dos outros '
             'mapas; e levar o uso do solo para o formato RS2, do Vista SAGA, e trazer de volta.', ''),
            ('0:25', 'Menu Vista Saga Plugin aberto; clique em Conversor de Formatos.',
             'Abra o menu do Vista Saga Plugin e escolha Conversor de Formatos.', ''),
            ('0:32', 'Lista Converter aberta mostrando as seis operações.',
             'São seis conversões: de RS2 para GeoTIFF, de GeoTIFF para RS2, de RS2 e de GeoTIFF para vetor, e de vetor '
             'para GeoTIFF ou para RS2. A janela mostra só os campos da operação escolhida.', 'Seis conversões'),
            ('0:48', 'Escolher Vetor → GeoTIFF; em Camada vetorial do projeto, Bairros; clicar em Selecionar.',
             'Escolha Vetor para GeoTIFF. Em Camada vetorial do projeto, escolha Bairros e clique em Selecionar.', ''),
            ('1:00', 'Campo para rasterizar: CODIGO; Tamanho do pixel: 10 (zoom nos dois campos).',
             'Em Campo para rasterizar, escolha CODIGO: é o valor que cada célula vai receber. Em Tamanho do pixel, dez. '
             'Como o SRC é UTM, a unidade é o metro.', 'Pixel de 10 m'),
            ('1:15', 'Arquivo de saída: resultados\\bairros.tif; clicar em Executar; camada carregada.',
             'Indique o arquivo de saída e clique em Executar. O raster é carregado já com um estilo que mostra só as '
             'classes que existem.', ''),
            ('1:30', 'Propriedades da camada > Informações: 200 × 200, pixel 10.',
             'Repare: duzentas por duzentas células de dez metros. Exatamente a grade dos outros mapas, porque os '
             'bairros cobrem toda a área de estudo. Isso vai ser essencial na Assinatura.', '200 × 200 células'),
            ('1:48', 'Simbologia do raster: rótulos "Classe 1…6"; editar para os nomes dos bairros; OK.',
             'O GeoTIFF guarda os códigos, e o QGIS mostra Classe 1, Classe 2. Dê nome às classes na Simbologia: um, '
             'Beira-Rio; dois, Centro; e assim por diante. A Assinatura usa esses nomes.', 'Dê nome às classes'),
            ('2:15', 'Tabela de atributos de Bairros ao lado da Simbologia (CODIGO e NOME).',
             'Dica: a tabela de atributos do vetor tem a correspondência entre código e nome. Deixe-a aberta ao lado e '
             'copie os nomes sem erro.', 'Dica'),
            ('2:30', 'Voltar ao Conversor; escolher GeoTIFF → RS2; entrada uso_solo_2020.tif; saída uso_solo_2020.rs2.',
             'Agora, a ponte com o Vista SAGA. Escolha GeoTIFF para RS2, indique o uso do solo de 2020 e o arquivo de '
             'saída com extensão ponto rs2.', 'GeoTIFF → RS2'),
            ('2:48', 'Clicar em Executar; gerenciador de arquivos mostrando .rs2 e .rs2.json.',
             'Execute. Além do arquivo RS2, o plugin grava um arquivo lateral, ponto rs2 ponto json. O RS2 não guarda o '
             'sistema de coordenadas; esse arquivo guarda o SRC, a legenda e a correspondência dos códigos.', '.rs2.json = SRC'),
            ('3:10', 'Clicar em Propriedades do RS2…: cabeçalho, legenda e grade.',
             'O botão Propriedades do RS2 mostra o cabeçalho, a legenda e a grade antes de qualquer conversão. Use-o '
             'para conferir arquivos recebidos do Vista SAGA.', ''),
            ('3:25', 'Escolher RS2 → GeoTIFF; entrada uso_solo_2020.rs2; SRC preenchido (EPSG:31985); Executar.',
             'Para conferir, faça o caminho de volta: RS2 para GeoTIFF. O SRC aparece preenchido, lido do arquivo '
             'lateral. Execute.', ''),
            ('3:42', 'Lado a lado: uso_solo_2020.tif e uso_solo_2020_de_volta.tif, com a mesma legenda.',
             'O GeoTIFF que voltou é idêntico ao original, célula por célula, com os mesmos nomes e cores das classes.',
             'Ida e volta idêntica'),
            ('3:58', 'Lista de dicas em tela.',
             'Três cuidados. Leve sempre o ponto rs2 ponto json junto com o RS2. Ao copiar um GeoTIFF de classes, leve '
             'também o ponto aux ponto xml e o ponto qml, que guardam nomes e estilo. E para converter muitos arquivos '
             'de uma vez, marque Processar vários arquivos.', 'Leve .rs2.json, .aux.xml e .qml'),
            ('4:30', 'Encerramento padrão; cartão para o vídeo da Assinatura.',
             'No próximo vídeo, vamos usar esse raster dos bairros na Assinatura, para descobrir de que é feito cada '
             'bairro. Até lá.', 'Próximo: Assinatura'),
        ],
        'description': 'Aprenda a usar o Conversor de Formatos do Vista Saga Plugin para QGIS 4: rasterizar um vetor na '
                       'grade do seu estudo, dar nome às classes e trocar dados com o formato RS2 do Vista SAGA, com '
                       'ida e volta sem perda. Dados do exemplo (cidade fictícia de Vila Serena) e tutorial completo no '
                       'site oficial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Abertura', '0:25 As seis conversões', '0:48 Vetor para GeoTIFF', '1:48 Dar nome às classes',
                     '2:30 GeoTIFF para RS2', '3:25 RS2 de volta para GeoTIFF', '3:58 Cuidados', '4:30 Próximo vídeo'],
        'tags': 'QGIS, QGIS 4, Vista SAGA, SAGA UFRJ, RS2, GeoTIFF, rasterização, conversão de formatos, geoprocessamento, Vista Saga Plugin',
    },
    {
        'title': '2. Assinatura',
        'sheet': ['Assinatura: de que é feita esta área? | Vista Saga Plugin para QGIS',
                  '6 min',
                  'Medir a composição de uma área (uso do solo, solos, declividade) dentro de bairros selecionados e '
                  'ler as duas porcentagens do Vista SAGA.',
                  'bairros.tif (do vídeo 1, com as classes nomeadas), uso_solo_2020.tif, solos.tif, declividade.tif',
                  'Raster dos bairros gerado no vídeo do Conversor.',
                  'DE QUE É FEITO ESTE BAIRRO?'],
        'scenes': [
            ('0:00', 'Abertura padrão.', '', 'Assinatura'),
            ('0:05', 'Mapa de Vila Serena com os bairros Centro e Beira-Rio destacados.',
             'De que são feitos os bairros Centro e Beira-Rio? Quanto deles é cidade, vegetação, pastagem? Que solos e '
             'que relevo eles têm? É isso que a Assinatura responde, para vários mapas de uma vez.', ''),
            ('0:22', 'Abrir Vista Saga Plugin > Assinatura; guia Raster.',
             'Abra a Assinatura e fique na guia Raster. Raster e vetor não se misturam: cada guia trabalha com um tipo.', ''),
            ('0:32', 'Adicionar Bairros (raster) primeiro, depois Uso do solo 2020, Solos, Declividade.',
             'Em Mapas, adicione primeiro o raster dos bairros. A regra é simples: o primeiro da lista é a referência, '
             'como o mapa de cima no Vista SAGA. Depois, adicione uso do solo, solos e declividade.',
             'O 1º mapa é a referência'),
            ('0:55', 'Botões Mover para cima e Mover para baixo (zoom).',
             'Se errar a ordem, use Mover para cima. Todos os mapas precisam estar no mesmo SRC e na mesma grade; se '
             'não estiverem, o plugin avisa e não reprojeta nada por conta própria.', 'Mesmo SRC, mesma grade'),
            ('1:12', 'Em Seleção na referência, marcar 1 - Beira-Rio e 2 - Centro.',
             'Em Seleção na referência aparecem as classes do primeiro mapa, com os nomes que você deu na Simbologia. '
             'Marque Beira-Rio e Centro. Essa seleção é o limite da análise.', ''),
            ('1:28', 'Opções: Resultado por feição ligado; título e Salvar em assinatura.csv; Executar.',
             'Deixe Resultado por feição ligado: além da união dos dois bairros, sai um bloco para cada um. Dê um '
             'título, escolha onde salvar o CSV, e o TXT vai junto. Execute.', ''),
            ('1:45', 'Guia Resultados com a tabela da união; zoom nas colunas.',
             'A guia Resultados mostra a tabela. A união tem cento e trinta hectares: setenta da Beira-Rio e sessenta '
             'do Centro. A tabela do próprio mapa de referência mostra cem por cento nas classes marcadas: é a '
             'conferência do tamanho do limite.', '130 ha'),
            ('2:10', 'Destaque nas linhas do uso do solo; coluna % Área Asn.',
             'Agora, o uso do solo. A coluna Porcentagem da área assinada diz de que é feito o lugar: quarenta e cinco '
             'vírgula cinco por cento dos dois bairros é área urbana; vinte e cinco, pastagem. Essa coluna soma cem.',
             '% Área Asn. = de que é feito'),
            ('2:35', 'Destaque na coluna % Categoria.',
             'A coluna Porcentagem da categoria diz quanto da classe está ali: cinquenta e quatro por cento de toda a '
             'área urbana de Vila Serena está nesses dois bairros, e metade da água. Essa coluna não soma cem, e não '
             'deve ser somada.', '% Categoria = concentração'),
            ('3:00', 'Lista Recorte: trocar de União da seleção para Centro e depois Beira-Rio.',
             'Na lista Recorte, veja cada bairro. O Centro é setenta por cento urbano. A Beira-Rio, só vinte e quatro, '
             'com quarenta e seis por cento de pastagem. E um terço do Centro está sobre neossolo flúvico, solo de '
             'várzea.', 'Centro: 71% urbano'),
            ('3:35', 'Abrir assinatura.txt e assinatura.csv no editor e na planilha.',
             'O TXT é o relatório completo, no modelo do Vista SAGA. O CSV abre direto na planilha: filtre a coluna '
             'Recorte e monte uma tabela dinâmica por mapa e classe.', 'TXT + CSV'),
            ('4:00', 'Lista de dicas em tela.',
             'Duas dicas. Não some os blocos por bairro para chegar à união: use o bloco da união. E se as classes '
             'aparecerem como Classe 1, Classe 2, é porque o arquivo não tem nomes: dê nome na Simbologia e execute '
             'de novo.', 'Use o bloco da união'),
            ('4:25', 'Guia Vetorial (visão rápida): Selecionar no mapa e contador de feições.',
             'Com dados vetoriais, a lógica é a mesma, na guia Vetorial: você seleciona as feições no mapa do QGIS com '
             'o botão Selecionar no mapa, e o plugin faz a interseção exata.', ''),
            ('4:45', 'Encerramento padrão; cartão para o vídeo da Monitoria.',
             'No próximo vídeo, a Monitoria: o que mudou em Vila Serena entre 2000 e 2020.', 'Próximo: Monitoria'),
        ],
        'description': 'A Assinatura do Vista Saga Plugin mede de que é feita uma área: selecione bairros (ou qualquer '
                       'limite) num mapa de referência e veja, para vários mapas de uma vez, a área e as duas '
                       'porcentagens do Vista SAGA (% da área assinada e % da categoria). Exemplo com a cidade fictícia '
                       'de Vila Serena. Dados e tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Abertura', '0:22 A referência é o primeiro mapa', '1:12 Seleção na referência',
                     '1:45 Lendo a tabela', '2:10 % Área Asn.', '2:35 % Categoria', '3:00 Por bairro',
                     '3:35 TXT e CSV', '4:25 Guia Vetorial', '4:45 Próximo vídeo'],
        'tags': 'QGIS, Vista SAGA, assinatura ambiental, uso do solo, estatística zonal, geoprocessamento, planejamento urbano, Vista Saga Plugin',
    },
    {
        'title': '3. Monitoria',
        'sheet': ['Monitoria: o que mudou entre duas datas? | Vista Saga Plugin para QGIS',
                  '5 min',
                  'Comparar o uso do solo de 2000 e 2020, gerar o mapa de transições e ler a matriz de transição.',
                  'uso_solo_2000.tif, uso_solo_2020.tif',
                  'Projeto de Vila Serena aberto.',
                  'A CIDADE TRIPLICOU. ÀS CUSTAS DE QUÊ?'],
        'scenes': [
            ('0:00', 'Abertura padrão.', '', 'Monitoria'),
            ('0:05', 'Uso do solo 2000 e 2020 lado a lado.',
             'Em vinte anos, a mancha urbana de Vila Serena cresceu muito. Mas cresceu sobre o quê? A Monitoria compara '
             'dois mapas e mostra, lugar por lugar, o que permaneceu e o que mudou.', ''),
            ('0:20', 'Abrir Monitoria, guia Raster; Mapa inicial: Uso do solo 2000; Período 2000.',
             'Abra a Monitoria. Em Mapa inicial, escolha o uso do solo de 2000 e escreva o período: 2000.', ''),
            ('0:35', 'Mapa final: Uso do solo 2020; Período 2020; título; Salvar em; Executar.',
             'Em Mapa final, o de 2020, período 2020. Dê um título, indique onde salvar e execute. Os dois mapas '
             'precisam estar na mesma grade.', ''),
            ('0:55', 'Mapa de transições carregado: permanências em cinza, mudanças em cores.',
             'O mapa de transições chega pronto: permanências em cinza, mudanças em cores, com a legenda em palavras. '
             'O anel colorido em volta do centro é a expansão urbana.', ''),
            ('1:15', 'Guia Resultados: resumo com permanência e mudança.',
             'No resumo, sessenta e nove por cento da área permaneceu e trinta e um por cento mudou: cento e vinte e '
             'três hectares.', '31% mudou'),
            ('1:32', 'Tabela de transições ordenada por área; destaque nas cinco maiores mudanças.',
             'Ordene as transições por área. A maior mudança é pastagem que virou cidade: quarenta e sete hectares. '
             'Depois, vegetação nativa que virou pastagem, trinta hectares, e vegetação que virou cidade, vinte e dois.',
             'Pastagem → Área urbana: 47 ha'),
            ('2:05', 'Abrir _matriz.csv na planilha; destacar diagonal e uma linha.',
             'A matriz de transição tem a classe de 2000 nas linhas e a de 2020 nas colunas. A diagonal é o que '
             'permaneceu. Leia por linha: a linha da vegetação nativa mostra para onde ela foi.', 'Leia a matriz por linha'),
            ('2:30', 'Gráfico/realce: área urbana 32,5 → 109,7 ha; vegetação 120,5 → 52,3 ha.',
             'Resultado: a área urbana passou de trinta e dois para quase cento e dez hectares, três vezes e meia. A '
             'vegetação nativa perdeu mais da metade da área.', 'Vegetação: -57%'),
            ('2:55', 'Destaque na água (12,8 ha nas duas datas).',
             'Repare na água: doze vírgula oito hectares nas duas datas. É um controle de qualidade. Se o rio '
             '"mudasse", eu desconfiaria dos mapas, não da realidade.', 'Água = controle'),
            ('3:15', 'Opções avançadas: legenda (palavras ou códigos; tabela de nomes).',
             'Em Opções avançadas, você escolhe a legenda em palavras ou por códigos, e pode indicar uma tabela com os '
             'nomes das classes de cada período, útil quando os rasters não têm nomes gravados.', ''),
            ('3:35', 'Guia Vetorial (visão rápida).',
             'Com polígonos, use a guia Vetorial: escolha o campo de classe de cada data. Só a área comum às duas '
             'camadas é comparada.', ''),
            ('3:50', 'Lista de dicas em tela.',
             'Cuidado com legendas diferentes entre as datas: se o código três é água num mapa e floresta no outro, '
             'aparecem mudanças falsas. Padronize a legenda antes.', 'Padronize a legenda'),
            ('4:10', 'Encerramento padrão; cartão para o vídeo da Combinação.',
             'No próximo vídeo, a Combinação de Mapas: que associações de uso do solo e solo existem em Vila Serena.',
             'Próximo: Combinação'),
        ],
        'description': 'A Monitoria do Vista Saga Plugin compara dois mapas de datas diferentes e entrega o mapa de '
                       'transições, a tabela de transições e a matriz, com áreas e porcentagens. Exemplo: a expansão '
                       'urbana de Vila Serena entre 2000 e 2020. Dados e tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Abertura', '0:20 Mapas inicial e final', '0:55 Mapa de transições', '1:32 Maiores mudanças',
                     '2:05 Matriz de transição', '2:55 Controle de qualidade', '3:15 Opções e guia Vetorial',
                     '4:10 Próximo vídeo'],
        'tags': 'QGIS, Vista SAGA, detecção de mudanças, uso e cobertura da terra, matriz de transição, expansão urbana, Vista Saga Plugin',
    },
    {
        'title': '4. Combinação de Mapas',
        'sheet': ['Combinação de Mapas: que associações existem e quanto ocupam? | Vista Saga Plugin para QGIS',
                  '4 min',
                  'Cruzar uso do solo e solos, ler a tabela de combinações e achar a cidade construída sobre solo de '
                  'várzea.',
                  'uso_solo_2020.tif, solos.tif',
                  'Projeto de Vila Serena aberto.',
                  'CIDADE SOBRE VÁRZEA: ONDE?'],
        'scenes': [
            ('0:00', 'Abertura padrão.', '', 'Combinação de Mapas'),
            ('0:05', 'Mapas de uso do solo 2020 e de solos lado a lado.',
             'Onde há cidade construída sobre solo de várzea, sujeito a inundação? Para responder, é preciso cruzar dois '
             'mapas. A Combinação faz isso e dá um código para cada associação encontrada, sem pesos nem notas.', ''),
            ('0:22', 'Abrir Combinação de Mapas, guia Raster; adicionar Uso do solo 2020 e Solos.',
             'Abra a Combinação de Mapas, guia Raster, e adicione o uso do solo de 2020 e depois os solos. A ordem da '
             'lista é a ordem das colunas na tabela.', ''),
            ('0:40', 'Salvar em; Executar; mapa combinado carregado com cores e legenda.',
             'Indique onde salvar e execute. O mapa combinado é carregado com cores e legenda.', ''),
            ('0:55', 'Abrir _combinacoes.csv; ordenar por área.',
             'A tabela de combinações traz cada associação com área e porcentagem. São treze combinações em '
             'quatrocentos hectares. A maior é pastagem sobre argissolo: noventa e oito hectares.', '13 combinações'),
            ('1:25', 'Destaque na linha Área urbana | Neossolo flúvico.',
             'E a que interessa à prefeitura: área urbana sobre neossolo flúvico, dezessete vírgula nove hectares, '
             'quatro e meio por cento da cidade. É cidade em solo de várzea.', 'Cidade em várzea: 17,9 ha'),
            ('1:50', 'Simbologia do mapa combinado: desmarcar todas as classes menos a 3.',
             'Para ver onde ficam, abra a Simbologia do mapa combinado e deixe só essa combinação visível.', ''),
            ('2:10', 'Ferramenta Identificar sobre uma célula; código igual ao ID_COMB do CSV.',
             'Com a ferramenta Identificar, o valor da célula é o código da combinação, o mesmo ID da tabela.',
             'Valor da célula = ID_COMB'),
            ('2:25', 'Guia Vetorial: campos de classe e de legenda; resumo com lascas.',
             'Na guia Vetorial, escolha o campo de classe e o de legenda de cada camada. O resultado traz os campos COD '
             'e LEG de cada mapa. Lascas de cruzamento com menos de um centímetro de largura média são incorporadas ao '
             'vizinho e registradas no resumo.', 'Lascas < 1 cm'),
            ('2:55', 'Lista de dicas em tela.',
             'Comece com poucos mapas: com muitas classes, as combinações se multiplicam. E use a Combinação para '
             'explorar antes de uma Avaliação: ela mostra o que existe, sem julgar.', 'Explore antes de avaliar'),
            ('3:20', 'Encerramento padrão; cartão para o vídeo da Avaliação.',
             'No próximo vídeo, a Avaliação: onde Vila Serena pode crescer.', 'Próximo: Avaliação'),
        ],
        'description': 'A Combinação de Mapas do Vista Saga Plugin cruza dois ou mais mapas categóricos e dá um código '
                       'a cada associação de classes, com área e porcentagem. Raster ou vetor. Exemplo: uso do solo e '
                       'solos em Vila Serena. Dados e tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Abertura', '0:22 Montando a combinação', '0:55 Tabela de combinações',
                     '1:25 Cidade sobre várzea', '2:10 Identificar', '2:25 Guia Vetorial', '3:20 Próximo vídeo'],
        'tags': 'QGIS, Vista SAGA, tabulação cruzada, sobreposição de mapas, solos, uso do solo, Vista Saga Plugin',
    },
    {
        'title': '5. Avaliação',
        'sheet': ['Avaliação multicritério com pesos e notas | Vista Saga Plugin para QGIS',
                  '6 min',
                  'Montar uma avaliação de aptidão à expansão urbana (declividade, solos, uso do solo), validar, '
                  'executar e interpretar a carta.',
                  'declividade.tif, solos.tif, uso_solo_2020.tif, aptidao_expansao.geosaga.json',
                  'Projeto de Vila Serena aberto.',
                  'ONDE A CIDADE PODE CRESCER?'],
        'scenes': [
            ('0:00', 'Abertura padrão.', '', 'Avaliação'),
            ('0:05', 'Mapas de declividade, solos e uso do solo.',
             'Onde Vila Serena pode crescer com menos conflito? A Avaliação responde com uma média ponderada: cada mapa '
             'é um critério com um peso, e cada classe recebe uma nota.', ''),
            ('0:20', 'Tabela em tela com pesos e notas.',
             'Vamos usar três critérios: declividade, com quarenta por cento; solos, vinte e cinco; uso do solo, trinta '
             'e cinco. Os pesos e as notas deste exemplo são didáticos: num estudo real, precisam de justificativa.',
             'Pesos: 40 / 25 / 35'),
            ('0:42', 'Abrir Avaliação, guia Raster; Escala das notas 0 a 10; adicionar os três mapas.',
             'Abra a Avaliação, guia Raster. Escolha a escala de zero a dez e adicione os três mapas.', ''),
            ('0:58', 'Pesos entram em branco; digitar 40, 25, 35 usando Tab.',
             'Os pesos entram em branco, de propósito. Digite os pesos; a tecla Tab salta de um para o outro. Embaixo, '
             'a mensagem confirma: cem por cento, distribuição válida.', 'Tab salta entre pesos'),
            ('1:18', 'Selecionar Declividade; notas 10, 8, 4, 1. Solos: 7, 9, 2.',
             'Selecione cada mapa e dê nota às classes. Declividade: plano dez, suave ondulado oito, ondulado quatro, '
             'forte ondulado um. Solos: argissolo sete, latossolo nove, neossolo flúvico dois.', ''),
            ('1:45', 'Uso do solo: 8, 1, 6, 9; Água: marcar Não avaliar.',
             'Uso do solo: área urbana oito, vegetação nativa um, agricultura seis, pastagem nove. E na água, marque '
             'Não avaliar: ela fica fora do resultado.', 'Água: Não avaliar'),
            ('2:05', 'Uma classe sem nota destacada; clicar em Validar; mensagem listando o pendente.',
             'Se alguma classe ficar sem nota, ela aparece destacada, e o botão Validar lista o que falta. O plugin '
             'nunca supõe nota zero: nenhuma classe entra na conta sem decisão sua.', 'Nunca supõe nota 0'),
            ('2:30', 'Clicar em Abrir projeto… e escolher aptidao_expansao.geosaga.json; tudo preenchido.',
             'Atalho: em Abrir projeto, escolha o arquivo pronto do tutorial. Mapas, pesos e notas são carregados de '
             'uma vez. É assim que você repete ou ajusta uma avaliação.', 'Abrir projeto…'),
            ('2:50', 'Salvar em aptidao_expansao.tif; relatórios marcados; Executar.',
             'Indique onde salvar, mantenha os relatórios CSV e TXT marcados e execute.', ''),
            ('3:05', 'Carta carregada; legenda de 3 a 9.',
             'A carta de aptidão chega ao QGIS. As notas vão de três a oito vírgula nove, com média de seis vírgula '
             'três. A água, sem avaliação, fica de fora.', 'Média 6,3'),
            ('3:25', 'Relatório TXT: resumo por nota final; destacar notas 8 e 9.',
             'No relatório, o resumo por nota final: as notas oito e nove somam noventa e oito hectares, quase todas em '
             'relevo plano ou suave, sobre argissolo, em pastagem ou área já urbana.', 'Notas 8-9: 98 ha'),
            ('3:50', 'Destaque nas combinações da nota 3.',
             'A nota três junta o pior de tudo: vegetação nativa em encosta forte. O relatório mostra exatamente que '
             'combinação de classes gerou cada nota.', ''),
            ('4:10', 'Comparar: latossolo na serra com nota média baixa.',
             'Um detalhe que ensina: o latossolo tem nota nove, mas a média dele no mapa é a mais baixa, porque fica na '
             'serra. A declividade pesa mais e domina. Os pesos importam tanto quanto as notas.', 'Peso domina nota'),
            ('4:35', 'Arquivo _pesos_notas.geosaga.json na pasta.',
             'Cada execução grava um arquivo com os pesos e as notas usados. Guarde-o com o relatório: é o registro '
             'do que você decidiu.', ''),
            ('4:50', 'Guias Vetorial (Atributos) e (Sobreposição), visão rápida.',
             'Com dados vetoriais, use as guias Vetorial Atributos, para campos de uma mesma camada, ou Vetorial '
             'Sobreposição, para cruzar camadas. O leiaute é o mesmo.', ''),
            ('5:05', 'Encerramento padrão; cartão para o vídeo do Voronoi.',
             'Teste a sensibilidade: troque os pesos e compare as cartas. No próximo vídeo, as Análises Voronoi.',
             'Próximo: Voronoi'),
        ],
        'description': 'A Avaliação do Vista Saga Plugin faz análise multicritério por pesos e notas, no modelo do Vista '
                       'SAGA: média ponderada, classes sem nota bloqueiam a execução, relatórios CSV e TXT e projeto '
                       'reutilizável. Exemplo: aptidão à expansão urbana em Vila Serena. Dados e tutorial: '
                       'https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Abertura', '0:20 Critérios e pesos', '0:58 Digitando pesos', '1:18 Notas das classes',
                     '2:05 Validar', '2:30 Abrir projeto', '3:05 A carta de aptidão', '3:25 Relatório por nota',
                     '4:10 Peso domina nota', '5:05 Próximo vídeo'],
        'tags': 'QGIS, Vista SAGA, análise multicritério, média ponderada, aptidão, planejamento urbano, Vista Saga Plugin',
    },
    {
        'title': '6. Análises Voronoi',
        'sheet': ['Áreas de influência com Voronoi: simples, com massa e com atrito | Vista Saga Plugin para QGIS',
                  '6 min',
                  'Delimitar a área de influência de escolas pela distância, pelo porte (matrículas) e pela dificuldade '
                  'de deslocamento (atrito do rio).',
                  'escolas.gpkg, atrito.tif',
                  'Projeto de Vila Serena aberto.',
                  'O RIO MUDA QUEM ATENDE QUEM'],
        'scenes': [
            ('0:00', 'Abertura padrão.', '', 'Análises Voronoi'),
            ('0:05', 'Mapa com as seis escolas e o rio.',
             'Qual escola atende cada parte de Vila Serena? Depende da pergunta: pela distância, pelo tamanho da escola '
             'ou pela dificuldade de chegar. As Análises Voronoi fazem as três versões.', ''),
            ('0:22', 'Abrir Análises Voronoi, guia Raster; lista Modalidade aberta.',
             'Abra as Análises Voronoi. São quatro modalidades: Simples, Com Massa, Com Atrito e Com Massa e Atrito, '
             'todas validadas contra o Vista SAGA original.', 'Validado contra o Vista SAGA'),
            ('0:38', 'Modalidade Simples; Pontos geradores: Escolas; Identificação: NOME.',
             'Comece pela Simples. Em Pontos geradores, escolas; em Identificação do ponto, o campo NOME.', ''),
            ('0:50', 'Extensão da análise: Grade de raster de referência; Raster de referência: Atrito.',
             'Em Extensão da análise, escolha Grade de raster de referência e indique o raster de atrito. Assim o '
             'resultado cai exatamente na grade dos outros mapas. Execute.', 'Use a grade de referência'),
            ('1:10', 'Resultado Simples carregado; tabela _centros.csv.',
             'Cada lugar fica com a escola mais próxima. A tabela de centros traz a área de cada região.', ''),
            ('1:22', 'Modalidade Com Massa; Campo de massa: MATRICULAS; Executar.',
             'Agora, Com Massa. Em Campo de massa, escolha matrículas. O critério é massa dividida pela distância ao '
             'quadrado, como no Vista SAGA.', 'Critério: M/d²'),
            ('1:40', 'Comparar Simples × Com Massa; destaque na E. E. Darcy Ribeiro.',
             'A Escola Darcy Ribeiro, com mil e duzentas matrículas, passa de quarenta para cem hectares. A Cora '
             'Coralina, com duzentas e cinquenta, cai de quarenta para vinte e três.', 'Darcy Ribeiro: 40 → 100 ha'),
            ('2:05', 'Texto explicativo em tela: 4× massa = 2× alcance.',
             'Um detalhe importante: uma escola com quatro vezes mais massa alcança o dobro da distância, não o '
             'quádruplo. É a raiz quadrada da razão das massas.', '4× massa = 2× alcance'),
            ('2:25', 'Modalidade Com Atrito; Tipo de superfície Raster; Superfície de atrito: Atrito; Executar.',
             'Agora, Com Atrito. Escolha o tipo de superfície raster e o mapa de atrito. Nele, andar na cidade custa um, '
             'na pastagem dois, na vegetação quatro, e atravessar a água custa dez.', 'Água: atrito 10'),
            ('2:50', 'Comparar Simples × Com Atrito; destaque na E. M. Monteiro Lobato.',
             'A Escola Monteiro Lobato, junto ao rio, perde área: de cinquenta e nove para cinquenta hectares, porque '
             'atravessar a água ficou caro. A Cecília Meireles ganha: de oitenta e seis para noventa e oito.', ''),
            ('3:15', 'Diagrama em tela: reta escola-lugar atravessando o rio.',
             'Atenção ao modelo: o custo é medido na reta entre a escola e cada lugar, como no Vista SAGA. Não é o '
             'caminho de menor custo do GRASS: a reta não contorna o rio, ela paga pela travessia.',
             'Custo na reta, não no menor caminho'),
            ('3:40', 'Guia Vetorial: Simples e Com Massa com fronteiras exatas.',
             'Na guia Vetorial, o resultado sai em polígonos, com fronteiras exatas na Simples e na Com Massa, e '
             'traçadas sem rasterizar nas modalidades com atrito.', ''),
            ('3:58', 'Botão Combinar várias superfícies de atrito (visão rápida).',
             'E se o atrito vier de vários mapas, como relevo e uso do solo, marque Combinar várias superfícies e '
             'defina pesos e notas, como na Avaliação.', ''),
            ('4:15', 'Lista de dicas em tela.',
             'Três dicas. Nota de atrito zero é recusada: para quase sem atrito, use zero vírgula um. Em empate, ganha '
             'o primeiro ponto da camada. E use sempre um SRC em metros.', 'Atrito 0 é recusado'),
            ('4:40', 'Encerramento padrão; cartão para o vídeo do Sequenciador.',
             'No último vídeo da série, o Sequenciador de Mapas: a expansão de Vila Serena em animação.',
             'Próximo: Sequenciador'),
        ],
        'description': 'As Análises Voronoi do Vista Saga Plugin delimitam áreas de influência em quatro modalidades '
                       '(Simples, Com Massa, Com Atrito, Com Massa e Atrito), no modelo do Vista SAGA e validadas contra '
                       'ele. Raster ou vetor, com superfície de atrito raster ou poligonal. Exemplo: escolas de Vila '
                       'Serena e o rio. Dados e tutorial: https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Abertura', '0:22 As quatro modalidades', '0:38 Simples', '1:22 Com Massa (M/d²)',
                     '2:25 Com Atrito', '3:15 Custo na reta', '3:40 Guia Vetorial', '4:15 Dicas',
                     '4:40 Próximo vídeo'],
        'tags': 'QGIS, Vista SAGA, Voronoi, polígonos de Thiessen, área de influência, superfície de atrito, gravitacional, Vista Saga Plugin',
    },
    {
        'title': '7. Sequenciador de Mapas',
        'sheet': ['Sequenciador de Mapas: GIF animado da evolução no tempo | Vista Saga Plugin para QGIS',
                  '4 min',
                  'Montar uma animação GIF (e quadros PNG) com o uso do solo de 2000, 2010 e 2020.',
                  'uso_solo_2000.tif, uso_solo_2010.tif, uso_solo_2020.tif',
                  'Projeto de Vila Serena aberto, com a simbologia final das camadas.',
                  '20 ANOS EM 3 SEGUNDOS'],
        'scenes': [
            ('0:00', 'Abertura padrão.', '', 'Sequenciador de Mapas'),
            ('0:05', 'O GIF final rodando em tela cheia.',
             'Vinte anos de expansão urbana em três segundos. Para apresentar mudanças no tempo, uma animação comunica '
             'melhor que três mapas lado a lado. O Sequenciador de Mapas faz isso direto do QGIS.', ''),
            ('0:22', 'Abrir Sequenciador, guia Raster; adicionar 2000, 2010 e 2020.',
             'Abra o Sequenciador, guia Raster, e adicione os três mapas de uso do solo. O plugin lê o ano no nome da '
             'camada e o mostra na lista.', ''),
            ('0:40', 'Botões Editar data… e Ordenar por data.',
             'Se precisar, edite a data de um quadro ou use Ordenar por data. Mover para cima e para baixo ajustam a '
             'ordem à mão.', ''),
            ('0:55', 'Dimensões: 600 × 600; Duração 1000 ms; Exibir data ligado; legenda temática.',
             'Em Dimensões e composição, use seiscentos por seiscentos pixels e um segundo por quadro. Ligue a data '
             'sobre o mapa; se quiser, a legenda temática, com até dez categorias.', '1 s por quadro'),
            ('1:15', 'Saídas: arquivo .gif; marcar quadros PNG; Executar; pré-visualização na janela.',
             'Indique o arquivo GIF e marque a exportação dos quadros em PNG. Execute. A pré-visualização aparece na '
             'própria janela.', ''),
            ('1:35', 'Pasta com quadro_001_2000.png, quadro_002_2010.png, quadro_003_2020.png.',
             'Na pasta, além do GIF, os três quadros em PNG, em cores exatas.', ''),
            ('1:48', 'Guias Vetorial e Misto (visão rápida); opção acumulativa.',
             'Nas guias Vetorial e Misto, você anima camadas vetoriais, inclusive por um campo de data, e pode sobrepor '
             'vetores a um raster de fundo. A opção acumulativa mantém as feições dos períodos anteriores: ótima para '
             'mostrar crescimento.', 'Acumulativo = crescimento'),
            ('2:15', 'Lista de dicas em tela.',
             'Duas dicas. O GIF tem no máximo duzentas e cinquenta e seis cores; para slides, use os PNGs. E os quadros '
             'usam a simbologia do QGIS: ajuste cores e legenda antes de exportar.', 'Ajuste a simbologia antes'),
            ('2:35', 'Encerramento da série: os sete módulos em mosaico; site oficial.',
             'Com este vídeo, você conheceu os sete módulos do Vista Saga Plugin. O tutorial completo, o manual e os '
             'dados de Vila Serena estão no site oficial. Bom trabalho!', 'headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com'),
        ],
        'description': 'O Sequenciador de Mapas do Vista Saga Plugin gera um GIF animado (e quadros PNG) a partir de '
                       'mapas em ordem, com data, nomes e legenda sobre cada quadro, usando a simbologia do QGIS. '
                       'Exemplo: a expansão urbana de Vila Serena de 2000 a 2020. Dados e tutorial: '
                       'https://headless-ceujfwuqhus-ezrandrad0-140a.wix-site-host.com/',
        'chapters': ['0:00 Abertura', '0:22 Adicionando quadros', '0:55 Dimensões e composição', '1:15 Gerando o GIF',
                     '1:48 Vetorial, Misto e acumulativo', '2:15 Dicas', '2:35 Encerramento da série'],
        'tags': 'QGIS, Vista SAGA, GIF animado, série temporal, animação de mapas, expansão urbana, Vista Saga Plugin',
    },
]
