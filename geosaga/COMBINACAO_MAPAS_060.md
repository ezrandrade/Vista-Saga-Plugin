# Combinação de Mapas — Vista Saga Plugin 0.6.0

## Objetivo

Reproduzir a lógica de **combinação de classes temáticas** do Vista SAGA:
identificar, codificar e medir todas as associações observadas em mapas de entrada,
sem atribuir pesos ou notas. Não é uma avaliação multicritério.

## Uso no QGIS 4.x

1. Abra **Raster → Vista Saga Plugin → Painel de módulos → Combinação de Mapas**.
2. Na aba **Combinação raster** (ou **Combinação vetorial**), adicione pelo menos dois mapas.
3. Ordene os mapas com os botões **Subir** e **Descer**. A ordem define a legenda composta.
4. Em vetor, selecione também o campo de código e, opcionalmente, o campo com nomes das classes.
5. Defina a saída `.tif` (raster) ou `.gpkg` (vetor); clique em **Combinar mapas**.
6. Consulte `_combinacoes.csv` e `_resumo.txt` ao lado do mapa criado.

## Saídas

- Raster: GeoTIFF **Int32**, com ID positivo distinto por combinação presente e 0 reservado a NoData de saída.
  Entradas com código 0 válido não são descartadas indevidamente.
- Vetor: GeoPackage com `C01`, `L01`, `C02`, `L02` etc. (código/legenda de cada mapa),
  `ID_COMB`, `LEGENDA`, `AREA_M2`, `AREA_HA`, `PCT_AREA`.
- Em ambas as modalidades: CSV UTF-8 com colunas por critério e resumo TXT.
- O conversor **GeoTIFF → Vetor** reconhece os arquivos gerados pelo módulo e recupera
  as legendas compostas de `_combinacoes.csv`. **Mantenha esse CSV ao lado do TIFF**.

## Metodologia e limites

- Raster: mapas categóricos **monobanda**, com mesma dimensão, SRC e alinhamento de pixels.
  Diferenças residuais inferiores a 1e-5 pixel são admitidas sem reamostragem.
  Pixels NoData em qualquer mapa são excluídos da combinação.
- Raster: áreas em hectares somente quando o SRC permite área métrica projetada.
  Em SRC geográfico, pixels e percentuais são calculados, mas hectares ficam indisponíveis.
- Vetor: camadas **poligonais**, com geometrias válidas e mesmo SRC.
  Não podem conter sobreposições internas de polígonos que causariam contagem duplicada.
  O cruzamento utiliza **interseção geométrica**. Áreas sem cobertura simultânea não compõem o resultado.
- Para conjuntos excessivamente fragmentados, o processamento vetorial pode criar muitas
  feições e exigir tempo/memória. Não eliminar polígonos pequenos sem avaliação metodológica.
- Máximo de 100.000 combinações distintas, para impedir uso excessivo de memória e relatórios inviáveis.
- Os campos numéricos de classe devem representar códigos inteiros; números decimais
  contínuos precisam ser classificados primeiro.
- Os códigos `ID_COMB` são determinísticos para o conjunto de classes e a ordem dos mapas,
  mas podem mudar se categorias observadas forem acrescentadas ou removidas em outra execução.
- A legenda raster é guardada no CSV associado. Os arquivos originais nunca são modificados.
- O relatório tem área percentual calculada apenas sobre a **área de interseção válida**.

## Teste no QGIS

Abra o Console Python do QGIS e execute:

```python
from geosaga.tests.integration_combination_qgis import run
run()
```

Os dados de ensaio são gerados em uma pasta temporária. Devem resultar quatro combinações raster,
quatro combinações vetoriais e área total vetorial de 0,04 ha.

Esta versão foi submetida a testes automatizados fora do QGIS e depende de homologação da
interface Qt6 e da execução PyQGIS/GDAL real em Windows e Linux/Flatpak.
