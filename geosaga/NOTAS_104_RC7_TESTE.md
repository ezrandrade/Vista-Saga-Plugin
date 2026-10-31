# Vista Saga Plugin 1.0.4-rc7 — teste visual

Motivação: usuário relata que os sete módulos abrem normalmente, mas o ícone da rc6 não aparece na barra geral do QGIS.

Correção: uma barra específica `Vista Saga Plugin` é criada com `iface.addToolBar` e recebe um QToolButton real com menu instantâneo, PNG colorido e iconSize 32x32. A barra fica visível ao ativar o complemento, independentemente da barra genérica Complementos. Ao desativar, a barra e seus recursos são liberados.

**Teste:** ativar o plugin e verificar uma barra com o ícone da mão e o globo; clicar no ícone e conferir os sete módulos. Desativar/reativar para verificar a ausência de barras duplicadas. Repetir em Windows 11 e Linux/Flatpak. Caso a barra seja ocultada manualmente, reativar em Exibir → Barras de ferramentas → Vista Saga Plugin. A referência pt_BR/en permanece homologada da rc4.

**Importante:** não homologado em QGIS real nesta etapa. Não substitui a versão publicada 1.0.3. 
