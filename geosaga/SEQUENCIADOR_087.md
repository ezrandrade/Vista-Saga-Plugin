# Sequenciador de Mapas — Vista Saga Plugin 0.8.7

## Visão geral

O módulo dispõe das abas **Raster**, **Vetorial** e **Misto**, com sequências de quadros independentes. O usuário seleciona mapas do projeto QGIS ou arquivos, ordena períodos e exporta um GIF animado. Opcionalmente, exporta cada quadro como PNG. Todos os quadros de uma sequência usam extensão, SRC do projeto e dimensão comuns, preservando visualmente a simbologia das camadas de origem.

## Raster

Adicione dois ou mais mapas raster, edite datas, ordene e exporte. Preserva o fluxo da versão 0.8.6.

## Vetorial

**Múltiplas camadas:** adicione mapas vetoriais (GeoPackage, Shapefile, GeoJSON etc.) em ordem temporal. O GIF apresenta cada camada em um quadro.

**Uma camada com campo temporal:** selecione a camada, o campo de ano/data e clique em **Gerar quadros por valores do campo temporal**. Cada valor distinto gera um quadro. Habilite **acumulativo** para mostrar também as feições dos períodos anteriores. O programa cria uma cópia temporária em memória em cada quadro; **não altera o filtro, os atributos nem a simbologia da camada original**. A renderização copia o estilo de simbologia e a configuração de rotulagem. Se a simbologia depende de junções complexas/campos virtuais, revise os resultados. Valores nulos são ignorados; até 120 períodos e leitura de até 200 mil feições no planejamento automático.

## Misto

Selecione o **raster de fundo** e o **vetor sobreposto** e adicione um quadro. Repita com outros pares se necessário. Alternativamente, selecione o campo temporal do vetor para criar vários quadros com o mesmo raster de fundo. O vetor fica acima do raster. É possível usar animação cumulativa de feições vetoriais.

## Exportação

- GIF: formato principal, com duração configurável por quadro e reprodução repetida; sem FFmpeg ou Pillow como dependência do plugin.
- PNG: opcional, um arquivo por quadro (`quadro_001_1985.png` etc.), nas cores renderizadas pelo QGIS, em pasta selecionável. A pasta padrão é `<nome_do_gif>_quadros_png`.
- Legenda temática: categorizada/graduada/simples conforme classes disponibilizadas pelo renderizador. Limitada às primeiras dez categorias. Revise especialmente legendas raster e simbologias complexas.
- Data e nome das camadas são opcionais. Nomes e data podem ser editados após a inclusão.
- Escala e enquadramento: uniformes dentro da sequência; a extensão considerada é a união das extensões das camadas. Quadros e GIF **não têm georreferenciamento**.
- GIF é limitado a 256 cores; cenas mais complexas serão quantizadas (PNG conserva a renderização original). Não é saída para medições quantitativas.
- Proteção inicial: até 120 quadros e 30 milhões de pixels RGB somados. Fontes vetoriais extensas podem demandar tempo e memória elevados.
- Cancelamento é verificado **entre quadros**, não durante uma renderização QGIS individual. PNGs já produzidos podem permanecer em caso de interrupção ou erro.

## Verificação no QGIS 4.2.2

1. Abra um projeto com 3 rasters e 3 vetores, confira que a aba Raster continua criando GIF.
2. Aba Vetorial: adicione três vetores separados por período e gere GIF/PNG; confira o estilo e os rótulos.
3. Na mesma aba, selecione um GeoPackage contendo um campo `ano` com 1985, 2000 e 2024; compare saídas *individual* e *acumulativa*.
4. Aba Misto: escolha um raster de fundo e um vetor por quadro, confira a ordem de desenho (vetor na frente).
5. Ainda na aba Misto, gere quadros por atributo com um fundo raster estático.
6. Confira dimensões, datas, legenda, GIF, PNG e se as camadas do projeto mantêm o estilo e o filtro anteriores.
7. Salve e reabra o projeto, em especial depois de fazer a animação.

Para teste automatizado integrado a partir do Console Python QGIS:

```python
from geosaga.tests.integration_sequence_maps_qgis import run
run()
```

Este teste cria dados sintéticos em memória e em diretório temporário, sem modificar seu projeto.

**Estado:** código e testes de unidade concluídos; interface/execução no QGIS 4.2.2 Windows e no QGIS 4.x Flatpak ainda não foram homologadas.
