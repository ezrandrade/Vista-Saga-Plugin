# Vista Saga Plugin 1.2.0 — notas da versão

> **Em desenvolvimento.** Esta versão reúne as alterações dos módulos **Conversor de Formatos** e
> **Combinação de Mapas**; outras mudanças serão acrescentadas antes do lançamento.

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

### Combinação de Mapas

- As guias chamam-se **Raster** e **Vetorial**, como nos demais módulos.
- O botão que inclui a camada escolhida no menu suspenso chama-se **Adicionar camada selecionada**.
- **Resultado sempre carregado no QGIS.** Sem arquivo em “Salvar em”: camada temporária em memória
  (vetor) ou arquivo temporário (raster). Salve-o antes de fechar o QGIS. Sem arquivo indicado, os
  relatórios `_combinacoes.csv` e `_resumo.txt` ficam na pasta temporária do QGIS.
- **Trocar o campo de classe de qualquer camada já adicionada:** selecione-a em “Camadas
  adicionadas” e escolha outro campo em “Campos de classe e legenda”; a alteração vale na hora.
  Sem seleção na lista, os campos são os da camada do menu suspenso, que será adicionada.
- Cada camada entra **uma única vez**, com o campo de classe escolhido para ela. Se a mesma camada
  for adicionada de novo, um aviso mostra o campo já usado.

## Compatibilidade

- Nenhum algoritmo de conversão ou de combinação foi alterado: RS2, GeoTIFF, vetores, mapas
  combinados e relatórios gerados são os mesmos da 1.1.0.
- Os identificadores internos e os algoritmos Processing `geosaga:*` não mudam; projetos e modelos
  antigos continuam funcionando.
