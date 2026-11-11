# Vista Saga Plugin 1.0.5 — notas da versão

Versão de estabilidade. Nenhum algoritmo numérico foi alterado; identificadores `geosaga:*` preservados.

- Mensagens de erro e avisos traduzidas conforme o idioma do QGIS (inglês como reserva).
- Exceções GDAL/OGR/OSR ligadas apenas durante as conversões, sem alterar o estado global do QGIS.
- Datasets GDAL fechados antes da limpeza de pastas temporárias (evita erros mascarados no Windows).
- Assinatura: contexto de transformação do Processing e mensagens claras de falha de reprojeção.
- Driver `MEM` do GDAL ≥ 3.11 (com alternativa), tipos `QMetaType` em campos.
- Falhas inesperadas registradas com traceback na aba "Vista Saga Plugin" do painel de mensagens.
- API pública do plugin preservada (`open_signature`, `open_monitoring`, … `open_algorithm`).

Verificado em QGIS 4.2.3 (Qt 6.11, GDAL 3.13), Linux. Validação em Windows pendente.
Detalhes em `CHANGELOG.md`.
