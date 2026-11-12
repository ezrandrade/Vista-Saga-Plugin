# Vista Saga Plugin 1.2.0 — notas da versão

> **Em desenvolvimento.** Esta versão reúne as alterações do módulo **Conversor de Formatos**;
> outras mudanças serão acrescentadas antes do lançamento.

Inclui tudo da 1.1.0.

## O que muda para quem usa

- O módulo **Conversão de Formatos** passa a se chamar **Conversor de Formatos** (menu e título
  da janela). Em inglês, “Format converter”; em espanhol, “Conversor de formatos”.
- A janela do Conversor tem a mesma aparência dos demais módulos (cores das seções e linhas de
  contorno, como no Sequenciador de Mapas).
- O título grande no topo da tela foi retirado, como nos demais módulos; o nome do módulo continua
  na barra de título da janela.
- A altura da janela acompanha o conteúdo de cada operação, sem espaço vazio na parte inferior;
  ao abrir as opções avançadas ou ativar o lote, ela cresce (até 90% da altura da tela).

## Compatibilidade

- Nenhum algoritmo de conversão foi alterado: RS2, GeoTIFF e vetores gerados são os mesmos da 1.1.0.
- Os identificadores internos e os algoritmos Processing `geosaga:*` não mudam; projetos e modelos
  antigos continuam funcionando.
