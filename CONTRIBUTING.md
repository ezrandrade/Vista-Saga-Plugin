# Contribuindo

Relate falhas em [Issues](https://github.com/ezrandrade/Vista-Saga-Plugin/issues), informando versão do QGIS/Qt/Python, sistema operacional, versão do plugin, modalidade e etapas para reproduzir. Dados e logs devem ser anonimizados antes de compartilhar.

Mudanças em algoritmos devem vir acompanhadas de teste de regressão e discussão da metodologia, especialmente para Voronoi com Atrito. Evite alterar o diretório Python `geosaga` e os IDs `geosaga:*` sem plano explícito de migração.

Antes de enviar contribuições, execute as duas suítes de testes e verifique o funcionamento no QGIS 4.x. Não marque recursos novos como homologados sem testá-los em ambiente real.

```bash
python -m unittest discover -s geosaga/tests -p 'test_*.py'
python -m pytest -q tests/unit
```

Textos de interface e mensagens passam por `tr()` e precisam de tradução nos dois catálogos, `geosaga/i18n/en.json` e `geosaga/i18n/es.json`; mensagens montadas em tempo de execução usam modelos com `{0}`, `{1}`… Os testes falham se faltar alguma frase em qualquer um dos catálogos.
