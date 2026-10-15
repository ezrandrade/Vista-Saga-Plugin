# Voronoi Espacial 0.7.1 — usabilidade e vetor direto

A modalidade **Simples** não exige massa ou raster de referência. O campo massa aparece somente em **Com Massa**. As modalidades com atrito ainda não estão implementadas.

## Extensão
- Extensão do mapa QGIS (padrão, transformada para o SRC dos pontos se necessário).
- Extensão de camada poligonal: para GeoPackage direto, as feições são recortadas aos polígonos; para raster, utiliza-se o retângulo envolvente.
- Extensão manual: X mínimo, Y mínimo, X máximo, Y máximo, no SRC dos pontos.
- Pontos com margem: usa envelope dos pontos mais margem; saída finita.
- Grade de raster de referência: somente para saída raster, com SRC/resolução/transformação do raster escolhido.

## Resultado
- GeoTIFF: discretização por pixel (Simples ou Com Massa).
- GeoPackage **direto**: divisão do retângulo de análise em semiplanos euclidianos, sem resolução/pixels, apenas Simples.
- GeoTIFF + GeoPackage: poligonização raster; limites discretizados, ambas as modalidades disponíveis.
- CSV e TXT por centro, área em hectares e participação no total; saídas temporárias no QGIS por padrão.

Os valores de área são planares no SRC projetado, convertidos a m² conforme unidade linear declarada pelo SRC. Se a extensão for definida pelos próprios pontos, ela depende da margem (não significa área de estudo oficial).

A equivalência quantitativa com o Vista SAGA/UFRJ ainda requer confronto com casos conhecidos. Esta revisão não implementa atrito.
