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

## Verificação da versão 1.0.5 (QGIS 4.2.3, Linux)

Ambiente: QGIS 4.2.3, Qt 6.11, PyQt 6.11, GDAL 3.13 (conda-forge), modo `offscreen`.

| Suíte | Resultado |
|---|---|
| `geosaga/tests` (unittest; testes de versão/menu reescritos como verificações estruturais em `_support.py`) | 321 testes, 0 falhas, 14 pulados (Shapely/rasterio/PIL ausentes, arquivos de referência antigos) |
| `tests/unit` (pytest) | 35/35 |
| `tests/qgis/smoke_qgis.py`, exceções GDAL ligadas e desligadas | 45/45 em cada modo |
| `tests/qgis/gui_monkey.py` em `pt_BR` e `en_US` | 0 exceções não tratadas |

Pendente: execução das mesmas suítes no QGIS para Windows (OSGeo4W) e comparação numérica com o Vista SAGA/UFRJ. Instruções em [`tests/README.md`](../tests/README.md).

## Homologação da versão 1.1.0 (12/11/2026)

Módulo Avaliação (guias Raster, Vetorial (Atributos) e Vetorial (Sobreposição)). Build de teste
`1.1.0-dev6` aprovado pelo autor no QGIS para Windows, com a interface em português, inglês e
espanhol. Suítes locais: `geosaga/tests` OK (23 pulados por falta de GDAL/Shapely/rasterio no
contêiner); `tests/unit` 36/36. Nenhum algoritmo de cálculo alterado.

## Homologação parcial da versão 1.2.0 (build `1.2.0-dev6`)

Conversor de Formatos, só alterações de interface: novo nome do módulo ("Conversor de
Formatos"), aparência igual à dos demais módulos (área com rolagem com moldura), título do topo
da tela retirado e altura da janela ajustada ao conteúdo. Aprovado pelo autor no QGIS para
Windows. Suítes locais: `geosaga/tests` OK (23 pulados); `tests/unit` 36/36. Nenhum algoritmo de
conversão alterado; não exige validação no Vista SAGA original. A 1.2.0 segue em
desenvolvimento: novas alterações exigirão nova homologação.

### Build `1.2.0-dev12` — Combinação vetorial com tolerância de lascas e incorporação de resíduos

Caso real do autor (Renda × Escolaridade, EPSG:31985, 2.343,27 ha; dados fora do repositório):
no QGIS para Windows, a combinação das camadas originais concluiu com **15 combinações**, o mesmo
número previsto pela simulação com GEOS (antes: 24, das quais 9 formadas só por resíduos).
Regras cobertas por `test_120_sliver_tolerance.py` e `test_120_combination_fields.py`.
Conferido e homologado pelo autor: área total de 2.343,27 ha no `_resumo.txt`; linhas de lascas
toleradas e resíduos incorporados presentes no resumo; campos `COD_nn`/`LEG_nn` sem feições de
área quase nula na tabela; botões “Mover para cima/baixo” na Combinação e no Sequenciador.

### Build `1.2.0-dev15` — Monitoria

Homologado pelo autor no QGIS para Windows: resultado sempre carregado (raster em arquivo
temporário, vetor em memória) ou salvo; rótulos iguais nas guias Raster e Vetorial; Mann–Kendall
retirado (sem série temporal, sem `_tendencias_mk.csv`, sem seção no resumo); aviso de feições sem
classe (caso real Uso 1997 × 2011: com `CODIGO`, aviso; com `CLASSE`, área comum completa de
cerca de 4.225 ha); cópia das tabelas Raster e Vetorial para planilhas com Ctrl+A/Ctrl+C e decimal
do idioma. Suítes locais: `geosaga/tests` OK (16 pulados); `tests/unit` 36/36.

## Versão 1.2.0 fechada (16/11/2026)

Conversor de Formatos (dev6), Combinação de Mapas e Sequenciador (dev12) e Monitoria (dev15)
homologados pelo autor no QGIS para Windows. Pendente: revisão nativa das frases novas em inglês
e espanhol.

## Versão 1.2.1 fechada (16/11/2026)

Correções de interface (traduções do Sequenciador e texto do botão de opções avançadas do
Conversor). Fechada e incorporada a pedido do autor, com o build `1.2.1-dev1`. Suítes locais:
`geosaga/tests` OK (16 pulados); `tests/unit` 36/36; `test_121_i18n_fixes.py` novo.

## Versão 1.3.0 fechada (17/11/2026)

Análises Voronoi com guias Raster e Vetorial e vetor exato Com Massa (círculos de Apolônio).
Homologada pelo autor no QGIS para Windows com o build `1.3.0-dev3` (commit `9476819`): roteiro
de seis itens das notas da versão conferido. Suítes locais: `geosaga/tests` OK (423 testes, 38
pulados neste contêiner, sem GDAL); testes novos `test_130_voronoi_mass_direct.py` e
`test_130_voronoi_vector_output.py`. Guia Raster idêntica byte a byte à 1.2.1 (Simples e Com
Massa). Modelo de atrito inalterado; revisão prevista para a 1.4.0.
