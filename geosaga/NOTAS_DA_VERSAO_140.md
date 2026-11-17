# Vista Saga Plugin 1.4.0 — notas da versão (em teste)

> Versão em teste (17/11/2026). Inclui tudo da 1.3.0. **Muda o método** das modalidades Com
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
  somava 1 + atrito. **Rasters de atrito antigos com valor 0 passam a ter custo zero**: revise-os.
- NoData continua sendo barreira (sem resultado e sem passagem). A célula do polo é sempre dele.
- Empates: vence o polo que vem primeiro na lista (mesma regra do Vista SAGA).
- As duas modalidades deixam de ser marcadas como "experimentais".

### Superfície de atrito vetorial (nova)

Em Com Atrito e Com Massa e Atrito, a superfície de atrito pode ser uma **camada de polígonos**
com a nota numa **coluna de atrito** (escolhida em "Coluna de atrito"; sem atribuição manual).

- Área sem polígono e feições com a coluna vazia são **barreira** (sem resultado e sem passagem).
- Em sobreposições vale a última feição.
- **Sem reprojeção:** a camada de polígonos define o SRC da análise (os pontos são convertidos para
  ele, como no atrito raster).

**Guia Vetorial: vetor direto, sem rasterização.** O resultado não é mais a poligonização de uma
grade. O plugin usa a **versão contínua** do modelo do Vista SAGA:

> custo = ∫ (distância ao polo) × (nota) ao longo do segmento reto polo → ponto

calculado exatamente pelos cruzamentos do segmento com as bordas dos polígonos (com massa,
dividido por M). As fronteiras entre as regiões não têm fórmula fechada: são traçadas
numericamente, com tolerância de 1 cm, a partir de uma malha de busca ("Espaçamento da busca")
com refinamento local. No caso de teste, mais de 99,9% dos pontos de fronteira ficam a menos de 2 cm
da fronteira do modelo, com qualquer espaçamento de 5 a 40 m; pontas de cunhas muito finas e
encontros de três regiões podem ficar encurtados em alguns decímetros (área desprezível). Regiões menores que o espaçamento da busca podem não ser
detectadas; use um espaçamento menor que os menores detalhes que importam. A partição não tem
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

**Guia Raster:** os polígonos viram notas na grade da análise (extensão e resolução escolhidas),
pela regra do centro da célula, e o cálculo segue o modelo célula a célula do Vista SAGA.

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
- **Pendente:** teste do autor no QGIS 4 (ZIP `-dev3`).
