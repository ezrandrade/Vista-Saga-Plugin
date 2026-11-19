# CLAUDE.md — Vista Saga Plugin

Instruções para o Claude ao trabalhar neste repositório. Leia também `CONTRIBUTING.md`.

## O projeto

- Complemento independente para **QGIS 4.x / Qt6 / Python 3.12**, inspirado no Vista SAGA/UFRJ,
  **sem código do programa original**. Sete módulos: Assinatura, Monitoria, Avaliação, Análises
  Voronoi, Combinação de Mapas, Conversor de Formatos e Sequenciador de Mapas.
- O autor usa o plugin na **tese de doutorado**. Mudanças em algoritmos são decisões de método:
  exigem teste de regressão, justificativa escrita e, quando envolvem o formato RS2 ou resultados
  comparáveis ao Vista SAGA, validação do autor no **Vista SAGA original**.
- Converse com o autor em **português brasileiro**. Documentação e mensagens de commit também.

## Estrutura

- `geosaga/` — pacote instalável. **Não renomear** o diretório nem os identificadores
  Processing `geosaga:*` (projetos e modelos antigos dependem deles).
- `geosaga/plugin.py` — menu: a tupla `MODULES` é desempacotada **pela posição** em vários
  pontos; não acrescente colunas. Ícones dos módulos ficam em `MODULE_ICONS`
  (`icons/modulos/*.svg`); ícone principal em `icon.png` e `icons/icon_<tamanho>.png`.
- `geosaga/tests/` — suíte histórica (`unittest`, sem PyQGIS); `tests/unit/` (pytest);
  `tests/qgis/` (QGIS real: `smoke_qgis.py`, `gui_monkey.py`); ver `tests/README.md`.
- `scripts/build_release.py` — gera o ZIP instalável em `dist/`, a partir da versão do
  `metadata.txt`; exclui testes, `home_dialog.py` (painel antigo, sem uso) e a maior parte dos `.md`.

## Comandos

```bash
python -m unittest discover -s geosaga/tests -p 'test_*.py'
python -m pytest -q tests/unit
python scripts/build_release.py
```

Os testes com GDAL real precisam de `osgeo` (no contêiner do Claude Code, use `python3.12` após
`apt-get install python3-gdal`). Testes que dependem de rasterio ou Shapely são pulados quando
essas bibliotecas faltam.

## Regras técnicas

- **Exceções GDAL só com escopo local:** decore com `gdal_scope.with_gdal_exceptions`. Nunca chame
  `gdal.UseExceptions()` de forma global: isso altera o GDAL para todo o QGIS e outros complementos.
  Valide entradas antes de importar `osgeo` quando possível.
- **SRC:** nunca deduza EPSG a partir de coordenadas; nunca reprojete implicitamente. O RS2 não
  guarda SRC: ele fica no arquivo lateral `.rs2.json`, e o usuário confirma o SRC na interface.
- **Formato RS2** (especificação empírica em `geosaga/FORMATO_RS2.md`; confirmada contra arquivos
  gravados pelo Vista SAGA original):
  - 11 bytes de prefixo; bordas uint32; linhas e colunas uint16; **quantidade de classes uint16**;
    depois **n pares (código uint16 + nome CP1252 + NUL), inclusive a primeira classe**;
  - códigos únicos, **não necessariamente consecutivos nem iniciados em 0**; o FUNDO pode ter
    código diferente de 0 (na avaliação do Vista SAGA, é o 11). Use `RS2Header.background_code`,
    `legend_codes` e `legend()`; nunca indexe nomes ou cores pela posição;
  - RLE por linha; paleta de 32.769 × 4 bytes indexada pelo código, **logo após a matriz**; podem
    existir bytes residuais após a paleta;
  - com o primeiro código igual a 0, a gravação deve continuar idêntica byte a byte às amostras.
- **Arredondamento:** o Vista SAGA converte médias em classes por **"meio para par"**
  (`round()` do Python/NumPy), não por "meio para cima".
- **Tradução:** textos de interface e mensagens passam por `tr()`; mensagens montadas em tempo de
  execução precisam do modelo correspondente (`{0}`, `{1}`…) em `geosaga/i18n/en.json` **e** em
  `geosaga/i18n/es.json` (o espanhol é completo desde a 1.1.0, e um teste exige os dois catálogos).
  Formatos: `en.json` com recuo de 2 e quebra de linha final, na ordem de inserção; `es.json` com
  recuo de 1, chaves ordenadas e sem quebra de linha final. Relatórios CSV/TXT, sufixos de arquivo
  e o campo `MOTIVO` ficam sempre em português.

## Padrões de interface

- **Traço simples (-), nunca travessão (—)**, em textos de interface, títulos, nomes de camadas e
  relatórios. Exceções: o marcador “—” de nota não definida e as meias-riscas de intervalos
  (0–10, 1985–2024, Mann–Kendall). Um teste confere.
- **Fundo:** toda `QScrollArea` dentro de guia chama `use_tab_background()` (em `ui_shared.py`)
  logo após `setWidget`, para usar o fundo padrão da guia do QGIS. Um teste confere.
- **Rótulos** com maiúscula só na primeira palavra (“Escala das notas”, não “Escala das Notas”).
- **Tabelas:** números alinhados à direita e textos à esquerda (`table_item`, `weight_spin`,
  `score_spin`, `centered_check` em `ui_shared.py`).
- **Resultado (Avaliação, Combinação e Monitoria):** sem caixas “temporário” ou “adicionar ao
  projeto”. Campo “Salvar em” vazio: vetor como camada temporária em memória
  (`materialize_in_memory`), raster em arquivo temporário; preenchido: salvo. Sempre carregado.
  O **Conversor de Formatos mantém** as caixas, o lote vetorial desligado e as opções avançadas
  ocultas, por decisão do autor na 1.2.0 (não reabrir sem pedido).
- **Tabelas de resultado** copiáveis para planilhas com `enable_table_copy` (Ctrl+A/Ctrl+C, decimal
  do idioma); botões de ordem “Mover para cima/baixo”; guias “Raster” e “Vetorial”.
- **Combinação vetorial (1.2.0, decisões de método):** sobreposições internas com largura média
  < 1 cm são toleradas (registradas no resumo); resíduos de cruzamento < 1 cm são incorporados ao
  vizinho de maior fronteira comum. Campos do mapa: `COD_nn`/`LEG_nn`.
- **Voronoi (1.3.0):** guias “Raster” e “Vetorial” (grupos de modelo e dados compartilhados,
  movidos em `_tab_changed`); “Salvar em” no padrão do plugin (vetor temporário em memória via
  `materialize_in_memory`); formatos de `rs2_vector.VECTOR_FORMATS` pelo filtro do “Salvar
  como…”, gravados via `voronoi_output.py`. Vetorial: Simples e Com Massa exatos
  (`save_vector_voronoi`; Com Massa = `mass_voronoi_polygons`, decisão de método do autor na
  1.3.0: discos de Apolônio e bissetrizes em OGR/GEOS, tolerância de 1 cm, desvio máximo 2/3 cm,
  sem viés, disco gerado sobre a extensão inteira para os vizinhos coincidirem). O autor
  retirou “Vetor (poligonização)” e “GeoTIFF + vetor”: não reintroduzir sem pedido.
- **Voronoi (1.4.0, decisões de método do autor):** Com Massa = M/d²; atrito no modelo célula a célula do
  Vista SAGA na guia Raster e, na guia Vetorial, vetor direto pelo modelo contínuo (ver
  `NOTAS_DA_VERSAO_140.md`). **Critério de comparabilidade com o Vista SAGA** (19/11/2026): ≥ 99% das
  células da área de estudo, ≥ 90% das divergências na fronteira, ≤ 1% de diferença de área por região;
  conferir com `scripts/comparar_caso_bacia.py` antes de mudar o atrito. Na bacia real, a guia Raster
  falha no critério 3 no Com Atrito (1,33%, região pequena), declarado sem rever o critério.
- **Mann–Kendall** saiu da Monitoria na 1.2.0 e volta como módulo próprio na 2.0;
  `monitoring_trends.py` e as funções de relatório ficam reservadas.
- **Avaliação:** as três guias têm o mesmo leiaute (projeto, escala, critérios e pesos, classes,
  resultado). A nota “—” bloqueia a execução, e o plugin nunca supõe nota 0 nem exclui classes
  sozinho; pesos novos entram em branco, e a divisão igual só ocorre pelo botão. Campo “Salvar
  em” vazio: vetor em memória, raster em arquivo temporário. Cada execução grava
  `*_pesos_notas.geosaga.json` (formato em `evaluation_config.py`).

## Versões e lançamento

- A versão do `metadata.txt` deve ser **igual à primeira seção** (`## <versão>`) do
  `geosaga/CHANGELOG.md` (os testes conferem). Por convenção, o `changelog=` do `metadata.txt`
  também começa pela versão atual.
- Toda versão estável tem `geosaga/NOTAS_DA_VERSAO_<versão sem pontos>.md` (incluída no ZIP).
- Builds de teste (`-devN`) mudam a versão **só dentro do ZIP**, nunca no repositório.
- Não enviar ao catálogo oficial do QGIS sem pedido explícito do autor.

## Fluxo de trabalho

1. Cada versão numa **branch nova** a partir da `main`; as melhorias da mesma versão acumulam-se
   nessa branch e num único PR, com ZIPs `-devN` a cada lote, até o fechamento.
2. Rodar as suítes; gerar um **ZIP de teste** para o autor validar no QGIS (e no Vista SAGA, quando
   couber). Não declarar algo homologado sem esse teste.
3. Abrir o **pull request**; **o merge é feito pelo autor**, depois da validação, ou pelo Claude
   quando o autor pedir explicitamente (via API do GitHub, `merge_method=merge`, título
   `Merge PR #N: …`). PRs que dependem de outros entram na ordem das dependências.
4. Arquivos de dados do autor (RS2, Shapefiles, GeoTIFF) **não vão para o repositório**, que é
   público: recrie a estrutura com dados sintéticos nos testes.

## Pendências registradas

- **Contexto entre sessões:** leia `docs/CONTEXTO_SESSOES.md` no início de cada sessão (o histórico até a
  1.4.2 está em `docs/CONTEXTO_SESSOES_HISTORICO_ate_1.4.2.md`) e
  atualize-o **a cada ação finalizada** (decisões, achados, pendências), com commit + push imediato
  e envio do arquivo ao autor (pedido do autor em 18/11/2026, após sessões bloqueadas sem registro).
  Mantenha a seção "Retomada rápida" sempre em dia. A versão válida é a do repositório.

- **Tags (adiadas pelo autor em 16/11/2026):** commits já conferidos (último merge de cada versão
  na `main`): v1.0.5 `0063fe2`, v1.0.6 `27b06e5`, v1.0.8 `760620e`, v1.0.9 `1ee4d8c`, v1.1.0
  `bcb08fb` (PR #9: README do ZIP já na 1.1.0), v1.2.0 `92d35ea`, v1.2.1 `4b165de`. **O proxy das
  sessões do Claude recusa criar tags** (por `git push` e pela API REST): o autor cria pelo GitHub
  Codespaces, com o comando registrado na sessão de 16/11/2026. Releases também ficam com o autor.
- **Na versão final:** Releases no GitHub e limpeza das branches já incorporadas; conferir antes
  `fix/testes-desatualizados` e `docs/logo-readme`, que têm 1 commit fora da `main`.
- **QRibbonSkin:** erro ao descarregar o plugin (barra de ferramentas apagada); tratar só quando o
  trabalho for no próprio QRibbonSkin.
