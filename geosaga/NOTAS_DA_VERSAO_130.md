# Vista Saga Plugin 1.3.0 — notas da versão

> Versão em desenvolvimento. Inclui tudo da 1.2.1. Nenhum algoritmo de cálculo foi alterado.

## O que muda para quem usa

### Análises Voronoi: saída vetorial em todas as modalidades

Em **3. Resultado → Formato de saída** há agora quatro opções:

| Opção | Modalidades | O que é gravado |
|---|---|---|
| GeoTIFF (raster) | todas | GeoTIFF, CSV e TXT |
| Vetor direto (somente Simples) | Simples | polígonos exatos (sem grade), CSV e TXT |
| **Vetor (poligonização)** (nova) | todas | camada vetorial, CSV e TXT |
| GeoTIFF + vetor (poligonização) | todas | GeoTIFF, camada vetorial, CSV e TXT |

- **Com Massa, Com Atrito e Com Massa e Atrito** passam a ter saída só vetorial. O cálculo continua
  na grade raster, como antes; o GeoTIFF intermediário é descartado no fim.
- **Formato vetorial:** GeoPackage (padrão), Shapefile, GeoJSON ou FlatGeobuf, os mesmos do
  Conversor de Formatos. Vale para as três saídas vetoriais.
- Os campos da camada não mudam: `CENTRO_ID`, `CENTRO`, `MASSA` e `AREA_HA` na poligonização;
  no vetor direto, também `AREA_M2` e `PCT_AREA`. Todos têm até 10 caracteres, compatíveis com
  Shapefile; o Shapefile é gravado em UTF-8 (arquivo `.cpg`), preservando acentos.

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
5. Saída padrão (GeoTIFF + vetor em GeoPackage): resultado igual ao da 1.2.1 para os mesmos dados.
