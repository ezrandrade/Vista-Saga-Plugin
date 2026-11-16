# Vista Saga Plugin 1.3.0 — notas da versão

> Versão em desenvolvimento. Inclui tudo da 1.2.1. Os cálculos existentes não mudaram; a 1.3.0
> acrescenta um cálculo novo, o vetor direto Com Massa.

## O que muda para quem usa

### Análises Voronoi: saída vetorial em todas as modalidades

Em **3. Resultado → Formato de saída** há agora quatro opções:

| Opção | Modalidades | O que é gravado |
|---|---|---|
| GeoTIFF (raster) | todas | GeoTIFF, CSV e TXT |
| Vetor direto (Simples e Com Massa) | Simples, Com Massa | polígonos exatos (sem grade), CSV e TXT |
| **Vetor (poligonização)** (nova) | todas | camada vetorial, CSV e TXT |
| GeoTIFF + vetor (poligonização) | todas | GeoTIFF, camada vetorial, CSV e TXT |

- **Com Massa, Com Atrito e Com Massa e Atrito** passam a ter saída só vetorial. O cálculo continua
  na grade raster, como antes; o GeoTIFF intermediário é descartado no fim.
- **Formato vetorial:** GeoPackage (padrão), Shapefile, GeoJSON ou FlatGeobuf, os mesmos do
  Conversor de Formatos. Vale para as três saídas vetoriais.
- Os campos da camada não mudam: `CENTRO_ID`, `CENTRO`, `MASSA` e `AREA_HA` na poligonização;
  no vetor direto, também `AREA_M2` e `PCT_AREA`. Todos têm até 10 caracteres, compatíveis com
  Shapefile; o Shapefile é gravado em UTF-8 (arquivo `.cpg`), preservando acentos.

### Vetor direto Com Massa (cálculo novo)

- Cada ponto do território pertence ao centro de **maior M/d**, a mesma regra do raster, mas
  calculada sobre a geometria, sem pixels.
- **Fronteiras:** entre dois centros de massas diferentes, a fronteira é um **círculo de
  Apolônio**: o centro mais leve fica com um disco ao seu redor, onde
  d_leve / d_pesado < M_leve / M_pesado. Entre massas iguais, a fronteira é a bissetriz, como no
  Simples (com todas as massas iguais, o resultado é idêntico ao do Voronoi Simples).
- **Arcos:** gravados como segmentos de reta com desvio de no máximo 2/3 de 1 cm do círculo
  verdadeiro, posicionados para que a área não tenha viés. Vizinhos usam exatamente o mesmo
  arco: não há sobreposições nem lacunas, e a soma das áreas é a área da extensão. O `_resumo.txt`
  registra a tolerância.
- **Uma região pode ter mais de uma parte:** fica numa única feição multipolígono por centro.
- **Raster × vetor direto:** o raster Com Massa classifica o centro de cada pixel; suas áreas
  convergem para as do vetor direto quando a resolução diminui. Num teste com 25 centros em
  10 × 10 km, a diferença média de área foi de 2,0% a 100 m, 0,5% a 30 m e 0,04% a 10 m. Para
  comparar com o **Vista SAGA original**, que trabalha por pixel, use a saída raster na mesma
  grade; o vetor direto é a referência geométrica do modelo M/d.
- Tempo: cerca de 12 s para 1.000 centros (o caso comum, dezenas de centros, leva frações de
  segundo).

### O que observar ao usar a poligonização

- **Os polígonos seguem os pixels.** Nas modalidades com massa ou atrito, a fronteira entre duas
  áreas de influência é curva (com massa, arcos de circunferência); a poligonização a representa
  em degraus do tamanho da célula. A área de cada polígono é exatamente a soma dos pixels do
  centro, igual à do CSV. Para bordas mais finas, reduza a resolução raster.
- **Um centro pode ter mais de um polígono.** Se a área de influência de um centro estiver dividida
  em partes separadas, cada parte é uma feição, com o mesmo `CENTRO_ID`; some `AREA_HA` por centro.
- O `_resumo.txt` registra que os polígonos vêm da poligonização, o tamanho da célula e o formato.
- **GeoJSON:** a especificação atual do formato prevê coordenadas em WGS 84; o GDAL grava o SRC
  projetado como extensão antiga do formato. Para a tese ou para troca de dados, prefira
  GeoPackage.

## Homologação pedida ao autor (QGIS para Windows)

1. Voronoi **Com Massa** → "Vetor (poligonização)" → **Shapefile**, temporário: a camada abre no
   QGIS com cores por centro; nomes com acento corretos na tabela de atributos.
2. A mesma análise salva em pasta escolhida: conferir `.shp/.shx/.dbf/.prj/.cpg`, `_centros.csv`
   e `_resumo.txt`, e que **nenhum** `.tif` foi deixado.
3. "GeoTIFF + vetor" em FlatGeobuf: GeoTIFF e `.fgb` carregados.
4. Simples → "Vetor direto" → GeoJSON: polígonos exatos carregados.
5. **Com Massa → "Vetor direto" → GeoPackage:** fronteiras curvas (arcos), sem degraus; conferir
   que a soma de `AREA_HA` é a área da extensão e comparar com "GeoTIFF" Com Massa em resolução
   fina (as áreas devem ficar próximas). Repetir com "Polígono da área de estudo".
6. Saída padrão (GeoTIFF + vetor em GeoPackage): resultado igual ao da 1.2.1 para os mesmos dados.
