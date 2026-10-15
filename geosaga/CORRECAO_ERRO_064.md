# Correção da Avaliação Espacial — versão 0.6.4

A aba "Vetorial — sobreposição" falhava com `UnboundLocalError: cannot access local variable 'QPushButton' where it is not associated with a value`.

A classe `QPushButton` já era importada no escopo de módulo, mas uma segunda importação dentro de `_build()` fazia Python tratar o nome como local em todo o método. A importação local redundante foi removida.

A verificação foi realizada por análise estática, testes automatizados e compilação de sintaxe. A validação visual continua pendente no QGIS 4.x.

O rastreamento fornecido pelo usuário mostrava `dialog_type(self.iface, self)`, chamada da 0.6.2, não da 0.6.3, que utiliza `dialog_type(self.iface, parent=self, embedded=True)`. Caso essa chamada antiga permaneça após instalar a 0.6.4, confirmar a versão carregada e reiniciar o QGIS.
