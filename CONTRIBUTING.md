# Contribuindo

Relate falhas em [Issues](https://github.com/ezrandrade/Vista-Saga-Plugin/issues), informando versão do QGIS/Qt/Python, sistema operacional, versão do plugin, modalidade e etapas para reproduzir. Dados e logs devem ser anonimizados antes de compartilhar.

Mudanças em algoritmos devem vir acompanhadas de teste de regressão e discussão da metodologia, especialmente para Voronoi com Atrito. Evite alterar o diretório Python `geosaga` e os IDs `geosaga:*` sem plano explícito de migração.

Antes de enviar contribuições, execute os testes unitários e verifique o funcionamento no QGIS 4.x. A versão 0.9.0 é candidata experimental à 1.0; não marque recursos novos como homologados sem testá-los em ambiente real.
