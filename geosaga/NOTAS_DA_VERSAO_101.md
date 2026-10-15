# Vista Saga Plugin 1.0.1 — Correção de segurança QGIS

Atualização pontual da versão 1.0.0 para atender ao analisador Bandit no repositório de complementos do QGIS.

- Em `rs2_dialog.py`, as duas exceções amplas de simbologia vetorial deixam de ser ignoradas silenciosamente.
- Falhas opcionais de renderização categórica de vetores RS2 ou GeoTIFF são registradas em **Exibir → Painéis → Mensagens de Log** (categoria **Vista Saga Plugin**, nível **Aviso**).
- O dado vetorial gerado continua utilizável mesmo que a simbologia falhe.
- Nenhum algoritmo de conversão, monitoria, avaliação, assinatura, combinação de mapas, Análises Voronoi ou Sequenciador de Mapas foi alterado.
- A pasta `geosaga` e os identificadores `geosaga:*` foram preservados.

Esta atualização deve passar novamente pela análise automática da infraestrutura QGIS. O sucesso nos testes locais não substitui a aprovação na plataforma.
