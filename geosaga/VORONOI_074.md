# Vista Saga Plugin 0.7.4 — Voronoi com Atrito (experimental)

## Abrangência da versão

A partir da base 0.7.3 homologada, adiciona a terceira modalidade **Com Atrito** à janela **Voronoi Espacial**. As modalidades **Simples** e **Com Massa** permanecem com os respectivos cálculos, interfaces e saídas anteriores. A quarta modalidade (**Com Massa e Atrito**) permanece desabilitada até a implementação e validação específica.

## Fundamento metodológico e limitações

O modelo de influência descrito por Moura e Xavier-da-Silva pode considerar a distância euclidiana do centro e o atrito acumulado ao longo da trajetória. Esta versão implementa **experimentalmente**, no raster, uma variante de percurso *reto*, sem busca de caminho de menor custo:

- Cada segmento liga o ponto gerador ao centro da célula avaliada.
- Um algoritmo DDA percorre todas as células tocadas em sua trajetória, sem contar contatos exclusivamente pontuais nos vértices.
- O custo de cada célula visitada é **1 + C_k**, sendo `C_k >= 0` o valor numérico de atrito fornecido pelo usuário. Esse custo basal de 1 é uma convenção explícita para evitar atrito total nulo e permitir valores de atrito iguais a zero; não é uma regra histórica comprovada do software original.
- Calcula-se **S_i(x) = D_i(x) · Σ_k(1 + C_k)**. A célula é atribuída ao centro com menor S; empates são resolvidos pela ordem dos centros.
- Células com NoData são **barreiras**: qualquer trajetória que as cruze torna aquele centro inelegível para a célula analisada. Uma célula que nenhum centro consegue alcançar permanece como NoData (0) no resultado.
- Não há reprojeção/reescala implícita do raster de atrito. O GeoTIFF deve estar em SRC projetado, ter uma única banda e grade norte-acima, sem rotação.

**Limite científico:** a documentação consultada sustenta a acumulação do atrito no trajeto e sua combinação com a distância, mas não fornece especificação completa da rasterização, dos valores nulos, dos zeros, empates e cortes das trajetórias do executável histórico. Por isso, **não se afirma equivalência numérica com o Vista SAGA/UFRJ**. Esse cotejo requer superfícies e mapas de saída do software original para os mesmos centros e parâmetros.

## Como utilizar no QGIS 4.x

1. Instale o ZIP e reinicie o QGIS.
2. Carregue uma camada de pontos com SRC projetado e um GeoTIFF monobanda de **atrito** no QGIS.
3. Acesse **Painel de módulos → Voronoi Espacial → Com Atrito (experimental)**.
4. Selecione os pontos e a superfície de atrito. A grade de saída herdará extensão, resolução e SRC do raster de atrito.
5. Escolha GeoTIFF ou GeoTIFF + GeoPackage. Selecione resultado temporário ou permanente.
6. Execute e confira o mapa, a tabela `_centros.csv` e o relatório `_resumo.txt`.

Os centros devem ficar no interior de uma célula válida do raster de atrito. Raster RS2 deve ser convertido previamente para **GeoTIFF monobanda** usando o Conversor de Formatos existente; a atribuição do SRC não deve ser presumida a partir das coordenadas.

## Restrições e segurança

- Para limitar memória e tempo nesta primeira implementação, o raster de atrito admite até **8 milhões de células**, até **500 pontos**, e uma estimativa de até **700 milhões de travessias de células**. Superfícies amplas podem requerer recorte ou grade de menor resolução. A estimativa é preventiva, não uma afirmação sobre o desempenho do computador.
- O processamento é executado em `QgsTask`, com progresso e cancelamento, sem `QApplication.processEvents()` no worker.
- O raster de saída é codificado por `CENTRO_ID`; o valor 0 é NoData. GeoPackage opcional é produzido pela poligonização de células válidas.
- Se houver áreas de NoData, apenas pixels classificados são considerados nos percentuais. O relatório informa a quantidade de pixels excluídos.
- A fonte raster de atrito e a camada de pontos são preservadas. A saída é montada em diretório temporário de estágio e publicada com restauração dos arquivos anteriores caso a publicação falhe.

## Testes

A função `geosaga.tests.integration_voronoi_friction_qgis.run()` pode ser executada pelo Console Python do QGIS para verificar um exemplo de 5 células, sem modificar os dados do usuário.

Referências orientadoras: Moura, *Aplicação do modelo de polígonos de Voronoi em estudos de áreas de influência de escolas públicas* (Revista Brasileira de Estudos Regionais e Urbanos), e material de Tiago Badre Marino sobre Vista SAGA.
