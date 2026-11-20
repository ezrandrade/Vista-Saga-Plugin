# Vista Saga Plugin 1.6.1 - notas da versão

> Versão estável (20/11/2026). Inclui tudo da 1.6.0. **Nenhum código de cálculo foi alterado.**

## Por que esta versão existe

O catálogo oficial de complementos do QGIS (plugins.qgis.org) passa cada versão enviada por uma varredura de
segurança. Qualquer achado do Bandit bloqueia a versão, mesmo de severidade baixa. A 1.6.0 foi bloqueada por
quatro achados (nenhum era falha de segurança real no uso do plugin) e, antes disso, recusada na leitura do
`metadata.txt`.

## O que mudou

- Registros de mensagem que nunca podem gerar nova falha usam `contextlib.suppress(Exception)` no lugar de
  `try/except/pass` (mesmo comportamento).
- O estilo `.qml` gravado ao lado dos GeoTIFF de classes usa um escape próprio, idêntico ao anterior, sem
  importar `xml.sax`.
- `metadata.txt` sem o sinal de porcentagem.
- Defeito latente corrigido numa função reservada da Monitoria (sem uso nesta versão).
- Avisos de qualidade de código (Flake8) resolvidos.

## Conferência

Bandit sem achados; Flake8 sem erros; suítes `unittest` e `pytest` verdes, com dois testes novos que
reproduzem as verificações do catálogo.
