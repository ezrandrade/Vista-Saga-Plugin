# Assinatura 1.5.0 - proposta de escopo

Proposta do Claude para aprovação do autor (20/11/2026), consolidando as decisões das perguntas 1 a 5
registradas em `docs/CONTEXTO_SESSOES.md`. Nada foi programado ainda. Todos os itens
[decidir] foram respondidos pelo autor em 20/11/2026.

## 1. Conceito

- Uma lista de mapas; o **primeiro é a referência** (equivalente ao "mapa de cima" do Vista SAGA).
- Na referência, seleciona-se o limite (classes no raster; feições no vetor).
- **Todos os mapas da lista são assinados dentro do limite, inclusive a referência**, mapa a mapa (sem
  cruzamento de combinações).
- Dois resultados: **união** do que foi selecionado (como o Vista SAGA) e **por feição** (caixa
  "Resultado por feição", ligada por padrão; no raster, um resultado por classe marcada).

## 2. Regras de entrada

- **Sem mistura de formatos:** guia Raster só com raster; guia Vetorial só com vetor.
- **Mesmo SRC em todos os mapas**, com mensagem clara; o plugin não reprojeta (corrige o defeito da
  reprojeção silenciosa em `signature_engine.py:316`).
- **Guia Raster: mesma grade** (resolução, extensão, alinhamento) em todos os mapas; grades diferentes geram
  erro com a sugestão de alinhar antes. Raster categórico de uma banda, nos formatos lidos pelo GDAL
  (OSGeo) **e o RS2** (decisão do autor, 20/11/2026); o SRC do RS2 vem do `.rs2.json` ou da confirmação
  do usuário, como nos demais módulos.
- **SRC projetado em metros** (decisão do autor, 20/11/2026, revendo "somente UTM": aceita UTM, Albers,
  Policônica, LTM/RTM etc.; recusa SRC geográfico em graus e unidades que não sejam metros), verificado
  pela definição do SRC, nunca pelas coordenadas.
- Nada selecionado: execução recusada com mensagem (o plugin não supõe "mapa inteiro").

## 3. Seleção

- **Raster:** lista das classes da referência com caixas; "Marcar todas" (= "Assinar o mapa inteiro",
  inclusive o FUNDO) e "Desmarcar todas". Feição = classe inteira (diferença aceita para o balde do Vista
  SAGA, que marca a região conexa por 4 vizinhos).
- **Vetorial:** seleção da camada de referência feita no QGIS (ferramentas nativas); a janela mostra
  "N feições selecionadas", atualizada quando a seleção muda; botão "Selecionar todas"; campo opcional de
  nome da feição para o resultado por feição.

## 4. Contas (validadas pelo caso de referência do autor)

Para cada mapa assinado e cada classe:

- `Total Pixels` / `Total Ha`: a classe no mapa inteiro;
- `Pixels Asn.` / `Área Asn. Ha`: a classe dentro do limite;
- `% Área Asn.` = área da classe no limite / área do limite;
- `% Categoria` = área da classe no limite / área da classe no mapa inteiro.

Todas as classes aparecem, inclusive as zeradas. FUNDO (RS2) e NoData (GeoTIFF) contam como classe
qualquer. Na guia Vetorial, a parte do limite sem polígono, ou fora da extensão do mapa assinado, é a
linha **"Sem classe"**, dentro da base, com aviso no resumo. Sobreposição de classes num mapa vetorial
assinado: tratamento atual (exclui a região ambígua e registra a área, ou modo estrito).

Áreas: raster = células × área da célula; vetor = área planimétrica no SRC projetado dos mapas.

## 5. Saídas

TXT e CSV no padrão do plugin (decisão do autor, 20/11/2026) (campo "Salvar em"; sem as caixas "temporário" e "carregar"):

- `*.txt`: relatório no leiaute do Vista SAGA (um bloco por mapa, na ordem da lista: colunas acima e linha
  `Total`), seguido dos blocos por feição; cabeçalho com mapas, SRC, seleção e avisos;
- `*.csv`: as mesmas linhas em formato de tabela (`MAPA`, `FEICAO`, `CODIGO`, `CLASSE`, as seis colunas),
  separador `;`, UTF-8 com BOM, como os demais relatórios do plugin;
- guia "Resultados" com a tabela copiável para planilhas (`enable_table_copy`);
- **Sem GeoPackage:** o `_areas.gpkg` do módulo atual é retirado (decisão do autor, 20/11/2026); pode
  voltar como saída opcional se fizer falta.

## 6. Projeto

Como na Avaliação (decisão do autor, 20/11/2026): botões **Novo projeto**, **Abrir projeto…** e **Salvar
projeto…**, arquivo `*.geosaga.json` com caminhos relativos à pasta do arquivo quando possível. Guarda a
configuração (mapas e ordem, classes marcadas no raster, feições selecionadas no vetor, opções), nunca os
resultados.

## 7. Compatibilidade

- O identificador Processing `geosaga:assinatura` não pode ser renomeado. Hoje ele faz o caso misto
  (união dos polígonos + raster, centro da célula, reprojeção do vetor). **Decisão do autor: manter o
  algoritmo antigo** com o cálculo intacto. Disposição: **marcado como obsoleto e oculto** (decisão
  do autor, 20/11/2026): some da Caixa de Ferramentas e do Modelador, mas modelos e scripts antigos
  continuam funcionando (indicador de obsoleto do Processing; conferir o nome no QGIS 4).

## 8. Validação

- Teste de regressão com dados sintéticos que reproduzem a estrutura do caso de referência (célula ligada só
  pela diagonal, classes zeradas, FUNDO).
- Script de comparação com o relatório do Vista SAGA (como `scripts/comparar_caso_bacia.py`), para o autor
  rodar com os dados reais: esperado 100% no relatório 2 (mapa inteiro) e diferença de 1 célula no
  relatório 1 (Poço), pela decisão da feição = classe inteira.

## 9. Fora deste escopo

Ferramentas de pintura; clique por região no raster; mistura de formatos; percentual só entre classes
reais; dicas em todos os módulos (item 2 da 1.5.0, depois da Assinatura).
