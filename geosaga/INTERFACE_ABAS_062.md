# Vista Saga Plugin 0.6.2 — Homologação de UX

## Escopo

Alterações somente em `home_dialog.py`, `evaluation_dialog.py`, `monitoring_dialog.py`, `vector_evaluation_dialog.py` (navegação entre abas) e `vector_monitoring_dialog.py` (destino dos resultados).

### Avaliação

- Aba Raster: permanece com o formulário da 0.6.1.
- Vetorial — atributos: agora exibe diretamente camada, campos, pesos, notas, exclusões, saída e execução.
- Vetorial — sobreposição: exibe diretamente a pilha de camadas, campo temático de cada uma, pesos/notas, saída e execução; controles originais reaproveitados.
- O botão para navegar entre as modalidades vetoriais muda de aba, em vez de abrir outra janela.

### Monitoria

- Aba Raster: inalterada.
- Aba Vetorial: apresenta diretamente os dois mapas de entrada, campos e períodos, destino e execução.
- Aba Resultados: subtabs Raster/Vetorial; após execução, navega automaticamente à subaba pertinente.
- Os controles de execução raster ficam ocultos nas abas que não sejam Raster, impedindo executar o modo errado.

### Painel

Cinco cartões de mesmo estilo, em duas linhas. Somente duas frases instrutivas são mostradas além dos nomes, números e botões dos módulos.

## Testes no QGIS

1. Abrir painel; conferir cinco cartões equivalentes e o texto instrutivo.
2. Avaliação: entrar em Vetorial por atributos, configurar dois campos e executar; retornar à Raster; abrir Sobreposição, empilhar duas camadas, editar pesos/notas e executar.
3. Monitoria: entrar na aba Vetorial, definir mapas de anos diferentes, classes/legendas, executar e verificar Resultados → Vetorial; depois repetir Monitoria raster e verificar Resultados → Raster.
4. Conferir os botões Fechar, o comportamento durante tarefas e se Assinatura/Combinação permanecem idênticos à 0.6.1.

> O ambiente de construção do pacote não dispõe de Qt6/PyQGIS instalado. A execução gráfica requer homologação no QGIS 4.x.
