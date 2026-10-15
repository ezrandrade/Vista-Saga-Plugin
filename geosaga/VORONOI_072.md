# Voronoi Espacial 0.7.2 — Correção do processamento raster

## Motivo

A versão 0.7.1 interrompia o cálculo se `largura × altura × número de centros > 300.000.000`, independentemente da memória disponível. Isso impedia análises raster viáveis.

## Mudança

- O limite artificial de comparações foi removido. Mantém-se o limite de 50 milhões de pixels para impedir saídas excessivamente grandes.
- A grade é processada em janelas adaptativas de aproximadamente 200 mil pixels, preservando progresso e cancelamento.
- Para **Voronoi Simples**, quando o Python do QGIS possui SciPy, usa-se um índice espacial `cKDTree`, com conferência de empates. **SciPy é opcional**: sem ele, a análise usa o cálculo NumPy original, potencialmente mais lento.
- Para **Voronoi com Massa**, mantém-se a fórmula original `M/d`; o cálculo é feito por janelas, mas sua duração ainda aumenta com a quantidade de pontos.
- Os resultados, os códigos, o formato dos relatórios, o carregamento no QGIS, a opção de GeoPackage direto e as demais análises são preservados.
- O modelo de atrito permanece pendente de implementação e comparação com o Vista SAGA/UFRJ.

## Validação

A suíte automatizada verifica equivalência de classificação em grade comum e rotacionada, máscara, empate e preservação da ponderação por massa. A geração real via GDAL e o tempo de execução com grandes bases precisam ser testados em QGIS 4.x no Windows e Linux/Flatpak.

## Teste sugerido

Repita a análise que antes exibia o limite de 300 milhões. Use saída GeoTIFF temporária, confira o consumo de RAM, progresso e CSV. Em projetos com muitos centros e grandes dimensões, o tempo de execução pode ser considerável, sobretudo se SciPy não estiver disponível.
