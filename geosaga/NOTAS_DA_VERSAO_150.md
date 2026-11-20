# Vista Saga Plugin 1.5.0 — notas da versão

> Versão estável (20/11/2026), homologada pelo autor no QGIS 4. Inclui tudo da 1.4.2. As dicas (caixas
> amarelas) em todos os módulos, previstas de início para esta versão, passaram para a 1.6.0 (decisão do
> autor).

## Assinatura no modelo do Vista SAGA

O módulo foi refeito a partir de vídeos e relatórios do Vista SAGA original enviados pelo autor.

### Como funciona

1. **Mapas:** monte a lista; o **primeiro é a referência** (o "mapa de cima" do Vista SAGA). Use "Mover para
   cima/baixo" para trocar a ordem e "Remover selecionadas"/"Remover todas" para limpar.
2. **Seleção na referência:** é o limite da assinatura.
   - Guia **Raster**: marque as classes na lista ("Marcar todas" equivale a "Assinar o mapa inteiro",
     inclusive o FUNDO). Cada classe marcada entra inteira.
   - Guia **Vetorial**: selecione as feições no mapa do QGIS ("Selecionar no mapa" ativa a camada de
     referência e liga a ferramenta de seleção; há também "Selecionar todas" e "Desselecionar todas").
3. **Opções:** "Resultado por feição" (ligado por padrão): além da união da seleção, um resultado para cada
   feição (no raster, para cada classe marcada).
4. **Resultado:** relatórios **TXT** e **CSV** ("Salvar em" vazio: pasta temporária, com o nome
   "Assinatura - Raster" ou "Assinatura - Vetorial").

Todos os mapas da lista são assinados dentro do limite, inclusive a referência, mapa a mapa (sem cruzar
combinações). Para cada classe: total no mapa inteiro, área assinada, **% Área Asn.** (área da classe no
limite ÷ área do limite) e **% Categoria** (área da classe no limite ÷ área da classe no mapa inteiro).

### Regras de entrada

- Sem mistura de formatos: Raster só com raster; Vetorial só com vetor.
- Mesmo SRC em todos os mapas, **projetado em metros**; o plugin não reprojeta (o módulo antigo reprojetava
  sem avisar).
- Guia Raster: **mesma grade** (dimensões, resolução, extensão e alinhamento); formatos do GDAL e RS2 (o SRC
  do RS2 vem do `.rs2.json` ou é confirmado ao adicionar o mapa).
- FUNDO (RS2) e NoData (GeoTIFF) contam como classe; nomes das classes vêm do arquivo ou do estilo da camada
  no QGIS (Paletado/Valores únicos).
- Guia Vetorial: parte do limite sem polígono = "Sem classe"; sobreposição entre classes diferentes excluída
  ("Sobreposição excluída") ou execução interrompida (modo estrito); **lascas e frestas com largura média
  < 1 cm** são imprecisão de coordenadas, sem linha própria, registradas no TXT (mesma regra da Combinação).

### Validação contra o Vista SAGA original

| Caso (RS2 de 10 m, 496 × 1108 células) | Classes coincidentes |
|---|---|
| Mapa inteiro (Bairros, Uso do Solo, Escolaridade, Pedologia) | 100% |
| 4 bairros (Antares, Gruta de Lourdes, Jacintinho, Poço) | 28 de 31 |
| Barro Duro | 27 de 31 e 28 de 32 |

Todas as diferenças são **células da classe ligadas ao resto só pela diagonal**: o balde do Vista SAGA marca a
região contínua por 4 vizinhos e as deixa de fora; o plugin marca a classe inteira (1 célula no Poço, 4 no
Barro Duro). Diferença aceita pelo autor. O CSV gerado no QGIS 4 do autor é idêntico ao calculado no teste.
Para repetir: `scripts/comparar_assinatura_vista_saga.py`.

### O que saiu

- O GeoPackage das áreas (`_areas.gpkg`) e as caixas "Resultado temporário"/"Carregar GeoPackage".
- O caso "polígonos como limite com mapa raster" (mistura de formatos): converta antes, no Conversor.
- O algoritmo Processing `geosaga:assinatura` fica **obsoleto e oculto** (Caixa de Ferramentas e Modelador);
  modelos e scripts antigos continuam funcionando.

## Conversor de Formatos

- **Vetor → GeoTIFF grava sempre a paleta** (cores padrão quando falta `COR_HEX`): antes, o QGIS abria o mapa
  em tons de cinza e não mostrava os nomes das classes.
- **Vetor → GeoTIFF e RS2 → GeoTIFF gravam `<nome>.qml`**, que o QGIS carrega sozinho: a legenda mostra só as
  classes reais (antes listava 256 entradas, "4", "5"...).
- **Vetor → RS2 não deixa mais pastas `.vista_vector_rs2_*`** na pasta de saída (Windows). Apague à mão as
  que já existirem.

## Nomes dos resultados (todos os módulos)

Resultado temporário: arquivo e camada com o nome **"Módulo - operação"** (ex.: "Análises Voronoi - Com
Atrito", "Conversor de Formatos - Vetor para GeoTIFF"). Resultado salvo: a camada recebe o nome do arquivo.

## Testes

- Suítes verdes (503 e 42); integração da Assinatura em QGIS real (3.34, sem interface).
- Teste do autor no QGIS 4: **Assinatura e Conversor homologados** (20/11/2026).
