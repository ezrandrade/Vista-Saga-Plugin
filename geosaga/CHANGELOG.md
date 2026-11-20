## 1.6.0 — Dicas em todos os módulos (2026-11-20)

- **Dicas (caixas amarelas do QGIS) em todos os botões, campos, caixas de marcar e listas dos sete módulos**
  (decisão do autor: sem cabeçalhos de tabela nem abas). Antes, 184 widgets não tinham dica: Avaliação 44,
  Monitoria 32, Análises Voronoi 25, Combinação de Mapas 24, Conversor de Formatos 26, Sequenciador de Mapas
  33 (a Assinatura já tinha todas na 1.5.0). Textos curtos, no indicativo, traduzidos para inglês e espanhol.
- Dicas compartilhadas no `ui_shared.py`: seção "3. Resultado" da Avaliação e campos de peso e nota das tabelas.
- **Correções de tradução:** dicas passadas à função `button()` nunca eram traduzidas (ex.: "Atualiza a lista de
  camadas raster…", "Divide 100% igualmente…"); rótulos "X mínimo:", "Y mínimo:", "X máximo:", "Y máximo:" do
  Voronoi apareciam em português nos outros idiomas.
- **Catálogo do QGIS:** o `metadata.txt` não usa mais o sinal de porcentagem (trocado por "percent"): o catálogo lê o arquivo com `ConfigParser` e recusava o pacote. Novo teste `tests/unit/test_metadata_catalogo.py`.
- Nenhum cálculo alterado.
- Testes: `tests/qgis/tooltip_inventory.py` (abre cada módulo em QGIS real, todas as guias, e falha se houver
  widget sem dica; `--lista` exporta as dicas para revisão); `tests/unit/test_i18n.py` passa a conferir o texto
  e a dica de `button()`.

## 1.5.0 — Assinatura no modelo do Vista SAGA (2026-11-20)

- **Assinatura refeita no modelo do Vista SAGA** (decisões do autor de 20/11/2026; ver
  `NOTAS_DA_VERSAO_150.md`): lista de mapas com a **referência no topo**; a seleção na referência é o limite;
  **todos os mapas da lista são assinados**, inclusive a referência; resultado da **união** e, opcionalmente,
  **por feição**; colunas do Vista SAGA (total e assinado, **% Área Asn.** e **% Categoria**); FUNDO e NoData
  contam como classe.
- **Guia Raster:** formatos do GDAL e **RS2**; mesmo SRC projetado em metros e mesma grade obrigatórios (o
  plugin não reprojeta); seleção por lista de classes ("Marcar todas" = "Assinar o mapa inteiro"); nomes das
  classes do arquivo ou do estilo da camada no QGIS. **Validada contra o Vista SAGA original** em três casos
  (mapa inteiro 100%; seleções parciais iguais, salvo as células da classe ligadas só pela diagonal, que o
  balde do Vista SAGA exclui e a seleção por classe inclui).
- **Guia Vetorial:** interseção exata; seleção pelas ferramentas do QGIS ("Selecionar no mapa", "Selecionar
  todas", "Desselecionar todas"); linhas "Sem classe" e "Sobreposição excluída"; **lascas e frestas com largura
  média < 1 cm toleradas** e registradas (regra da Combinação).
- **Saídas:** relatórios TXT e CSV, sem o GeoPackage das áreas e sem as caixas "temporário"/"carregar";
  "Remover todas" na lista de mapas. O algoritmo Processing `geosaga:assinatura` fica **obsoleto e oculto**
  (modelos e scripts antigos continuam funcionando). Corrige a reprojeção silenciosa do módulo antigo.
- **Conversor de Formatos:** Vetor → GeoTIFF grava sempre a paleta (o QGIS abria em tons de cinza, sem os
  nomes das classes); Vetor → GeoTIFF e RS2 → GeoTIFF gravam um estilo `.qml` só com as classes reais (a
  legenda listava 256 entradas); Vetor → RS2 não deixa mais pastas temporárias `.vista_vector_rs2_*` na saída
  (Windows).
- **Nomes dos resultados em todos os módulos:** temporário com o nome "Módulo - operação" (arquivo e camada);
  resultado salvo carregado com o nome do arquivo.
- Testes: `test_150_assinatura_motor.py`, `test_150_assinatura_janela.py`, `integration_signature_150_qgis.py`,
  `test_150_vetor_geotiff_paleta.py`, `test_150_vetor_rs2_temporarios.py`, `test_150_nomes_resultados.py`;
  `scripts/comparar_assinatura_vista_saga.py`.

## 1.4.2 — Sequenciador: guias com a mesma altura (2026-11-19)

- **Sequenciador de Mapas: as guias Raster, Vetorial e Mista têm a mesma altura, compacta** (264 px no
  teste), decisão do autor. Na 1.4.1, a área das guias acompanhava a guia aberta: a lista "1. Sequência
  de quadros" subia e descia ao trocar de guia, e nas guias Vetorial e Mista a barra de abas descia
  18 px (o Qt calculava a altura do texto quebrado pela maior guia).
- Os **textos explicativos das guias Vetorial e Mista viraram dicas** (passar o mouse sobre a aba ou o
  botão de gerar quadros); sem eles, a maior guia baixou de 334 para 264 px, e a guia Raster fica com
  menos espaço livre que na 1.4.0 (cerca de 140 px, antes cerca de 210).
- Nenhum cálculo alterado. Teste: `test_161_sequenciador_guias.py` (reescrito).

## 1.4.1 — Rodapé padrão em todos os módulos (2026-11-19)

- **Botão de ação "Executar" em todos os módulos** (antes: "Calcular assinatura", "Executar monitoria",
  "Executar avaliação", "Executar sobreposição e avaliação", "Gerar Voronoi", "Combinar mapas", "Gerar GIF";
  o Conversor de Formatos já usava "Executar"). Pedido do autor.
- **Rodapé padrão: [Executar] [Fechar]**, com **[Validar] só na Avaliação** (única exceção, decisão do
  autor), sempre fora das guias. Na Monitoria (guia Vetorial) e na Avaliação (guias vetoriais), os botões do
  formulário da guia passaram para o rodapé da janela; antes ficavam numa linha própria ou no fim da área
  com rolagem.
- **Sem linha de status, barra de progresso ou Cancelar fixos no rodapé** (Monitoria raster e Avaliação
  raster tinham barra e/ou Cancelar permanentes). O progresso e o Cancelar aparecem numa janela só durante
  a execução, como já era em Voronoi, Combinação, Assinatura, Conversor e Sequenciador. O desfecho
  (concluída, cancelada, prévia limitada) vai para a barra de mensagens do QGIS; falhas continuam em
  caixas de mensagem.
- **Conversor de Formatos:** "Propriedades RS2…" saiu do rodapé para junto do campo "Arquivo de entrada",
  que é o arquivo que ele inspeciona.
- **Títulos das janelas (dev2):** "Vista Saga Plugin - Conversor de Formatos", como no menu (antes,
  "formatos" em minúscula); as janelas de progresso de todos os módulos usam o título da janela do módulo
  (antes, "Vista Saga - Assinatura", "Vista Saga Plugin - conversor", "Vista Saga - Monitoria vetorial" ou
  nenhum título próprio).
- **Sequenciador de Mapas (dev3):** a área das guias passa a ter a altura da guia aberta. Antes, tinha a
  altura da maior guia (Mista), e a guia Raster ficava com um espaço vazio grande abaixo dos botões de
  adicionar, alongando a barra de rolagem (área das guias: 334 → 122 px na guia Raster).
- Nenhum cálculo alterado. Testes: `test_160_rodape_padrao.py`, `test_161_sequenciador_guias.py`.

## 1.4.0 — Voronoi fiel ao Vista SAGA e atrito vetorial (2026-11-19)

- **Mudança de método, validada contra o Vista SAGA original** (caso sintético de 80 × 60
  células, comparação célula a célula; ver `NOTAS_DA_VERSAO_140.md`):
  - **Com Massa: maior M/d²** (antes, M/d). Raster: menor d²/M. Vetor exato: discos de Apolônio
    com razão √(M_leve/M_pesado). Reproduz 100% das células do Vista SAGA (exceto empates); o
    modelo antigo divergia em 15,6% das células.
  - **Atrito no modelo do Vista SAGA:** custo acumulado = soma de distância ao polo × nota ×
    passo (√2 na diagonal) nas células da reta de Bresenham polo-célula; com massa, dividido
    pela massa (equivale a M/d²). A **nota entra direto como custo** (nota 1 = custo basal; sai o
    1 + C). Reproduz 99,7% das células; as diferenças ficam na fronteira entre regiões. A célula
    do polo é sempre dele. Poda exata reformulada.
  - Com Atrito e Com Massa e Atrito deixam de ser "experimentais".
- **Superfície de atrito vetorial** (Com Atrito e Com Massa e Atrito): polígonos com a nota na
  **coluna de atrito** (sem atribuição manual). Área sem polígono e coluna vazia: **sem resultado,
  atravessáveis com nota 1** (custo basal do Vista SAGA, padrão da classe FUNDO; dev5). A regra
  anterior (barreira) distorcia áreas de estudo côncavas: a reta que saía da área ficava bloqueada.
  - **Guia Vetorial: vetor direto, sem rasterização (modelo contínuo).** Custo = integral de
    distância ao polo × nota ao longo do segmento polo-ponto, calculada exatamente pelos
    cruzamentos com as bordas dos polígonos; com massa, dividido por M. Fronteiras traçadas
    numericamente (malha de busca deslocada, refinamento local, tolerância de 0,5 m desde a dev4;
    pontas de cunhas finas e junções podem ficar encurtadas); partição
    sem sobreposições nem lacunas; recorte exato pela cobertura dos polígonos. Coincide com o
    Vista SAGA em 99,60% (com massa) e 99,52% (sem massa) das células; com nota uniforme,
    reproduz os discos de Apolônio do Com Massa a menos de 1 cm. Regiões menores que o espaçamento
    da busca podem não ser detectadas (a conferência automática reduz essa chance).
  - **Conferência automática do traçado:** cada célula é testada nos lados e no interior, com
    subdivisão onde houver suspeita; depois, o modelo é comparado com os polígonos em um ponto por
    célula, com novo traçado local onde divergir (até 3 passadas). O `_resumo.txt` informa o
    resultado e avisa se restar divergência. Corrige a região partida em duas (espaçamento 20 m) do
    teste do autor.
  - **Sem o campo "Espaçamento da busca" (dev4):** o espaçamento é escolhido pelos dados (maior lado
    da extensão / 100, até 1/4 da largura do polígono de atrito mais estreito, com teto de 100 mil
    nós) e a tolerância padrão é de 0,5 m (ou 1/2000 do maior lado em extensões pequenas), coerente
    com mapas temáticos 1:10.000. Os dois valores saem no `_resumo.txt`.
  - **Desempenho e progresso (dev5, teste com dados reais do autor: 40 mil vértices, 10 polos):** índice
    angular das arestas por polo (exato; 70× mais rápido); o refinamento vai até estabilizar (o limite
    fixo de rodadas deixava pontas soltas e regiões fundidas); conferência final por carimbo das
    regiões; execução em segundo plano (tarefa do QGIS) com progresso em porcentagem e cancelamento.
    O caso real, que não terminava em mais de 18 min, leva cerca de 2 min.
  - **Guia Raster:** os polígonos viram notas na grade da análise (extensão e resolução), pelo
    centro da célula, e o cálculo segue o modelo célula a célula do Vista SAGA (99,7%).
  - Sem reprojeção: a camada de polígonos define o SRC da análise.
- **dev6 (teste da dev5 com dados reais):** guia Raster **recorta pela área de estudo** quando a extensão
  vem de camada poligonal (antes, só o retângulo envolvente); **NoData do raster de atrito sem resultado,
  atravessável com nota 1** (antes, barreira); lascas do recorte final (largura média < 2 × tolerância)
  incorporadas ao vizinho; `_resumo.txt` do vetor direto com o tempo de cálculo e as partes com área
  < 25 m² (só informadas); resumo do raster com atrito com a regra de passagem conforme a fonte.
- **Nota de atrito 0 recusada** (raster, coluna vetorial e combinação de superfícies): custo zero cria
  empates resolvidos pela ordem dos pontos, e o comportamento do Vista SAGA com nota 0 não foi
  testado. Para "quase sem atrito", use um valor pequeno, como 0,1. Rasters de atrito antigos com
  valor 0 precisam ser revistos.
- Sem opção do modelo da 1.3 na interface: para reproduzir resultados antigos, use o ZIP da 1.3.0.
- **Segundo caso de validação, independente (bacia real, 19/11/2026):** Simples e Com Massa 100% (5 m);
  com atrito (10 m), guia Raster 99,46% / 99,42% das células, 97-98% das divergências na fronteira; guia
  Vetorial 99,29% / 99,06%. Pelo critério de comparabilidade aceito pelo autor (células ≥ 99%, fronteira
  ≥ 90%, área ≤ 1% por região), a guia Raster atende no Com Massa e Atrito e falha no critério 3 no Com
  Atrito (uma região pequena, 1,33%); a guia Vetorial falha no 3 (e no 2 com massa). Declarado sem rever
  o critério. Para comparar com o Vista SAGA, use a guia Raster. Limitação observada do Vista SAGA
  original: com atrito, saída vazia ou incompleta, sem aviso, fora da grade de 10 m do caso.
- Scripts de validação: `scripts/gerar_caso_atrito.py`, `scripts/comparar_caso_atrito.py`,
  `scripts/comparar_vetor_plugin.py`, `scripts/comparar_caso_bacia.py` (critérios de comparabilidade).
- Guia Vetorial: vetor direto nas quatro modalidades (antes, com atrito, poligonização da grade).
- Interface do Voronoi sem menções ao Vista SAGA (introdução e notas de método, em português, inglês e
  espanhol), a pedido do autor; relatórios, notas da versão e documentação mantêm a descrição da validação.

## 1.3.0 — Voronoi: guias Raster e Vetorial, vetor exato Com Massa (2026-11-17)

- **Análises Voronoi no padrão dos demais módulos:** guias “Raster” e “Vetorial”, como na
  Combinação de Mapas e na Monitoria; grupos “Modelo de influência”, “Dados de entrada” e
  “Resultado”, compartilhados pelas duas guias (o preenchimento acompanha a troca de guia).
- **Saída no padrão do plugin:** campo “Salvar em” com “Salvar como…”. Em branco: raster em
  arquivo temporário; vetor em camada temporária em memória. Preenchido: salvo nesse arquivo.
  Sempre carregado no QGIS. Saem as caixas “Resultado temporário” e “Adicionar ao projeto”, o
  menu “Formato de saída” e o seletor de formato vetorial.
- **Formatos vetoriais pelo filtro do “Salvar como…”**, como no QGIS: GeoPackage, Shapefile,
  GeoJSON ou FlatGeobuf (os do Conversor de Formatos). Sem arquivo indicado, GeoPackage
  temporário copiado para a memória.
- **Guia Vetorial nas quatro modalidades:**
  - Simples: polígonos exatos (bissetrizes), como antes;
  - **Com Massa (cálculo novo):** fronteiras exatas, sem grade: arcos de círculos de Apolônio
    entre massas diferentes (o mais leve vence no disco em que d_leve/d_pesado < M_leve/M_pesado),
    bissetrizes entre massas iguais. Arcos com desvio máximo de 2/3 de 1 cm, sem viés de área;
    vizinhos usam o mesmo arco (sem sobreposições nem lacunas); regiões podem ser
    multipolígonos. As áreas do raster Com Massa convergem para as do vetor (25 centros:
    diferença média de 2,0% a 100 m, 0,5% a 30 m e 0,04% a 10 m);
  - **Com Atrito e Com Massa e Atrito:** o atrito é uma superfície raster, sem fronteira
    geométrica exata; o cálculo é feito na grade da superfície de atrito e convertido em
    polígonos (bordas nos pixels), sem guardar o GeoTIFF. O `_resumo.txt` registra isso.
- Saem as opções “Vetor (poligonização)” e “GeoTIFF + vetor (poligonização)”.
- Aviso antes de substituir resultados existentes, como na Combinação de Mapas.
- Mensagens de conclusão do Voronoi traduzidas para inglês e espanhol.
- **Cálculos existentes inalterados:** o GeoTIFF e o CSV da guia Raster são idênticos byte a
  byte aos da 1.2.1 (modalidades Simples e Com Massa conferidas).

## 1.2.1 — Correções de interface (2026-11-16)

Correções encontradas ao escrever o manual de uso da 1.2.0. Nenhum algoritmo foi alterado.

- **Sequenciador de Mapas:** a lista de quadros mostrava “Sem data”, “sobre” e “[campo temporal]”
  em português com o QGIS em inglês ou espanhol; agora esses textos são traduzidos. A observação
  da exportação (“com quantização GIF” / “com cores preservadas”) e a mensagem “GIF salvo em”
  também passam a ser traduzidas.
- **Conversor de Formatos:** o botão de opções avançadas mostrava só a seta; agora exibe o texto
  “Mostrar opções avançadas” / “Ocultar opções avançadas” ao lado dela.
- Teste de regressão: `test_121_i18n_fixes.py`.

## 1.2.0 — Conversor de Formatos, Combinação, Sequenciador e Monitoria (2026-11-16)

Interface dos módulos Conversor de Formatos, Combinação de Mapas, Sequenciador de Mapas e
Monitoria, com duas decisões de método na combinação vetorial (tolerância de lascas e
incorporação de resíduos) e a retirada temporária do Mann–Kendall da Monitoria.

**Conversor de Formatos**


- **Novo nome do módulo:** “Conversão de Formatos” passou a “Conversor de Formatos” no menu e no
  título da janela (inglês: “Format converter”; espanhol: “Conversor de
  formatos”). Os identificadores internos (`rs2_dialog`, `open_rs2_converter`, `geosaga:*`) não
  mudam, e projetos e modelos antigos continuam funcionando.
- **Aparência igual à dos demais módulos:** a área com rolagem da janela passa a ter a moldura
  padrão, como no Sequenciador de Mapas; as seções deixam de aparecer com outros tons de cinza e
  outra linha de contorno no Windows.
- **Sem título no topo da tela:** como nos demais módulos, a janela começa pelo texto de
  apresentação; o nome do módulo fica na barra de título.
- **Altura da janela ajustada ao conteúdo:** sem espaço vazio embaixo. A janela acompanha os
  campos de cada operação, o lote e as opções avançadas, até 90% da altura útil da tela (acima
  disso, aparece a rolagem). A largura escolhida pelo usuário é mantida.
- Nenhum algoritmo de conversão foi alterado.

**Monitoria**

- **Resultado no padrão dos demais módulos:** saem as caixas “Resultado temporário no QGIS” e
  “Adicionar … ao projeto QGIS”, nas guias Raster e Vetorial. Campo “Salvar em” vazio: mapa de
  transições raster em arquivo temporário; resultado vetorial como camada temporária em memória.
  Com um arquivo indicado, salvo e carregado. Sempre carregado no QGIS.
- **Mesmos rótulos nas duas guias:** seção “Resultado”, “Título do estudo:”, “Salvar em:”,
  “Camada no QGIS:”, “Ou arquivo:” e “Executar monitoria”.
- **Mann–Kendall retirado (por enquanto).** Saem a série temporal das opções avançadas, o arquivo
  `_tendencias_mk.csv` e a seção de Mann–Kendall do `_resumo.txt` (raster) e a nota sobre ele
  no resumo vetorial. O teste volta como módulo próprio na 2.0; o código do cálculo
  (`monitoring_trends.py` e as funções de relatório) e os testes unitários dele foram mantidos.
  Transições, matriz e áreas não mudaram.
- **Aviso de feições sem classe na monitoria vetorial:** feições sem valor no campo de classe
  (ou sem geometria) ficam fora da monitoria e viravam vazios no mapa sem nenhum alerta (só uma
  linha no `_resumo.txt`). Agora a conclusão avisa quantas feições de cada mapa foram ignoradas,
  com o nome do campo, e sugere preenchê-lo ou usar outro campo. Caso real: classe
  MATA ATLANTICA com `CODIGO` vazio nos dois anos, 1.474 ha (35% da área) fora do resultado.
- **Copiar resultados para planilhas:** nas subguias Raster e Vetorial de Resultados, Ctrl+A
  seleciona a tabela inteira e Ctrl+C copia as linhas selecionadas (ou todas), com o cabeçalho,
  em texto separado por tabulação; também pelo botão direito do mouse. Os números saem com o
  separador decimal do idioma do QGIS (em português, “548,808”), para não serem lidos como
  milhares na planilha. A prévia continua limitada a 500 linhas; o CSV traz tudo.
- Correções: na guia Vetorial embutida, o botão “Fechar” interno era escondido comparando o
  texto em português (falhava em inglês e espanhol); o “Fechar” da janela não ocupa mais a linha
  inteira nessa guia.

**Sequenciador de Mapas**

- **“Mover para cima” e “Mover para baixo”** no lugar de “Subir” e “Descer”.

**Combinação de Mapas**

- **Guias “Raster” e “Vetorial”**, como nos demais módulos (antes “Combinação raster” e
  “Combinação vetorial”).
- **“Adicionar camada selecionada”** no lugar de “Adicionar camada”, nas duas guias.
- **“Mover para cima” e “Mover para baixo”** no lugar de “Subir” e “Descer”, nas duas guias.
- **Resultado sempre carregado no QGIS:** saíram as caixas “Saída temporária no QGIS” e
  “Carregar resultado no projeto QGIS”. Campo “Salvar em” vazio: vetor como camada temporária em
  memória; raster em arquivo temporário (o QGIS não mantém rasters em memória). Com um arquivo
  indicado, o resultado é salvo e carregado no QGIS. Os relatórios `_combinacoes.csv` e
  `_resumo.txt` continuam sendo gerados (na pasta temporária do QGIS quando não há arquivo).
- **Campo de classe editável para qualquer camada da lista:** ao selecionar uma camada em
  “Camadas adicionadas”, a seção “Campos de classe e legenda” (antes “Classificação da próxima
  camada vetorial”) mostra os campos dela, e a troca vale na hora; a lista mostra o campo novo.
  Sem seleção na lista, a seção volta a valer para a camada do menu suspenso, a ser adicionada.
  Com várias camadas selecionadas, os campos ficam desativados.
- **Aviso de camada repetida mais claro:** cada camada entra uma única vez na combinação (com um
  campo de classe próprio). Ao repetir uma camada, o aviso informa o nome e o campo já usado e
  indica como trocar o atributo. Em “Adicionar várias do QGIS…” e “Adicionar arquivos…”, a
  repetição é detectada antes de perguntar o campo.
- **Tolerância de lascas na combinação vetorial (decisão de método).** Antes, qualquer
  sobreposição entre polígonos de uma mesma camada maior que 10⁻¹⁰ da área do menor polígono
  bloqueava a combinação, inclusive lascas de precisão invisíveis (casos reais: lascas de até
  0,04 mm de largura e 0,03 m² no total, em camadas de 2.343 ha). Agora o critério é a
  **largura média** de cada pedaço sobreposto (2 × área ÷ perímetro): abaixo de **1 cm**, o
  pedaço é tratado como imprecisão de coordenadas e **mantido**, e o `_resumo.txt` registra, por
  mapa, o número de lascas e a área duplicada (a janela de conclusão também informa). A partir
  de 1 cm, a combinação continua bloqueada, e a mensagem lista **todos** os pares (até 10), com
  classes, área e largura média. Justificativa: a largura separa ruído de coordenadas de erro
  real independentemente do tamanho dos polígonos, e 1 cm fica muito abaixo da precisão
  cartográfica de bases municipais. Em SRC geográfico, 1 cm é convertido para graus pela
  conversão aproximada do QGIS. Teste de regressão: `test_120_sliver_tolerance.py`.
- **Resíduos do cruzamento incorporados ao vizinho (decisão de método, opção C).** Mapas
  traçados sobre a mesma base têm fronteiras quase coincidentes; o cruzamento gerava tiras
  microscópicas que criavam combinações inexistentes no terreno (caso real Renda × Escolaridade:
  225 a 462 resíduos, 0,0007 a 0,07 m², e 8 a 9 combinações falsas em 23 a 24; o menor pedaço
  real tinha 512 m² e 4,9 m de largura média). Agora o resultado é separado em partes simples, as
  partes com largura média abaixo de 1 cm são marcadas como resíduos e fundidas ao vizinho de
  maior fronteira comum pela ferramenta “Eliminar polígonos selecionados” do QGIS, que mantém os
  atributos do vizinho. A área total não muda e as combinações falsas desaparecem (simulação no
  caso real: 15 combinações). Resíduos sem vizinho são excluídos. O `_resumo.txt` e a janela de
  conclusão registram quantos resíduos foram incorporados ou excluídos e a área. Com isso, o mapa
  vetorial passa a ter uma feição por parte simples (antes, por par de feições cruzadas). Teste
  de regressão em `test_120_sliver_tolerance.py`.
- **Campos do mapa vetorial combinado renomeados:** `C01`/`L01`, `C02`/`L02`… passam a
  `COD_01`/`LEG_01`, `COD_02`/`LEG_02`… (código e legenda da classe de cada mapa, na ordem da
  lista), com o mesmo prefixo `COD_` do `_combinacoes.csv`. Estilos, expressões ou modelos feitos
  sobre resultados antigos precisam usar os nomes novos; arquivos já gerados não mudam.
- Fora a tolerância de lascas e a incorporação de resíduos, nenhum algoritmo de combinação foi alterado.

## 1.1.0 — Avaliação: guias vetoriais no padrão da guia Raster (2026-11-12)

Nenhum algoritmo de cálculo foi alterado: notas, pesos, interseção e relatórios usam os mesmos
motores da 1.0.9. Muda a interface do módulo Avaliação e a forma de entregar o resultado.

- **Guias renomeadas:** “Vetorial (Atributos)” e “Vetorial (Sobreposição)”.
- **Mesmo leiaute nas três guias:** Novo/Abrir/Salvar projeto; “Escala das notas”;
  1. critérios e pesos; 2. classes do critério selecionado; 3. Resultado.
- **Sobreposição:** a seção 1 reúne “Adicionar camadas do QGIS…”, o novo “Adicionar de
  arquivo(s)…” (abre na pasta das camadas já carregadas no QGIS) e “Remover”. Saíram o seletor
  de camada e campo e o botão “Adicionar camada”, redundantes: o campo temático já é escolhido
  na importação. A lista do QGIS mostra apenas camadas de polígonos.
- **Atributos:** novo botão “Arquivo…” ao lado da camada; saiu o botão que abria a
  sobreposição em outra janela (as guias já cumprem esse papel).
- **Terminologia e alinhamento:** “Categorias” passou a “Classes” e “Excluir” a “Não avaliar”,
  como na guia Raster. Valores numéricos (pesos, quantidades, notas e classes numéricas) ficam à
  direita; classes textuais, à esquerda, como numa planilha. A caixa “Não avaliar” é centralizada.
- **Notas vetoriais** com o mesmo controle da guia Raster: “—” é nota não definida, e marcar
  “Não avaliar” desativa a nota da classe.
- **Resultado:** saíram as caixas “Resultado temporário” e “Adicionar resultado ao QGIS”. Campo
  “Salvar em” vazio: o resultado vetorial é carregado como camada temporária em memória; o raster,
  como arquivo temporário (o QGIS não mantém rasters em memória). Com um arquivo indicado, o
  resultado é salvo e carregado no QGIS. Relatórios CSV e TXT mantidos.
- **Ordenação das classes:** clicar no cabeçalho (Classe, Feições/Descrição, Nota ou Não avaliar)
  ordena a tabela; clicar de novo inverte a ordem. Classes numéricas seguem a ordem numérica
  (2 antes de 11), e as notas digitadas são preservadas.
- **TAB entre pesos e entre notas:** TAB e Shift+TAB saltam direto para o próximo campo de peso ou
  de nota, com o valor já selecionado para digitação; classes em “Não avaliar” são puladas.
- **Mesmo fundo em todo o plugin:** as áreas com rolagem (guias vetoriais da Avaliação e da
  Monitoria, Assinatura, Voronoi, Conversão de formatos e Sequenciador) deixam de pintar o fundo
  de cinza e passam a usar o fundo padrão da guia do QGIS.
- **Classes sem nota em evidência:** a nota “—” continua bloqueando a execução (o plugin nunca
  supõe nota 0 nem exclui a classe sozinho), mas agora as classes pendentes ficam destacadas, a
  coluna Classes mostra “7 (2 sem nota)” e o destaque some à medida que as notas são digitadas.
  “Validar” e “Executar” listam todas as pendências, por camada ou mapa (antes, só as 5 primeiras
  apareciam). Feições com o campo temático vazio não bloqueiam: aparecem como aviso em “Validar”
  e na lista de pendências. A dica da tabela foi encurtada; “Repetir a mesma nota nas classes
  selecionadas” substitui “Nota selecionada”, e o botão passou a “Aplicar”.
- **Pesos sem distribuição automática:** mapas e critérios novos entram com o peso em branco;
  remover um item não altera os demais. A divisão por igual só ocorre no botão “Distribuir pesos
  igualmente”.
- **Traço simples no lugar do travessão** em todos os textos de interface, títulos de janela,
  nomes de camadas e cabeçalhos de relatório, nos sete módulos (catálogos en/es atualizados). O
  “—” permanece só como marcador de nota não definida. Meias-riscas de intervalos (0–10,
  1985–2024, Mann–Kendall) não foram alteradas.
- **Guia Raster sem Título e Autor:** o título dos relatórios e dos metadados do GeoTIFF passa a
  ser o nome do arquivo salvo (vazio no resultado temporário); o autor fica em branco. Projetos
  antigos com título e autor continuam abrindo (os campos são ignorados).
- **Espanhol completo em todo o plugin:** o catálogo espanhol passou de 226 para todas as 1.508
  frases (antes, a interface em espanhol mostrava a maior parte dos textos em inglês). Um teste
  novo exige que toda frase nova entre nos catálogos inglês e espanhol. No inglês, a linha de
  situação dos pesos usa o mesmo texto nas três guias da Avaliação.
- **Arquivo de pesos e notas:** cada execução grava `<resultado>_pesos_notas.geosaga.json`
  (pesos, notas, classes não avaliadas, camada e campo de origem), que “Abrir projeto…” reaplica
  em outra avaliação. Classes que deixaram de existir e classes novas sem nota são informadas.
  Nas guias vetoriais, “Salvar projeto…” grava o mesmo arquivo a qualquer momento.

## 1.0.9 — ícone principal em alta qualidade (2026-11-12)

Nenhum código ou algoritmo de processamento foi alterado.

- **Ícone principal:** `icon.png` e `icons/icon_*.png` passam a vir da imagem original do desenho,
  e não do SVG vetorizado automaticamente. Em 256 e 512 px (Gerenciador de Complementos), somem
  as faixas de cor duras e as bordas serrilhadas da vetorização; de 16 a 48 px o desenho é o
  mesmo. Os tamanhos 16, 24, 32, 48, 64, 128, 256 e 512 px vêm do pacote do autor; 19 e 50 px
  (QRibbonSkin e barra) foram reduzidos da imagem original de 1.254 px (Lanczos, transparência
  pré-multiplicada).
- **README:** logotipo do repositório trocado pelo novo desenho, em PNG de 512 px
  (`docs/assets/vista-saga-mark.png`); o SVG do logotipo antigo foi removido.

## 1.0.8 — novos ícones (2026-11-12)

Nenhum algoritmo de processamento foi alterado; os identificadores `geosaga:*` foram preservados.

- **Ícone principal:** o botão do plugin, os menus Raster e Complementos e a guia do QRibbonSkin
  passam a usar o novo desenho da mão com o globo, em estilo plano. Os PNG de 16 a 512 px
  (inclusive o de 19 px do QRibbonSkin) foram gerados a partir de um único SVG
  (`icons/vista_saga_plugin.svg`), sem mudança no código do botão.
- **Ícones dos módulos:** cada um dos sete itens do menu suspenso exibe o ícone do seu módulo
  (`icons/modulos/*.svg`). Arquivo ausente não remove o item do menu.
- Teste novo garante que todo módulo do menu tem um SVG existente, quadrado e sem scripts ou
  referências externas.
- A 1.0.7 existiu apenas como build interno de teste (1.0.7-dev1) e não foi lançada.

## 1.0.6 — conversão Vetor → RS2 e correção do formato RS2 (2026-11-11)

- **Nova operação Vetor → RS2 (rasterização Vista SAGA)** no Conversor de formatos, sem a etapa
  manual Vetor → GeoTIFF → RS2. As cinco operações anteriores não foram alteradas.
  - Grade copiada de um RS2 de referência (para cruzamento célula a célula) ou alinhada a
    múltiplos inteiros do pixel; exige SRC projetado e não reprojeta.
  - Códigos inteiros preservados (inclusive não consecutivos, como 125 e 158) ou renumerados;
    campos textuais em ordem alfabética; campos decimais recusados.
  - A legenda gravada contém apenas o FUNDO e as classes com células, como o Vista SAGA grava.
  - `.rs2.json` com SRC, correspondência de códigos e células por classe; relatório de
    sobreposições, feições ignoradas e classes sem células.
- **Correção do formato RS2**, a partir de um arquivo regravado pelo próprio Vista SAGA: a legenda
  admite códigos não consecutivos (por exemplo, 0, 125 e 158 com n = 3), a paleta é indexada pelo
  código e fica logo após a matriz, e bytes residuais no fim do arquivo são tolerados. Antes, o
  leitor recusava esses arquivos. Leitura por código, e não por posição, também em RS2 → GeoTIFF,
  GeoTIFF → RS2, RGB, RS2 → Vetor, GeoTIFF → Vetor, Monitoria e Combinação de Mapas. Legendas
  consecutivas continuam idênticas byte a byte.
- **Correção do cabeçalho RS2 (avaliação do Vista SAGA):** a quantidade de classes ocupa 2 bytes
  e é seguida do código de cada classe, inclusive a primeira. RS2 de avaliação (notas 1–10 e
  FUNDO com código 11, sem código 0) eram recusados com "Quantidade de classes RS2 inválida".
  O FUNDO passa a ser o código 0 ou a classe chamada FUNDO, usado como NoData e omitido na
  vetorização. GeoTIFF → RS2 sem metadados deixa de acrescentar um código 0 vazio.
- **SRC nas conversões a partir de RS2** (RS2 → GeoTIFF e RS2 → Vetor): o RS2, inclusive o do
  Vista SAGA original, não registra o SRC, e as saídas ficavam com SRC desconhecido quando o campo
  "SRC do RS2" estava em "Não definido". Agora o último SRC escolhido é lembrado entre sessões
  (separado do SRC opcional de GeoTIFF → Vetor); o SRC registrado no `.rs2.json` de RS2 criados
  pelo plugin é usado automaticamente; e converter sem SRC exige confirmação. O SRC nunca é
  deduzido das coordenadas.
- **Exceções GDAL:** a nova operação usa o escopo local da 1.0.5; sem GDAL instalado, o escopo
  deixa de importá-lo antes das validações de entrada.
- Mensagens novas traduzidas para o inglês.
- **Validação:** builds de teste 1.0.5-dev1 a dev3 avaliados no Vista SAGA original (Windows); o
  caso de pluviometria com códigos não consecutivos foi corrigido no dev3 e validado. O pacote
  1.0.6 completo (incluindo a 1.0.5) ainda precisa ser homologado no QGIS e no Vista SAGA.

## 1.0.5 — versão de estabilidade (2026-11-07)

Nenhum algoritmo numérico foi alterado; os identificadores `geosaga:*` foram preservados.

- **Tradução das mensagens de erro e avisos.** As cerca de 700 mensagens de validação e erro passam a ser exibidas no idioma do QGIS. O catálogo aceita modelos com marcadores (`{0}`), o que traduz também mensagens montadas em tempo de execução e mensagens aninhadas. Idiomas sem catálogo usam inglês.
- **Exceções GDAL com escopo local.** As conversões RS2/GeoTIFF/vetor ligavam `gdal.UseExceptions()` de forma global e permanente, alterando o comportamento do GDAL para todo o QGIS e para outros complementos. Agora as exceções valem apenas durante a operação, e o estado anterior é restaurado (`gdal_scope.py`).
- **Pastas temporárias.** Na rasterização de vetores, os datasets GDAL são fechados antes da remoção da pasta temporária. No Windows, arquivos abertos impediam a limpeza e substituíam a mensagem real (por exemplo, "Operação cancelada") por um erro de permissão.
- **Assinatura (Processing e módulo).** A reprojeção usa o contexto de transformação da execução, e falhas de reprojeção de feições geram mensagem clara em vez de exceção crua.
- **Compatibilidade com GDAL ≥ 3.11.** Uso do driver vetorial `MEM`, com alternativa `Memory` para versões anteriores.
- **Qt6/QGIS 4.** Tipos de campo `QMetaType` no lugar de `QVariant`, obsoleto.
- **Diagnóstico.** Falhas inesperadas são registradas com traceback na aba "Vista Saga Plugin" do painel de mensagens. A descarga do complemento não é interrompida por falha em um único módulo.
- **Consistência.** Títulos "GeoSAGA" visíveis substituídos por "Vista Saga"; `run_evaluation` aceita configuração em texto JSON; imports não utilizados removidos.
- **Pacote.** Notas de testes de versões candidatas removidas do pacote de instalação; `LICENSE.md` renomeado para `NOTICE.md`.
- **Verificação.** QGIS 4.2.3 (Qt 6.11, PyQt 6.11, GDAL 3.13) em Linux: 35 testes unitários; 45 testes de integração (carga/descarga, 7 diálogos, 3 algoritmos Processing, todos os motores, cancelamento sem arquivos residuais, entradas inválidas, estado global do GDAL) com e sem exceções GDAL globais; e teste de estresse da interface em português e inglês, sem exceções não tratadas.

## 1.0.4 — versão estável para publicação (2026-10-31)

- Reconhecimento do idioma da interface do QGIS, com português brasileiro e inglês homologados.
- Botão principal com ícone de mão e globo, menu único com os sete módulos, sem painel intermediário.
- Compatibilidade visual com a interface clássica e a guia Complementos do QRibbonSkin; mantido o indicador de submenu no canto inferior para esta versão.
- Atualização do endereço oficial do projeto para https://vistasagaplugin.wordpress.com/.
- Validação funcional relatada pelo responsável em Windows 11 e Linux/Flatpak.
- Preservação dos algoritmos e identificadores geosaga:*; espanhol permanece parcial.

## 1.0.4-rc10 (teste — menu padronizado no QRibbonSkin)

- Encurta o rótulo da ação e o título do submenu para **Vista Saga Plugin**.
- Mantém a descrição longa apenas na dica de ferramenta (tooltip).
- Inclui uma variante do ícone com 19 × 19 px, dimensão padrão dos botões
  principais do QRibbonSkin v1.1.44, sem alterar a identidade visual.
- Mantém QMenu/QAction nativos para menu suspenso de sete módulos com popup
  gerenciado pelo QRibbonSkin, sem personalizar o widget Ribbon.
- Preserva o botão clássico em 24 px e o ciclo de criação/remoção das ações.
- Não altera os algoritmos nem os identificadores de processamento.
- Exige validação visual em QGIS real antes de homologação.

## 1.0.4-rc9 (teste — ícone Vista Saga na Ribbon)

- Corrige a apresentação do Vista Saga Plugin na interface QRibbonSkin,
  passando a registrar somente a ação principal com ícone e submenu em
  Raster > Vista Saga Plugin, além de Complementos.
- Impede que a Ribbon use a ação Assinatura como botão principal, com
  Monitoria/Avaliação e demais comandos em “Outras ferramentas”.
- O submenu continua contendo exatamente sete módulos, em ordem homologada.
- Preserva o botão compacto de 24 px na interface padrão QGIS.
- Mantém inalterados os algoritmos de processamento e os catálogos PT/EN.
- Testes de integração visual no QGIS com QRibbonSkin ainda são necessários.

## 1.0.4-rc8 (teste — ação nativa para QGIS e QRibbonSkin)

- Reduz o botão próprio para 24 px na interface padrão QGIS.
- Usa uma QAction nativa com o ícone oficial e menu suspenso dos sete módulos.
- Registra essa mesma ação também em Complementos > Vista Saga Plugin,
  permitindo que o QRibbonSkin apresente um botão com ícone na guia Complementos.
- Não modifica o QRibbonSkin e não requer dependências externas adicionais.
- Preserva as ações no menu Raster e todos os mecanismos de geoprocessamento.
- Compatibilidade visual com QRibbonSkin exige teste real e reconstrução da
  Ribbon após instalar/atualizar o Vista Saga Plugin.

## 1.0.4-rc7 (teste — barra própria do Vista Saga Plugin)

- Cria uma barra exclusiva, visível no QGIS, com um único botão de menu suspenso.
- Utiliza um QToolButton real, com o ícone multicolorido aprovado e validação de pixmap.
- Não depende de a barra padrão Complementos estar visível.
- Os sete módulos permanecem disponíveis também no menu Raster.
- Sem alterações nos algoritmos, saídas, traduções validadas e identificadores.
- Esta versão exige homologação visual no QGIS 4.x antes de publicação.

## 1.0.4-rc6 (candidata — correção de iconografia)

- Correção do ícone ausente na barra do QGIS: botão baseado em QAction com QMenu.
- Aplicação do símbolo colorido previamente criado de mão e globo geográfico; versões PNG em múltiplas resoluções.
- Remoção limpa da ação e do menu ao desativar o plugin.
- Sem alterações nos algoritmos, identificadores de processamento, relatórios ou traduções homologadas.
- Manutenção do registro de testes funcionais em Windows 11 e Linux/Flatpak.

## 1.0.4-rc5 (candidata de testes)

- Substituição do painel de módulos por botão de menu suspenso no QGIS.
- Aplicação do símbolo visual mão/globo em ícone de plugin e botão principal.
- Registro atualizado: validação funcional em Linux/Flatpak informada pelo responsável.
- A internacionalização de português e inglês aprovada na rc4 foi preservada.
- Motores geoespaciais, identificadores Processing e formatos de dados preservados.

## 1.0.3 — Correções de estilo e qualidade de código

- F402: removida importação local redundante de `QCheckBox` em `combination_dialog.py`.
- E741: variável ambígua `l` renomeada para `candidate_layer` em `evaluation_dialog.py`.
- F811: removida importação duplicada de `QAbstractItemView` em `signature_dialog.py`.
- Nenhum algoritmo matemático, contrato de processamento ou identificador `geosaga:*` foi alterado.

## 1.0.2 — Correção de enums QGIS 4.x/Qt6

- Corrigidos os seis usos de enums legados reportados pelo verificador de compatibilidade: 3 tarefas canceláveis, 2 tipos de geometria em Voronoi e 1 opção de CRS no conversor.
- Nenhum algoritmo matemático ou formato de arquivo foi alterado.
- A aprovação depende de novo exame automatizado no repositório QGIS.

## 1.0.1 — Correção de exceções silenciosas identificadas pelo Bandit

- Removidos dois `except Exception: pass` de `geosaga/rs2_dialog.py` na aplicação opcional de simbologia vetorial RS2 e GeoTIFF.
- Falhas de renderização agora são registradas como avisos no `QgsMessageLog` (canal Vista Saga Plugin), sem invalidar os arquivos exportados.
- A matemática dos módulos e os IDs históricos permanecem inalterados.

## 1.0.0 — Padronização final da interface pública

- Ordem do menu do QGIS e do painel: Assinatura, Monitoria, Avaliação, Análises Voronoi, Combinação de Mapas, Conversão de Formatos e Sequenciador de Mapas.
- Removido “Espacial” dos nomes públicos de Assinatura, Monitoria e Avaliação, inclusive títulos de janelas e tarefas; sem alterar IDs legados `geosaga:*`.
- Nenhuma alteração na matemática dos algoritmos e nos arquivos dos motores de análise.
- Sete módulos homologados funcionalmente no QGIS 4.2.2 para Windows; Linux/Flatpak e comparação numérica com o Vista SAGA/UFRJ continuam sem validação independente.

## 0.8.7 — Sequenciador de Mapas: raster, vetor e misto (candidata a homologação)

- Renomeado o módulo **Sequenciador de Imagens** para **Sequenciador de Mapas**.
- Três abas independentes: Raster (preservado), Vetorial (múltiplas camadas ou período em atributo) e Misto (raster sob vetor ou raster fixo com atributos temporais).
- Suporte a filtro temporal por período ou acumulação, preservando a camada original com materialização temporária e estilo copiado.
- Exportação em GIF com PNGs individuais opcionais, sem FFmpeg/Pillow em produção.
- Grade comum, cores/simbologia do QGIS, título/ano, legenda categórica limitada e prévia.
- Os motores de Voronoi, avaliação, monitoria, assinatura, conversão e combinação não foram modificados.
- Homologação gráfica no QGIS 4.2.2 Windows e Linux/Flatpak pendente.

## 0.8.6 — Otimização verificada e diagnóstico de desempenho

- Nas modalidades Com Atrito e Com Massa e Atrito, os trajetos são interrompidos antecipadamente quando o custo acumulado, que não pode diminuir, já ultrapassou o limite que permitiria vencer o melhor centro. Mantém empates, NoData, pesos de massa e interpretação das células.
- Relatório TXT e metadados GeoTIFF informam tempo do cálculo matricial, trajetórias avaliadas, trajetórias interrompidas durante o percurso, visitas a células e descarte prévio de pares centro–célula.
- Benchmarks sintéticos controlados e testes de equivalência com o procedimento exaustivo; ganhos de tempo não garantidos para todas as bases.
- Interface do Sequenciador de Imagens não alterada; mantida a necessidade de homologação gráfica no QGIS 4.2.2. `geosaga` permanece como identificador técnico. Não é versão 1.0 nem validação matemática com Vista SAGA/UFRJ.

## 0.8.5 — Restauração do nome público

- Nome público **Vista Saga Plugin** restaurado nos metadados, menu Raster, painel, diálogos e provedor Processing.
- Módulo **Análises Voronoi** e interfaces de atrito múltiplo mantidos.
- Sem alterações nos cálculos; pacote Python `geosaga` e IDs de algoritmos preservados.
- Teste funcional no QGIS 4.x permanece recomendado.

## 0.8.4 — Correção da interface de atrito múltiplo

- Seleção e edição das superfícies movidas para uma janela própria de tamanho adequado; acessível pelo botão **Selecionar e configurar superfícies…**.
- Ao marcar o modo de atrito múltiplo, a janela de seleção se abre automaticamente na primeira utilização.
- Inclusão múltipla de rasters do projeto ou arquivos GeoTIFF, remoção múltipla, pesos e notas por classe editáveis em tabela.
- Janela principal com rolagem e resumo da quantidade de superfícies configuradas.
- Motores matemáticos e saídas dos demais módulos preservados.
- Teste gráfico Qt6/QGIS 4.x ainda necessário.

## 0.8.3 — Padronização e superfícies múltiplas (experimental)
- Nome público: VistaSagaPlugin. Módulo: Análises Voronoi.
- No Voronoi com atrito, combinação de até 12 superfícies com pesos e notas por categoria, validando SRC e grade; NoData vira barreira.
- Relatório TXT e metadados raster registram composição, pesos e fórmula. Sem mudança dos algoritmos de avaliação raster/vetorial e das modalidades de Voronoi simples/massa.
- `geosaga` (diretório e IDs Processing) preservado para compatibilidade.
- Métodos com atrito seguem experimentais até comparação quantitativa com Vista SAGA/UFRJ.

## 0.8.2 — Correção de progresso Voronoi no Qt6

- `QgsTask.progressChanged` agora chega a um `@pyqtSlot(float)` na thread da interface,
  que converte e limita os valores para `int` antes de chamar `QProgressDialog.setValue`.
- Ignora notificações de progresso pendentes após o término/cancelamento.
- Nenhuma alteração nos motores de cálculo das quatro modalidades de Voronoi,
  nos cinco módulos anteriores ou no Sequenciador de Imagens.
- O Voronoi com Atrito e com Massa e Atrito continuam experimentais.

## 0.8.0 — Sequenciador de Imagens (GIF) — candidata de homologação

- Sétimo módulo acessível no Painel e no menu Raster: sequenciamento de mapas georreferenciados em GIF animado.
- Exportação sem dependências de FFmpeg/Pillow, prévia Qt, ordenação dos mapas, datas, extensão e SRC comuns, simbologia dos rasters, legendas opcionais.
- Código GIF com preservação exata das cores quando a sequência usa <=256 cores; quantização 3-3-2 em demais casos.
- Mantida a quarta modalidade de Voronoi com Massa e Atrito introduzida na 0.7.5, experimental e aguardando validação contra o software original.
- Sem mudanças intencionais nos algoritmos de Avaliação, Monitoria, Assinatura, Combinação e Conversão.

## 0.7.5 — Voronoi com Massa e Atrito (experimental)

- Quarta modalidade integrada; campo de massa e superfície de atrito habilitados em conjunto.
- Ponderação do índice de atrito acumulado por massa positiva, em tarefa do QGIS.
- Corrigida variável de referência não inicializada em saída permanente da modalidade de atrito.
- 273 testes automatizados; falta homologação com PyQGIS/Qt6 e comparação numérica ao Vista SAGA original.

## 0.7.4 — Voronoi com Atrito (experimental)

- Novo processamento em grade de atrito ao longo de segmentos retos (DDA), custo basal explícito, NoData como barreira, raster/GeoPackage e relatórios.
- Seleção do raster de atrito na interface, herança de extensão, resolução e SRC.
- Modelo limitado em custo computacional; não reivindica equivalência com o executável original até validação comparativa.
- Mantidas as rotinas anteriores, inclusive tarefas assíncronas QgsTask.

# 0.7.2 — Otimização e correção do Voronoi raster

- Remove o bloqueio artificial de 300 milhões de comparações.
- Processa em janelas de aproximadamente 200 mil pixels.
- Aceleração espacial opcional (SciPy cKDTree) no Voronoi Simples, com fallback NumPy.
- Mantém todas as funcionalidades 0.7.1; atrito permanece futuro.

## 0.7.1 — Voronoi (ajuste de fluxo)

Voronoi Simples não exige massa nem raster de referência. Permite extensão pelo mapa, por camada poligonal, manual ou pontos + margem. Saída GeoPackage vetorial direta, sem rasterização; saída GeoTIFF e poligonização continuam disponíveis. Voronoi com Massa permanece raster nesta etapa. Os modos com atrito continuam reservados.

## 0.7.0 — Voronoi Espacial (etapa I)

- Novo cartão e menu Voronoi Espacial no painel.
- Cálculo simples e ponderado por massa (maior M/d), com grade raster e GeoPackage opcional.
- Campo de massa, pontos geradores, raster de referência opcional e saídas temporárias.
- Relatórios quantitativos TXT/CSV e legenda categorizada.
- Atrito e massa+atrito explicitamente reservados a 0.7.1 / 0.7.2.
- Equivalência matemática com o Vista SAGA original ainda NÃO certificada por mapas de referência.
- Preserva motores de avaliação, monitoria, assinatura, combinação e conversão.

## 0.6.5 — Padronização visual das abas da Assinatura Espacial

- `QTabBar.setExpanding(False)` aplicado exclusivamente às abas Raster e Vetorial da Assinatura Espacial; agora permanecem compactas e alinhadas à esquerda, como nos demais módulos.
- Formulários, indicadores, algoritmos, relatórios, conversões e demais janelas permanecem iguais aos da 0.6.4.
- Registrado teste automatizado de regressão para a apresentação compacta das abas.
- Correção de código verificada localmente; a inspeção gráfica final deve ser feita no QGIS 4.x.

## 0.6.4 — Correção pontual do erro de interface

- Removida a importação local redundante de `QPushButton` em `VectorOverlayEvaluationDialog._build()`, que provocava `UnboundLocalError` ao abrir a aba de sobreposição.
- Mantidas a interface e as rotinas de cálculo da versão 0.6.3.
- Incluído teste de regressão estática para detectar retorno do mesmo erro.

## 0.6.3 — Correção de abas e painel

- Formulários vetoriais de Avaliação e Monitoria corrigidos como QWidget embutidos em QScrollArea.
- Diagnóstico de falhas de montagem exibido no formulário e no log do QGIS.
- Descrições dos cinco cartões restauradas; informação de autoria, filiação IGDEMA/UFAL e independência no rodapé.
- Motores de cálculo preservados.

## 0.6.2 — Usabilidade e coerência das abas

- A **Avaliação Espacial** passa a mostrar os controles completos de atributos e sobreposição nas próprias abas. A lógica de pesos, categorias, notas, exclusões, relatórios e saídas vetoriais é a mesma da 0.6.1.
- A **Monitoria Espacial** mostra os dois períodos vetoriais, campos de classes e legendas, execução e destino diretamente na aba Vetorial; os resultados raster/vetorial são acessíveis na aba Resultados. Os motores raster e vetorial são preservados.
- O painel de módulos agora tem **cinco cartões iguais**: Avaliação, Monitoria, Assinatura, Combinação e Conversão. O texto exibido abaixo do título passa a ser apenas: “Escolha um módulo para começar. Uma nova janela será aberta para cada módulo.”
- **Assinatura Espacial** e **Combinação de Mapas** não sofreram alterações em suas interfaces ou cálculos.
- Os formulários vetoriais são criados somente quando a aba respectiva for selecionada; não há instanciação de processamento adicional ao abrir o painel.
- Testes automatizados de núcleo e verificações estruturais não substituem testes de uso da interface real em QGIS 4.x.

## 0.6.1

- Abas Raster/Vetorial, seleção múltipla e saídas temporárias; veja INTERFACE_SAIDAS_TEMPORARIAS_061.md.
- Núcleos analíticos da versão 0.6.0 preservados.

## 0.6.0 — Combinação de Mapas

- Novo módulo com interface gráfica e acesso pelo painel e menu Raster.
- Combinação categórica raster por tuplas, GeoTIFF Int32, CSV e TXT, sem pesos ou notas.
- Combinação vetorial por interseção de duas ou mais camadas poligonais, com GeoPackage, atributos e áreas.
- Legendas de combinação recuperáveis na conversão do GeoTIFF combinado em vetores.
- Validação de origem, SRC, alinhamento, NoData, conflitos geométricos e substituição de saídas.
- Módulos da versão 0.5.2 preservados. Consulte COMBINACAO_MAPAS_060.md.

## 0.5.2 — Padronização de interfaces e terminologia

- Painel preservado com Avaliação Espacial, Monitoria Espacial e Assinatura Espacial.
- Botão **Fechar** na avaliação raster, avaliação vetorial por atributos, avaliação por sobreposição e monitoria raster; fechamento bloqueado enquanto houver tarefa em execução.
- Os botões de fechar do Conversor, Assinatura e Monitoria vetorial permanecem como na versão anterior.
- Títulos de relatórios TXT atualizados para terminologia espacial, mantendo estrutura e campos de saída.
- Identificadores de algoritmos `geosaga:*`, estrutura dos projetos e cálculos não sofreram alterações.

## 0.5.1 — Assinatura vetorial: tratamento de sobreposições

- Polígonos temáticos da mesma categoria são dissolvidos dentro de cada área de análise; não duplicam área.
- Interseções reais entre classes diferentes podem ser excluídas da distribuição (padrão) ou impedir a análise (modo estrito, escolhido no formulário). Nunca existe atribuição arbitrária de uma área a duas classes.
- O CSV e o TXT incluem área em conflito (ha) e porcentagem sobre a área de análise; o GeoPackage recebe `AREA_CONF_HA` e `PCT_CONF`.
- Os percentuais por classe mantêm como denominador somente a área validamente atribuída a uma classe. Interseções conflitantes não entram nesse denominador.
- Raster, Avaliação Espacial, Monitoria, conversor e as saídas anteriormente homologadas permanecem inalterados.
- Teste funcional com PyQGIS/GDAL no QGIS 4.x permanece necessário.

## 0.5.0 — Assinatura Ambiental interativa

- Interface própria no painel de módulos e no menu Raster; menus Processing da Assinatura retirados do fluxo operacional, com `geosaga:assinatura` mantido no provedor para compatibilidade.
- Assinatura de raster categórico monobanda dentro de cada área poligonal, por centro de pixel, com exclusão de NoData e nomes do raster quando conhecidos.
- Assinatura de polígonos temáticos por interseção exata com áreas de análise. Recusa sobreposição geométrica dos polígonos temáticos na mesma área para evitar duplicidade de superfície.
- Relatórios UTF-8 CSV/TXT de classes e percentuais por área, com GeoPackage de polígonos contendo área total, área temática coberta, cobertura percentual, número de classes e classe predominante.
- Validação de SRC e geometrias, progressão, cancelamento e publicação coordenada dos três arquivos.
- **Limite:** em raster geográfico não estima hectares dos pixels; usa contagens e percentuais. Os vetores usam cálculo elipsoidal ou unidades projetadas.
- Base: versão 0.4.3 homologada, sem alteração dos motores anteriores.

## 0.4.3 — Monitoria vetorial direta

- Comparação entre duas camadas poligonais por `native:intersection`, sem rasterizar.
- Interface compacta acessível pela Configuração da Monitoria, com campos
  de classes e de legendas para os dois períodos.
- GeoPackage com transições categóricas, campos descritivos e áreas m²/ha/%.
- CSV de transições, matriz em hectares e relatório TXT com ressalvas metodológicas.
- Mantidos o painel e todos os procedimentos raster da versão 0.4.2.

## 0.4.2 — Monitoria compacta e atributos vetoriais

- Janela da Monitoria com abas Configuração/Resultados e opções avançadas inicialmente recolhidas.
- Mapa de transições inclui metadados de legenda, quando pequenos o suficiente; o CSV associado é lido na vetorização.
- GeoTIFF → Vetor: transferência de classes inicial/final, situação, legendas de mudança e permanência; campos AREA_M2, AREA_HA e PCT_AREA.
- Simbologia categorizada na abertura do vetor exportado.
- Mantidos os cálculos de monitoria raster, suas matrizes e o teste MK.
- Monitoria diretamente entre vetores fica em avaliação para versão futura.

## 0.4.1 — Legendas descritivas e tendências temporais

- Legendas `Permaneceu` e `Deixou de ser ... | Tornou-se ...` no QGIS e no CSV/TXT; opção de códigos mantida.
- Importação opcional de nomes de classes por tabela CSV distinta para períodos inicial e final.
- Seleção opcional de mapas adicionais por ano; séries de 5 ou mais datas geram estatísticas Mann–Kendall por porcentagem de ocupação, inclinação de Sen e correção FDR BH; com 2 datas, informa claramente `NAO_APLICAVEL` e não gera p fictício.
- Saída adicional `_tendencias_mk.csv`, proteção do conjunto de arquivos, tolerância a deslocamento inferior a 0,000005 pixel.
- Avaliação Espacial, Conversor e Assinatura sem alterações.

## 0.4.0 — Monitoria Ambiental interativa

- Painel e menu abrem a janela de Monitoria sem exigir Processing. Algoritmo `geosaga:monitoria` continua registrado para projetos existentes.
- Seleção de dois rasters categóricos locais, carregados no QGIS ou por caminho; rótulos dos períodos e título do estudo.
- Verificação de dimensões, geotransformação e SRC; máscaras NoData e NaN; sem reprojeção ou reamostragem implícita.
- Mapa GeoTIFF categórico de transições (IDs estáveis), matriz de contingência CSV, CSV detalhado e resumo TXT.
- Cálculos de pixels/percentuais por transição e permanência/mudança; área em ha apenas quando o SRC é projetado e as unidades são conhecidas.
- Execução por QgsTask, indicador de progresso e cancelamento; resultados anteriores preservados caso haja falha.
- Sem alterações nos módulos de Avaliação Espacial, conversor, Assinatura, nem nas bibliotecas legadas.

## 0.3.12 — Relatórios de Avaliação Espacial e áreas (14/10/2026)

- Novo relatório de combinações por nota final em TXT e CSV, seguindo a organização do exemplo histórico do Vista SAGA fornecido pelo usuário.
- Para raster: registro das combinações de classes durante a própria avaliação, sem releitura; contagens de pixels, notas, pesos, produtos, percentuais, áreas quando SRC projetado e metragem linear conhecida; área em hectares não é inventada para graus geográficos.
- A classificação da nota final nos relatórios usa arredondamento half-up; o GeoTIFF mantém notas ponderadas decimais sem alteração.
- Para vetores por atributos e por sobreposição: novos campos AREA_M2, AREA_HA e PCT_AREA, além dos campos de nota e auditoria; relatórios de combinações e áreas por classe final.
- SRC geográfico em vetores: área elipsoidal com QgsDistanceArea; CRS projetado: área planar convertida para m² pelas unidades lineares WKT.
- Relatórios TXT/CSV opcionais, habilitados por padrão; publicação coordenada dos três arquivos vetoriais com possibilidade de restauração em falhas.
- Demais operações do conversor RS2/GeoTIFF/Vetor e módulos Monitoria/Assinatura preservados.
- A interface e a gravação espacial reais requerem homologação em QGIS 4.x no Windows e Linux/Flatpak.

## 0.3.10
- Avaliação Espacial vetorial por atributos em camada poligonal com pesos, notas, exclusões e GeoPackage; campo de pontuação e notas individuais.
- Acesso pela interface Avaliação Espacial; painel de módulos e núcleo raster preservados.
- Teste unitário independente do QGIS e teste integrado para executar no QGIS 4.x.
- Sobrescrita protegida por geração temporária; projeto de regras vetoriais e sobreposição espacial ficam para a próxima etapa.

## 0.3.9 — Vetorização de rasters contínuos (14/10/2026)

- GeoTIFF Float32/Float64 de Avaliação Espacial aceito em GeoTIFF → Vetor.
- Divisão do intervalo de valores em 2 a 20 classes de igual amplitude (5 padrão), configuráveis nas opções avançadas.
- Geração dos atributos `CODIGO`, `CLASSE`, `COR_HEX`, `VALOR_MIN` e `VALOR_MAX` para resultados contínuos.
- NoData, NaN e infinito omitidos; valor 0 permanece quando válido. GeoTIFF original não modificado.
- Demais rotinas e módulos preservados; vetorização testável no QGIS 4.x.

# 0.3.8 — Rasterização de vetores

- Quinta operação **Vetor → GeoTIFF** no mesmo conversor, sem substituir os quatro modos anteriores.
- Arquivos vetoriais locais em GPKG, SHP, GeoJSON e FGB; seleção de camadas carregadas no QGIS.
- Campo de entrada e tamanho do pixel configuráveis; preservação do SRC projetado original.
- Campos inteiros/decimais preservados; campos de texto codificados como classes.
- Legendas e cores HEX dos atributos são incorporadas quando disponíveis; fundo categórico = 0.
- Configuração avançada ALL_TOUCHED, progresso/cancelamento, publicação transacional e carregamento da saída.
- Testes unitários e script de integração QGIS acrescentados; homologação no QGIS ainda necessária.

# 0.3.7 — Consolidação funcional e Avaliação Espacial

- Versão 0.3.6 homologada e adotada como base funcional para o projeto.
- Painel de módulos confirmado como componente permanente até a versão 1.0.
- Nomenclatura do módulo alterada para **Avaliação Espacial**, mantendo o cálculo raster intacto.
- Acesso redundante de Avaliação pelo Processing removido do menu Raster;
  o algoritmo registrado `geosaga:avaliacao` permanece disponível para retrocompatibilidade.
- Preservados os projetos `.geosaga.json` e os IDs internos dos algoritmos.
- Modalidade vetorial avaliada tecnicamente e documentada; não implementada nesta versão.
- Nenhuma modificação na rotina RS2 ↔ GeoTIFF nem nas vetorizacões RS2/TIFF.

# 0.3.6 — GeoTIFF → Vetor (inclusão pontual)

- Quarta operação no conversor: GeoTIFF → polígonos em GPKG, SHP, GeoJSON e FlatGeobuf.
- GeoTIFF monobanda categórico: preserva o código inteiro dos pixels, legendas/paleta ou metadados `.tif.rs2.json`, SRC e geometria.
- TIFF RGB/RGBA classificado: códigos criados por cor HEX (não são códigos históricos), com limites de cores; evita interpretar a banda vermelha como classe.
- Reutiliza opções vetoriais existentes (FUNDO, 4/8 vizinhos, seleção de camadas QGIS, lote, progresso, sobrescrita segura).
- Demais módulos e funções da 0.3.5 preservados sem mudança em seu processamento.
- Regressões e teste de integração QGIS adicionais; validação na instalação real do QGIS 4.x ainda necessária.

# 0.3.5 — Interface reorganizada e vetorização RS2

- Layout próximo às ferramentas Processing do QGIS: Operação, Entrada, Saída, sistema de referência e opções avançadas recolhíveis.
- RS2 → GPKG, SHP, GeoJSON e FlatGeobuf via GDAL/OGR Polygonize, com campos CODIGO, CLASSE e COR_HEX.
- Processamento em lote para conversões vetoriais, com máscara opcional para FUNDO e 4/8 vizinhos.
- Backup/restauração da família de arquivos vetoriais ao substituir saídas; evita sobrescrever camadas abertas no projeto.
- Preserve integralmente o núcleo RS2 ↔ GeoTIFF homologado na 0.3.4.
- Teste adicional de integração no próprio QGIS e documentação RS2_VETORIZACAO.md.

## 0.3.4 — Interoperabilidade, SRC nativo e conversão em lote

- Seletor `QgsProjectionSelectionWidget` com opção SRC não definido.
- TIFFs locais carregados no projeto podem ser escolhidos via `QgsMapLayerComboBox`.
- Conversão em lote: mesmas dimensões/resolução, aviso para grades deslocadas.
- Substituição transacional de TIFF, JSON, XML, TFW/TIFW e preservação de metadados externos.
- Atualização de documentação após confirmação externa de RS2 no Vista SAGA.
- Testes de segurança e regressão.

## 0.3.3 — Entrada detectada automaticamente e RGB sem referência

- Corrigido encaminhamento de entrada `.rs2` ao GDAL (quando modo TIFF → RS2
  permanecia selecionado); direção agora deriva da extensão da entrada.
- RS2 → GeoTIFF e GeoTIFF categórico → RS2 sem arquivos de referência.
- TIFF RGB também pode ser convertido sem RS2 auxiliar, mas os códigos são
  NOVOS e criados a partir das cores, sem herdar semântica dos mapas antigos.
- TIFF sem coordenadas: opção de inserir extensão manual comprovada.
- Evita reaproveitamento silencioso de referências antigas entre mapas.
- Cinco testes adicionais de lógica/mapeamento/validação (34 ao todo);
  cinco ida-e-voltas categóricas RS2 → TIFF → RS2 idênticas byte a byte;
  quatro TIFFs RGB legados importados sem referência mediante extensão manual.
- Nenhuma alteração na matemática dos módulos ambientais.

## 0.3.2 — Compatibilidade TIFF RGB → RS2

- Recuperação por correspondência exata das cores RGB/RGBA para códigos categóricos,
  usando um RS2 original fornecido explicitamente como referência.
- Tratamento seguro de TIFF sem georreferenciamento a partir de grade/legenda do RS2
  correspondente; validação de dimensão e georreferenciamento divergentes.
- Proteção contra paletas ambíguas, cores desconhecidas e substituição do RS2 de referência.
- Sugestões de nomes de saída que preservam arquivos originais.
- Quatro testes reais de ida e volta RGB → RS2 idênticos byte a byte;
  seis novos testes unitários de mapeamento RGB.
- Nenhuma alteração nas rotinas matemáticas dos três módulos ambientais.

## 0.3.1 — RS2 e GeoTIFF categórico

- Leitura integral da variante RS2 observada em cinco mapas de referência,
  com RLE, coordenadas, legendas CP1252 e paleta RGB.
- Conversão para GeoTIFF de banda única, com opção de atribuir EPSG
  confirmado pelo usuário; não atribui zona/datum sem evidência.
- Escrita RS2 experimental de rasters categóricos de banda única.
- Diálogo integrado ao menu Raster e ao painel inicial.
- Testes de regressão para leitor/gravador; documentação de limitações.
- Manutenção integral dos três módulos ambientais da versão 0.3.0.

# Histórico do Vista Saga Plugin

## 0.3.0 — primeira etapa da continuidade incremental

- Nome comercial alterado de GeoSAGA Ambiental para Vista Saga Plugin.
- Preservada a pasta interna `geosaga` e todos os IDs do Processing para permitir atualização em lugar e compatibilidade com projetos de avaliação v0.2.
- Implementado painel de entrada para Avaliação, Monitoria e Assinatura.
- Corrigida importação de `QAction` exigida pelo Qt6.
- Mantido editor existente de Avaliação; Monitoria e Assinatura permanecem no Processing.
- Adicionados testes NumPy/unittest e conferência de registro de algoritmos no QGIS.
- Sem alterações nas fórmulas matemáticas de cálculo do núcleo v0.2.0.

## 0.2.0 — base preservada

- Editor visual de pesos, notas e categorias de Avaliação Ambiental.
- Projetos `.geosaga.json`, resultado GeoTIFF e relatório CSV.
- Algoritmos experimentais de Monitoria e Assinatura Ambiental.

## 0.3.11 — Avaliação Espacial por sobreposição vetorial

- Permite empilhar duas ou mais camadas poligonais independentes na interface gráfica.
- Campo categórico, notas por classe e peso próprios para cada camada.
- Interseção geométrica sucessiva das camadas, validações e resultado em GeoPackage.
- Preserva inteiramente a modalidade por atributos, a avaliação raster, o painel e as cinco operações de conversão.
- Inclui testes de planejamento e um teste funcional sintético para executar no QGIS.
