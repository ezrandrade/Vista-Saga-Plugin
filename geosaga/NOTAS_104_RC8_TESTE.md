# Vista Saga Plugin v1.0.4-rc8 — teste de integração visual

## Interface clássica

O botão do Vista Saga Plugin aparece na barra própria, com tamanho de ícone
**24 x 24 px** e um menu suspenso de **sete módulos**. A barra é removida no
`unload()` do complemento.

## Interface QRibbonSkin

O QRibbonSkin oculta as barras nativas do QGIS ao ativar o Ribbon. Por isso,
a mesma `QAction` com seu `QMenu` é registrada no menu nativo **Complementos**,
que o QRibbonSkin utiliza para compor sua aba correspondente. Isso evita
acesso aos componentes internos do outro plugin.

1. Instale/habilite o Vista Saga Plugin.
2. Use a interface clássica e confira o ícone de 24 px e os sete módulos.
3. Habilite o QRibbonSkin; verifique em **Complementos > Vista Saga Plugin**
   o botão com ícone e seu menu dos sete módulos.
4. Se a Ribbon já estava ativa, alterne uma vez para interface clássica e
   habilite novamente; o QRibbonSkin constrói as ações da aba na ativação.
5. Alterne de volta para QGIS clássico e verifique se o botão reaparece.
6. Desabilite/reabilite o Vista Saga e confira a ausência de botões duplicados.

Esta versão não altera algoritmos, dados de saída ou identificadores geosaga:*.
A compatibilidade visual ainda requer validação real no QGIS 4.x com QRibbonSkin.
