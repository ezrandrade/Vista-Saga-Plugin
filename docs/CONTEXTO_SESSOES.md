# Contexto entre sessões

Registro das decisões, achados e pendências que ficaram fora do código. Serve para que uma nova
sessão do Claude (ou o próprio autor) retome o trabalho sem depender do histórico de conversas.
Atualize ao fim de cada sessão de trabalho. As entradas mais recentes ficam no topo.

---

## 18/11/2026 — resultados do teste da 1.4.0-dev3 recebidos

- O autor enviou `voronoi_vetorial_5m.zip` e `voronoi_vetorial_20m.zip` (QGIS 4, dev3). Análise em
  andamento nesta sessão.

## 18/11/2026 — decisões pendentes da dev1 fechadas pelo autor

O autor acatou as três recomendações (entram na dev4, junto com o padrão automático e a tolerância de
0,5 m):

1. **Área sem polígono e coluna de atrito vazia = barreira** (sem resultado e sem passagem); o plugin
   não inventa nota; o relatório informa as feições com a coluna vazia. (Já é o comportamento atual.)
2. **Sem opção "legado 1.3"** na interface; resultados antigos se reproduzem com o ZIP/tag da 1.3.0.
   (Já é o comportamento atual; registrar nas notas da versão.)
3. **Nota de atrito 0 bloqueada:** exigir nota > 0 (raster, coluna vetorial e combinação de superfícies),
   com mensagem sugerindo um valor pequeno (ex.: 0,1) para "quase sem atrito". Motivo: custo zero cria
   empates resolvidos pela ordem dos pontos, e o comportamento do Vista SAGA com nota 0 não foi testado.
   **A implementar na dev4** (`check_rating`, `validate_friction`, `voronoi_friction_stack`, mensagens
   en/es, testes que hoje usam nota 0).

## 18/11/2026 — proposta para a 1.4.0-dev4: padrão automático, tolerância pela escala dos dados

- O autor questionou o campo "Espaçamento da busca" (parece raster) e propôs um padrão único, aceitando
  a área de influência como estimativa. Discussão: (1) incerteza das entradas domina: +10% numa nota
  ou massa muda 0,4-1% da área (0,2-0,5 ha no caso de teste); PEC Classe A (Decreto 89.817/1984) a
  1:10.000 = 5 m (EP 3 m); logo 1 cm de tolerância é falsa precisão; (2) mas os defeitos corrigidos na
  dev3 eram topológicos, sistemáticos, silenciosos e dependentes de parâmetro arbitrário: a conferência
  automática (topologia) fica inegociável.
- Escala dos polígonos de atrito do autor: **1:10.000**.
- Medição (caso de teste, espaçamento 10): tolerância 0,01 / 0,1 / 0,5 / 1 m → vértices 902 / 520 /
  385 / 371; 0,8 / 0,6 / 0,5 / 0,5 s; coincidência com o Vista SAGA 99,60% em todas; maior diferença de
  área frente a 1 cm: 0 / 16 / 27 / 72 m².
- **Aprovado pelo autor (18/11):** tolerância padrão 0,5 m e a ordem (primeiro o teste da dev3, depois a
  dev4). Plano da dev4: sem o campo; espaçamento automático (≈ 1/200 do maior
  lado da extensão, ≤ 1/4 da largura média do polígono de atrito mais estreito, teto de ~100 mil nós);
  tolerância padrão 0,5 m (1/6 do EP a 1:10.000), limitada a extensão/2000 em áreas pequenas; ambos
  no `_resumo.txt`; conferência de topologia mantida. **Próximo passo:** aguardar os resultados do
  teste da dev3 (de preferência com espaçamento de 20 m) e então implementar a dev4.

## 18/11/2026 — resultados do teste da 1.4.0-dev2 recebidos

- O autor enviou `Voronoi_Vetorial.zip` (QGIS 4, guia Vetorial, 4 modalidades). Partição exata nas 4;
  coincidência com o Vista SAGA: Simples 99,96% (2 empates), Com Massa 100%, Atrito 99,50% (espaçamento
  5), Massa e Atrito 99,60% (espaçamento 20). Áreas estáveis entre espaçamentos (0,1-0,4 cm médios).
- **Defeito achado no teste do autor:** Massa e Atrito com espaçamento 20 m: região A em 2 partes (um
  triângulo de 3 m² separado por um fio de C de 0,14 mm). Causa: lado de célula com duas trocas de
  região (C→A→fora) perto da borda; a junção caiu na célula errada. O autor notou que mudar o
  espaçamento faz o defeito sumir (coerente: depende de onde caem as células).
- Correções (não commitadas como versão; WIP na branch): (1) lado com duas trocas se denuncia pelo
  rótulo ao lado da troca achada ≠ rótulo da ponta → as duas células se dividem em 4, recursivamente;
  (2) faces-fio (largura média < 2 × tolerância) vão ao vizinho de maior fronteira comum; (3) corda
  conferida em 1/4, 1/2 e 3/4 (uma cunha fina de B de 5 m × 2 m no canto do corredor era cortada, com
  desvio de até 2 m), dividida no ponto do meio; busca da fronteira com alcance crescente.
  Resultado no caso: 1 parte por região em qualquer espaçamento (5-40 m); >99,9% dos pontos de
  fronteira a < 2 cm da verdadeira; pontas de cunhas encurtadas em até ~0,5 m (área desprezível).
  A afirmação "desvio máximo de 1 cm" foi corrigida para "tolerância de 1 cm" + ressalva (relatório,
  interface, notas).
- **Em aberto:** `test_random_polygons_partition_and_labels` falha: faixa estreita (~7 m) da região 2
  entre duas partes da região 4 atravessa o lado de uma célula de 15 m com as duas pontas iguais
  (4→2→4): troca dupla invisível, ~100 m² com rótulo errado. É a limitação declarada ("detalhes menores
  que o espaçamento"), mas silenciosa. Proposta: verificação automática das faces (amostras internas)
  com refinamento local, ou aviso ao usuário.
- **Decisão do autor (18/11): opção 1, verificação automática com correção** (conferir pontos dentro de
  cada célula/face; onde houver rótulo inesperado, subdividir e traçar de novo; relatar a conferência).
- **Implementado (dev3):** `trace()` em `friction_voronoi_polygons`: malha adaptativa (dict de células
  (i0, j0, tamanho)), conferência por célula com avaliação em lote (lados: 1/4, 1/2, 3/4 e cantos das
  vizinhas menores; interior: centro e quartos; lado duplo da bisseção), só das células novas e das
  vizinhas das divididas. Conferência final: 1 ponto por célula base (posição fixa 0,618/0,414), contra
  os polígonos; divergência a > 5 × tolerância da fronteira aprofunda a pré-divisão (8 × 8, 64 × 64)
  da célula e vizinhas e refaz o traçado (até 3 passadas; orçamento de 400 mil células). Rotulagem com
  uma passada por polo (poda exata conferida contra avaliação exaustiva). Relatório informa a
  conferência e avisa se restar divergência.
- Provas: caso aleatório 0 divergências e 0/6000 numa amostra independente (espaçamentos 15/30/60 m);
  com as conferências internas novas desligadas, a final achou e corrigiu a faixa estreita (30 m).
  Desligar a conferência dos lados quebra a coerência entre células grossas e refinadas (não é
  opcional). Tempo: caso de teste 0,5-3 s; caso aleatório (9 polos, 13 polígonos) ~4-5 s.
- Suítes: 450 (3 pulados) + 36. QGIS 3.34 offscreen: Vetorial 99,60% / 99,48%, Raster 99,69%.
- ZIP `Vista_Saga_Plugin_QGIS4_v1.4.0-dev3.zip`.

## 17/11/2026 (noite) — 1.4.0-dev2 implementada: vetor direto com atrito

- `geosaga/voronoi_friction_continuous.py` (novo): `FrictionSurface` (polígonos com nota, sobreposição
  = última feição, arestas com interior à esquerda, união = cobertura), custo exato
  A = D²·[Σ ±f·τ²/2 + f(x)/2] por cruzamentos (vetorizado, sem ordenar), barreira = sair da
  cobertura; polo deslocado 1 µm nos testes de cruzamento (o caso de teste tinha segmentos passando
  exatamente por cantos e dava paridade errada). `ContinuousModel.labels` com poda A >= f_mín·D²/2.
  `friction_voronoi_polygons`: malha deslocada (1/π, 1/e do espaçamento), bisseção diádica nos lados
  (pontos idênticos nas arestas comuns), refinamento local 8 × 8 das células com junção/sela,
  propagado quando um lado troca de rótulo mais de uma vez; junção por subdivisão; refinamento de
  corda até a tolerância; poligonização GEOS (noding por união com uma linha, GDAL < 3.7);
  recorte de cada face pelo domínio antes do rótulo, rótulo por pedaço; resíduos finos ao vizinho
  de maior fronteira comum.
- `save_vector_voronoi` aceita 'friction'/'mass_friction' (friction_features, search_spacing).
- Diálogo: guia Vetorial = vetor direto nas 4 modalidades; com atrito, só polígonos + "Coluna de
  atrito" + "Espaçamento da busca" (o campo de resolução, rotulado de novo). Saíram a tabela
  classe → nota e o controle de área sem polígono (barreira fixa). Corrigido: colunas vazias quando a
  camada já vinha selecionada.
- Resultados: caso validado 99,60% (com massa) / 99,52% (sem massa) no centro das células; partição
  exata; nota uniforme = Apolônio a < 1 cm (espaçamento 10-20 m; com 40 m, 6 cm: detalhe perdido).
  QGIS 3.34 offscreen: Vetorial 99,60% em 0,6 s; Raster com polígonos 99,69%. Suítes: 448 (3
  pulados) + 36.
- ZIP `Vista_Saga_Plugin_QGIS4_v1.4.0-dev2.zip`; teste com `caso_atrito_vetorial.gpkg` (coluna ATRITO).

Pendências:
- [ ] Autor testa a dev2 no QGIS 4: guia Vetorial (esperado 99,60% com massa; 99,48% sem) e Raster.
- [ ] Autor confirma: área sem polígono/coluna vazia = barreira; sem "legado 1.3"; nota 0 permitida.
- [ ] Desempenho com dados reais (muitos polos/polígonos) não medido; o custo cresce com
      polos × arestas × nós avaliados.

## 17/11/2026 (noite) — decisões para a 1.4.0-dev2: vetor direto com atrito

- O autor não quer o resultado com atrito obtido por poligonização de raster: **a guia Vetorial passa a
  usar o modelo contínuo** do atrito (A = ∫₀^D s·f(s) ds ao longo do segmento polo → ponto, f = nota
  do polígono atravessado; com massa, A/M), com fronteiras traçadas numericamente até uma tolerância
  declarada. Mostrado ao autor antes da decisão (figuras): no caso validado, o modelo contínuo
  coincide 99,50% (sem massa) e 99,60% (com massa) com o Vista SAGA, contra 99,67%/99,69% do modelo
  discreto da guia Raster; diferenças a menos de uma célula da fronteira. Guia Raster continua no
  modelo discreto do Vista SAGA.
- **Atribuição do atrito simplificada:** só pela **coluna de atrito** da camada de polígonos; sai a
  tabela classe → nota.
- Decisões do orientador, a confirmar com o autor: área sem polígono e feições com a coluna vazia =
  barreira (sem resultado e sem passagem), sem controle manual; na guia Vetorial, superfície de atrito
  só vetorial (polígonos).

## 17/11/2026 (noite) — 1.4.0-dev1 implementada

Decisões do autor (17/11): massa **M/d²**; **atrito vetorial** nas modalidades com atrito, com notas
por **classe** (tabela, como na Avaliação) **ou por coluna**; a **área sem polígono** recebe nota
informada (ou barreira); custo = **nota direta** (sem 1 + C). Sem modelo "legado 1.3" na interface:
quem precisar reproduzir resultados antigos usa o ZIP da versão antiga (decisão do orientador, a
confirmar com o autor).

Implementado na branch `feat/voronoi-atrito-fiel` (versão 1.4.0 no `metadata.txt`):

- `voronoi_core.assign_window('mass')`: d²/M. `voronoi_vector._apollonius_disk`: k = √(M_l/M_p).
- `voronoi_friction.py` reescrito: `_vista_saga_cost_batch` (Bresenham vetorizado, Σ d × nota ×
  passo), poda exata com limite nota_mín × lado² × n(n+1)/2, célula do polo sempre do polo, sem
  `baseline`. Reproduz exatamente os números da validação (16 e 15 células).
- `voronoi_friction_vector.py` (novo): notas por classe/coluna, área sem polígono (nota, barreira
  ou exigência de cobertura total), rasterização pelo centro da célula (MEM/"Memory" do OGR).
- Diálogo: "Tipo de superfície" (Raster/Vetorial), camada de polígonos, "Notas por", campo de
  classe + "Notas das classes…", coluna de atrito, "Área sem polígono" (“—”/nota + Barreira);
  grade da análise (extensão + resolução) também na guia Vetorial com atrito vetorial; o SRC da
  análise é o da camada de polígonos (pontos convertidos, como no atrito raster).
- Modalidades com atrito sem "(experimental)"; textos, metadados e `_resumo.txt` atualizados.
- Testes: 074/081/086 reescritos contra `geosaga/tests/friction_reference.py` (Python puro);
  `test_140_voronoi_vista_saga_case.py` (regressão do caso) e `test_140_friction_vector.py`.
  Suítes: 440 (3 pulados) + 36, verdes.
- Conferência de ponta a ponta em **QGIS 3.34 offscreen** (o do Ubuntu; não é o alvo): caso em
  polígonos → 99,69% (classes, com massa), 99,67% (coluna), 99,69% (guia Vetorial); mensagens de
  cobertura incompleta, polo sobre barreira e classe sem nota conferidas. `gui_monkey`: nenhuma
  exceção no Voronoi (só as do Processing, API exclusiva do QGIS 4).
- ZIP de teste: `Vista_Saga_Plugin_QGIS4_v1.4.0-dev1.zip` + `caso_atrito_vetorial.gpkg`
  (camadas `uso_atrito`, com CLASSE e ATRITO, e `pontos`, nos centros usados pelo Vista SAGA).

Pendências:
- [ ] Autor testa a dev1 no QGIS 4 com `caso_atrito_vetorial.gpkg` (esperado: 99,69% com massa e
      classes; 99,67% com atrito e coluna; Simples e Com Massa 100%, exceto empates).
- [x] Esclarecido pelo autor (17/11): o desenvolvimento do plugin é separado da tese, que fica fora
      destas sessões. Não perguntar sobre mapas da tese nas sessões do plugin; o autor chama quando
      voltar à tese. O rigor de método do `CLAUDE.md` continua valendo para o plugin.
- [ ] Autor confirma: sem opção "legado 1.3" na interface.
- [ ] Nota 0: permitida (custo zero), comportamento do Vista SAGA com nota 0 não testado.
- [ ] Leitura/gravação do arquivo de pontos do Vista SAGA (contagem a partir de 1): não feito.

## 17/11/2026 (noite) — decisões do autor para a 1.4.0

- **Massa: M/d²** (como o Vista SAGA), no raster e no vetor exato (discos de Apolônio com razão √M).
- **Atrito com superfície vetorial** nas modalidades Com Atrito e Com Massa e Atrito (pedido do autor).
- Perguntas sobre a tese (mapas da 1.3, significado da massa): fora do escopo destas sessões, por
  decisão do autor (ver entrada da dev1).

## 17/11/2026 (noite) — reteste no QGIS com os pontos corrigidos: Simples homologado

O autor refez o vetorial com `docs/caso_atrito/pontos_qgis.csv` (`Voronoi_Plugin_{Simples,Massa}_2.gpkg`).
`python3.12 scripts/comparar_vetor_plugin.py VS PLUGIN _2 qgis`:

- **Simples: 99,96% (2 células), e as 2 são empates exatos** entre B e C (células 45:23 e 55:26,
  equidistantes). Excluídos os empates, 100%. **Homologado pelo autor no QGIS 4.2.2.**
- **Desempate do Vista SAGA:** nas 4 células empatadas da grade (45:23, 55:26, 65:29, 75:32), vence o
  polo que vem **primeiro no arquivo** (B antes de C). É a mesma regra do raster do plugin (`<` estável
  em `assign_window`). No vetor, o empate é a própria fronteira; a rasterização pelo centro escolhe
  qualquer lado, o que não é erro do plugin.
- **Com Massa: 84,39% (749 células), exatamente o previsto** a partir do código; 100% contra o modelo do
  próprio plugin. Polo C: 512 células no Vista SAGA, 143 no plugin. Diagnóstico confirmado: a
  divergência é só o modelo (M/d × M/d²).

## 17/11/2026 (noite) — vetor do plugin (QGIS 4.2.2) × Vista SAGA

O autor rodou no QGIS o Voronoi **vetorial** Simples e Com Massa (`Voronoi_Plugin_{Simples,Massa}.gpkg`,
SIRGAS 2000 / UTM 25S, extensão igual à do mapa) com os pontos do `pontos_utm.txt`, que estão
**deslocados 1 célula** (+10 m em X, −10 m em Y) em relação ao Vista SAGA, por causa da contagem a
partir de 1. Comparação pelo centro das células: `python3.12 scripts/comparar_vetor_plugin.py VS PLUGIN`.

| | Simples | Com Massa |
|---|---|---|
| plugin × Vista SAGA, bruto | 97,67% (112) | 82,82% (824) |
| plugin × modelo do próprio plugin nos pontos usados | 99,98% (1, empate exato) | **100%** |
| modelo do plugin × Vista SAGA, nos pontos do Vista SAGA | **100%** | **84,39% (749)** |

- **A cadeia do plugin está correta**: camada → SRC → vetor exato reproduz o modelo do plugin. No
  Simples, a única diferença é a célula 46:24, equidistante de B e C (empate na bissetriz).
- **Simples:** a diferença bruta (112 células) vem **só** do deslocamento dos pontos; com os pontos no
  lugar, 100%.
- **Com Massa:** a diferença vem do **modelo** (M/d no plugin × M/d² no Vista SAGA). Polo C (M = 1):
  512 células no Vista SAGA, 143 no plugin; Polo A (M = 9): 2.693 × 3.518.
- Observações menores: no Simples o campo `MASSA` sai 1 para todos (massa ignorada, mas pode confundir);
  o metadado QGIS embutido no GPKG de saída tem SRC vazio (o SRC da camada está certo).
- Para refazer o teste da 1.4.0: usar `pontos_qgis.csv` (centros 500115/8900455, 500595/8900105,
  500715/8900505), gerado nesta sessão.

## 17/11/2026 (noite) — validação caixa-preta do Voronoi contra o Vista SAGA

Comparação célula a célula (`python scripts/comparar_caso_atrito.py PASTA`) das quatro saídas do
Vista SAGA com o caso de teste. Arquivos recebidos: `voronoi_saga_{simples,massa,atrito,massa_atrito}.rs2`
(R4, R3, R1, R2) e `pontos_saga.txt`, este **idêntico byte a byte** ao `pontos_pixel.txt`.

**Confirmado:**

1. **Arquivo de pontos:** `Nome;Massa;X:Y`, sem cabeçalho, CRLF, `[ATRITOS]` com uma nota por classe a
   partir da classe 0; X:Y = **coluna:linha contadas a partir de 1** (12:15 caiu na célula 11:14
   contada a partir de 0, nos quatro resultados).
2. **Saída:** classe 0 "Ponto" marca as células dos polos; classes 1..n = polos, na ordem do arquivo.
3. **Simples:** distância euclidiana entre centros, 100% (0 divergências).
4. **Com Massa (sem atrito): max M/d², não M/d.** min d/√M acerta 100%; o expoente é nítido (k = 0,48
   ou 0,52 já dá 26 e 35 divergências). Coincide com a fórmula do manual, FZ = M/(D × A), em que
   A cresce com D. **O plugin 1.3 usa M/d e diverge em 749 células (84,4%)**, inclusive no vetor
   exato (discos de Apolônio com razão M; a correção é usar √M).
5. **Atrito:** Σ (distância do polo à célula × nota × √2 nos passos diagonais) / M, na reta polo →
   célula: 99,67% (sem massa) e 99,69% (com massa). Era a leitura do executável; agora validada pela
   saída. O "efeito √M" é a mesma propriedade do item 4, presente também sem atrito.
6. Plugin 1.3 (código real, notas 1, 1, 3, 5 como C, basal 1): Atrito 96,73% (157), Massa + Atrito
   98,37% (78).

**Resíduo:** 10 a 16 células, **todas na fronteira entre regiões**, com margem de custo ≤ 10%: detalhe
do traçado (raios até a borda, regra de sobreposição, variante da reta). Raios até a borda com "último
raio vence" dão 10 divergências no Massa + Atrito, mas foram escolhidos entre 32 variantes **no mesmo
caso**: é ajuste, não validação. Decidir entre variantes exige um segundo caso, independente.

**Não testado:** notas 0, classes excluídas, mapas com FUNDO dentro da área, polos na borda.

## 17/11/2026 (noite) — resultados do teste perdidos em sessão bloqueada

- O autor **já rodou o caso de teste no Vista SAGA** e enviou os RS2 de saída numa sessão que foi
  bloqueada antes de qualquer registro; nada chegou ao repositório. É o **segundo bloqueio** (o
  primeiro foi o de 16/11). Causa desconhecida.
- Medidas combinadas: registrar o contexto **no início** da sessão e logo após cada achado (não só
  no fim); validação **caixa-preta** (entrada → saída do Vista SAGA), sem nova análise do executável;
  os RS2 de saída não vão para o repositório (regra do `CLAUDE.md`); só o script de comparação e os
  números resumidos.
- **Reenviado** (`teste_voronoi_atrito_2.zip`). Respostas do autor:
  - funcionou o `pontos_pixel.txt`: coordenadas do arquivo de pontos em **coluna:linha**;
  - notas de atrito exibidas como 1, 1, 3, 5 (lidas corretamente);
  - a versão do Vista SAGA usada **não oferece** a escolha entre M/(d + a) e M/(d × a);
  - não testou atrito igual a 0.

## 17/11/2026 (tarde) — 1.3.0 fechada; caso de teste do atrito

- **1.3.0 fechada e mesclada** (merge `87406de` na `main`). Tag `v1.3.0` pendente (autor).
- **Branch da 1.4.0:** `feat/voronoi-atrito-fiel` ("atrito fiel ao Vista SAGA"). Versão do
  `metadata.txt` ainda 1.3.0: muda junto com a primeira alteração de código.
- **Caso de teste enviado ao autor** (`teste_voronoi_atrito.zip`), reproduzível com
  `python scripts/gerar_caso_atrito.py PASTA` (gera arquivos idênticos byte a byte):
  - `teste_atrito.rs2`: 80 × 60 células de 10 m; bordas X 500000–500800, Y 8900000–8900600;
    classes 0 FUNDO (ausente do mapa), 1 Atrito baixo, 2 Atrito médio, 3 Atrito alto;
    faixa vertical de atrito alto (colunas 30–39) com corredor de atrito baixo (linhas 25–34) e
    bloco alto (linhas 5–19, colunas 55–69);
  - pontos (coluna, linha, a partir de 0): Polo A M=9 (12, 15); Polo B M=4 (60, 50);
    Polo C M=1 (72, 10); notas `[ATRITOS]` 1, 1, 3, 5;
  - `pontos_pixel.txt` (X:Y = coluna:linha) e `pontos_utm.txt` (X:Y = centro da célula), porque
    a unidade das coordenadas não foi confirmada.
- **Roteiro pedido ao autor:** abrir o RS2 e conferir com `mapa_previa.png`; carregar
  `pontos_pixel.txt` (se falhar, `pontos_utm.txt`; anotar qual funcionou e qualquer deslocamento);
  conferir as notas; rodar e salvar R1 atrito sem massa, R2 atrito com massa, R3 sem atrito com
  massa, R4 simples; salvar o arquivo de pontos pelo Vista SAGA (`pontos_salvo.txt`).
- **Próximo passo:** com os quatro RS2 e o `pontos_salvo.txt`, comparar pixel a pixel com a
  simulação da leitura do executável e fixar o modelo da 1.4.0.

## 17/11/2026 — recuperação do contexto da sessão de 16/11 (noite)

A sessão de 16/11 que produziu a 1.3.0 foi interrompida por bloqueio automático antes de registrar
o contexto. O resumo abaixo foi reconstruído a partir do histórico dela.

### Estado da versão 1.3.0

- **Branch:** `feat/voronoi-saida-vetorial`; **PR:**
  [ezrandrade/Vista-Saga-Plugin#12](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/12),
  sem merge.
- **Build de teste:** `Vista_Saga_Plugin_QGIS4_v1.3.0-dev3.zip` = commit `9476819`.
  O autor testou no QGIS e aprovou ("Deu certo").
- Conteúdo: ver `geosaga/NOTAS_DA_VERSAO_130.md` e `geosaga/CHANGELOG.md`.
- **Decisão do autor (17/11):** fechar a 1.3.0 como está e tratar o atrito na 1.4.0.

### Achado de método: o modelo de atrito do Voronoi

Modelo atual do plugin (experimental desde a 0.7.5):

> escore = D × Σ(1 + atrito de cada célula atravessada) / M

Testes com atrito zero, na sessão de 16/11:

1. **O custo depende da direção.** Segmentos de mesmo comprimento custaram 10.100 (0°),
   13.100 (22,5°) e 7.200 (45°), porque a soma conta células, não comprimento percorrido. Também
   depende da resolução.
2. **No modo Com Massa e Atrito, as massas valem como √M.** Como Σ cresce com D, o escore fica
   proporcional a D²/M. Com massas 1 e 9 e atrito zero, a área do centro leve foi de 4.016
   células, contra 401 no Com Massa; o modelo com √M dá 4.420 (98,3% de coincidência).

**Fonte primária da fórmula:** manual do Vista SAGA (texto enviado pelo autor; não vai para o
repositório por direitos autorais), que define

> FZ(Gi) = M(Gi) / [ D(x→Gi) × A(x→Gi) ], com A = Σ Cₖ sobre as células da trajetória reta.

O manual chama o procedimento de "exploratório". O expoente 1 em M/d vem do manual.

**Análise estática dos programas originais** (sem executar e sem copiar código; só o método).
As conclusões são **leituras do executável, ainda não validadas** com um mapa gerado pelo
Vista SAGA:

| | VORONOI.EXE (ancestral, 16 bits) | Vista SAGA (integrado, 32 bits) |
|---|---|---|
| Fórmula | escolha: M/(d + a), padrão, ou M/(d × a) | sem escolha |
| Percurso | reta de cada célula até cada polo | raios de cada polo até as células da borda |
| Atrito | nota por classe, por trecho de classe constante | nota por classe, célula a célula no raio |
| Acúmulo | soma: (D + Σ notas)/M; produto: Σ(L × nota)/M | Σ (distância do polo à célula × nota × √2 nos passos diagonais) / M |
| Classes excluídas | não | sim (atravessadas, sem resultado) |

- No **Vista SAGA integrado**, a referência da tese, o efeito √M **também existe** (simulação:
  99,8% de coincidência com o modelo √M). Logo, é propriedade do método original, a ser declarada
  na tese, e não erro do plugin.
- Diferenças restantes entre o plugin e o Vista SAGA:
  1. peso do atrito: o Vista SAGA pondera a nota pela distância da célula ao polo; o plugin soma
     células com peso igual e multiplica por D;
  2. custo basal: o plugin usa 1 + C; o Vista SAGA usa a nota direto (padrão 1);
  3. percurso: raios até a borda com √2 nas diagonais × reta célula-polo;
  4. classes excluídas: só no Vista SAGA.
- Não confirmados: a rotina final que preenche células não alcançadas pelos raios; o efeito da
  caixa de atrito desmarcada (provavelmente nota 1 em todas as classes).

**Proposta registrada para a 1.4.0 ("atrito fiel ao Vista SAGA"):**

1. Implementar o modelo do Vista SAGA como padrão; manter o atual como "legado 1.3" para
   reproduzir resultados já gerados.
2. **Validação obrigatória:** o autor roda no Vista SAGA um caso pequeno (RS2 com 3 ou 4 classes,
   3 pontos, massas e notas diferentes) e envia o RS2 de saída para comparação pixel a pixel.
   Sem isso, o modelo "fiel" não é conferido e não serve para a tese.
3. Atrito vetorial depois, convertido em grade (o cálculo do Vista SAGA é célula a célula).
4. Registrar a justificativa escrita da mudança de método (exigência do `CLAUDE.md`).

### Formato do arquivo de pontos do Voronoi

Lido no executável do Vista SAGA integrado (não confirmado com arquivo salvo pelo programa):

```
Nome;Massa;X:Y
Nome;Massa;X:Y
[ATRITOS]
nota da classe 0
nota da classe 1
```

- sem cabeçalho e sem aspas; separador `;`; massa inteira (`StrToInt`);
- coordenada `X:Y`, aparentemente **coluna:linha da matriz**, não metros, apesar do rótulo
  "Coordenada UTM"; não se sabe se começa em 0 ou em 1;
- provável CP1252 e CRLF; separador decimal das notas não verificado.

O arquivo de pontos de exemplo do autor (formato do ancestral: cabeçalho, aspas, sete colunas)
mostrou uma grade implícita de células de 700 m, com a relação exata Leste = origem + 700 × X e
Norte = origem − 700 × Y. Datum e fuso não podem ser deduzidos das coordenadas (regra de SRC do
`CLAUDE.md`): o autor precisa confirmá-los.

### Pendências abertas

- [x] 1.3.0 fechada em 17/11/2026 e PR 12 mesclado a pedido do autor. Tag `v1.3.0` pendente:
      usar o commit de merge do PR 12 na `main` (o autor cria pelo Codespaces).
- [x] Caso de teste gerado e enviado (17/11).
- [ ] Autor roda o caso de teste no Vista SAGA e envia R1–R4 e `pontos_salvo.txt`.
- [ ] Autor responde: o Vista SAGA que usa tem a escolha entre M/(d + a) e M/(d × a)?
- [ ] Autor responde: faixa de valores de atrito usada (há notas 0?).
- [ ] Conversão do arquivo de pontos do autor para o formato do Vista SAGA integrado: interrompida
      pelo bloqueio; o autor precisa reenviar o arquivo.
- [ ] Decidir se o plugin deve ler e gravar o formato de pontos do Vista SAGA (útil para a
      validação cruzada).
- [ ] Definir por escrito o critério de "plugin finalizado" (escopo fechado), proposto pelo
      orientador em 17/11.
