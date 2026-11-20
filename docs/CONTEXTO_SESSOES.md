# Contexto entre sessões

Registro das decisões, achados e pendências que ficam fora do código, para que uma nova sessão do Claude
(ou o próprio autor) retome o trabalho sem depender do histórico de conversas. **Atualizar a cada ação
finalizada, com commit + push imediato e envio do arquivo ao autor** (`CLAUDE.md`). As entradas mais
recentes ficam no topo. **A versão válida é a do repositório.**

Histórico completo até a 1.4.2 (validação do Voronoi contra o Vista SAGA, decisões de método, testes):
`docs/CONTEXTO_SESSOES_HISTORICO_ate_1.4.2.md`.

---

## >>> RETOMADA RÁPIDA (atualizada em 20/11/2026: 1.6.0 fechada, revisão geral feita, manual DOCX em revisão pelo autor) <<<

### Teste do autor com o dev2 (20/11/2026, manhã; guia Raster; vetorial a seguir)

- O autor rodou o **plugin nos GeoTIFF** (`Bairros_10m.tif`, `Escolaridade_10m.tif`, `UsoSolo_10m.tif`) e o
  **Vista SAGA nos RS2**, em dois casos: bairro Barro Duro e mapa inteiro. **Os TIF não são os mesmos dados
  dos RS2:** grade 495 × 1107 contra 496 × 1108, origem deslocada cerca de 8 m e outra numeração de classes
  (Barro Duro = 7 no TIF, 2 no RS2); provavelmente rasterizados de vetores. Comparação TIF × RS2 não vale.
- O Claude rodou o **plugin nos mesmos RS2** (`scripts/comparar_assinatura_vista_saga.py`): mapa inteiro
  **31/31 = 100%**; Barro Duro 27/31, e as 4 diferenças são **4 células do Barro Duro ligadas só pela
  diagonal** (linhas 571-573, colunas 435-436), excluídas pelo balde do Vista SAGA (15.779 × 15.783).
  Mesma causa do Poço; diferença aceita. Segundo caso de referência confirmado.
- Nos TIF do ZIP, o plugin mostrou "Classe N": os arquivos vieram **sem o `.aux.xml`**, onde o GeoTIFF
  guarda os nomes das classes (o `UsoSolo_10m.tif` mostrou nomes, provavelmente de um `.rs2.json` ao lado).
- **dev3 (20/11/2026, pedido do autor): nomes das classes pelo estilo da camada no QGIS** (simbologia
  Paletado/Valores únicos), quando o mapa vem do projeto; prevalecem sobre a legenda do arquivo; rótulos
  iguais ao código são ignorados. Também força a leitura do `.aux.xml` (o GDAL 3.8 só o carrega depois de
  outra consulta ao arquivo; o motor já fazia essa consulta antes, agora explícita). Testes novos (motor e
  integração em QGIS real). Suítes: 507 (3 pulados) e 42. ZIP `Vista_Saga_Plugin_QGIS4_v1.5.0-dev3.zip`.
  Renumeração: o lote "projeto + legado + limpeza do motor antigo" passa a ser o **dev4**.
- **Observação do autor sobre o Conversor:** no Vetor → GeoTIFF salvo pelo Conversor (com `.aux.xml` ao
  lado), o QGIS não mostrava os nomes das classes. **Causa:** sem o campo `COR_HEX`, o Conversor não gravava
  paleta, e o QGIS abria o mapa em tons de cinza (os nomes ficavam só no `.aux.xml`). No contêiner, salvo e
  temporário abriam iguais (cinza); a diferença que o autor viu no temporário não foi reproduzida.
  **Correção (dev4, 20/11/2026):** (1) Vetor → GeoTIFF grava sempre a paleta, com as cores padrão do
  Vetor → RS2 quando falta `COR_HEX`; (2) Vetor → GeoTIFF e RS2 → GeoTIFF gravam um estilo `<nome>.qml`
  (Paletado, só as classes reais, sem o NoData), que o QGIS carrega sozinho: sem ele, a paleta de 8 bits
  lista 256 entradas na legenda ("4", "5"...). O `.qml` entra na família de auxiliares publicada junto do
  TIF (`rs2_outputs.output_family`). Teste `test_150_vetor_geotiff_paleta.py`; conferido no QGIS 3.34
  (3 classes no vetor; 20 bairros no RS2). Suítes: 510 (3 pulados) e 42. ZIP
  `Vista_Saga_Plugin_QGIS4_v1.5.0-dev4.zip`. Renumeração: projeto + legado + limpeza passa a ser o **dev5**.

### Teste do autor com o dev4 (20/11/2026; Conversor e guia Raster)

- Mapas: Bairros, Escolaridade e **Pedologia** (novo), em RS2 (Vista SAGA e plugin) e em GeoTIFF gerado pelo
  Vetor → GeoTIFF do plugin; casos Barro Duro e mapa inteiro.
- **Plugin × Vista SAGA nos RS2:** mapa inteiro **32/32 = 100%**; Barro Duro 28/32, só as 4 células
  diagonais já conhecidas. **O CSV do plugin no QGIS 4 do autor é idêntico ao do motor no contêiner** (32
  linhas). Nomes das classes e o FUNDO aparecem nos relatórios dos TIF (correção do dev4 confirmada).
- TIF × RS2 diferem por construção: o Vetor → GeoTIFF usa a extensão do vetor (495 × 1107, origem não
  inteira, numeração pela ordem do vetor). Ex.: Barro Duro 15.756 células no TIF, 15.783 no RS2. Ideia para
  o futuro (sem decisão): opção de alinhar o Vetor → GeoTIFF à grade de um raster de referência, como o
  Vetor → RS2 já faz.
- **Defeito achado no ZIP do autor:** pastas `.vista_vector_rs2_*` com `cobertura.tif` deixadas na pasta de
  saída pelo Vetor → RS2. Causa: a variável do laço que prepara as grades temporárias mantinha o
  `cobertura.tif` aberto; no Windows a limpeza falhava em silêncio (`ignore_cleanup_errors`). **Corrigido
  (dev5)** com `raster = None` após o laço; teste estrutural `test_150_vetor_rs2_temporarios.py` (falha sem
  a correção). As pastas que já existem precisam ser apagadas à mão. Suítes: 511 (3 pulados) e 42.

### Teste do autor com o dev5 (20/11/2026)

- Vetor → RS2 sem pastas ocultas: correção confirmada pelo autor.
- **Guia Vetorial: o autor não conseguiu selecionar uma feição** (só havia "Selecionar todas") e, ao
  executar, recebeu "Selecione pelo menos uma feição do mapa de referência". Falha de projeto da janela: a
  instrução de usar as ferramentas do QGIS estava só na dica, e a ferramenta de seleção do QGIS age sobre a
  **camada ativa**, que podia não ser a referência.
- **Correção (dev6):** texto visível no grupo "2. Seleção na referência"; botões **"Selecionar no mapa"**
  (ativa a camada de referência com `iface.setActiveLayer` e liga `iface.actionSelect()`), "Selecionar
  todas" e **"Desselecionar todas"**; mensagem de erro que explica o que fazer quando nada está
  selecionado. Integração em QGIS real com interface simulada. Suítes: 511 (3 pulados) e 42. ZIP
  `Vista_Saga_Plugin_QGIS4_v1.5.0-dev6.zip`. O lote projeto + legado + limpeza passa a ser o **dev7**.

### Teste do autor com o dev6 (20/11/2026; guia Vetorial)

- Seleção funcionou (Barro Duro e os 20 bairros). Mapas vetoriais: `Bairros_Reginaldo`, `Escolaridade_31985`,
  `Pedologia_31985` (EPSG:31985). Sem relatório do Vista SAGA (ele não assina vetor); comparação com o
  raster do plugin no Barro Duro: maior diferença de % Área asn. = 0,09 ponto (ex.: Neossolos Flúvicos
  5,27% no vetor × 5,36% no raster; Barro Duro 157,60 ha × 157,83 ha).
- **Corrigido (sem ZIP ainda):** nome repetido quando o código da classe é texto ("Barro Duro - Barro Duro");
  agora "código - nome" só quando são diferentes (`ClassRow.display`). Teste novo; suítes 512 (3 pulados) e 42.
- Resíduos geométricos minúsculos entre polígonos vizinhos geravam linhas e avisos de "0,0000 ha".
  **Decisão do autor (20/11/2026, opção b): regra da Combinação vetorial (1.2.0)** — pedaços de
  sobreposição entre classes e de fresta sem polígono com largura média < 1 cm (2 × área ÷ perímetro;
  `combination_core.SLIVER_WIDTH_M`, `mean_width`) não viram "Sobreposição excluída" nem "Sem classe" nem
  aviso; ficam no resumo do TXT ("Tolerância de lascas"). A lasca de sobreposição fica nas duas classes
  (área duplicada informada). Lascas não interrompem o modo estrito. "Sem classe" passa a ser calculado
  geometricamente (limite menos a união dos polígonos do mapa, sem as frestas toleradas). **dev7**:
  `SignatureResult.notes`; testes de lasca e fresta abaixo e acima de 1 cm. Suítes: 514 (3 pulados) e 42.
  ZIP `Vista_Saga_Plugin_QGIS4_v1.5.0-dev7.zip`. O lote projeto + legado + limpeza passa a ser o **dev8**.

### dev8 (20/11/2026)

- **Decisão do autor: sem Novo/Abrir/Salvar projeto na Assinatura** (item retirado do escopo; a proposta
  previa replicar a Avaliação).
- Botão **"Remover todas"** no grupo "1. Mapas - o primeiro é a referência" (pedido do autor).
- Algoritmo Processing `geosaga:assinatura` **obsoleto e oculto** (`flags()` com
  `Qgis.ProcessingAlgorithmFlag.Deprecated`, com recuo para `FlagDeprecated` antes do QGIS 3.36);
  conferido no QGIS 3.34: oculto na Caixa de Ferramentas e no Modelador; identificador preservado.
- **Motor antigo retirado:** `signature_engine.py`, `signature_core.py` e seus testes (`test_signature_core`,
  `test_signature_overlap`, `integration_signature_qgis`, `integration_signature_overlap_qgis`);
  `tests/qgis/smoke_qgis.py` passa a usar o motor novo; verificações de menu e Processing movidas para
  `test_150_assinatura_janela.py`. Suítes: 500 (3 pulados) e 42. ZIP `Vista_Saga_Plugin_QGIS4_v1.5.0-dev8.zip`.

### dev9 (20/11/2026): nomes dos resultados em todos os módulos

- **Decisão do autor:** em **todos os módulos**, o resultado temporário (arquivo e camada carregada) se chama
  **"Módulo - operação"**, e o resultado salvo é carregado com o **nome do arquivo**. Implementação:
  `ui_shared.result_name(módulo, operação)` e `ui_shared.layer_name(caminho)`; `temporary_destination` passa a
  manter acentos, espaços, hífens e parênteses (até 80 caracteres); a camada recebe sempre o nome do arquivo,
  e como o temporário já tem o nome da operação, a regra é uma só. Nomes: "Avaliação - Raster",
  "Avaliação - Vetorial (Atributos)", "Avaliação - Vetorial (Sobreposição)", "Monitoria - Raster",
  "Monitoria - Vetorial", "Análises Voronoi - Simples/Com Massa/Com Atrito/Com Massa e Atrito"
  (`VORONOI_MODES`), "Combinação de Mapas - Raster/Vetorial", "Conversor de Formatos - RS2 para GeoTIFF"
  etc. (`CONVERSION_NAMES`; pasta de lote "Conversor de Formatos - Lote"), "Assinatura - Raster/Vetorial"
  (CSV e TXT). Retirados os nomes fixos ("Combinação de Mapas", "Análises Voronoi", "Vista Saga -
  Avaliação", "Monitoria vetorial") e as constantes `RESULT_NAME`. Conferido no QGIS 3.34: temporário
  "Avaliação - Vetorial (Atributos).gpkg" carregado com esse nome. Teste `test_150_nomes_resultados.py`;
  `test_130_voronoi_vector_output` atualizado. Suítes: 503 (3 pulados) e 42. ZIP
  `Vista_Saga_Plugin_QGIS4_v1.5.0-dev9.zip`. Ponto a conferir no Windows: nomes com acento na pasta
  temporária.

### Homologação e fechamento da Assinatura (20/11/2026)

- **Autor testou o dev9: "está tudo certo"** — Assinatura (Raster e Vetorial), correções do Conversor e nomes
  dos resultados **homologados**.
- Fechamento da parte Assinatura: `metadata.txt` 1.5.0 (com `changelog=` em inglês), seção 1.5.0 no
  `CHANGELOG.md` (marcada "em andamento: dicas em todos os módulos"), `NOTAS_DA_VERSAO_150.md` e regras no
  `CLAUDE.md`. ZIPs seguintes da versão: `-dev10` em diante (só dentro do ZIP).
- **Próximo: item 2 da 1.5.0, dicas (tooltips) em todos os módulos.** Método proposto: inventário dos
  widgets sem dica por módulo, textos curtos e padronizados via `tr()` (en/es), teste que confira a
  cobertura (como `test_150_assinatura_janela.test_botoes_e_campos_com_dica`). A Assinatura já tem.

### 1.5.0 fechada; dicas viram a 1.6.0 (20/11/2026)

- **Decisão do autor:** registrar as dicas como **versão 1.6.0**; a 1.5.0 fecha com Assinatura, Conversor e
  nomes dos resultados (CHANGELOG sem "em andamento"; notas como versão estável). PR #16 aguarda o merge do
  autor; tag `v1.5.0` = commit de merge do #16.
- **1.6.0 (dicas):** branch `feat/dicas-todos-modulos`, criada a partir da `feat/assinatura-e-dicas` (o #16
  ainda não foi mesclado); o PR da 1.6.0 abre com base na `main` depois do merge do #16.
- **Escopo das dicas (decisão do autor):** só **botões, campos, caixas de marcar e listas** (sem cabeçalhos
  de tabela nem abas). **Começar pela Avaliação.** Lotes de 2-3 módulos, um ZIP por lote.

### 1.6.0-dev1 (20/11/2026): dicas da Avaliação

- Ferramenta `tests/qgis/tooltip_inventory.py`: abre o módulo em QGIS real (todas as guias, inclusive as
  montadas sob demanda), lista botões, campos, caixas de marcar e listas sem dica e falha se houver algum
  (ignora peças internas do Qt: botão de canto da tabela, botão de limpar do campo, setas das abas). Sem
  argumentos, confere os módulos concluídos (`DONE`: Assinatura e Avaliação).
- **Avaliação: 44 widgets sem dica → 0**, nas três guias. Dicas na seção "3. Resultado" (`OutputSection`) e
  nos campos de peso e nota das tabelas (`weight_spin`, `score_spin`) ficam no `ui_shared.py` e valem para
  todos os módulos que os usam. Padrão dos textos: frase curta no indicativo ("Acrescenta…", "Retira…").
- **Falha antiga corrigida:** dicas passadas à função `button()` nunca eram traduzidas (ex.: "Atualiza a lista
  de camadas raster…", "Divide 100% igualmente…"); `tests/unit/test_i18n.py` passou a conferir o texto e a
  dica de `button()`. Dica da nota sem o caractere "—" (o teste de travessão barrou).
- Testes antigos que procuravam `button('Fechar', self.close)` etc. ajustados para o começo da chamada.
  Suítes: 503 (3 pulados) e 42. ZIP `Vista_Saga_Plugin_QGIS4_v1.6.0-dev1.zip` (versão só no ZIP; o
  `metadata.txt` fica 1.5.0 até o fechamento da 1.6.0).

### 1.6.0-dev2 (20/11/2026): dicas da Monitoria e das Análises Voronoi

- Autor aprovou os textos da Avaliação (dev1).
- **Monitoria: 32 widgets sem dica → 0** (guias Raster e Vetorial). **Voronoi: 25 → 0** (inclusive a janela
  das superfícies de atrito integradas). Rótulos "X mínimo:", "Y mínimo:", "X máximo:", "Y máximo:" do
  Voronoi não eram traduzidos (sem `tr()`); corrigido.
- `tests/qgis/tooltip_inventory.py`: mostra o atributo e o rótulo do formulário de cada widget sem dica;
  opção `--lista arquivo.md` exporta, em português, todas as dicas para revisão; `DONE` com Assinatura,
  Avaliação, Monitoria e Voronoi. Suítes: 503 (3 pulados) e 42. ZIP `Vista_Saga_Plugin_QGIS4_v1.6.0-dev2.zip`.
- Restam: Combinação de Mapas, Conversor de Formatos e Sequenciador de Mapas (próximo lote).

### 1.6.0-dev3 (20/11/2026): dicas da Combinação, do Conversor e do Sequenciador

- Autor aprovou os textos da Monitoria e do Voronoi (dev2).
- **Combinação: 24 → 0; Conversor de Formatos: 26 → 0; Sequenciador: 33 → 0.** Com isso, **os sete módulos
  têm dica em todos os botões, campos, caixas de marcar e listas** (`tests/qgis/tooltip_inventory.py` sem
  argumentos confere os sete; o seletor de SRC do QGIS conta como peça interna, e o próprio seletor tem dica).
- Suítes: 503 (3 pulados) e 42. ZIP `Vista_Saga_Plugin_QGIS4_v1.6.0-dev3.zip`.
- Próximo: aprovação do autor e fechamento da 1.6.0 (CHANGELOG, `metadata.txt` 1.6.0, `NOTAS_DA_VERSAO_160.md`).

### 1.6.0 fechada (20/11/2026)

- Autor aprovou os textos do dev3 e a explicação da leitura dos relatórios da Assinatura. **1.6.0 fechada e
  homologada:** CHANGELOG, `metadata.txt` 1.6.0 (changelog em inglês), `NOTAS_DA_VERSAO_160.md`. ZIP
  `Vista_Saga_Plugin_QGIS4_v1.6.0.zip`.
- Pendências: merge do PR #16 (1.5.0) e então PR da 1.6.0 (base `main`); tags `v1.5.0` e `v1.6.0`.
- Pedidos seguintes do autor: (1) revisão de tudo o que foi feito em todos os módulos, pendências e registros
  para versões futuras; (2) **manual do usuário em DOCX** (pt-BR, en, es), detalhado, apresentável, com figuras,
  conceitos, diferenças para rotinas similares, rotinas de uso, resultados e dicas ocultas.

### Revisão geral (20/11/2026)

- Documento `docs/REVISAO_GERAL_1.6.0.md`: versões e pendências administrativas, estado de cada módulo, questões
  que dependem do autor (atrito vetorial do Voronoi converte os pontos para o SRC dos polígonos; Processing
  `avaliacao`/`monitoria` visíveis; maiúsculas das modalidades em inglês; textos explicativos fixos → dicas;
  nomes temporários com acento no Windows) e registros para versões futuras.
- **Correções de texto (sem cálculo):** README do ZIP (dizia 1.3.0, "1 + atrito" e "equivalência não
  demonstrada"), README do repositório e "Sobre" do `metadata.txt` atualizados para a 1.6.0 e as validações.
- Próximo: manual do usuário em DOCX (pt-BR, en, es).

### Manual do usuário em DOCX (20/11/2026)

- Três arquivos em `docs/manual/saida/`: `Manual_Vista_Saga_Plugin_1.6.0_pt-BR.docx` (45 p.),
  `User_Manual_Vista_Saga_Plugin_1.6.0_en.docx` (44 p.) e `Manual_Usuario_Vista_Saga_Plugin_1.6.0_es.docx` (45 p.).
- Estrutura: capa, sumário, Apresentação (panorama + referência rápida), Instalação, Conceitos, um capítulo por
  módulo (para que serve, diferenças para rotinas similares, facilidade de uso, janelas, tabela de campos com o
  texto real das dicas, rotina, resultados, dicas ocultas, erros comuns), Validação (painel), Solução de
  problemas e Glossário.
- Fontes reprodutíveis em `docs/manual/` (ver `README.md` ali): `capture_windows.py` (capturas no QGIS com dados
  **sintéticos** e `campos.json`), `build_figures.py` (infográficos calculados pelos motores do plugin),
  `content_<idioma>.py` (texto), `build_manual.py` + `build_docx.js` (DOCX com sumário estático em duas passadas).
- No espanhol, os nomes dos módulos seguem a interface: Firma espacial, Monitoreo, Evaluación, Análisis de
  Voronoi, Combinación de mapas, Conversor de formatos, Secuenciador de mapas.
- Pendência: o autor revisa o conteúdo (sobretudo afirmações conceituais e as "dicas ocultas") antes de
  divulgar. O manual não vai no ZIP do plugin (decisão a confirmar com o autor).

### Próximo passo (início da sessão 6)

1. O autor testa `Vista_Saga_Plugin_QGIS4_v1.5.0-dev2.zip` no QGIS 4 (roteiro abaixo) e relata o resultado.
   Roteiro: (a) guia Raster com os 3 RS2 (Bairros primeiro, informar o SRC), marcar Antares, Gruta de
   Lourdes, Jacintinho e Poço e comparar com `assinatura01.txt` (esperado: só a diferença de 1 célula do
   Poço); (b) "Marcar todas" e comparar com `assinatura02.txt` (esperado: 100%); (c) guia Vetorial com
   camadas do autor, seleção pelas ferramentas do QGIS e contador da janela; (d) leiaute, textos, dicas e o
   que faltar em relação ao módulo antigo.
2. dev8 feito (Remover todas, legado obsoleto e oculto, motor antigo retirado; projeto descartado pelo
   autor); dev9 feito (nomes dos resultados em todos os módulos); tudo homologado pelo autor. Próximo: dicas.
3. Fechamento da Assinatura (CHANGELOG, `metadata.txt` 1.5.0, `NOTAS_DA_VERSAO_150.md`, homologação) e
   então as dicas em todos os módulos (a janela da Assinatura já tem dicas em todos os botões e campos).
4. Para comparar de novo com o Vista SAGA, os dados do autor (3 RS2, 2 relatórios, 2 vídeos) **não ficam
   entre sessões**: pedir que ele os reenvie (`assinaturas.zip`) e usar
   `scripts/comparar_assinatura_vista_saga.py --src EPSG:31985` (SRC usado só porque o RS2 não registra).

> **Natureza do projeto (registro do autor, 20/11/2026):** o Vista Saga Plugin é um **projeto pessoal
> do autor e não a tese de doutorado dele**. Menções anteriores a "tese" (inclusive no histórico e no
> `CLAUDE.md` até a 1.4.2) estão superadas. O rigor de método (testes de regressão, justificativa
> escrita, validação no Vista SAGA quando houver comparabilidade) continua valendo como boa prática.

### Onde está o trabalho

| Versão | Situação | Branch / PR | Commit de merge na `main` |
|---|---|---|---|
| 1.4.0 | fechada, homologada, **mesclada** | `feat/voronoi-atrito-fiel` / [#13](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/13) | `49056f9` |
| 1.4.1 | fechada, homologada, **mesclada** | `feat/interface-padrao` / [#14](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/14) | `5c6c876` |
| 1.4.2 | fechada, homologada, **mesclada** | `fix/sequenciador-guias` / [#15](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/15) | `0d58783` |
| 1.5.0 | fechada, homologada, **sem merge** | `feat/assinatura-e-dicas` / [#16](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/16) (base `main`) | - |
| 1.6.0 | fechada, homologada, **sem PR** | `feat/dicas-todos-modulos` (a partir da 1.5.0) / PR depois do merge do #16 | - |

**Pendências do autor (o proxy das sessões recusa criar tags):**
1. Tags (no remoto só existe a `v1.0.4`, conferido em 20/11/2026): `v1.3.0` = `87406de`,
   `v1.4.0` = `49056f9`, `v1.4.1` = `5c6c876`, `v1.4.2` = `0d58783`.
   Comandos (Codespaces): `git fetch origin`; `git tag -a vX.Y.Z <commit> -m "Vista Saga Plugin X.Y.Z"`;
   `git push origin vX.Y.Z`. Tags antigas (v1.0.5 a v1.2.1): commits no `CLAUDE.md`.

### Versão 1.5.0 (pedido do autor, 19/11/2026)

Branch `feat/assinatura-e-dicas`, criada da `main` (`0d58783`) em 20/11/2026; um único PR, com ZIPs
`-devN` a cada lote (fluxo do `CLAUDE.md`). Escopo combinado:

1. **Revisão do módulo Assinatura** (`signature_dialog.py`, motor, Processing `geosaga:assinatura`,
   relatórios). Escopo detalhado a definir com o autor no início da sessão (sugestão: levantar primeiro o
   que o módulo faz hoje, as diferenças para o Vista SAGA e os problemas conhecidos, e só então propor).
   **Achados do levantamento (20/11/2026):**
   - **No Vista SAGA, a Assinatura trabalha com um mapa ou com vários mapas ao mesmo tempo** (informação
     do autor). O plugin hoje aceita **um único mapa temático** por execução (raster ou vetorial):
     lacuna de funcionalidade, não só de interface.
   - Raster conta pixels pelo centro da célula (cobertura pode passar de 100%); vetorial por interseção
     exata, com exclusão da região de sobreposição entre classes (padrão) ou modo estrito.
   - Interface fora do padrão do plugin: caixas "Resultado temporário" e "Carregar GeoPackage" e CSV
     obrigatório; três textos explicativos fixos (candidatos a dicas).
   - Mensagens de erro do motor montadas com f-string e traduzidas por `tr(str(exc))` provavelmente não
     casam com o catálogo (a confirmar).
   - Sem registro de validação contra o Vista SAGA original (a 0.5.0 consta como "homologação pendente").
   **Funcionamento no Vista SAGA (descrição do autor, 20/11/2026; o plugin deve funcionar de forma análoga):**
   - **Um mapa:** selecionam-se todas as classes (no mapa ou na legenda) e calculam-se a área e o
     percentual de cada classe em relação à área total.
   - **Vários mapas:** carregam-se todos; o **mapa de referência fica por cima** e dita a assinatura. As
     feições ou classes selecionadas nele (uma ou mais) servem de limite, e dentro desse limite calculam-se
     as áreas e os percentuais de todas as classes/feições dos demais mapas. Exemplo: mapas de bairros,
     escolaridade e uso do solo; mede-se quanto de escolaridade e de uso do solo cai nos bairros
     selecionados. É contagem **mapa a mapa** dentro do limite, não cruzamento de combinações.
   - Diferenças para o plugin atual: referência só vetorial (sem classes de raster como limite); todas as
     feições da camada de áreas, sem seleção; um único mapa temático; sem modo "um mapa sozinho".
   **Caso de referência do autor (20/11/2026; 2 vídeos, 2 relatórios, 3 RS2 de 1108 × 496 células de
   10 m: `Bairros_Reginaldo`, `UsoSolo`, `Escolaridade`; dados só na sessão, nunca no repositório).**
   O Claude reproduziu o relatório 1 com 100% de coincidência (contagens e percentuais). Conclusões:
   - **Pergunta 1 respondida: resultado único da união** do que foi marcado (4 bairros: Antares, Gruta de
     Lourdes, Jacintinho, Poço = 82.191 células), não um resultado por feição.
   - **A seleção é uma máscara pintada sobre a referência**, com as "Ferramentas de Pintura": lápis e
     borracha; balde; retângulo, elipse, polígono e linha; lista de classes; botão "Assinar o mapa
     inteiro"; transparência da pintura. Projeto salvo em `*.ASN`.
   - **O balde preenche a região conexa por 4 vizinhos** (não a classe inteira): o Poço tem 17.415
     células, mas 1 célula só toca o resto na diagonal (linha 934, coluna 277) e ficou de fora (17.414,
     "99,99%"). Ou seja, no raster "feição" = região conexa por 4 vizinhos.
   - **Todos os mapas da lista são assinados, inclusive a referência**, na ordem da lista ("Lista de mapas a
     serem assinados em ordem de assinatura"; status "Processando assinatura - mapa 2 de 3").
   - Colunas do relatório por mapa: `Cat. - Legendas`, `Total Pixels`, `Total Ha` (classe no mapa inteiro),
     `Pixels Asn.`, `Área Asn. Ha`, `% Área Asn.` (= células da classe na máscara / células da máscara) e
     `% Categoria` (= células da classe na máscara / células da classe no mapa); linha `Total` com o total
     do mapa e o total da máscara. Todas as classes aparecem, inclusive as zeradas e o FUNDO.
   - **Base do percentual = a própria máscara, com o FUNDO dentro dela se ele for marcado**: no relatório 2
     ("Assinar o mapa inteiro") o FUNDO entra com 57,36% e 100,00%.
   **Decisões do autor (20/11/2026, pergunta 1):**
   - **Sem ferramentas de pintura** (lápis, borracha, retângulo, elipse, polígono): eram limitação
     tecnológica do Vista SAGA. No plugin, **só selecionar e desselecionar**, nas guias Vetorial e Raster.
   - **Resultado da união (como o Vista SAGA) e também o resultado por feição** (como o plugin já faz).
   - **Guia Raster: feição = classe inteira**, marcada numa lista de classes com caixas na janela (sem
     ferramenta de clique no mapa). Diferença conhecida para o Vista SAGA, aceita pelo autor: o balde dele
     marca a região conexa por 4 vizinhos; no caso de referência, a máscara do plugin terá 82.192 células
     contra 82.191 (a célula diagonal do Poço). Resultado por feição no raster = um por classe marcada.
     "Qualquer arrependimento posterior, refazemos de outra forma" (autor). Clique por região: fora do
     escopo, possível no futuro.
   - **Guia Vetorial (proposta do Claude, a confirmar ao discutir a interface):** a seleção da camada de
     referência feita com as ferramentas nativas do QGIS.
   - Pergunta 1 encerrada.
   **Decisões do autor (20/11/2026, pergunta 2, recomendação do Claude aceita):**
   - **As duas porcentagens do Vista SAGA:** `% Área Asn.` (base = máscara) e `% Categoria` (base = classe
     no mapa inteiro).
   - **FUNDO (RS2) e NoData (GeoTIFF) contam como classe qualquer**, dentro da base, como no Vista SAGA
     (o caso de referência valida a conta inteira). Percentual só entre classes reais: não incluído
     (possível coluna extra, se o autor pedir).
   **Decisões do autor (20/11/2026, pergunta 3, recomendações do Claude aceitas): mostrar a falta de dado.**
   - Guia Vetorial, parte do limite sem polígono no mapa assinado: linha **"Sem classe"**, dentro da base.
   - Mapa assinado que não cobre toda a extensão do limite: a parte de fora também vai para "Sem classe",
     com aviso no resumo da área do limite fora do mapa.
   - Sobreposição de classes num mapa vetorial assinado: mantém o tratamento atual (0.5.1): exclui a
     região ambígua e registra a área (padrão) ou modo estrito.
   **Pergunta 4 (20/11/2026):**
   - **Decisão do autor: sem mistura de formatos.** Guia Raster: referência e mapas assinados todos raster;
     guia Vetorial: todos vetoriais. **O autor aceita a perda** do caso atual "polígonos como limite + mapa
     temático raster" (converter antes, no Conversor ou no QGIS).
   - **Mesmo SRC obrigatório em todos os mapas** (decisão do autor), com mensagem clara. Corrige o defeito
     antigo: o motor atual reprojeta as áreas para o SRC do mapa temático sem avisar
     (`signature_engine.py:316`), contra a regra do `CLAUDE.md`.
   - **Guia Raster: mesma grade obrigatória** (resolução, extensão, alinhamento), como o Vista SAGA
     (decisão do autor); grades diferentes geram erro com sugestão de alinhar antes.
   - Pergunta 4 encerrada.
   **Pergunta 5 (20/11/2026, recomendações do Claude aceitas "por hora"; ajustes depois):**
   - Lista de mapas na janela, **referência no topo**, ordem por "Mover para cima/baixo"; todos assinados.
   - Raster: lista de classes com caixas, "Marcar todas" (= mapa inteiro) e "Desmarcar todas".
   - Vetorial: **só a seleção do QGIS** na camada de referência; janela mostra "N feições selecionadas";
     botão "Selecionar todas"; campo opcional de nome.
   - Nada selecionado: execução recusada com mensagem.
   - Caixa **"Resultado por feição", ligada por padrão**.
   - **Perguntas 1 a 5 encerradas.** Proposta consolidada em `docs/ASSINATURA_150_PROPOSTA.md`,
     aguardando aprovação do autor.
   **Decisões do autor sobre a proposta (20/11/2026):** manter o algoritmo Processing antigo (disposição no
   Processing **obsoleto e oculto**); saídas TXT e CSV no padrão do plugin, **sem GeoPackage**; **qualquer
   SRC projetado em metros** (revendo "somente UTM" após a ressalva do Claude); guia Raster com os formatos
   do GDAL (OSGeo) e o RS2; projeto como na Avaliação (`*.geosaga.json`, Novo/Abrir/Salvar).
   **Proposta sem pendências.** Plano de lotes aprovado (20/11/2026): dev1 motor e validação; dev2 janela
   nova; dev3 projeto, legado obsoleto e traduções; fechamento (CHANGELOG, notas, homologação); depois as
   dicas em todos os módulos.
   **dev1 concluído (20/11/2026), sem mudança de interface (a janela atual ainda usa o motor antigo):**
   - `geosaga/signature_model.py` (linhas e porcentagens; "Sem classe", "Sobreposição excluída", NoData),
     `signature_raster.py` (GDAL + RS2, mesmo SRC projetado em metros, mesma grade, feição = classe;
     NoData com nome na legenda, como o FUNDO de um RS2 convertido, conta como essa classe),
     `signature_vector.py` (OGR/GEOS, testável sem QGIS; a janela entregará WKB e classes),
     `signature_reports.py` (TXT e CSV em português; CSV `;`, UTF-8 com BOM).
   - `geosaga/tests/test_150_assinatura_motor.py` (22 testes, dados sintéticos com a célula diagonal);
     suítes: 499 (3 pulados) e 42.
   - `scripts/comparar_assinatura_vista_saga.py`, rodado pelo Claude com os dados do autor: relatório 2
     (mapa inteiro) 31/31 classes = 100%; relatório 1 (4 bairros) 28/31: as 3 diferenças são exatamente a
     célula diagonal do Poço (1 célula em cada mapa), diferença prevista e aceita.
   - **Decisão do autor (20/11/2026):** na guia Vetorial, a sobreposição excluída entra na base como linha
     própria ("Sobreposição excluída"), e as porcentagens de cada mapa somam 100%.
   **dev2 (20/11/2026): janela nova da Assinatura**, ZIP `Vista_Saga_Plugin_QGIS4_v1.5.0-dev2.zip`
   (aguardando teste do autor no QGIS 4):
   - `signature_dialog.py` reescrito: guias Raster/Vetorial; "1. Mapas - o primeiro é a referência" (camada
     do QGIS, várias do QGIS, arquivos; Remover, Mover para cima/baixo); Raster: lista de classes com caixas,
     "Marcar todas"/"Desmarcar todas"; RS2 sem `.rs2.json` pede o SRC ao adicionar; Vetorial: campos de
     classe e legenda por mapa, "Feições selecionadas em X: N" atualizado pela seleção do QGIS, "Selecionar
     todas", campo de nome da feição; "3. Opções" (Resultado por feição ligado; sobreposição só no vetor);
     "4. Resultado" (Título; Salvar em = CSV, TXT ao lado; vazio = pasta temporária); guia Resultados com
     recorte (união ou feição) e tabela copiável. Dicas (`setToolTip`) em todos os botões e campos novos.
     Execução no thread da GUI com janela de progresso e Cancelar (como antes).
   - Testes: `test_150_assinatura_janela.py` (estrutura) e `integration_signature_150_qgis.py` (QGIS real,
     Raster e Vetorial; aprovado no QGIS 3.34 do contêiner). Suítes: 505 (3 pulados) e 42.
   - `tests/qgis/smoke_qgis.py` e `gui_monkey.py` não carregam o plugin no QGIS 3.34 do contêiner
     (`Qgis.ProcessingSourceType` é do QGIS 4); igual na `main`, sem relação com a 1.5.0. O macaco deu as
     mesmas 4 exceções antes e depois.
   - O motor antigo (`signature_engine.py`, `signature_core.py`) ficou sem uso pela janela; sai no dev3
     junto com os testes dele (o algoritmo Processing legado não depende dele).
   - Próximo: dev3 (projeto como na Avaliação, legado obsoleto e oculto, limpeza do motor antigo).
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

## 20/11/2026 (sessão 5) — resumo do encerramento

- Registro do autor: o plugin é projeto pessoal, não a tese (`CLAUDE.md` corrigido).
- Assinatura redesenhada no modelo do Vista SAGA a partir de vídeos e relatórios do autor; perguntas 1 a 5 e
  pendências da proposta decididas (`docs/ASSINATURA_150_PROPOSTA.md`).
- dev1 (motor) e dev2 (janela) feitos; PR #16 aberto; ZIP `-dev2` entregue para teste no QGIS 4.
- Detalhes das decisões e dos lotes na Retomada rápida, item "Versão 1.5.0".

## 20/11/2026 (sessão 5)

- PR #15 já mesclado (`0d58783`); branch `feat/assinatura-e-dicas` criada para a 1.5.0.
- Registro do autor: o plugin é projeto pessoal, não a tese; `CLAUDE.md` corrigido.
- Levantamento inicial da Assinatura (achados na Retomada rápida); informação do autor: no Vista SAGA a
  Assinatura aceita um mapa ou vários; depois, descrição do funcionamento (mapa de referência por cima,
  seleção de feições/classes como limite, contagem mapa a mapa), registrada na Retomada rápida.
- Vídeos e relatórios do Vista SAGA analisados; relatório 1 reproduzido com 100% de coincidência;
  pergunta 1 respondida (união); seleção = máscara pintada, balde por 4 vizinhos.
- Decisão do autor: sem pintura, só selecionar/desselecionar (Raster e Vetorial); união e também por feição.
- Guia Raster: feição = classe inteira, por lista de classes (recomendação do Claude aceita). Pergunta 1 encerrada.
- Pergunta 2: duas porcentagens do Vista SAGA; FUNDO/NoData contam como classe (recomendação aceita).
- Pergunta 3: falta de dado aparece como "Sem classe" na base, com aviso; sobreposição como na 0.5.1.
- Pergunta 4 encerrada: sem mistura de formatos (perda do caso misto aceita), mesmo SRC e mesma grade obrigatórios.
- Pergunta 5 encerrada (recomendações aceitas por hora); proposta em `docs/ASSINATURA_150_PROPOSTA.md`.
- Pendências da proposta resolvidas: legado obsoleto e oculto, TXT+CSV sem GeoPackage, SRC projetado em metros,
  GDAL + RS2, projeto como na Avaliação.
- dev1 (motor novo da Assinatura) concluído: 22 testes; comparação com o Vista SAGA 100% no mapa inteiro e só a
  diferença prevista (célula diagonal) na seleção de 4 bairros.
- dev2 (janela nova da Assinatura) pronto; ZIP `-dev2` enviado ao autor; PR da 1.5.0 aberto.

## 19/11/2026 (sessão 4) — resumo do encerramento

- Validação do atrito na bacia real contra o Vista SAGA; critério de comparabilidade aceito e falha
  declarada; 1.4.0 fechada e mesclada.
- 1.4.1 (rodapé padrão em todos os módulos; títulos; Sequenciador) fechada, homologada e mesclada.
- 1.4.2 (Sequenciador com guias da mesma altura) fechada e homologada; PR #15 aberto.
- Contexto reiniciado neste arquivo; histórico movido para `docs/CONTEXTO_SESSOES_HISTORICO_ate_1.4.2.md`.
- Próximo: pausa; a sessão seguinte começa a 1.5.0 (Assinatura + dicas em todos os módulos).
