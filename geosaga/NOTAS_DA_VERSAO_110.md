# Vista Saga Plugin 1.1.0 — notas da versão

Versão de interface do módulo **Avaliação**. Inclui tudo da 1.0.9. Nenhum algoritmo de cálculo
foi alterado: os resultados numéricos são os mesmos da versão anterior.

## O que muda para quem usa

- As guias vetoriais chamam-se **Vetorial (Atributos)** e **Vetorial (Sobreposição)** e seguem o
  leiaute da guia **Raster**: projeto, escala das notas, (1) critérios e pesos, (2) classes,
  (3) resultado.
- **Sobreposição:** as camadas entram por “Adicionar camadas do QGIS…” ou por “Adicionar de
  arquivo(s)…”, que abre na pasta das camadas já carregadas no QGIS. O campo temático é escolhido
  na entrada de cada camada.
- **Classes** e **Não avaliar** nas três guias; números alinhados à direita.
- **Resultado sempre carregado no QGIS.** Sem arquivo indicado: camada temporária em memória
  (vetor) ou arquivo temporário (raster). Salve-o antes de fechar o QGIS.
- **Ordenação pelo cabeçalho** das tabelas de classes (clique de novo para inverter).
- **TAB salta entre os pesos e entre as notas**, já com o valor selecionado para digitar.
- **Guia Raster sem Título e Autor**; o título dos relatórios passa a ser o nome do arquivo salvo.
- **Pesos e notas reaproveitáveis:** cada execução grava `<resultado>_pesos_notas.geosaga.json`.
  Para repetir a configuração em outra avaliação, use “Abrir projeto…” na mesma guia.

## Atenção

- Sem arquivo indicado em “Salvar em”, os relatórios e o arquivo de pesos e notas ficam na pasta
  temporária do QGIS, que é apagada ao fechá-lo. Para guardá-los, indique um arquivo ou use
  “Salvar projeto…”.
- Os projetos da guia Raster (`*.geosaga.json`) continuam compatíveis; projetos vetoriais e
  raster não se misturam (cada guia recusa o arquivo da outra, com aviso).
