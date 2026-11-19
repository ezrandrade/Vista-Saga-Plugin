# Vista Saga Plugin 1.4.1 — notas da versão (em teste)

> Versão em teste (19/11/2026). Inclui tudo da 1.4.0. **Só interface: nenhum cálculo muda**; resultados
> da 1.4.0 se reproduzem byte a byte.

## O que muda para quem usa

### O mesmo rodapé em todos os módulos

Todos os módulos terminam com os mesmos botões, à direita e fora das guias:

> **[Executar] [Fechar]** (na Avaliação: **[Validar] [Executar] [Fechar]**)

| Módulo | Antes | Agora |
|---|---|---|
| Assinatura | Calcular assinatura | Executar |
| Monitoria (Raster) | barra 0%, Executar monitoria, Cancelar | Executar |
| Monitoria (Vetorial) | Executar monitoria, numa linha acima do Fechar | Executar, no rodapé |
| Avaliação (Raster) | Validar, Executar avaliação, Cancelar execução, dentro da guia | Validar, Executar |
| Avaliação (Vetorial) | Validar, Executar avaliação / Executar sobreposição e avaliação, no fim da rolagem | Validar, Executar, no rodapé |
| Análises Voronoi | Gerar Voronoi | Executar |
| Combinação de Mapas | Combinar mapas | Executar |
| Conversor de Formatos | Propriedades RS2… à esquerda, Executar | Executar (Propriedades RS2… ao lado do arquivo de entrada) |
| Sequenciador de Mapas | Gerar GIF | Executar |

### Progresso e cancelamento só durante a execução

A linha de status à esquerda do rodapé, a barra de progresso e os botões Cancelar permanentes saíram.
Durante a execução, abre-se uma janela com a porcentagem e o botão **Cancelar**, que fecha sozinha ao
terminar (o padrão que Voronoi, Combinação, Assinatura, Conversor e Sequenciador já usavam). Nada deixou
de poder ser cancelado.

O desfecho que antes aparecia na linha de status (concluída, cancelada, prévia limitada a 500 transições,
projeto salvo ou carregado) aparece na **barra de mensagens do QGIS**, acima do mapa. Falhas continuam
em caixas de mensagem.

## Decisões do autor (19/11/2026)

- Botão de ação "Executar" em todos os módulos; "Validar" só na Avaliação (única exceção).
- Progresso e Cancelar numa janela só durante a execução (sem perder o cancelamento).
- Sem linha de status no rodapé.
- Versão própria (1.4.1), separada da 1.4.0 já validada.

## Testes

- Suítes verdes; `test_160_rodape_padrao.py` confere os rótulos, a ausência de status, barra e Cancelar
  fixos, o Validar só na Avaliação, a janela de progresso e o rodapé comum das guias vetoriais.
- Janelas abertas em QGIS 3.34 sem interface gráfica (não é o alvo): rodapés capturados nos 7 módulos e
  nas guias, e a janela de progresso.
- **Pendente:** teste do autor no QGIS 4 (ZIP `-dev1`).
