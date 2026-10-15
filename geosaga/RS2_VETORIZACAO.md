# RS2 → formatos vetoriais (Vista Saga Plugin 0.3.5)

## Procedimento

A função **RS2 → Vetor (polígonos)** converte células categóricas do Vista SAGA
em polígonos de regiões contíguas de mesmo código, conforme a lógica da
ferramenta **Polygonizar** do QGIS/GDAL. Os códigos vêm da matriz RS2, não das
cores RGB. As cores e legendas originais são mantidas nos atributos:

- `CODIGO`: inteiro categórico exato da matriz RS2;
- `CLASSE`: nome registrado no cabeçalho RS2;
- `COR_HEX`: cor da paleta RS2 no formato `#RRGGBB`.

As geometrias são polígonos; polígonos da mesma classe, mas fisicamente
separados, permanecem feições distintas. Por padrão, pixels da classe 0
(`FUNDO`) são excluídos. Em **Opções avançadas**, altere para incluir o fundo
ou considerar 8 conexões (vizinhos em diagonais), em vez de 4.

A saída padrão é **GeoPackage (.gpkg)**, recomendado para nomes de classe
longos, atributos Unicode e grandes quantidades de polígonos. Os outros
formatos disponíveis são **ESRI Shapefile (.shp)**, **GeoJSON (.geojson)** e
**FlatGeobuf (.fgb)**, quando os respectivos drivers GDAL/OGR estiverem
habilitados na instalação QGIS. Em Shapefile, nomes de atributos são restritos
a 10 caracteres; `CODIGO`, `CLASSE` e `COR_HEX` respeitam esse limite. Os textos
de classe longos podem ser truncados pelas limitações do DBF.

O SRC só será atribuído se selecionado pelo usuário com o controle nativo do
QGIS: os RS2 legados analisados informam coordenadas, mas não identificam
inequivocamente a zona/datum. **Atribuir um SRC não reprojeta os dados**.

## Conversão em lote

Marque **Processar vários arquivos (lote)**, adicione RS2 de mesma resolução
e dimensões, selecione o formato e escolha a pasta de saída. Mapas espacialmente
deslocados geram um alerta (não são reamostrados). Os arquivos são criados
separadamente, não fundidos. Grandes matrizes fragmentadas podem resultar em
milhões de polígonos; nesse caso, o processo e as saídas podem ser muito grandes.

## Implementação

Para cada arquivo, o plugin:

1. Lê o RS2 com `RS2Reader` e cria um GeoTIFF categórico **temporário**, que
   é excluído automaticamente no fim do processo;
2. Executa `gdal.Polygonize()` com máscara para excluir a classe 0, se escolhida;
3. Atribui `CLASSE` e `COR_HEX` aos polígonos em um GeoPackage temporário;
4. Converte para o formato desejado com `gdal.VectorTranslate`, se necessário;
5. Publica o vetor e seus auxiliares em conjunto, com backup e rollback em
   erros de sobrescrita; descarta os arquivos temporários.

Quando o plugin carrega o resultado no QGIS, aplica, quando possível, uma simbologia
categorizada usando a cor HEX registrada em cada classe.

O processo não modifica o arquivo RS2 e não exige conversão manual prévia para
GeoTIFF. Suporta cancelamento e progresso. Saídas vetoriais já carregadas no
QGIS não são sobrescritas para reduzir risco de travamento no Windows.

## Homologação QGIS 4.x

No Console Python do QGIS, após instalar o ZIP e reiniciar, execute:

```python
from geosaga.tests.integration_rs2_ui_qgis import run
run()
from geosaga.tests.integration_rs2_vector_qgis import run as vetor
vetor()
```

O teste usa um mapa RS2 sintético 4 × 3 e avalia os quatro formatos com
atributos e códigos de classe, além da opção de incluir o fundo. Todos os
arquivos de teste são temporários. No ambiente de desenvolvimento sem bindings
GDAL/OGR e PyQGIS, só é possível rodar os testes unitários independentes do QGIS.

## GeoTIFF → Vetor (0.3.6)

Agora o mesmo diálogo aceita um GeoTIFF categórico monobanda ou um TIFF
RGB classificado, gerando polígonos no mesmo conjunto de formatos acima.
Selecione **GeoTIFF → Vetor (polígonos)**, a camada TIFF do projeto ou
arquivo no disco, o formato e a saída. Para GeoTIFFs georreferenciados,
o SRC é herdado do raster; sem coordenadas, informe a extensão manual.

A banda inteira mantém valores de classe em `CODIGO`. A categoria descrita
em arquivos auxiliares do Vista Saga `.tif.rs2.json`, tabelas de cores
ou nomes de categorias GDAL é recuperada para `CLASSE` e `COR_HEX`.
Em RGB, uma cor única dá origem a um código de classe novo; não é possível
recuperar nomes/códigos sem metadados categóricos. TIFFs com gradientes
contínuos devem ser previamente classificados.

Execute os testes reais no Console Python do QGIS:

```python
from geosaga.tests.integration_tiff_vector_qgis import run
run()
```
