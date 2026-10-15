# Monitoria Ambiental 0.4.1 — legendas descritivas e série temporal

A Monitoria mantém a comparação entre dois mapas categóricos como operação principal. O GeoTIFF de transições conserva o mesmo ID numérico por par de classes.

## Legenda da transição

Opções na janela:

- **Descritiva** (padrão): `Permaneceu: <classe>` ou `Deixou de ser: <classe inicial> | Tornou-se: <classe final>`.
- **Códigos**: `1 → 2` (estilo anterior).

O nome de classe é lido de metadados GDAL ou do arquivo `.tif.rs2.json` quando disponíveis. Caso contrário, usa `Classe <código>`. Para corrigir o nome e a correspondência dos códigos de classes entre os dois períodos, informe um CSV UTF-8 com ponto e vírgula como delimitador e os campos obrigatórios:

```csv
PERIODO;CODIGO;CLASSE
1986;1;Pastagem
2016;1;Vegetação nativa
1986;2;Área urbana
2016;2;Área urbana
```

Esse CSV é **apenas ilustrativo**: substitua os códigos e nomes pelas legendas reais de seus mapas. `PERIODO` pode ser `Inicial` / `Final` ou os rótulos digitados na janela. Não se deve presumir que códigos iguais significam categorias iguais quando foram produzidos a partir de campos categóricos de texto diferentes.

Com legendas em ambos os períodos, a permanência é identificada pelo mesmo nome de classe (ignorando maiúsculas/minúsculas), ainda que os códigos sejam diferentes. Se um dos períodos não trouxer legenda, o critério passa a ser a igualdade dos códigos, exigindo harmonização prévia. A legenda descritiva é incluída na simbologia do QGIS e nos relatórios. As colunas originais dos relatórios de transições são preservadas, com acréscimo de `LEGENDA`, `DEIXOU_DE_SER` e `TORNOU_SE`.

## Mann–Kendall

A comparação simples 1986–2016 tem **duas observações** e não permite testar uma tendência temporal com Mann–Kendall. Nesse caso, `_tendencias_mk.csv` informa `NAO_APLICAVEL`, com estatísticas vazias, e `_resumo.txt` explicita a limitação. Nenhuma inferência estatística é inventada.

Para análise temporal opcional, marque **Adicionar mapas de outros anos para Mann–Kendall**, informe os anos nas duas entradas principais e acrescente, por meio de arquivos adicionais, pelo menos **três mapas intermediários ou de outros anos** (total de **cinco datas**). Séries com **oito a dez observações ou mais são recomendadas**. Os anos devem ser distintos, e todas as grades devem representar um mesmo domínio espacial e usar códigos temáticos consistentes. Mapas com SRC/grade incompatíveis são rejeitados; não há reamostragem implícita.

O algoritmo calcula, para cada categoria, a porcentagem de pixels ocupados em cada data, usando **somente a interseção espacial de pixels válidos em todas as datas**, eliminando alterações artificiais de denominador. Registra a estatística S, tau de Kendall, Z, p bilateral (exato para 5–7 observações; aproximação normal para 8+), inclinação de Sen (pontos percentuais por ano), correção Benjamini–Hochberg entre as classes, e significância nominal FDR 5%.

**Limites:** Mann–Kendall identifica tendências monotônicas de ocupação, não demonstra causalidade territorial nem valida a classificação cartográfica. Autocorrelação temporal, dependência entre proporções de classes, erros de classificação e não-independência espacial afetam a interpretação do p. O teste não substitui avaliação de acurácia dos mapas e estudos de causalidade.

## Novas saídas

Além do GeoTIFF, `_transicoes.csv`, `_matriz.csv` e `_resumo.txt`, o plugin gera `_tendencias_mk.csv`. Os cinco arquivos são escritos temporariamente e substituídos juntos, com proteção dos anteriores em caso de falha.

## Homologação QGIS 4.x

No Console Python do QGIS:

```python
from geosaga.tests.integration_monitoring_trends_qgis import run
run()
```

O script cria cinco mapas categóricos de teste em um diretório temporário e verifica a significância estatística calculada pelo GDAL real.
