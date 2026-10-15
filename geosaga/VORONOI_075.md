# Voronoi Espacial 0.7.5 — Massa e Atrito (experimental)

Quatro modalidades visíveis e disponíveis: Simples, Com Massa, Com Atrito, Com Massa e Atrito.

Para massa+atrito, o índice de influência por centro e célula é `D × SUM(1 + C_k) / M`, em que D é a distância euclidiana, C_k é o valor de atrito das células atravessadas pelo segmento reto e M é a massa positiva do centro. A célula é atribuída ao menor índice; empates preservam a ordem dos geradores.

**Limitação científica**: a soma usa custo basal 1 e traçado DDA sobre o segmento reto. Não busca caminhos alternativos de custo mínimo e não foi validada contra a implementação original do Vista SAGA/UFRJ. Não utilizar como equivalente à versão original sem teste comparativo.

Requisitos: pontos com campo numérico de massa positiva, GeoTIFF de atrito monobanda em CRS projetado compatível. NoData é barreira, valor 0 é permitido como atrito mínimo. O GeoTIFF de entrada é somente leitura.

**Testes de homologação**: comparar com Voronoi com Atrito usando massas iguais; verificar predominância esperada do centro com maior massa; testar rasters pequenos com barreiras e comparar o resultado com o software original.
