# Relatórios de Avaliação Espacial — versão 0.3.12

## Referência histórica

O arquivo `teste.txt`, fornecido pelo usuário, contém blocos "Combinações que originaram a nota final", com nomes das classes, nota, peso, produto, pixels, hectares, percentual da nota e percentual da área do mapa final. A presente implementação organiza TXT e CSV sob o mesmo conceito.

## Avaliação raster

No painel da Avaliação Espacial (raster), selecionar opcionalmente os dois relatórios na área "Resultado". Saída ao lado do GeoTIFF: `<nome>_relatorio.txt` e `<nome>_relatorio.csv`.

- Combinações: códigos conjuntos dos rasters de entrada em pixels válidos, recolhidos durante o cálculo do GeoTIFF.
- Nota ponderada por combinação é a média dos critérios originais; agrupa-se em nota inteira somente no relatório (floor(nota + 0,5), para notas não negativas). O GeoTIFF permanece Float32 sem reclassificação.
- Contagem por combinação e nota final; contribuição nota×peso/100, nomes de classes disponíveis na legenda da camada e pesos originais.
- `% Nota`: total de pixels da combinação dividido pelos pixels que pertencem à mesma nota final agrupada.
- `% área do mapa final`: área da combinação dividida pela área total da grade, inclusive pixels sem avaliação.
- Área em hectares: área de cada célula dada pelo determinante da geotransformação e pelas unidades lineares do SRC projetado, convertidas para metros. Se SRC geográfico (graus), área em hectares fica não calculada, evitando graus² confundidos com hectares; recomenda-se projetar em SRC métrico apropriado.
- Máximo recomendado por execução: 100.000 combinações únicas; limite evita explosão de memória. Desmarcar a geração de relatórios ou generalizar critérios se o limite for excedido.

## Avaliação vetorial — atributos e sobreposição

Nas duas janelas vetoriais, o GeoPackage de saída acrescenta os campos:

| Campo | Significado |
| --- | --- |
| `AVALIACAO` | Nota final ponderada, ou NULL quando invalida |
| `VALIDO` | 1 para avaliada, 0 para excluída/nula |
| `MOTIVO` | Razão da exclusão/nulo |
| `NOTA_01`, `NOTA_02`... | Notas dos critérios |
| `AREA_M2` | Área da feição em metros quadrados |
| `AREA_HA` | Área da feição em hectares |
| `PCT_AREA` | Participação da área dessa feição na soma de áreas das feições de saída |

Áreas de polígonos com SRC projetado são medidas planimetricamente, corrigidas pelas unidades lineares; em SRC geográfico, são medidas geodesicamente no elipsoide por `QgsDistanceArea`. O denominador de `PCT_AREA` inclui feições excluídas/nulas. Em camadas com sobreposição interna de polígonos, o total é *soma das áreas das feições*, não área dissolvida da união. No resultado de sobreposição, a referência espacial é somente a área comum às entradas.

Os relatórios `*_relatorio.txt` e `*_relatorio.csv` incluem combinações de categorias dos critérios, notas, pesos, produtos, quantidade de feições, soma de área em hectares, percentual da área da nota e percentual da área total do resultado. Classes excluídas e notas por classe são listadas em apêndice; feições não avaliadas entram no denominador de área total, não nas combinações classificadas.

Os relatórios são opcionais e vêm habilitados por padrão. O arquivo vetorial de entrada não é editado.

## Teste em QGIS 4.x

Após instalar o plugin, abrir Console Python e executar:

```python
from geosaga.tests.integration_evaluation_reports_qgis import run
run()
```

O teste cria rasters e polígonos temporários, produz dois relatórios por modalidade e verifica os campos e áreas no resultado vetorial. Os arquivos de teste são apagados automaticamente.
