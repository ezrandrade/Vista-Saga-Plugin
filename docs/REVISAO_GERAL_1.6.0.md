# Revisão geral do Vista Saga Plugin — versão 1.6.0

Revisão pedida pelo autor (20/11/2026), depois do fechamento da 1.6.0: tudo o que foi feito nos sete módulos,
pendências e registros para versões futuras. Fontes: `docs/CONTEXTO_SESSOES.md` (e o histórico até a 1.4.2),
`CLAUDE.md`, `geosaga/CHANGELOG.md`, notas das versões, código e testes.

## 1. Situação das versões

| Versão | Conteúdo principal | Situação |
|---|---|---|
| 1.4.0 | Voronoi fiel ao Vista SAGA (M/d²; atrito pelo custo do Vista SAGA; atrito vetorial) | mesclada (`49056f9`) |
| 1.4.1 | Rodapé padrão [Executar] [Fechar] em todos os módulos | mesclada (`5c6c876`) |
| 1.4.2 | Sequenciador com guias da mesma altura | mesclada (`0d58783`) |
| 1.5.0 | Assinatura no modelo do Vista SAGA; Conversor (paleta, `.qml`, temporários do Vetor → RS2); nomes dos resultados | homologada, **PR #16 sem merge** |
| 1.6.0 | Dicas em todos os módulos | homologada, **PR a abrir** depois do merge do #16 |

### Pendências administrativas (autor)

1. **Merge do PR #16** (1.5.0); depois, PR da 1.6.0 (`feat/dicas-todos-modulos`, base `main`). O Claude pode fazer
   o merge pela API se o autor pedir explicitamente.
2. **Tags** (o proxy das sessões recusa criar tags): `v1.3.0` = `87406de`, `v1.4.0` = `49056f9`,
   `v1.4.1` = `5c6c876`, `v1.4.2` = `0d58783`, `v1.5.0` e `v1.6.0` = commits de merge; antigas (v1.0.5 a v1.2.1) no
   `CLAUDE.md`.
3. **Catálogo oficial do QGIS** ainda com a 1.0.3; envio só com pedido explícito do autor.
4. **Na versão final:** Releases no GitHub e limpeza das branches incorporadas (conferir antes
   `fix/testes-desatualizados` e `docs/logo-readme`, com 1 commit fora da `main`).

## 2. Estado de cada módulo

| Módulo | Estado | Validação | Observações |
|---|---|---|---|
| **Assinatura** | refeito na 1.5.0 | contra o Vista SAGA em 3 casos (mapa inteiro 100%; parciais: só células ligadas pela diagonal) | sem projeto (decisão do autor); Processing antigo obsoleto e oculto |
| **Monitoria** | estável (1.2.0) | testes de motor; homologada pelo autor | Mann–Kendall reservado para módulo próprio na 2.0 (`monitoring_trends.py`) |
| **Avaliação** | estável (1.1.0) | testes de motor e de interface; homologada | três guias com o mesmo leiaute; projeto `*.geosaga.json` |
| **Análises Voronoi** | refeito na 1.4.0 | contra o Vista SAGA (Simples e Com Massa 100%; atrito 99,4–99,7%) | guia Raster falha no critério 3 de comparabilidade no Com Atrito (1,33%, região pequena), declarado |
| **Combinação de Mapas** | estável (1.2.0) | testes de motor; homologada | tolerância de lascas de 1 cm (também adotada na Assinatura vetorial) |
| **Conversor de Formatos** | estável; correções na 1.5.0 | formato RS2 conferido contra arquivos do Vista SAGA | paleta e `.qml` nos GeoTIFF de classes; mantém caixas "temporário/adicionar" (decisão de 1.2.0) |
| **Sequenciador de Mapas** | estável (1.4.2) | homologado | GIF e PNG; JPEG XL animado adiado para a 2.0 |

Todos os módulos: interface em português, inglês e espanhol; dicas em todos os botões, campos, caixas de marcar e
listas; resultado temporário com o nome "Módulo - operação" e camada salva com o nome do arquivo.

## 3. Correções feitas nesta revisão (só texto, sem mudança de cálculo)

- **README do ZIP** (`geosaga/README.md`, lido por quem instala): dizia "versão 1.3.0", descrevia o atrito do
  Voronoi como "custo experimental 1 + atrito" (modelo trocado na 1.4.0) e afirmava que a equivalência com o Vista
  SAGA "não foi demonstrada". Atualizado para a 1.6.0, com as validações do Voronoi e da Assinatura.
- **README do repositório:** mesma correção; links das notas da 1.4.0 a 1.6.0.
- **"Sobre" do `metadata.txt`** (exibido no gerenciador de complementos do QGIS): trocada a frase "Numerical
  equivalence with the original Vista SAGA/UFRJ has not been established" pelas validações.

## 4. Questões que dependem do autor

1. **Voronoi com atrito vetorial converte os pontos para o SRC dos polígonos de atrito** (decisão da 1.4.0,
   registrada como "sem reprojeção" porque os polígonos definem o SRC da análise). Na Assinatura (1.5.0) a regra é
   recusar SRC diferentes. Uniformizar (recusar no Voronoi também) ou manter?
2. **Algoritmos Processing legados `geosaga:avaliacao` e `geosaga:monitoria`** continuam visíveis na Caixa de
   Ferramentas, com interface antiga (Avaliação por JSON). Ocultar como obsoletos, como o da Assinatura, ou manter?
3. **Inglês:** nomes das modalidades do Voronoi com maiúsculas irregulares ("With mass", "With Friction",
   "With Mass and Friction"). Uniformizar?
4. **Textos explicativos fixos** ainda ocupam espaço em vários módulos (Avaliação, Monitoria, Combinação,
   Conversor). No Sequenciador (1.4.2) eles viraram dicas. Fazer o mesmo nos outros, agora que todos têm dicas?
5. **Windows:** os nomes temporários passaram a ter acentos, espaços e parênteses (1.5.0). Funcionou no teste do
   autor; vale observar em outras máquinas.

## 5. Registros para versões futuras (sem decisão de implementar)

- **2.0:** Mann–Kendall como módulo próprio; animação em JPEG XL no Sequenciador.
- **Conversor:** opção de alinhar o Vetor → GeoTIFF à grade de um raster de referência, como já faz o Vetor → RS2
  (TIF e RS2 do mesmo vetor ficariam na mesma grade).
- **Assinatura:** coluna extra de percentual só entre classes reais (sem FUNDO/NoData); seleção por clique numa
  região raster (como o balde do Vista SAGA), opcional.
- **Vista SAGA:** leitura e gravação do arquivo de pontos do Vista SAGA no plugin.
- **Sequenciador:** espaço livre na guia Raster (cerca de 140 px; adiado pelo autor).
- **Critério escrito de "plugin finalizado"** (pendência antiga).
- **QRibbonSkin:** erro ao descarregar o plugin (tratar quando o trabalho for no QRibbonSkin).
- **Limpeza do repositório:** 58 arquivos `.md` históricos em `geosaga/` (fora do ZIP, salvo notas da versão,
  README, CHANGELOG e NOTICE); `geosaga/PLANO_DE_EVOLUCAO.md` (parado na 0.x), `docs/TESTES_E_HOMOLOGACAO.md`
  (1.0.0) e `tests/README.md` (contagens da 1.0.5) desatualizados; `home_dialog.py` (painel antigo, só para
  testes históricos).
- **Testes em QGIS real:** `tests/qgis/smoke_qgis.py` e `gui_monkey.py` só carregam o plugin no QGIS 4 (o
  contêiner das sessões tem o 3.34); rodar no QGIS 4 antes de cada versão final.

## 6. Qualidade e testes (1.6.0)

- `python3.12 -m unittest discover -s geosaga/tests -p 'test_*.py'`: 503 testes (3 pulados).
- `python3.12 -m pytest -q tests/unit`: 42 testes (inclui catálogos de tradução completos em inglês e espanhol).
- `tests/qgis/tooltip_inventory.py`: nenhum widget sem dica nos sete módulos (QGIS real).
- `geosaga/tests/integration_signature_150_qgis.py`: Assinatura em QGIS real (Raster e Vetorial).
- Validações reproduzíveis contra o Vista SAGA: `scripts/comparar_caso_bacia.py` (Voronoi) e
  `scripts/comparar_assinatura_vista_saga.py` (Assinatura); dados do autor nunca no repositório.
