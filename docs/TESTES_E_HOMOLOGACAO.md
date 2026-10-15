# Testes e homologação — Vista Saga Plugin 1.0.0

## Confirmado até o momento

- Sete módulos homologados funcionalmente pelo desenvolvedor/testador no QGIS 4.2.2 para Windows.
- Suíte local automatizada registrada no relatório de auditoria anterior: **324 testes + 12 subtestes**. Isso não equivale a testes de GUI no Qt6.
- Os motores de cálculo da 1.0.0 permanecem idênticos aos da 0.9.0. Mudanças da 1.0.0 se restringem a nomes públicos e ordem da interface, metadados e documentação.

## Checklist antes da versão 1.0 estável

1. Instalar o ZIP em perfil limpo do QGIS 4.x/Qt6, sem complementos de terceiros.
2. Abrir e executar uma amostra representativa de cada módulo com saída salva.
3. Salvar e reabrir um projeto `.qgz` que contenha resultados produzidos; verificar referências aos arquivos e estabilidade.
4. Verificar desativação/reativação do plugin e acesso à Caixa de Ferramentas Processing.
5. Testar em Linux/Flatpak, incluindo diretórios de entrada e saída autorizados pelo sandbox.
6. Realizar comparação numérica controlada da modalidade Voronoi com Atrito com resultados de referência Vista SAGA/UFRJ, diferenciando variantes metodológicas.
7. Rever os avisos de métodos experimentais, strings da interface, licença e metadados antes de solicitar publicação QGIS.

## Testes locais e integração

```bash
python -m compileall -q geosaga
python -m unittest discover -s geosaga/tests -p 'test_*.py'
```

Os arquivos `geosaga/tests/integration_*_qgis.py` destinam-se a um QGIS real; podem ser executados pelo Console Python do QGIS conforme as instruções de cada módulo.

**Aviso metodológico:** testes funcionais satisfatórios não demonstram por si só equivalência com a formulação numérica original do Vista SAGA/UFRJ.
