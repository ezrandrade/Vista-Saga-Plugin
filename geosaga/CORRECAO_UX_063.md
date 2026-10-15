# Vista Saga Plugin 0.6.3 — Correção da interface

## Correções

- As abas Avaliação vetorial por atributos e por sobreposição agora recebem formulários QWidget, e não janelas QDialog reclassificadas após a criação. Preservam as tabelas, campos e cálculos estabelecidos nas versões anteriores.
- O botão **Fechar** desses formulários fecha o módulo no modo incorporado e a janela correspondente no modo independente.
- A Monitoria vetorial utiliza a mesma estratégia de incorporação QWidget.
- Exceções na montagem de formulários vetoriais passam a ser registradas na seção **Vista Saga Plugin** das mensagens de log do QGIS e apresentadas resumidamente na própria aba, em vez de deixá-la completamente vazia.
- O painel mantém cinco cartões uniformes, incluindo descrições sucintas, e recupera a informação de desenvolvimento independente, autoria e filiação institucional (IGDEMA/UFAL).
- Os motores analíticos e os identificadores legados não foram modificados.

## Limitações de validação

Esta distribuição passou por testes de sintaxe e regressão sem ambiente gráfico. **A exibição real das abas e os sinais Qt6 devem ser homologados em uma instalação QGIS 4.x**. Caso apareça erro, consulte **Exibir → Painéis → Mensagens de Log → Vista Saga Plugin** e envie o rastreamento de pilha completo.

## Instalação

Atualize usando **Complementos → Gerenciar e Instalar Complementos → Instalar a partir de ZIP** e reinicie o QGIS para descarregar os módulos Python da versão anterior.
