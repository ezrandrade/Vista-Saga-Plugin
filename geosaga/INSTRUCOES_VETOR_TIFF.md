# Quinta operação: Vetor → GeoTIFF (versão 0.3.8)

Operação acrescentada à interface da 0.3.7, sem mudanças nas outras quatro.

1. No **Conversor de formatos**, escolher **Vetor → GeoTIFF (rasterização)**.
2. Escolher um arquivo local `.gpkg`, `.shp`, `.geojson` ou `.fgb` (ou selecioná-lo a partir das camadas vetoriais carregadas no projeto). Ao selecionar uma camada do projeto, a fonte OGR, inclusive `|layername=`, será mantida.
3. Selecionar o **campo para rasterizar**. O campo `CODIGO` é selecionado automaticamente quando existir.
4. Informar o **tamanho do pixel** nas unidades do SRC do vetor (por exemplo, 10 para 10 metros quando o SRC é métrico). A área do raster resulta da extensão da camada, com acréscimo de pixels inteiros quando necessário.
5. Definir o arquivo `.tif` de saída e executar. É possível marcar **ALL_TOUCHED** em Opções avançadas; o padrão usa o centro do pixel.

## Atributos e regras

- Campo inteiro: grava o mesmo código inteiro (>= 0). Campo real: grava o valor decimal em GeoTIFF Float64. Campo de texto: atribui códigos inteiros começando em 1, mantendo o texto como nome da categoria.
- Para camadas com campos `CODIGO`, `CLASSE` e `COR_HEX`, é incorporada a legenda, incluindo as cores HEX, quando possível.
- Em rasters categóricos, pixels fora das feições recebem 0 (fundo/NoData), como na convenção RS2. Se uma feição possuir código 0, não será distinguível do fundo sem consultar a geometria original.
- Feições com atributo nulo ou geometria vazia são ignoradas.
- O SRC de origem é preservado, sem reprojeção. É necessário usar camada com SRC definido. Em SRC geográfico, a resolução é em **graus** (não em metros), e a interface sugere 0,0001 grau como valor inicial; para resolução em metros, reprojete previamente no QGIS para um SRC projetado apropriado.
- Em caso de sobreposição de feições com valores diferentes, o valor gravado da última feição processada prevalece. Recomenda-se corrigir sobreposições antes da rasterização.
- Esta operação funciona, por ora, em **arquivo individual**. O lote permanece inalterado para as quatro operações anteriores.
- Quando a mesma área precisa se alinhar perfeitamente a um raster existente, a grade deve ser planejada com origem e resolução comuns. Este modo usa automaticamente a extensão do vetor, e não a grade de referência.
- Há proteção contra rasters com mais de 100 milhões de células; a resolução deverá ser aumentada para mapas muito extensos.

## Teste integrado no QGIS 4.x

No Console Python:

```python
from geosaga.tests.integration_vector_raster_qgis import run
run()
```

O teste usa apenas dados sintéticos e temporários e verifica as saídas categórica numérica e textual. A interface PyQGIS exige homologação em QGIS real.
