# CLAUDE.md — Vista Saga Plugin

Instruções para o Claude ao trabalhar neste repositório. Leia também `CONTRIBUTING.md`.

## O projeto

- Complemento independente para **QGIS 4.x / Qt6 / Python 3.12**, inspirado no Vista SAGA/UFRJ,
  **sem código do programa original**. Sete módulos: Assinatura, Monitoria, Avaliação, Análises
  Voronoi, Combinação de Mapas, Conversão de Formatos e Sequenciador de Mapas.
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
  execução precisam do modelo correspondente (`{0}`, `{1}`…) em `geosaga/i18n/en.json`.

## Versões e lançamento

- A versão do `metadata.txt` deve ser **igual à primeira seção** (`## <versão>`) do
  `geosaga/CHANGELOG.md` (os testes conferem). Por convenção, o `changelog=` do `metadata.txt`
  também começa pela versão atual.
- Toda versão estável tem `geosaga/NOTAS_DA_VERSAO_<versão sem pontos>.md` (incluída no ZIP).
- Builds de teste (`-devN`) mudam a versão **só dentro do ZIP**, nunca no repositório.
- Não enviar ao catálogo oficial do QGIS sem pedido explícito do autor.

## Fluxo de trabalho

1. Cada melhoria numa **branch nova** a partir da `main`.
2. Rodar as suítes; gerar um **ZIP de teste** para o autor validar no QGIS (e no Vista SAGA, quando
   couber). Não declarar algo homologado sem esse teste.
3. Abrir o **pull request**; **o merge é feito pelo autor**, depois da validação.
4. Arquivos de dados do autor (RS2, Shapefiles, GeoTIFF) **não vão para o repositório**, que é
   público: recrie a estrutura com dados sintéticos nos testes.
