# Vista Saga Plugin 1.4.0 — notas da versão

> Versão estável (19/11/2026). Inclui tudo da 1.3.0. **Muda o método** das modalidades Com
> Massa, Com Atrito e Com Massa e Atrito do Voronoi, para reproduzir o Vista SAGA original.
> Resultados gerados com a 1.3.0 ou anterior nessas modalidades não são reproduzidos pela 1.4.0;
> para reproduzi-los, use o ZIP da versão em que foram gerados.

## O que muda para quem usa

### Com Massa: M/d², como no Vista SAGA

Cada lugar pertence ao centro de **maior M/d²** (antes: M/d). Na prática, uma massa 9 alcança 3
vezes mais longe que uma massa 1, e não 9 vezes.

- Raster: menor d²/M em cada célula.
- Vetor exato: o centro mais leve fica com o disco de Apolônio em que
  d_leve / d_pesado < √(M_leve / M_pesado); entre massas iguais, bissetrizes (como antes).

### Atrito: o modelo do Vista SAGA

Para cada célula e cada polo, o custo acumulado é a soma, nas células da reta (Bresenham) entre a
célula do polo e a célula de destino, de

> distância do polo à célula × nota da célula × passo (lado da célula; √2 vezes na diagonal)

- Com Atrito: vence o menor custo. Com Massa e Atrito: vence o menor custo / massa. Como o custo
  cresce com a distância ao quadrado, a massa vale como M/d², a mesma lei do Com Massa.
- **A nota entra direto como custo** (nota 1 = custo basal do Vista SAGA). Antes, o plugin
  somava 1 + atrito.
- **Nota 0 é recusada** (raster, coluna vetorial e combinação de superfícies): custo zero criaria
  empates entre polos, resolvidos pela ordem dos pontos no arquivo, e o comportamento do Vista SAGA com
  nota 0 não foi testado. Para "quase sem atrito", use um valor pequeno, como 0,1. **Rasters de atrito
  antigos com valor 0 precisam ser revistos.**
- **NoData do raster de atrito** (e de qualquer superfície da combinação): **sem resultado, atravessável
  com nota 1** (dev6), a mesma regra da área sem polígono do atrito vetorial. Até a dev5 era barreira.
  Um centro sobre NoData continua recusado. A célula do polo é sempre dele.
- Empates: vence o polo que vem primeiro na lista (mesma regra do Vista SAGA).
- As duas modalidades deixam de ser marcadas como "experimentais".

### Superfície de atrito vetorial (nova)

Em Com Atrito e Com Massa e Atrito, a superfície de atrito pode ser uma **camada de polígonos**
com a nota numa **coluna de atrito** (escolhida em "Coluna de atrito"; sem atribuição manual).

- Área sem polígono e feições com a coluna vazia **não recebem resultado, mas podem ser atravessadas
  com nota 1** (custo basal do Vista SAGA, padrão da classe FUNDO). Até a dev4 eram barreira; o teste
  com dados reais (uma bacia hidrográfica, côncava) mostrou que a barreira bloqueava a reta polo-ponto
  que sai da área e volta, e os polos alcançavam só 48 a 96% da bacia.
- Em sobreposições vale a última feição.
- **Sem reprojeção:** a camada de polígonos define o SRC da análise (os pontos são convertidos para
  ele, como no atrito raster).

**Guia Vetorial: vetor direto, sem rasterização.** O resultado não é mais a poligonização de uma
grade. O plugin usa a **versão contínua** do modelo do Vista SAGA:

> custo = ∫ (distância ao polo) × (nota) ao longo do segmento reto polo → ponto

calculado exatamente pelos cruzamentos do segmento com as bordas dos polígonos (com massa,
dividido por M). As fronteiras entre as regiões não têm fórmula fechada: são traçadas
numericamente, com a tolerância de 0,5 m (dev4; até a dev3 era 1 cm), a partir de uma malha de busca
escolhida pelo plugin, com refinamento local. Pontas de cunhas muito finas e encontros de três regiões
podem ficar encurtados (área desprezível). Regiões menores que o espaçamento da busca podem não ser
detectadas; a conferência automática (abaixo) reduz muito essa chance. A partição não tem
sobreposições nem lacunas, e a fronteira com a área sem polígono é a borda exata dos polígonos.

**Conferência automática (dev3).** O traçado se confere sozinho, em duas camadas:
- durante o traçado, cada célula da malha de busca é testada nos lados (pontos intermediários, para
  achar trocas de região escondidas, mesmo com a mesma região nas duas pontas) e no interior (centro e
  quartos); qualquer suspeita subdivide a célula e as vizinhas, até estabilizar;
- depois do traçado, o modelo é comparado com os polígonos em um ponto de cada célula da malha de
  busca; se houver divergência longe da fronteira, aquela área é refinada e o traçado é refeito
  (até 3 passadas, com limite de memória).
O `_resumo.txt` informa quantos pontos foram conferidos e quantas divergências restaram; se restar
alguma, avisa para repetir com espaçamento menor. Isso torna visível o que antes era silencioso. A
limitação de fundo continua: um detalhe mais estreito que o espaçamento que não toque nenhum ponto
conferido ainda pode escapar, mas agora com chance muito menor.

**Sem parâmetros de traçado na interface (dev4).** O campo "Espaçamento da busca" saiu. O plugin escolhe
o espaçamento pelos dados (maior lado da extensão / 100, nunca maior que 1/4 da largura média do
polígono de atrito mais estreito, com teto de 100 mil nós) e usa a tolerância padrão de **0,5 m**
(1/2000 do maior lado em extensões pequenas). Justificativa: as áreas de influência são estimativas; a
incerteza das entradas domina (no caso de teste, +10% numa nota ou massa muda 0,4 a 1% da área), e
mapas temáticos 1:10.000 têm erro-padrão de 3 m no PEC Classe A (Decreto 89.817/1984). A tolerância de
0,5 m soma cerca de 1% a esse erro; a topologia (regiões inteiras, sem lacunas) continua garantida
pela conferência automática. Os valores usados saem no `_resumo.txt`.

**Desempenho e progresso (dev5).** Com dados reais (uso do solo com 3 classes em cerca de 980 manchas,
40 mil vértices; 10 polos; 2.343 ha), o cálculo não terminava em mais de 18 minutos e não mostrava
andamento. Agora: índice angular das arestas por polo (exato, 70 vezes mais rápido), refinamento até
estabilizar (um limite fixo de rodadas deixava pontas soltas na rede de fronteiras e regiões fundidas,
o que a conferência automática denunciou com 25% de divergência), conferência final por carimbo das
regiões e execução em segundo plano, com porcentagem e botão Cancelar. O caso real leva cerca de
2 minutos, com conferência sem divergências; as áreas coincidem com o modelo calculado ponto a ponto.

**Guia Raster:** os polígonos viram notas na grade da análise (extensão e resolução escolhidas),
pela regra do centro da célula, e o cálculo segue o modelo célula a célula do Vista SAGA.

**Ajustes da dev6 (teste da dev5 com dados reais; decisões do autor):**

- **Guia Raster recorta pela área de estudo** quando a extensão vem de uma camada poligonal: só as
  células com o centro dentro da área recebem resultado, como o recorte da guia Vetorial. Antes, a guia
  Raster usava só o retângulo envolvente: Simples e Com Massa avaliavam o retângulo inteiro, e a "% da
  área avaliada" não era comparável entre modalidades nem entre guias. No atrito, as células fora da
  área continuam atravessáveis com a própria nota (só ficam sem resultado). Com atrito raster, a grade
  continua sendo a do raster (sem recorte).
- **Lascas do recorte final** (vetor direto com atrito): partes com largura média menor que 2 ×
  tolerância (1 m, com a tolerância padrão), criadas onde uma fronteira encontra a borda da área de
  estudo quase tangente, vão para a região vizinha de maior fronteira comum (no teste: 0,02 m e 0,08 m
  de largura).
- **Partes abaixo da escala só informadas:** o `_resumo.txt` do vetor direto lista, por região, as
  partes com área menor que 25 m² ((5 m)², o PEC Classe A a 1:10.000); a geometria não muda. No teste
  com dados reais eram cerca de 20 partes, de 1 a 2 m de largura, nas modalidades com atrito. O raster
  também se fragmenta (até 37 partes por região): a fragmentação vem do modelo sobre um mosaico de uso
  do solo fragmentado, não só do traçado.
- `_resumo.txt`: tempo de cálculo no vetor direto; no raster com atrito, a regra de passagem conforme a
  fonte (sem a frase antiga "NoData = barreira") e a linha do recorte.

As duas guias dão resultados ligeiramente diferentes para a mesma entrada (veja a tabela abaixo):
o modelo contínuo é o limite do modelo célula a célula quando a célula tende a zero.

## Justificativa da mudança de método

A 1.3.0 usava M/d no Com Massa e D × Σ(1 + C) no atrito, modelos marcados como não validados.
Em 17/11/2026, o autor rodou no Vista SAGA original um caso sintético (mapa de 80 × 60 células de
10 m, três classes de atrito com notas 1, 1, 3 e 5, três polos com massas 9, 4 e 1) nas quatro
modalidades, e as saídas foram comparadas célula a célula com modelos candidatos (validação caixa
preta, sem uso de código do programa original):

| Modalidade | Plugin 1.3 | Plugin 1.4 |
|---|---|---|
| Simples | 100% | 100% |
| Com Massa | 84,4% | **100%** (o expoente é nítido: 0,48 ou 0,52 sobre a massa já erram) |
| Com Atrito | 96,7% | **99,67%** |
| Com Massa e Atrito | 98,4% | **99,69%** |

Guia Vetorial com atrito (modelo contínuo, vetor direto): **99,60%** com massa e **99,52%** sem
massa (avaliado no centro das células; os polígonos traçados dão 99,60% e 99,48%, por duas células
a milímetros da fronteira). Com nota uniforme, o modelo contínuo reproduz os discos de Apolônio do
Com Massa a menos de 1 cm, o que confirma a coerência entre as modalidades.

As diferenças restantes no atrito (15 a 16 células) ficam todas na fronteira entre regiões, com
margem de custo pequena: detalhe do traçado das retas. Escolher entre variantes de traçado exigiria
um segundo caso independente, para não ajustar o modelo ao mesmo caso que o valida.

O resultado é coerente com a fórmula do manual do Vista SAGA, FZ = M / (D × A), em que A (soma
das notas ao longo da trajetória) cresce com D: com notas uniformes, FZ é proporcional a M/D², a
forma clássica do modelo gravitacional.

O mesmo teste confirmou o arquivo de pontos do Vista SAGA: `Nome;Massa;X:Y`, com X:Y = coluna e
linha **contadas a partir de 1**.

## Segundo caso, independente: bacia real (19/11/2026)

O autor rodou no Vista SAGA original (Windows 7 de 32 bits) uma bacia urbana real: uso do solo com três
classes de atrito (notas 1, 3 e 5; FUNDO com nota 1), 10 polos com massas de 4.261 a 73.139 e área de
estudo de 2.347 ha. O plugin rodou sobre o **mesmo RS2**, na mesma grade e com os mesmos polos
(`scripts/comparar_caso_bacia.py`).

- **Simples e Com Massa, grade de 5 m (990 × 2.214): 100%** das 2.191.850 células, sem empates.
- **Com atrito, grade de 10 m (495 × 1.107)**, critérios calculados dentro da área de estudo:

| Modalidade | Guia | (1) Células | (2) Divergências na fronteira | (3) Maior diferença de área por região | Critério |
|---|---|---|---|---|---|
| Com Atrito | Raster | 99,46% | 97,2% | **1,33%** (região de 86 ha, -1,15 ha) | **não atende (3)** |
| Com Massa e Atrito | Raster | 99,42% | 97,9% | 0,82% | atende |
| Com Atrito | Vetorial | 99,29% | 93,4% | **1,91%** | **não atende (3)** |
| Com Massa e Atrito | Vetorial | 99,06% | **88,9%** | **1,99%** | **não atende (2, 3)** |

**Critério de comparabilidade** (aceito pelo autor em 19/11/2026, antes do cálculo região a região):
(1) pelo menos 99% das células da área de estudo iguais às do Vista SAGA na mesma grade; (2) pelo menos
90% das divergências na fronteira entre regiões; (3) nenhuma região com diferença de área maior que 1%
da própria área. **Decisão do autor:** manter o critério como foi aceito e declarar o resultado; o
critério não foi revisto depois de conhecidos os números.

**Leitura dos resultados.**
- A **guia Raster** atende os critérios 1 e 2 nas duas modalidades e o 3 no Com Massa e Atrito. No Com
  Atrito, falha no critério 3 por uma só região pequena: 98% das células divergentes dela ficam na
  fronteira, com saldo de 0,13 célula por célula de fronteira. É um viés pequeno de borda, que numa região
  pequena em grade de 10 m passa de 1% da área. Nenhuma região é deslocada.
- A **guia Vetorial** não é uma cópia do Vista SAGA: calcula o mesmo modelo no limite contínuo, sem a soma
  célula a célula. Perto dos polos coincide; longe deles, fora da área de estudo, as fronteiras se afastam
  mais (97,2% a mais de 1 km da bacia, contra 99,7% da guia Raster), o que é coerente com um termo de
  discretização da soma do Vista SAGA que o modelo contínuo não tem (interpretação não demonstrada).
- Na divergência entre as guias observada nos dados reais da dev5 (15 a 20 ha, sul da bacia), **o Vista
  SAGA fica com a guia Raster**.

**Qual guia usar.** Para resultados que precisam ser comparáveis ao Vista SAGA, use a **guia Raster**,
declarando a coincidência medida. A guia Vetorial é a versão contínua do mesmo método (independente da
resolução); se for usada, declare-a como tal, com a coincidência medida (99,1 a 99,3% das células).

**Limitação do Vista SAGA original, observada (causa não confirmada).** Com atrito, a saída só saiu
correta com a grade de 10 m (495 × 1.107). Com 5 m (990 × 2.214), a saída veio com metade das linhas e
colunas e sem nenhuma região (mapa todo amarelo, código fora da legenda); com 20 m (247 × 553), veio com
o dobro, e o cálculo ocupou só o canto superior esquerdo. Não houve mensagem de erro. Simples e Com Massa
funcionaram em 5 m. Confira sempre se a saída do Vista SAGA mostra as regiões antes de usá-la.

O critério 3 não foi calculado no caso sintético de 17/11 (as saídas daquele caso não estão nesta
sessão); os critérios 1 e 2 se cumprem nele (99,7%; diferenças só na fronteira).

## Testes

- Suíte histórica e `tests/unit` verdes; testes do atrito reescritos contra uma referência escalar
  em Python puro; regressão com o caso validado (`test_140_voronoi_vista_saga_case.py`).
- Vetor direto com atrito: testes do custo exato (contra integral numérica), da passagem exata por
  vértices, da partição (sem sobreposições nem lacunas) com polígonos e polos aleatórios, e da
  coincidência com os discos de Apolônio (`test_140_friction_continuous.py`).
- Fluxo do diálogo conferido em QGIS 3.34 sem interface gráfica: guia Vetorial 99,60% (com massa,
  0,6 s) e 99,48% (sem massa); guia Raster com polígonos 99,69%.
- Teste do autor da dev2 (QGIS 4): partição exata nas quatro modalidades; achou a região A partida
  em duas com espaçamento de 20 m (corrigido na dev3, junto com uma cunha cortada no canto do
  corredor e uma faixa estreita perdida nos testes com dados aleatórios).
- Teste do autor da dev3 (QGIS 4), com 5 m e 20 m: regiões inteiras, partição exata, conferência sem
  divergências, 99,60% (com massa) e 99,50% (sem massa) do Vista SAGA. **dev3 homologada.**
- Teste do autor da dev4 (QGIS 4): nota 0 bloqueada; espaçamento automático; regiões inteiras e
  conferência sem divergências. **dev4 homologada.** Teste com dados reais: lentidão e regiões
  distorcidas (corrigidas na dev5).
- Teste do autor da dev5 (QGIS 4, dados reais: bacia de 2.343 ha, 10 polos, uso do solo): 10 regiões,
  geometrias válidas, soma das áreas igual à da bacia nas quatro modalidades; conferência sem
  divergências. Vetor × raster (5 m), célula a célula: Simples e Com Massa 100%; **Com Atrito 99,36% e
  Com Massa e Atrito 99,14%** (15 a 20 ha de diferença, até 3,8 ha numa região, com deslocamento
  sistemático). É a diferença entre o modelo contínuo e o célula a célula em percursos longos sobre um
  mosaico fragmentado. Resolvido pelo segundo caso (bacia no Vista SAGA original, acima): o Vista SAGA
  fica com a guia Raster.
- dev6: suítes verdes (testes novos em `test_150_voronoi_dev6.py`); diálogo conferido em QGIS 3.34
  sem interface gráfica com dados sintéticos (bacia côncava, raster de atrito com faixa NoData).
- Teste do autor da dev6 (QGIS 4): **dev6 aprovada** (19/11/2026).
- Validação na bacia real contra o Vista SAGA original (19/11/2026): ver "Segundo caso, independente";
  `scripts/comparar_caso_bacia.py` e `tests/unit/test_comparar_caso_bacia.py`.
