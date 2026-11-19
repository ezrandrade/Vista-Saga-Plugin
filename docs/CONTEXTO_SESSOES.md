# Contexto entre sessões

Registro das decisões, achados e pendências que ficam fora do código, para que uma nova sessão do Claude
(ou o próprio autor) retome o trabalho sem depender do histórico de conversas. **Atualizar a cada ação
finalizada, com commit + push imediato e envio do arquivo ao autor** (`CLAUDE.md`). As entradas mais
recentes ficam no topo. **A versão válida é a do repositório.**

Histórico completo até a 1.4.2 (validação do Voronoi contra o Vista SAGA, decisões de método, testes):
`docs/CONTEXTO_SESSOES_HISTORICO_ate_1.4.2.md`.

---

## >>> RETOMADA RÁPIDA (criada em 19/11/2026, fim da sessão 4; próxima: versão 1.5.0) <<<

### Onde está o trabalho

| Versão | Situação | Branch / PR | Commit de merge na `main` |
|---|---|---|---|
| 1.4.0 | fechada, homologada, **mesclada** | `feat/voronoi-atrito-fiel` / [#13](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/13) | `49056f9` |
| 1.4.1 | fechada, homologada, **mesclada** | `feat/interface-padrao` / [#14](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/14) | `5c6c876` |
| 1.4.2 | fechada, homologada, **sem merge** | `fix/sequenciador-guias` / [#15](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/15) (base `main`) | - |

**Pendências do autor (o proxy das sessões recusa criar tags):**
1. Merge do PR #15 (ou pedir ao Claude, via API, `merge_method=merge`, título `Merge PR #15: …`).
2. Tags: `v1.3.0` = `87406de`, `v1.4.0` = `49056f9`, `v1.4.1` = `5c6c876`, `v1.4.2` = merge do #15.
   Comandos (Codespaces): `git fetch origin`; `git tag -a vX.Y.Z <commit> -m "Vista Saga Plugin X.Y.Z"`;
   `git push origin vX.Y.Z`. Tags antigas (v1.0.5 a v1.2.1): commits no `CLAUDE.md`.

### Próxima sessão: versão 1.5.0 (pedido do autor, 19/11/2026)

Começar com uma **branch nova a partir da `main`** (depois do merge do #15) e um único PR, com ZIPs
`-devN` a cada lote (fluxo do `CLAUDE.md`). Escopo combinado:

1. **Revisão do módulo Assinatura** (`signature_dialog.py`, motor, Processing `geosaga:assinatura`,
   relatórios). Escopo detalhado a definir com o autor no início da sessão (sugestão: levantar primeiro o
   que o módulo faz hoje, as diferenças para o Vista SAGA e os problemas conhecidos, e só então propor).
2. **Dicas (tooltips) em todos os módulos:** em todos os campos e botões, a explicação do que são e do que
   fazem, nas caixas amarelas do QGIS (`setToolTip`), como as dicas das guias Vetorial e Misto do
   Sequenciador na 1.4.2. Textos via `tr()`, com modelos em `en.json` e `es.json` (regra do `CLAUDE.md`).
   Sugestão de método: inventário dos widgets sem dica por módulo, textos curtos e padronizados, teste
   que confira a cobertura.

### Questões em aberto (sem decisão; não reabrir sem pedido)

- **Sequenciador, espaço livre na guia Raster:** o autor achou que o espaçamento ficou como antes na 1.4.2;
  a medição em QGIS 3.34 deu cerca de 140 px livres (1.4.0: cerca de 210). Deixado pelo autor "para outro
  momento".
- **Sequenciador, animação em .jxl:** discussão encerrada pelo autor até a versão 2.0 (não há codificador de
  JPEG XL animado no QGIS; opções levantadas: codificador próprio, programa externo, quadros avulsos).
- Pendências antigas, sem urgência: leitura/gravação do arquivo de pontos do Vista SAGA no plugin; critério
  escrito de "plugin finalizado"; Releases no GitHub e limpeza de branches na versão final (`CLAUDE.md`).

### Decisões do autor em vigor (não reabrir sem pedido)

- **Voronoi (1.4.0):** Com Massa = M/d²; atrito célula a célula do Vista SAGA na guia Raster e modelo
  contínuo (vetor direto) na guia Vetorial; atrito vetorial só pela coluna; tolerância 0,5 m e espaçamento
  automático; nota 0 recusada; área sem polígono, coluna vazia e NoData atravessáveis com nota 1, sem
  resultado; sem legado 1.3; Raster recorta pela área de estudo; partes < 25 m² só informadas.
- **Critério de comparabilidade com o Vista SAGA** (19/11/2026): ≥ 99% das células da área de estudo,
  ≥ 90% das divergências na fronteira, ≤ 1% de diferença de área por região; conferir com
  `scripts/comparar_caso_bacia.py`. Na bacia real (10 m), a guia Raster falha no critério 3 no Com Atrito
  (1,33%, região pequena), declarado sem rever o critério; a guia Vetorial falha no 3 (e no 2 com massa).
- **Interface do Voronoi sem menções ao Vista SAGA** (relatórios, notas e documentação mantêm a validação).
- **Rodapé padrão (1.4.1):** [Executar] [Fechar] em todos os módulos, [Validar] só na Avaliação, fora das
  guias; sem linha de status, barra ou Cancelar fixos (janela de progresso só durante a execução,
  `TaskProgressWindow`; desfecho na barra do QGIS, `report_outcome`); títulos "Vista Saga Plugin - <módulo>",
  também nas janelas de progresso.
- **Sequenciador (1.4.2):** as três guias com a mesma altura, compacta; textos explicativos como dicas.

### Validação do Voronoi contra o Vista SAGA original (resumo; detalhes no histórico)

- Caso sintético (17/11, 80 × 60 células): Simples e Com Massa 100%; atrito 99,67% / 99,69% (Raster).
- Bacia real (19/11; Vista SAGA em Windows 7 32 bits no VirtualBox): Simples e Com Massa 100% em 5 m
  (2.191.850 células); com atrito, só a grade de 10 m funcionou no Vista SAGA (5 m e 20 m saíram vazias ou
  incompletas, sem aviso). Raster 99,46% / 99,42%; Vetorial 99,29% / 99,06% (dentro da bacia).
- Dados do autor (RS2, GPKG, pontos, saídas): só na sessão, nunca no repositório.

### Como trabalhar no contêiner

- `apt-get update` e depois `apt-get install -y python3-gdal gdal-bin python3-pytest python3-shapely
  python3-scipy`; usar **python3.12**. Suítes: `python3.12 -m unittest discover -s geosaga/tests -p
  'test_*.py'` (477, 3 pulados) e `python3.12 -m pytest -q tests/unit` (42).
- Janelas reais: `apt-get install -y --no-install-recommends python3-qgis qgis-providers` (QGIS 3.34, não é
  o alvo) e rodar com `python3.12` e `QT_QPA_PLATFORM=offscreen` (o `python3` do sistema não carrega o
  QGIS). Capturas com `widget.grab()`; a interface sai no idioma do QGIS de teste (inglês).
- ZIP: `python3.12 scripts/build_release.py` (`dist/` não é versionado); ZIPs `-devN` trocam a versão só
  dentro do ZIP.
- GitHub: só a API REST (`gh api repos/ezrandrade/Vista-Saga-Plugin/...`); GraphQL indisponível nas sessões.

---

## 19/11/2026 (sessão 4) — resumo do encerramento

- Validação do atrito na bacia real contra o Vista SAGA; critério de comparabilidade aceito e falha
  declarada; 1.4.0 fechada e mesclada.
- 1.4.1 (rodapé padrão em todos os módulos; títulos; Sequenciador) fechada, homologada e mesclada.
- 1.4.2 (Sequenciador com guias da mesma altura) fechada e homologada; PR #15 aberto.
- Contexto reiniciado neste arquivo; histórico movido para `docs/CONTEXTO_SESSOES_HISTORICO_ate_1.4.2.md`.
- Próximo: pausa; a sessão seguinte começa a 1.5.0 (Assinatura + dicas em todos os módulos).
