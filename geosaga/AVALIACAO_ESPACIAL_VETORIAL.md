# Proposta técnica — Avaliação Espacial vetorial

**Situação:** viável; especificação preliminar. Nenhum algoritmo vetorial é
executado pela versão 0.3.7.

## Premissa metodológica

A unidade de avaliação raster é a célula; na modalidade vetorial, a unidade de
avaliação é uma feição da base ou uma partição poligonal resultante de operações
de sobreposição. Para cada unidade j: A_j = sum(w_i * s_ij) / sum(w_i).
Os pesos e as notas seguem a semântica da avaliação raster e não devem mudar
conforme a natureza do dado. Classes excluídas e áreas não cobertas necessitam
políticas distintas e explícitas.

## Modos propostos

1. **Atributos numa base comum**: um vetor poligonal com N campos de critérios.
   Operação sem alteração de geometria; mapeamento valor/categoria → nota;
   resultado gravado como campos `AVALIACAO`, `FAIXA`, `VALIDO` e, opcionalmente,
   indicadores por critério. Útil para setores censitários, municípios, imóveis.
2. **Sobreposição de mapas temáticos**: N camadas poligonais com categorias;
   validar/corrigir geometrias, conferir SRC e área de estudo, particionar
   espacialmente por interseções dos limites e aplicar pesos/notas aos polígonos
   atômicos. Requer atributos identificadores de cada tema, políticas explícitas
   de cobertura/nulos, e tratamento de interseções, sobreposições, geometrias
   inválidas e polígonos residuais (*slivers*).

## Arquitetura

- Um modelo comum de regras e notas `criterio/categoria/peso/nota/exclusão`
  independente do formato espacial, adaptando o atual núcleo raster.
- Processador vetorial separado do `raster_engine.py`, para não alterar o
  cálculo raster homologado.
- Preferir saída GeoPackage, com QGIS/GEOS para operações geométricas,
  índice espacial e cancelamento via QgsTask, considerando cuidados com API
  Qt/PyQGIS no processamento paralelo.
- Entradas categóricas poligonais no marco inicial. Pontos/linhas requerem
  transformação prévia explícita (buffers, distâncias, densidades ou zonas),
  não avaliação 'equivalente' direta sem definição da unidade espacial.
- Usar SRC projetado apropriado para operações métricas, sem inferir
  unidade do sistema de coordenadas. Sem reprojeção automática silenciosa.

## Estratégia de validação

- Cenário sintético de polígonos coincidindo, polígonos sobrepostos,
  lacunas, múltiplos polígonos, buracos, NoData e geometrias inválidas.
- Conferir equivalência numérica raster/vetor em um cenário com grade
  coincidente, mesma regra de categorias e tratamento de fundo.
- Testes de escala com camadas fragmentadas; grande quantidade de limites
  distintos pode aumentar drasticamente o número de polígonos de saída.
- Preservar os projetos `.geosaga.json` anteriores sem conversão obrigatória.

## Decisão pendente antes da implementação

Definir se o primeiro fluxo vetorial terá **uma base poligonal comum** ou
**múltiplos mapas temáticos independentes**. A primeira modalidade é mais
simples e previsível para um MVP, enquanto a segunda se aproxima da operação
raster sobre várias cartas temáticas, com maior custo geométrico.
