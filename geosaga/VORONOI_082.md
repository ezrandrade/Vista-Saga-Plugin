# Vista Saga Plugin 0.8.2 — Correção do progresso no QGIS 4.2.2 / Qt6

## Falha corrigida

Na versão 0.8.1, o sinal `QgsTask.progressChanged` (percentual como `float`) era
conectado diretamente a `QProgressDialog.setValue`, que recebe `int` no Qt6.
No QGIS 4.2.2 essa ligação causava `TypeError: setValue(self, progress: int):
argument 1 has unexpected type 'float'` durante a operação raster de Voronoi.

A 0.8.2 substitui a ligação direta por um slot `@pyqtSlot(float)` no objeto
`VoronoiDialog`, convertendo para inteiro, limitando a 0–100 e ignorando sinais
não finitos ou recebidos após a conclusão/cancelamento da tarefa.

## O que não mudou

Os motores do Voronoi Simples, com Massa, com Atrito e com Massa e Atrito são
**idênticos aos da 0.8.1**. Também estão inalterados os motores de Avaliação,
Monitoria, Assinatura, Combinação de Mapas, Conversão e Sequenciamento de GIF.

## Homologação necessária

1. Instalar o ZIP 0.8.2, reiniciar completamente o QGIS 4.2.2.
2. Repetir Voronoi com Atrito com os mesmos pontos e GeoTIFF de declividade.
3. Confirmar que o percentual evolui sem o TypeError. Conferir resultado GeoTIFF,
   relatório CSV/TXT, tempo e eventual aviso do próprio motor de cálculo.
4. Repetir em área pequena com Massa e Atrito, pois ambas usam o mesmo slot.

**Importante:** o modelo de atrito permanece experimental e ainda precisa ser
comparado numericamente ao Vista SAGA/UFRJ. Corrigir a barra de progresso
não demonstra que o cálculo completo foi concluído nem validado.
