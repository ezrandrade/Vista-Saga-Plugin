# Vista Saga Plugin 1.3.0 — notas da versão

> Versão em desenvolvimento. Inclui tudo da 1.2.1. Os cálculos existentes não mudaram; a 1.3.0
> acrescenta um cálculo novo, o vetor exato Com Massa.

## O que muda para quem usa

### Análises Voronoi no padrão dos demais módulos

- **Guias "Raster" e "Vetorial"**, como na Combinação de Mapas e na Monitoria. O modelo de
  influência e os dados de entrada são os mesmos nas duas guias: o que foi preenchido acompanha a
  troca de guia. Cada guia tem o próprio grupo "Resultado".
- **"Salvar em"**, com o botão "Salvar como…":
  - em branco, na guia Raster: arquivo temporário; na guia Vetorial: camada temporária em memória
    (salve-a antes de fechar o QGIS);
  - preenchido: o resultado é salvo nesse arquivo;
  - nos dois casos, o resultado é carregado no QGIS. Saem as caixas "Resultado temporário" e
    "Adicionar ao projeto".
- **Formato vetorial:** escolhido no filtro do "Salvar como…", como no QGIS: GeoPackage,
  Shapefile, GeoJSON ou FlatGeobuf. O Shapefile é gravado em UTF-8 (`.cpg`), com acentos.
- Antes de substituir resultados existentes, o plugin pede confirmação.
- `_centros.csv` e `_resumo.txt` continuam sendo gerados ao lado do resultado (sem arquivo
  indicado, na pasta temporária do QGIS).

### Guia Vetorial nas quatro modalidades

| Modalidade | Como os polígonos são obtidos |
|---|---|
| Simples | fronteiras exatas (bissetrizes), sem grade |
| **Com Massa** (cálculo novo) | fronteiras exatas (círculos de Apolônio), sem grade |
| Com Atrito / Com Massa e Atrito | cálculo na grade da superfície de atrito, convertido em polígonos |

**Com Massa.** Cada lugar pertence ao centro de maior M/d, a mesma regra do raster, calculada
sobre a geometria. Entre centros de massas diferentes, a fronteira é um círculo de Apolônio: o
mais leve fica com um disco ao redor de si, onde d_leve / d_pesado < M_leve / M_pesado. Entre
massas iguais, a fronteira é a bissetriz (com todas as massas iguais, o resultado é idêntico ao
Simples). Os arcos são gravados como segmentos com desvio de no máximo 2/3 de 1 cm, sem viés de
área; vizinhos usam exatamente o mesmo arco, sem sobreposições nem lacunas. Uma região pode ter
mais de uma parte (multipolígono). O `_resumo.txt` registra a tolerância.

**Raster × vetorial Com Massa.** O raster classifica o centro de cada pixel; suas áreas convergem
para as do vetor quando a resolução diminui. Num teste com 25 centros em 10 × 10 km, a diferença
média de área foi de 2,0% a 100 m, 0,5% a 30 m e 0,04% a 10 m (máxima: 15,5%, 4,0% e 0,27%). Para
comparar com o **Vista SAGA original**, que trabalha por pixel, use a guia Raster na mesma grade;
o vetor é a referência geométrica do modelo M/d.

**Com atrito.** O atrito é uma superfície raster: o custo muda célula a célula, e não existe
fronteira geométrica exata. A guia Vetorial calcula na grade da própria superfície de atrito
(como a guia Raster) e converte o resultado em polígonos, com bordas nos pixels; o GeoTIFF
intermediário não é guardado. O `_resumo.txt` registra o tamanho da célula.

**Campos da camada:** `CENTRO_ID`, `CENTRO`, `MASSA`, `AREA_HA` (e, nas fronteiras exatas,
`AREA_M2` e `PCT_AREA`), todos com até 10 caracteres.

**GeoJSON:** a especificação atual prevê coordenadas em WGS 84; o GDAL grava o SRC projetado como
extensão antiga do formato. Para a tese, prefira GeoPackage.

## Homologação pedida ao autor (QGIS para Windows)

1. Aparência: guias Raster e Vetorial iguais às da Combinação de Mapas; trocar de guia mantém o
   preenchimento.
2. Vetorial, **Com Massa**, "Salvar em" em branco: camada temporária em memória, com fronteiras
   curvas; a soma de `AREA_HA` é a área da extensão.
3. Vetorial, Com Massa, "Salvar como…" → Shapefile: `.shp/.shx/.dbf/.prj/.cpg`, `_centros.csv` e
   `_resumo.txt`; acentos corretos.
4. Vetorial, **Com Atrito** e **Com Massa e Atrito**: polígonos carregados, sem `.tif` na pasta.
5. Raster, em branco e salvo: resultado igual ao da 1.2.1 para os mesmos dados.
6. Salvar duas vezes no mesmo arquivo: o plugin pede confirmação antes de substituir.
