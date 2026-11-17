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

Em Com Atrito e Com Massa e Atrito, "Tipo de superfície" oferece **Raster** ou **Vetorial
(polígonos)**:

- **Notas por classes:** escolha o campo de classe e, em "Notas das classes…", dê a nota de cada
  classe, como na Avaliação. Classe com “—” bloqueia a execução; uma classe pode ser marcada
  como **barreira**.
- **Notas por coluna:** escolha uma coluna numérica que já traga a nota de cada polígono.
- **Área sem polígono:** informe uma nota ou marque "Barreira". Deixada em “—”, a execução só
  ocorre se os polígonos cobrirem toda a grade (o plugin nunca supõe uma nota).
- Os polígonos viram notas na **grade da análise** (extensão e resolução escolhidas), pela regra do
  centro da célula; em sobreposições vale a última feição. Feições com o campo vazio contam como
  área sem polígono.
- **Sem reprojeção:** a camada de polígonos define o SRC da análise (os pontos são convertidos para
  ele, como no atrito raster); um raster de referência precisa estar nesse SRC.
- O `_resumo.txt` registra camada, campo, notas, área sem polígono, resolução e contagens.

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
- Fluxo do diálogo conferido em QGIS 3.34 sem interface gráfica: o caso validado desenhado em
  polígonos reproduz os mesmos 99,69% e 99,67%, nas guias Raster e Vetorial.
- **Pendente:** teste do autor no QGIS 4 (ZIP `-dev`).
