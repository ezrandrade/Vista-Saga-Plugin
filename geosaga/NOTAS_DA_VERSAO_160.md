# Vista Saga Plugin 1.6.0 — notas da versão

> Versão estável (20/11/2026), homologada pelo autor no QGIS 4. Inclui tudo da 1.5.0. **Só interface:
> nenhum código de cálculo foi alterado.**

## Dicas em todos os módulos

Ao parar o mouse sobre qualquer **botão, campo, caixa de marcar ou lista** de qualquer módulo, aparece a caixa
amarela do QGIS explicando o que o elemento é e o que acontece ao usá-lo.

| Módulo | Elementos que ganharam dica |
|---|---|
| Avaliação (três guias) | 44 |
| Monitoria (Raster e Vetorial) | 32 |
| Análises Voronoi (inclusive a janela das superfícies de atrito) | 25 |
| Combinação de Mapas | 24 |
| Conversor de Formatos | 26 |
| Sequenciador de Mapas | 33 |
| Assinatura | já completa na 1.5.0 |

Os textos são curtos, descrevem a ação ("Acrescenta…", "Retira…", "Escolhe…") e foram revisados e aprovados pelo
autor, módulo a módulo. Inglês e espanhol completos.

## Decisão do autor (20/11/2026)

Dicas só em botões, campos, caixas de marcar e listas (sem cabeçalhos de tabela nem abas), começando pela
Avaliação, em lotes revisados um a um. As dicas, previstas de início para a 1.5.0, viraram esta versão.

## Correções

- Dicas de alguns botões (ex.: "Atualizar" e "Distribuir pesos igualmente" da Avaliação) apareciam em português
  com o QGIS em inglês ou espanhol.
- Rótulos da extensão manual do Voronoi ("X mínimo:" etc.) também apareciam em português.

## Testes

- Suítes verdes (503 e 42).
- `tests/qgis/tooltip_inventory.py`: abre os sete módulos em QGIS real, passa por todas as guias e confirma que
  nenhum botão, campo, caixa de marcar ou lista ficou sem dica.
- Teste do autor no QGIS 4: **versão homologada** (20/11/2026).
