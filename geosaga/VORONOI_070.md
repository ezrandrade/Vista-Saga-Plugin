# Voronoi Espacial — versão 0.7.0 (primeira etapa)

O Vista Saga Plugin mantém as quatro modalidades conceituais do programa original:

1. **Simples:** a menor distância euclidiana determina o centro de influência.
2. **Com Massa:** a força de influência é proporcional a `M/d`; utiliza o campo positivo de massa de cada ponto.
3. **Com Atrito:** planejada para a 0.7.1; exige acumulação espacial dos atritos do mapa raster.
4. **Com Massa e Atrito:** planejada para a 0.7.2; depende de validação prévia do atrito.

Os itens 3 e 4 aparecem desabilitados no menu. **Não existem resultados de atrito nessa versão.**

## Etapa 0.7.0

- Um mapa vetorial de **pontos** carregado no projeto QGIS como pontos geradores. Pontos multipartes são individualizados.
- Campo de nome opcional e campo de massa numérica obrigatório na modalidade Com Massa.
- Um **GeoTIFF de referência opcional** fornece extensão, grade, resolução e SRC; se não existir, o programa delimita a grade em torno dos pontos, com margem, usando resolução informada pelo usuário.
- A localização de cada centro é transformada para o SRC da grade; fonte inalterada.
- Somente SRC **projetado**; distância não é calculada diretamente em graus.
- Saída GeoTIFF de identificadores, CSV/TXT com áreas, e poligonização GeoPackage opcional. Arquivos temporários são carregados no QGIS e precisam ser salvos se forem importantes.
- Distância e massa são comparadas com os **centros dos pixels**. Em empates exatos, o primeiro ponto da ordem da camada vence.
- Para evitar excesso de memória: cálculo por faixas com até 50 milhões de células e 1.000 pontos.
- Não assume que todas as feições de uma camada poligonal sejam compatíveis: a fonte deve conter pontos.

## Limites metodológicos

A forma `F=M/d` é coerente com a equação publicada para o modelo complexo, assumindo atrito uniforme. A igualdade entre essa implementação discreta e os resultados pixel a pixel do programa original **ainda não foi demonstrada**. Para homologação metodológica, comparar os mapas gerados pelo Vista SAGA/UFRJ para os mesmos centros, massas, SRC e grade. Também verificar a regra original de empate, o tratamento de pontos coincidentes e o tamanho das células.

O Voronoi com atrito é diferente de uma simples aplicação de um coeficiente de fricção local a cada célula de destino. Uma implementação correta precisará computar a influência segundo a trajetória e as resistências da superfície, conforme a especificação original, e declarar quando empregar outro modelo de custo acumulado.

## Testes

Na instalação QGIS 4.x, Console Python:

```python
from geosaga.tests.integration_voronoi_qgis import run
run()
```

## Fontes de referência

- Marino, T. B. *Geoprocessamento para Análise Ambiental com SAGA*, slides 43–44: quatro modalidades e aquisição de centros/massas.
- Moura, A. C. M. *Aplicação do modelo de polígonos de Voronoi em estudos de áreas de influência de escolas públicas: estudo de caso em Ouro Preto–MG*, discussão de distância, massa e atrito (modelo de Xavier-da-Silva).
