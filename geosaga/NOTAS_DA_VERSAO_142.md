# Vista Saga Plugin 1.4.2 — notas da versão

> Versão estável (19/11/2026). Inclui tudo da 1.4.1. **Só interface (Sequenciador de Mapas): nenhum
> código de cálculo foi alterado.**

## O que muda para quem usa

### Sequenciador de Mapas: as três guias com a mesma altura

As guias **Raster**, **Vetorial** e **Misto** passam a ter a mesma altura, compacta. Ao trocar de guia,
a barra de abas e a lista "1. Sequência de quadros da aba selecionada" ficam sempre no mesmo lugar.

| | 1.4.0 | 1.4.1 | 1.4.2 |
|---|---|---|---|
| Altura das guias | todas 334 px | 122 / 298 / 334 px | **todas 264 px** |
| Espaço livre na guia Raster | cerca de 210 px | nenhum | cerca de 140 px |
| Lista de quadros ao trocar de guia | parada | sobe e desce | **parada** |

Os textos explicativos das guias Vetorial e Misto saíram de dentro das guias e viraram **dicas**: aparecem
ao passar o mouse sobre a aba ou sobre o botão de gerar quadros (no Misto, também sobre "Adicionar quadro
misto").

## Decisão do autor (19/11/2026)

Mesma altura nas três guias, compacta, com os textos explicativos como dicas (em vez de altura por guia,
que movia a lista, ou da altura antiga com os textos, que deixava espaço vazio na guia Raster).

## Testes

- Suítes verdes; `test_161_sequenciador_guias.py` reescrito.
- Janela aberta em QGIS 3.34 sem interface gráfica (não é o alvo): as três guias com 264 px e a barra de
  abas na mesma posição.
- Teste do autor no QGIS 4: **versão homologada** (19/11/2026). Observação do autor: o espaçamento da guia
  Raster pareceu igual ao de antes; a medição em QGIS 3.34 indica cerca de 140 px livres, contra cerca de
  210 px na 1.4.0. Questão deixada pelo autor para outro momento.
