# Vista Saga Plugin 0.7.3 — mitigação do travamento nativo do QGIS

O rastreamento Windows aponta para QCoreApplication.translate em algoritmo Processing ao abrir um projeto, não diretamente para o algoritmo Voronoi. Não é possível inferir a causa raiz apenas dessa pilha. Esta atualização elimina um risco de reentrância na execução do Voronoi raster: o uso de QApplication.processEvents() durante loops de GDAL/NumPy.

O Voronoi raster agora executa como `QgsTask` registrado no gerenciador de tarefas do QGIS. A thread de trabalho opera com tipos Python simples, NumPy e GDAL, não manipula widgets e não acessa camadas do projeto. Progresso e cancelamento são transmitidos pelos sinais de `QgsTask`. Resultados e mensagens são apresentados no método `finished`, na thread principal. Ao descarregar o plugin, a tarefa é cancelada e callbacks desassociados.

O Voronoi vetorial direto mantém a implementação síncrona da versão anterior; requer avaliação adicional para conjuntos de muitos centros. A paralelização GDAL não pode assegurar ausência de defeitos nativos externos. Esta versão não constitui uma correção comprovada do defeito apontado no componente Processing do QGIS.

## Diagnóstico comparativo no QGIS

1. Reiniciar o QGIS; abrir o mesmo projeto SEM executar o Voronoi.
2. Se houver falha, renomear temporariamente a pasta `%APPDATA%\QGIS\QGIS4\profiles\default\python\plugins\geosaga` com QGIS fechado e repetir; alternativamente usar um perfil limpo.
3. Testar a versão 0.7.3 com Voronoi raster pequeno, sem carregar grandes projetos simultaneamente.
4. Se ocorrer novamente, capturar relatório e instante exato da ação; informar se crash durante abertura de projeto, ao iniciar o Voronoi, durante processamento ou ao carregar o resultado.

Realizar backup de projeto e camadas antes de testes.
