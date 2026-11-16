# Vista Saga Plugin 1.2.0 — notas da versão

> **Em desenvolvimento.** Esta versão reúne as alterações dos módulos **Conversor de Formatos**,
> **Combinação de Mapas**, **Sequenciador de Mapas** e **Monitoria**; outras mudanças serão acrescentadas antes do lançamento.

Inclui tudo da 1.1.0.

## O que muda para quem usa

### Conversor de Formatos

- O módulo **Conversão de Formatos** passa a se chamar **Conversor de Formatos** (menu e título
  da janela). Em inglês, “Format converter”; em espanhol, “Conversor de formatos”.
- A janela do Conversor tem a mesma aparência dos demais módulos (cores das seções e linhas de
  contorno, como no Sequenciador de Mapas).
- O título grande no topo da tela foi retirado, como nos demais módulos; o nome do módulo continua
  na barra de título da janela.
- A altura da janela acompanha o conteúdo de cada operação, sem espaço vazio na parte inferior;
  ao abrir as opções avançadas ou ativar o lote, ela cresce (até 90% da altura da tela).

### Monitoria

- **Resultado sempre carregado no QGIS**, nas guias Raster e Vetorial: sem arquivo em “Salvar em”,
  arquivo temporário (raster) ou camada temporária em memória (vetor).
- As duas guias usam os mesmos rótulos.
- **O teste de Mann–Kendall saiu da Monitoria** e volta como módulo próprio na versão 2.0. Não
  são mais gerados `_tendencias_mk.csv` nem a seção de Mann–Kendall no `_resumo.txt`. Transições,
  matrizes e áreas são as mesmas da 1.1.0.

### Sequenciador de Mapas

- Os botões de ordem chamam-se **Mover para cima** e **Mover para baixo**.

### Combinação de Mapas

- As guias chamam-se **Raster** e **Vetorial**, como nos demais módulos.
- O botão que inclui a camada escolhida no menu suspenso chama-se **Adicionar camada selecionada**;
  os botões de ordem chamam-se **Mover para cima** e **Mover para baixo**.
- **Resultado sempre carregado no QGIS.** Sem arquivo em “Salvar em”: camada temporária em memória
  (vetor) ou arquivo temporário (raster). Salve-o antes de fechar o QGIS. Sem arquivo indicado, os
  relatórios `_combinacoes.csv` e `_resumo.txt` ficam na pasta temporária do QGIS.
- **Trocar o campo de classe de qualquer camada já adicionada:** selecione-a em “Camadas
  adicionadas” e escolha outro campo em “Campos de classe e legenda”; a alteração vale na hora.
  Sem seleção na lista, os campos são os da camada do menu suspenso, que será adicionada.
- Cada camada entra **uma única vez**, com o campo de classe escolhido para ela. Se a mesma camada
  for adicionada de novo, um aviso mostra o campo já usado.

- **Lascas de precisão não bloqueiam mais a combinação vetorial.** Sobreposições entre polígonos
  de uma mesma camada com largura média abaixo de 1 cm (por exemplo, fronteiras com vértices
  ligeiramente diferentes depois de reprojeção) são mantidas, e o `_resumo.txt` informa quantas
  são e a área duplicada. Sobreposições mais espessas continuam bloqueando, e a mensagem lista
  todos os pares com área e largura. Registre a tolerância na metodologia, se a usar.

- **Resíduos do cruzamento não viram mais combinações falsas.** Tiras com menos de 1 cm de largura
  média, criadas por fronteiras quase coincidentes entre os mapas, são fundidas ao vizinho de maior
  fronteira comum; a área total não muda. O `_resumo.txt` informa quantos resíduos foram tratados.
  O mapa vetorial passa a ter uma feição por parte simples.
- No mapa vetorial combinado, os campos `C01`/`L01`, `C02`/`L02`… chamam-se agora
  **`COD_01`/`LEG_01`, `COD_02`/`LEG_02`…**: código e legenda da classe de cada mapa, na ordem da
  lista (a correspondência mapa ↔ camada está no `_resumo.txt`).

## Compatibilidade

- Nenhum algoritmo de conversão foi alterado. Na combinação vetorial, mudam a tolerância de
  lascas (camadas antes recusadas por lascas passam a ser combinadas) e a incorporação de
  resíduos (combinações que só existiam em tiras microscópicas desaparecem; a área total é a
  mesma). O `_resumo.txt` ganha as linhas correspondentes. A combinação raster não mudou.
- Resultados vetoriais da Combinação gerados pela 1.2.0 usam `COD_nn`/`LEG_nn`; estilos e
  expressões feitos sobre `Cnn`/`Lnn` precisam ser ajustados.
- Os identificadores internos e os algoritmos Processing `geosaga:*` não mudam; projetos e modelos
  antigos continuam funcionando.
