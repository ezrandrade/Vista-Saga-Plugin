# Contexto entre sessões

Registro das decisões, achados e pendências que ficaram fora do código. Serve para que uma nova
sessão do Claude (ou o próprio autor) retome o trabalho sem depender do histórico de conversas.
Atualize ao fim de cada sessão de trabalho. As entradas mais recentes ficam no topo.

---

## >>> RETOMADA RÁPIDA (atualizada em 19/11/2026, sessão 4: 1.4.0 fechada; 1.4.1-dev2 em teste) <<<

Leia esta seção primeiro; o histórico detalhado vem depois, da entrada mais recente para a mais antiga.
**A versão válida deste arquivo é a do repositório** (branch `feat/voronoi-atrito-fiel`); cópias guardadas
pelo autor podem estar desatualizadas (aconteceu na sessão 3).

### Onde está o trabalho

- **Branch:** `feat/voronoi-atrito-fiel` (último commit de código: dev6). **PR:**
  [ezrandrade/Vista-Saga-Plugin#13](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/13), aberto,
  sem merge. `metadata.txt` = 1.4.0; ZIPs de teste `-dev1` a `-dev6` (versão `-devN` só dentro do ZIP;
  `dist/` não é versionado: refazer com `python3.12 scripts/build_release.py` + troca da versão no
  metadata do ZIP).
- **Homologadas pelo autor no QGIS 4:** dev3 e dev4. dev5 testada com os dados reais (sessão 2).
  **dev6 enviada (sessão 3), ainda não testada pelo autor no QGIS 4.**
- **Dados do autor** (uso do solo, bacia, centroides, RS2, saídas): só na sessão; nunca no repositório.
  Nesta sessão o autor enviou só o arquivo de pontos `pontos_reginaldo_vistasaga.txt` (10 polos, massas
  = população, inteiras); se precisar dele de novo, pedir.
- A **tese está fora destas sessões** (decisão do autor): não perguntar sobre mapas da tese.
- **Protocolo (pedido do autor):** atualizar este arquivo a cada ação finalizada, commit + push imediato
  e envio do arquivo ao autor. No contêiner: `apt-get update` antes do `apt-get install`.

### Estado em 19/11 (sessão 4) — o que retomar primeiro

- **dev6 testada e APROVADA pelo autor no QGIS 4 (19/11).**
- **Decisão do autor (19/11):** o Voronoi com atrito precisa ser comparável ao Vista SAGA, mas não
  precisa coincidir 100%. **Critério de comparabilidade aceito pelo autor (19/11):** (1) ≥ 99% das células
  da área de estudo iguais às do Vista SAGA na mesma grade; (2) ≥ 90% das divergências na fronteira entre
  regiões; (3) nenhuma região com diferença de área > 1% da própria área. Raster passa nos 3 (bacia 10 m);
  Vetorial passa em 1 e 3, não em 2 (54-58%): versão contínua do método, usar declarando-a.
  **CORREÇÃO (19/11, `scripts/comparar_caso_bacia.py`, critérios calculados na área de estudo e região a
  região):** a avaliação acima estava errada (o critério 2 tinha sido medido no retângulo e o 3 só pela
  maior diferença absoluta). Resultado correto, bacia em 10 m:
  Raster Com Atrito 99,463% / 97,2% / **1,33% (Mangabeiras, -1,15 ha de 86 ha): NÃO atende o 3**;
  Raster Com Massa e Atrito 99,419% / 97,9% / 0,82%: atende; Vetorial Com Atrito 99,289% / 93,4% /
  1,91% (Mangabeiras): não atende o 3; Vetorial Com Massa e Atrito 99,063% / 88,9% / 1,99% (Mangabeiras):
  não atende o 2 nem o 3. Fechamento suspenso até decisão do autor (manter o critério e declarar a
  falha, investigar a causa, ou rever o critério 3, com o risco de ajuste depois de ver os dados).
  **Decisão do autor (19/11): opção 1, manter o critério e declarar a falha.** Na guia Raster, Com
  Atrito, a região que falha (Mangabeiras) tem 98% das divergências na fronteira, saldo de 0,13 célula
  por célula de fronteira.
- **1.4.0 FECHADA (19/11, sessão 4):** notas e CHANGELOG sem "(em teste)", seção "Segundo caso,
  independente" com os critérios, decisão e limitação do Vista SAGA; `_resumo.txt` com a validação na
  bacia; `scripts/comparar_caso_bacia.py` + teste; `CLAUDE.md` com o critério. Suítes 465 (3 pulados) +
  42. ZIP final `dist/Vista_Saga_Plugin_QGIS4_v1.4.0.zip` enviado ao autor. **Falta (autor):** merge do
  PR #13 e tag `v1.4.0` (o proxy das sessões recusa tags).
- **Tempos medidos pelo autor no QGIS 4 (dev6, dados reais, 19/11):** vetor direto Com Atrito 1 min 50 s,
  Com Massa e Atrito 1 min 40 s; raster Com Atrito 3 min 40 s, Com Massa e Atrito 5 min 25 s.
- **Pedido do autor (19/11), escopo escolhido por ele:** só a **interface** do plugin, retirando todas as
  menções ao Vista SAGA (inclusive as de validação). Feito na janela do Voronoi: introdução e as três
  notas de método (pt, en, es). Ficam como estão (fora do escopo pedido): relatórios `_resumo.txt`,
  `metadata.txt`, CHANGELOG, notas da versão, comentários do código e metadados do GeoTIFF; os outros
  módulos usam "Vista SAGA" como nome de formato (RS2, relatório TXT), não de modelo. A chave antiga
  "Os modelos que utilizam atrito ainda exigem validação com o Vista SAGA original" continua nos catálogos,
  sem uso no código. ZIP final 1.4.0 refeito.
- **Pedido do autor (19/11): padronizar a interface de todos os módulos → versão 1.4.1** (branch e PR
  próprios, dependentes do PR #13; só interface, sem cálculo). Decisões do autor: botão de ação
  "Executar" em todos os módulos; rodapé padrão [Executar] [Fechar], com [Validar] só na Avaliação (única
  exceção); progresso e Cancelar numa janela que aparece só durante a execução (como Voronoi e
  Combinação), saindo a barra e o Cancelar fixos do rodapé (Monitoria raster, Avaliação raster); a linha de
  status à esquerda do rodapé sai.
- **1.4.1-dev1 implementada (19/11, branch `feat/interface-padrao`, a partir da `feat/voronoi-atrito-fiel`):**
  `ui_shared`: `RUN_TEXT = 'Executar'`, `FooterStatus` (substitui a linha de status, guarda o texto sem
  exibir), `report_outcome` (desfecho na barra de mensagens do QGIS), `TaskProgressWindow` (janela de
  progresso com Cancelar ligada à QgsTask). Rodapé fora das guias em todos os módulos; Monitoria (guia
  Vetorial) e Avaliação (guias vetoriais) trazem os botões do formulário embutido para o rodapé da janela
  (visibilidade por guia); Conversor: "Propriedades RS2…" ao lado do arquivo de entrada. Nenhum cálculo
  alterado. Suítes 472 (3 pulados) + 42; janelas capturadas em QGIS 3.34 offscreen. ZIP
  `Vista_Saga_Plugin_QGIS4_v1.4.1-dev1.zip`. **PR:**
  [ezrandrade/Vista-Saga-Plugin#14](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/14), base
  `feat/voronoi-atrito-fiel` (depende do #13; depois do merge do #13, mudar a base para `main`).
- **1.4.1-dev2 (19/11, pedido do autor):** título "Vista Saga Plugin - Conversor de Formatos" (como no
  menu); janelas de progresso com o título da janela do módulo (`self.window().windowTitle()`, também nos
  formulários embutidos). Mantida, por decisão do autor, a diferença de modalidade da janela de progresso
  (não bloqueia nos módulos em segundo plano; bloqueia nos demais). Não auditado ainda: o miolo de cada
  módulo (grupos, rótulos, alinhamentos, textos de ajuda). Suítes 475 (3 pulados) + 42. ZIP
  `Vista_Saga_Plugin_QGIS4_v1.4.1-dev2.zip`. Pendente: teste do autor no QGIS 4.
- **Pedidos do autor para a dev3 (19/11), Sequenciador de Mapas:** (a) espaço vazio abaixo dos botões da
  guia Raster: FEITO (`CurrentPageTabs`: sizeHint e minimumSizeHint pela guia aberta, política vertical
  Maximum; Raster 334 → 122 px; commit e183b86); (b) salvar a animação em **.jxl**: EM DECISÃO. Não há
  codificador de JPEG XL animado no QGIS (GDAL JPEGXL só grava imagem única; Pillow não tem JXL nativo; Qt
  sem plugin JXL). Opções apresentadas ao autor: codificador próprio em Python puro (sem perdas, modular),
  programa externo (cjxl/ffmpeg) se instalado, ou quadros .jxl avulsos pelo GDAL. Suporte de navegadores
  a JXL animado não confirmado.
- **Compatibilidade com QGIS 3.44 LTR:** discutida e adiada pelo autor para a 2.0 (não registrar como
  pendência ativa antes disso).
  Próximo: fechamento da 1.4.0 (nota de método das duas guias com a validação
  na bacia; tirar "(em teste)"; ZIP final; merge do PR #13 e tag v1.4.0 pelo autor).
- **Vista SAGA roda no Windows 7 32 bits em VirtualBox** (PC principal do autor). O `[ATRITOS]` resolveu o
  erro de abertura do arquivo de pontos. Notas 1, 1, 3, 5 (FUNDO, Classe 1, Classe 3, Classe 5).
- **Bacia em 5 m (990 × 2.214), Simples e Com Massa: 100% de coincidência com o plugin** (2.191.850 células,
  0 divergências, polos nas células do arquivo). Segundo caso independente que confirma M/d² e coluna:linha
  a partir de 1.
- **Com Atrito e Com Massa e Atrito em 5 m: saídas vazias.** Os dois RS2 são idênticos byte a byte;
  495 × 1.107 células de 10 m (metade da grade), todas com o código 11 (fora da legenda), sem células
  "Ponto". Tempo relatado ~5 s; na tela, mapa todo amarelo, sem regiões (relato do autor: falha visível,
  sem mensagem). Causa desconhecida (hipóteses: limite de tamanho da grade no atrito do
  Vista SAGA de 32 bits, que reduz a grade sem converter os pontos; ou rodada abortada).
- **Enviado ao autor:** `validacao_atrito.zip` com o caso em 10 m (495 × 1.107) e 20 m (247 × 553), gerado do
  `Uso_Atrito_Reginaldo.rs2` (moda por bloco, empate → nota maior; pontos convertidos). Aguardando as saídas
  (salvar Com Atrito e Com Massa e Atrito com nomes diferentes; anotar tempo, mensagens e tamanho).
  Ao receber: rodar o plugin raster sobre o MESMO RS2 (grade idêntica) e o vetor direto sobre o RS2
  poligonizado; comparar célula a célula. Leitor tolerante ao código 11: decodificar o RLE sem validar a
  legenda (o `RS2Reader` recusa).

- **Casos de 10 m e 20 m rodados no Vista SAGA (19/11):** 10 m = saída completa na mesma grade
  (495 × 1.107), polos nas células do arquivo. 20 m = saída numa grade DOBRADA (494 × 1.106, rotulada
  10 m): o cálculo (247 × 553) ocupa só o canto superior esquerdo, resto código 11. Com a falha em 5 m
  (saída reduzida à metade, vazia), indica que o atrito do Vista SAGA grava numa grade de tamanho
  próprio (~495 × 1.107 aqui) e só funciona quando a entrada tem esse tamanho. Achado empírico, causa
  não confirmada; registrar como limitação do Vista SAGA original.
- **Guia Raster do plugin × Vista SAGA (mesmo RS2, mesma grade):** 10 m Com Atrito 99,586% (retângulo),
  99,463% (bacia); Com Massa e Atrito 99,606% / 99,419%; 20 m: 99,27% / 99,31% (retângulo). 95-98% das
  divergências na fronteira entre regiões do Vista SAGA; manchas de até 25 células (10 m); diferenças de
  área na bacia ≤ 1,4 ha (10 m). Coerente com o caso sintético (99,67% / 99,69%). Tempo do plugin:
  56 s / 78 s (10 m).
- **Guia Vetorial (modelo contínuo) × Vista SAGA, caso de 10 m poligonizado** (608 polígonos em degrau,
  FUNDO com nota 1; 249 s / 202 s; conferência 0 divergências): Com Atrito 98,80% (retângulo) / 99,29%
  (bacia); Com Massa e Atrito 98,65% / 99,06%. Soma |dif.| de área na bacia: vetor 7,5 / 12,1 ha
  (máx 1,7 / 3,7 ha), raster 4,1 / 6,1 ha (máx 1,4 / 1,3 ha). Manchas grandes (até 2.193 células) fora
  da bacia, a 1-2,4 km, piorando com a distância (vetor 97,2-97,4% a > 1 km; raster 99,7-99,9%):
  interpretação (não demonstrada) = termo de discretização da soma célula a célula do Vista SAGA
  (≈ D·passo/2, depende da direção), que o modelo contínuo não tem, amplificado longe dos polos.
  Dentro da bacia, com massa, as maiores manchas são Jacintinho (VS e raster) × Poço (vetor) no sul:
  mesmo padrão da divergência de 15-20 ha da dev5 → **nessa divergência, o Vista SAGA fica com a guia
  Raster.** Conclusão: guia Raster = reprodução fiel do Vista SAGA; guia Vetorial = mesmo modelo no
  limite contínuo (independente da grade), a declarar como tal. Decisão do autor pendente: qual guia usar
  na tese e como justificar (fidelidade ao Vista SAGA × independência da resolução).

### Estado na pausa (sessão 3) — o que retomar

1. **Validação da bacia no Vista SAGA (prioridade; decide a divergência vetor × raster com atrito de
   15-20 ha da dev5).** O autor tem aberto no Vista SAGA o RS2 do uso do solo (legenda [0] FUNDO, [1]
   Classe 1, [3] Classe 3, [5] Classe 5) e carregou `pontos_reginaldo_A_posicao.txt` (pontos do autor +
   `[ATRITOS]` 1, 1, 3, 5), que mostrou FUNDO 1, Classe 1 1, Classe 3 3, Classe 5 5. **Achado: o
   `[ATRITOS]` é lido por posição na legenda.** Pedido ao autor: rodar R1 Com Atrito, R2 Com Massa e
   Atrito, R3 Com Massa, R4 Simples (Classes Excluídas vazia), anotar os tempos e enviar o RS2 de entrada
   + os 4 RS2 de saída + o arquivo A. Comparação planejada: plugin raster sobre o MESMO RS2 (grade
   idêntica) e vetor direto sobre o RS2 poligonizado; R3/R4 conferem a posição dos polos (classe
   "Ponto"). Script de comparação ainda não escrito (pode ser adiantado; base: `scripts/comparar_caso_atrito.py`).
2. **Perguntas em aberto ao autor:** a mensagem "Erro na tentativa de abertura de arquivo" sumiu com o
   `[ATRITOS]`? (seção obrigatória?); notas do uso do solo = códigos (1, 3, 5) como nos testes da dev5?;
   como o RS2 e as coordenadas coluna:linha foram gerados (resolução, origem, contagem a partir de 1)?
3. **O Vista SAGA funciona no PC atual do autor** (o erro era do arquivo sem `[ATRITOS]`, não do PC).
4. **Teste da dev6 no QGIS 4** (o que conferir: ver "Próximos passos" abaixo).
5. Depois: fechamento da 1.4.0 (item 3 dos próximos passos).

### O que a 1.4.0 contém (estado atual)

1. **Com Massa = M/d²** (Vista SAGA; antes M/d). Raster d²/M; vetor exato com discos de Apolônio de razão √M.
   Validado: 100% das células do Vista SAGA (exceto empates).
2. **Atrito, guia Raster:** modelo célula a célula do Vista SAGA (Σ distância ao polo × nota × passo, reta
   de Bresenham; com massa, ÷ M); nota direta como custo (sem 1 + C). Validado: 99,67% / 99,69%.
3. **Atrito, guia Vetorial: vetor direto, modelo contínuo** (∫ s·nota ds no segmento polo-ponto, exato
   pelos cruzamentos com as bordas; índice angular de arestas por polo). Fronteiras traçadas numa malha
   adaptativa com conferência automática (lados, interior e conferência final por carimbo, correção em até
   3 passadas, orçamento de 400 mil células). Validado: 99,60% (com massa) / 99,52% (sem massa) do Vista
   SAGA; com nota uniforme reproduz Apolônio a < 1 cm. Dados reais: ~2 min, 0 divergências.
4. **Superfície de atrito vetorial** pela **coluna de atrito** (sem tabela manual), nas duas guias.
5. **Sem campo de espaçamento** na guia Vetorial: espaçamento automático (maior lado / 100, ≤ 1/4 da
   largura do polígono mais estreito, teto de 100 mil nós, ≥ 8 × tolerância); **tolerância 0,5 m**
   (≤ maior lado / 2000). Valores e conferência no `_resumo.txt`.
6. **Nota 0 recusada** (raster, coluna, combinação de superfícies).
7. **Área sem polígono e coluna vazia: sem resultado, atravessáveis com nota 1** (dev5; antes barreira).
8. Vetor direto com atrito roda em **QgsTask** (`VoronoiVectorTask`), com progresso e cancelamento.
9. Modalidades com atrito sem "(experimental)"; **sem opção do modelo da 1.3** (reproduzir resultados
   antigos com o ZIP da 1.3.0).

### Decisões do autor já tomadas (não reabrir sem pedido)

M/d²; atrito vetorial só pela coluna; guia Vetorial com modelo contínuo; verificação automática com
correção (opção 1); campo de espaçamento removido; tolerância 0,5 m (mapas 1:10.000, EP 3 m no PEC
Classe A); nota 0 bloqueada; sem legado 1.3; área sem polígono atravessável com nota 1; (dev6, aprovada em 19/11) Raster
recorta pela bacia, partes < 25 m² só informadas, NoData do atrito atravessável com nota 1.

### Próximos passos

**Atualizado na sessão 3 (18/11): dev6 implementada, testada e enviada** (`Vista_Saga_Plugin_QGIS4_v1.4.0-dev6.zip`);
aguardando o teste do autor no QGIS 4. O que conferir no teste: guia Raster com extensão = bacia (sem
resultado fora da bacia; % comparável entre modalidades); raster de atrito com NoData (faixa sem
resultado, polos alcançando o outro lado); vetor direto com atrito (sem lascas na borda; tempo e
partes < 25 m² no `_resumo.txt`). Escopo da dev6 (decisões do autor, sessão 3):
- (1) lascas < 1 m na borda após o recorte (vetor direto com atrito);
- (2) cabeçalho do `_resumo.txt` raster conforme a fonte do atrito;
- (3) tempo de cálculo no `_resumo.txt` do vetor direto;
- (4) **guia Raster recorta pela bacia** quando a extensão vem de camada poligonal (máscara; fora = sem
  resultado), como a guia Vetorial;
- (5a) **partes abaixo da escala só informadas no resumo**, sem alterar a geometria; limiar 25 m²
  (= (5 m)², PEC Classe A a 1:10.000);
- (6) **NoData do raster de atrito atravessável com nota 1, sem resultado** (como a área sem polígono).
- Fora da dev6, de maior peso para a tese: vetor × raster com atrito divergem 15-20 ha; só um teste da
  bacia no próprio Vista SAGA decide qual modelo se aproxima mais. **O autor pediu o caso (sessão 3):**
  conversor `scripts/preparar_caso_vista_saga.py` pronto, mas o autor já tinha RS2 + pontos próprios:
  ver "Estado na pausa", item 1.

1. ~~Receber e analisar o teste da dev5 com os dados reais~~ (feito, sessão 2).
2. ~~Pergunta sobre o NoData do raster de atrito~~ (decidido na sessão 3: atravessável com nota 1).
3. **Fechamento da 1.4.0** (depois do teste): registrar o tempo de cálculo no `_resumo.txt` do vetor direto;
   tirar "(em teste)" do CHANGELOG/notas; ZIP final `1.4.0`; o autor faz o merge do PR #13 e cria a tag
   `v1.4.0` (o proxy das sessões recusa criar tags).
4. Pendências antigas, sem urgência: tags v1.0.5-v1.3.0 (ver `CLAUDE.md`); leitura/gravação do arquivo
   de pontos do Vista SAGA (`Nome;Massa;X:Y`, coluna:linha contadas a partir de 1); critério escrito de
   "plugin finalizado".

### Como trabalhar no contêiner

- `apt-get update` e depois `apt-get install -y python3-gdal gdal-bin python3-pytest python3-shapely`; usar **python3.12**.
  Suítes: `python3.12 -m unittest discover -s geosaga/tests -p 'test_*.py'` (465, 3 pulados) e
  `python3.12 -m pytest -q tests/unit` (36).
- Fluxo real do diálogo: `apt-get install -y --no-install-recommends python3-qgis qgis-providers` (QGIS 3.34,
  não é o alvo, mas abre o diálogo) e rodar com `QT_QPA_PLATFORM=offscreen`; `tests/qgis/gui_monkey.py`
  precisa de `QGIS_PY=/usr/share/qgis/python` (as 4 exceções de `Qgis.ProcessingSourceType` são da API do
  QGIS 4, esperadas no 3.34).
- Scripts de validação no repositório: `scripts/gerar_caso_atrito.py`, `scripts/comparar_caso_atrito.py`,
  `scripts/comparar_vetor_plugin.py`. As saídas do Vista SAGA do caso de teste não estão no repositório
  (o autor pode reenviar `teste_voronoi_atrito_2.zip`).
- Código central: `geosaga/voronoi_friction_continuous.py` (modelo contínuo e traçado),
  `voronoi_friction.py` (modelo discreto), `voronoi_friction_vector.py` (polígonos → grade),
  `voronoi_vector.py` (`save_vector_voronoi`), `voronoi_engine.py` (`run_voronoi`), `voronoi_dialog.py`.

## 18/11/2026 (sessão 3) — pausa pedida pelo autor

- Retomar pela seção "Estado na pausa" da Retomada rápida. Commits da sessão 3: contexto e `CLAUDE.md`
  (regra de atualizar a cada ação), dev6 (código, testes, notas, CHANGELOG), conversor
  `scripts/preparar_caso_vista_saga.py` + teste, registros do diagnóstico do Vista SAGA.
- Arquivos entregues ao autor fora do repositório: ZIP dev6, caso de 17/11 (`teste_voronoi_atrito.zip`),
  `pontos_reginaldo_A_posicao.txt` e `pontos_reginaldo_B_codigo.txt` (variantes do `[ATRITOS]`).

## 18/11/2026 (sessão 3) — autor não consegue rodar o Voronoi no Vista SAGA

- Relato: o módulo Voronoi do Vista SAGA não roda, nem em modo de compatibilidade. Em 17/11 o autor rodou
  o caso sintético nele (R1-R4 recebidos). O RS2 da bacia ainda não foi gerado (dados não reenviados),
  logo o problema não é o caso novo. Pedido diagnóstico caixa-preta (sem nova análise do executável,
  decisão de 17/11): sintoma exato, mensagem, o que mudou desde 17/11, reteste com
  `teste_atrito.rs2` + `pontos_pixel.txt` (`python3.12 scripts/gerar_caso_atrito.py PASTA`).
- **Esclarecido:** o autor está em outro computador, longe do PC em que rodou os testes de 17/11. Falha
  atribuída ao ambiente; não investigar este PC. Rodar o caso da bacia no PC de 17/11, quando o autor
  voltar a ele. Enquanto isso: teste da dev6 no QGIS 4 (se houver neste PC), reenvio dos dados para
  deixar RS2 + pontos prontos, script de comparação escrito antes.
- Mensagem no PC atual (print do autor): "Erro na tentativa de abertura de arquivo" (janela "Erro"; há um
  mapa aberto ao fundo, logo o programa abre mapas). Hipóteses caixa-preta: permissão de escrita (pasta
  do programa em Arquivos de Programas), caminho com acento/espaço/longo/OneDrive, arquivo de pontos
  inexistente ou em codificação diferente. Pedido: em que passo aparece; teste com tudo em `C:\VSAGA\`,
  como administrador, com o caso de 17/11.
- O erro aparece ao abrir o arquivo de pontos (o mesmo `pontos_pixel.txt` que funcionou em 17/11 no outro
  PC; bytes idênticos). Logo, não é o formato: é onde/como o arquivo está neste PC. Hipóteses: aberto de
  dentro do ZIP (sem extrair), caminho com acento/OneDrive/longo, arquivo somente leitura ou bloqueado
  (o programa pode abrir para leitura e escrita), permissão. Pedido: extrair para `C:\VSAGA\teste\`,
  nome curto (`P.TXT`), conferir Propriedades (Desbloquear, sem Somente leitura), executar como admin.
- **Corrigido:** o arquivo que dá o erro não é o do caso de 17/11, e sim um arquivo do autor para a bacia
  (`pontos_reginaldo_vistasaga.txt`: 10 polos, massas inteiras de 4.261 a 73.139, coluna:linha até
  923:1991; ASCII, CRLF, sem BOM, **sem a seção `[ATRITOS]`**). Depois do OK no erro, o Vista SAGA carrega
  os 10 pontos (nomes e massas certos). Hipótese principal (não confirmada): o erro vem da falta do
  `[ATRITOS]`. Teste proposto: acrescentar `[ATRITOS]` com uma nota por classe do RS2 aberto, na ordem dos
  códigos a partir da classe 0; se o erro sumir, a seção é obrigatória (anotar para a leitura/gravação
  do formato no plugin). Perguntado ao autor: como o RS2 e as coordenadas coluna:linha foram gerados
  (grade, resolução, origem, contagem a partir de 1?), classes e notas.
- O autor mostrou a tabela dos polos (NM_BAIRRO, POP, MASSA = POP, **ATRITO por bairro**: 5, 5, 2, 6, 5, 2,
  2, 6, 2, 9) e pediu o txt com esses atritos. **Alerta dado:** no Vista SAGA o `[ATRITOS]` é uma nota por
  CLASSE do mapa (a partir da classe 0), não por polo; a dev5 usou o uso do solo (3 classes) como atrito.
  Gerado (scratchpad, não versionado) `pontos_reginaldo_atrito_por_bairro.txt` = pontos do autor +
  `[ATRITOS]` 1 (FUNDO) + os 10 valores na ordem dos bairros: só correto se o RS2 aberto tiver classe 0 =
  FUNDO e classes 1-10 = bairros nessa ordem; conferir na guia "Atrito Ambiental". Pendente: qual RS2 está
  aberto; se for de bairros, a comparação com a dev5 (uso do solo) não vale.
- **Mapa aberto = uso do solo**, legenda com **códigos não consecutivos**: [0] FUNDO, [1] Classe 1, [3] Classe 3,
  [5] Classe 5; notas exibidas 0, 3, 5, 1 (origem desconhecida: o arquivo do autor não tinha `[ATRITOS]`).
  O arquivo "atrito por bairro" foi descartado (não se aplica). Questão de formato NÃO testada: com
  códigos não consecutivos, o `[ATRITOS]` é lido por posição na legenda ou por código? Gerados (scratchpad)
  `pontos_reginaldo_A_posicao.txt` (1, 1, 3, 5) e `pontos_reginaldo_B_codigo.txt` (1, 1, 1, 3, 1, 5; códigos
  2 e 4 inexistentes com 1). Esperado na guia "Atrito Ambiental": FUNDO 1, Classe 1 1, Classe 3 3, Classe 5
  5; a variante que der isso revela a regra. Suposição a confirmar: nota = código (1, 3, 5) e FUNDO = 1
  (regra do plugin). Ainda pendente: como o RS2 e as coordenadas coluna:linha foram gerados.
- **CONFIRMADO (caixa-preta, 18/11): o `[ATRITOS]` é lido POR POSIÇÃO NA LEGENDA**, não por código. Com a
  legenda 0, 1, 3, 5, a variante A (1, 1, 3, 5) deu FUNDO 1, Classe 1 1, Classe 3 3, Classe 5 5. Vale para a
  futura leitura/gravação do formato no plugin (usar `RS2Header.legend()` na ordem gravada). Pendente:
  se a mensagem de erro sumiu com a seção (seção obrigatória?).
- Plano: o autor roda no Vista SAGA as 4 modalidades sobre o RS2 do uso do solo com a variante A e envia o
  RS2 de entrada + os 4 RS2 de saída + tempos. Comparação: plugin raster sobre o MESMO RS2 (convertido em
  raster de notas, grade idêntica) e plugin vetor direto sobre o RS2 poligonizado (bordas das células),
  para isolar a diferença de modelo da diferença de rasterização. Simples e Com Massa conferem a posição
  dos polos (classe 0 "Ponto" da saída).
- Se o Vista SAGA ficar indisponível: a validação da bacia não acontece; a guia Raster reproduz o
  algoritmo do Vista SAGA (99,7% no caso sintético) e é a referência de fidelidade por inferência, não
  por teste em dados reais. Registrar como limitação.

## 18/11/2026 (sessão 3) — pergunta do autor: há no QGIS Voronoi com massa/atrito?

- Busca na web (plugins.qgis.org e doc.esri.com bloqueados para leitura direta nesta sessão; só resultados
  de busca): nenhum plugin QGIS encontrado de Voronoi ponderado (multiplicativo ou por massa), nem de
  Voronoi com atrito na reta polo-ponto. Vizinhos: Simples = "Polígonos de Voronoi" do QGIS e
  v.voronoi (GRASS); atrito = alocação por caminho de menor custo (GRASS r.cost `nearest`, SAGA
  Accumulated Cost com Allocation, WhiteboxTools CostAllocation), modelo diferente do Vista SAGA
  (caminho que contorna o atrito, custo Σ atrito × comprimento, sem peso pela distância ao polo, sem
  massa). Fora do QGIS: ArcGIS Pro "Generate Weighted Voronoi" (aditivo, multiplicativo, potência,
  expressão; sem atrito). Conclusão: nada substitui o Vista SAGA como referência da validação; r.cost
  pode servir de análise de sensibilidade do método (decisão da tese, fora destas sessões).

## 18/11/2026 (sessão 3) — conversor do caso real para o Vista SAGA

- O autor pediu o RS2 + arquivo de pontos da bacia para rodar no Vista SAGA (validação vetor × raster
  com atrito). **Os dados do autor não estão no contêiner** (ficaram na sessão 2): pedido o reenvio
  (uso do solo com a coluna de nota, bacia, centroides com massa).
- Enquanto isso: `scripts/preparar_caso_vista_saga.py` (genérico, sem dados): grade = retângulo da bacia
  alinhado a múltiplos inteiros da resolução (bordas do RS2 são inteiros; padrão 5 m, como o raster da
  dev5); classes = FUNDO (0, nota 1) + notas distintas (ou `--campo-classe`); rasterização do plugin
  (centro da célula, última feição); `pontos_vista_saga.txt` (coluna:linha a partir de 1, CP1252, CRLF,
  `[ATRITOS]`); `pontos_centros.csv` (polos no centro das células, para o plugin usar posições
  idênticas); `atrito_grade.tif` (mesma grade); `caso.json`; `previa.png`. Recusa: SRC diferentes,
  massas não inteiras sem `--escala-massa` (Vista SAGA lê inteiro), notas não inteiras sem `--decimal`
  (separador não verificado), dois polos na mesma célula. Teste: `tests/unit/test_preparar_caso_vista_saga.py`.
  Conferido com dados sintéticos: o plugin sobre `atrito_grade.tif` + `pontos_centros.csv` dá a célula de
  cada polo ao próprio polo.
- Plano da comparação (atualizado adiante: comparar sobre o RS2 do autor) (quando vierem as saídas do Vista SAGA): só dentro da bacia (o recorte não muda os
  custos); Vista SAGA × plugin raster na MESMA grade (modelo discreto em dados reais) e × vetor direto
  (modelo contínuo, rasterizado pelo centro). Script de comparação ainda não escrito.

## 18/11/2026 (sessão 3) — dev6 enviada ao autor

- CHANGELOG e `NOTAS_DA_VERSAO_140.md` atualizados (seção "Ajustes da dev6"; NoData; resultado do teste
  da dev5 com a ressalva vetor × raster com atrito, 15-20 ha, não decidido sem o Vista SAGA).
- ZIP `Vista_Saga_Plugin_QGIS4_v1.4.0-dev6.zip` (versão `1.4.0-dev6` só no metadata do ZIP); conferido
  extraindo o ZIP e rodando o roteiro do diálogo (QGIS 3.34 offscreen): os 6 cenários iguais aos do
  repositório.
- Não feito: `gui_monkey.py` (precisa da pasta de dados do smoke); integração antiga
  `geosaga/tests/integration_voronoi_friction_qgis.py` usa nota 0 (recusada desde a dev4) e está
  desatualizada (não roda nas suítes; corrigir no fechamento).

## 18/11/2026 (sessão 3) — dev6: código e testes dos itens 1-6

- (4) `run_voronoi(study_wkb=...)` + `_study_mask` (centro da célula); diálogo passa o WKB da área quando
  a extensão é "camada poligonal" na guia Raster (não com atrito raster: a grade é a do raster).
- (6) `_nodata_as_passage`: NoData do raster de atrito e da combinação de superfícies → nota 1, sem
  resultado; centro sobre NoData continua recusado.
- (2) resumo raster: linha de passagem conforme a fonte (vetorial: área sem polígono; raster: NoData,
  com a contagem); linha do recorte; "Pixels sem resultado" no lugar de "excluídos por máscara".
- (1) `absorb_clip_slivers` (voronoi_friction_continuous): lascas do recorte final, largura média
  < 2 × tolerância, à região de maior fronteira comum (só modalidades com atrito).
- (3) "Tempo de cálculo (s)" no resumo do vetor direto (todas as modalidades).
- (5a) `SMALL_PART_M2 = 25`: partes < 25 m² listadas por região no resumo do vetor direto; geometria
  inalterada.
- Textos de interface (NoData) e catálogos en/es atualizados. Suítes: 455 (11 pulados: Shapely ausente
  no contêiner) + 36, verdes. Contêiner: `apt-get update` antes do `apt-get install`.
- Testes novos: `geosaga/tests/test_150_voronoi_dev6.py` (10): recorte Simples/Com Massa pelo centro
  da célula (resultado dentro = sem recorte), atrito com recorte (custos inalterados), área vazia
  recusada; faixa de NoData = nota 1 sem resultado (igual ao raster com 1 na faixa), centro sobre NoData
  recusado; lasca de 2 cm movida e parte de 2 m mantida; partes < 25 m²; tempo e partes no resumo.
  Obs.: o GDAL inclui célula com centro exatamente sobre a borda da área (teste ajustado para não
  ter empate). Suítes: 465 (3 pulados) + 36, verdes (com `python3-shapely`).
- Diálogo real (QGIS 3.34 offscreen, dados sintéticos: bacia em L, uso do solo passando 20 m da bacia,
  raster de atrito com faixa NoData): Raster Simples, Com Massa e Atrito vetorial com extensão = bacia →
  0 células com resultado fora da bacia, 0 sem resultado dentro; Massa e Atrito raster → faixa NoData sem
  resultado, as 3 regiões alcançam o lado leste; Vetorial Com Atrito e Com Massa → tempo e linha das
  partes < 25 m² no resumo. Corrigida linha duplicada no resumo do raster com atrito vetorial.
  Roteiro no scratchpad (não versionado).
- Falta: CHANGELOG/notas, ZIP dev6.

## 18/11/2026 (sessão 3) — decisões da dev6

- O autor aceitou as recomendações: (4) recorte pela bacia na guia Raster; (5a) partes < 25 m² só
  informadas no resumo; (6) NoData do raster de atrito atravessável com nota 1, sem resultado.
  Implementação da dev6 iniciada (itens 1-6 da retomada rápida).

## 18/11/2026 (sessão 3) — retomada após novo bloqueio

- A sessão anterior foi bloqueada depois do último commit de contexto (`1c36c55`, 10:17 UTC, "pausa").
  O que aconteceu nela depois desse commit não está registrado: **perguntar ao autor se respondeu às
  decisões 4, 5 e 6 da dev6** ou enviou algo novo.
- O autor reenviou um arquivo de contexto **desatualizado** (sem as entradas da sessão 2). A versão
  válida é sempre a do repositório (`docs/CONTEXTO_SESSOES.md` na branch `feat/voronoi-atrito-fiel`).
- **Regra nova (pedido do autor, 18/11):** atualizar este arquivo **a cada ação finalizada**, com
  commit + push imediato, e enviar o arquivo ao autor. Registrada também no `CLAUDE.md`.
- Repositório anexado com autorização do autor (o primeiro pedido foi recusado pelo filtro de
  permissões da sessão).

## 18/11/2026 (sessão 2) — resultados da dev5 com dados reais recebidos e analisados

- Repositório anexado depois, com autorização do autor. Análise feita sobre as saídas enviadas (`dev5-gpkg.rar`, `dev5-geotif.rar`). Dois arquivos do RAR vieram
  corrompidos (`Reginaldo_Massa_Atrito_dev5_resumo.txt`, `Reginaldo_Massa_dev5_centros.csv`); áreas
  recalculadas a partir dos GPKG.
- Vetor (GPKG): 10 regiões, geometrias válidas, soma = 2.343,27 ha nas 4 modalidades. Com Atrito:
  espaçamento 23,4 m, tolerância 0,5 m, 3,0 milhões de nós, conferência 100.276 pontos, 0 divergências
  após 2 passadas (correção em 153 células). Partes: Simples 10, Massa 11, Atrito 100, Massa e Atrito 95.
- Raster (GeoTIFF, 5 m): cálculo matricial 219 s (Atrito) e 319 s (Massa e Atrito).
- Vetor × raster, pixel a pixel (vetor rasterizado pelo centro na grade do GeoTIFF): Simples 100%,
  Com Massa 100% (3 px), **Atrito 99,36% (6.024 px), Massa e Atrito 99,14% (8.074 px)**. Mediana da
  distância à fronteira 0 m; p95 15-18 m; manchas de até 1,4 ha. Maior diferença de área: Massa e
  Atrito, Jacintinho +3,83 ha e Poço -2,58 ha no raster (deslocamento sistemático, ao sul). É a diferença
  entre o modelo contínuo e o discreto em percursos longos sobre mosaico fragmentado; qual dos dois
  reproduz o Vista SAGA nos dados reais não se sabe sem rodar o caso no Vista SAGA.
- Achados:
  1. Lascas que escaparam da regra das faces-fio: 2 partes na borda do domínio (0,023 m², largura
     0,017 m; 0,38 m², largura 0,077 m). Provável recorte pelo domínio depois da eliminação. Defeito
     pequeno, a corrigir.
  2. Enclaves abaixo da escala: 23 (Atrito) e 21 (Massa e Atrito) partes < 25 m² (menores que 1 pixel),
     largura 1-2 m (menor que o EP de 3 m a 1:10.000). O raster também é fragmentado (até 37 partes por
     região), logo a fragmentação vem do modelo + mosaico, não só do traçado. Decisão do autor pendente:
     unidade mínima de mapeamento?
  3. Resumo do raster com atrito: cabeçalho diz "NoData no caminho = barreira" e o rodapé diz "área sem
     polígono atravessável com nota 1". Texto a condicionar à fonte (conferir no código).
  4. Raster Simples/Com Massa avaliaram o retângulo inteiro (2.190.870 px = 5.477 ha; "excluídos por
     máscara: 0"), enquanto com atrito avaliaram só a cobertura de uso do solo (937.388 px). A "% da área
     avaliada" não é comparável entre modalidades na guia Raster. Conferido no código: a guia Raster usa
     só o retângulo envolvente da "Extensão de camada poligonal" (`run_voronoi(mask=...)` existe, mas o
     diálogo não o usa); a guia Vetorial recorta pelo polígono. Incoerência entre as guias.
  5. Raster com atrito tem 108 px (0,27 ha) fora do domínio do vetor: a cobertura do uso do solo passa
     um pouco da bacia; o raster não recorta pela bacia.
- Pendente: tempo e comportamento da barra de progresso do vetor direto (não está no `_resumo.txt`).

## 18/11/2026 — 1.4.0-dev5 implementada (dados reais)

- Regra nova: área sem polígono/coluna vazia atravessável com nota 1, sem resultado, nas duas guias
  (`OUTSIDE_RATING`; Raster: máscara `no_result` em `rasterize_friction`/`run_voronoi`; Vetorial:
  `outside_rating` em `FrictionSurface`, custo do trecho fora pela borda orientada da cobertura).
- Progresso: faixas fixas por etapa, marcos dentro das rodadas (1ª rodada com metade da faixa),
  bisseção e montagem com progresso; `VoronoiVectorTask` (QgsTask) para o vetor direto com atrito.
- Avisos do GDAL eliminados (`_length` só mede partes lineares; rasterização da conferência silenciosa).
- Dados reais no diálogo (QGIS 3.34 offscreen, extensão pela bacia): Com Massa e Atrito 115-129 s,
  0 divergências, áreas = modelo ponto a ponto; paradas da barra de até ~16 s em blocos indivisíveis.
- Testes novos: área em L atravessável (raster e contínuo). Suítes: 455 (3 pulados) + 36.
- ZIP `Vista_Saga_Plugin_QGIS4_v1.4.0-dev5.zip`. Pendente: teste do autor com os dados reais.

## 18/11/2026 — teste da dev4 com dados reais: atrito vetorial sem fim aparente

- O autor enviou dados reais (uso do solo como atrito, pontos com massas e limite da área de
  interesse, resultados Simples e Com Massa). **Dados do autor: só na sessão, nunca no repositório.**
- Relato: Voronoi com atrito (guia Vetorial) rodando há 18 min sem indicação de andamento; falta barra
  de progresso em porcentagem.
- Dados: 3 classes de uso do solo (multipolígonos com 151-519 partes; 40.785 vértices), 10 polos, bacia
  de ~5 × 11 km (2.343 ha). Espaçamento automático 23,4 m (teto de 100 mil nós), tolerância 0,5 m.
- **Achados e correções (WIP, dev5):**
  1. Lentidão: 6,5 ms por ponto (segmento × 39.451 arestas). **Índice angular de arestas por polo**
     (`_AngularIndex`, exato: diferença 1e-15): 0,09 ms por ponto (70×).
  2. **Regra "área sem polígono = barreira" quebra áreas côncavas:** a bacia é côncava; reta polo-ponto
     que sai da bacia ficava bloqueada (confirmado 100% em 1.200 segmentos); polos alcançavam 48-96% da
     bacia. Recomendação minha da dev2, errada, e nem fiel ao Vista SAGA (lá a área fora é a classe
     FUNDO, com nota; classes excluídas são atravessadas sem resultado). Implementado
     `outside_rating` (passagem com nota, sem resultado), conferido contra integral numérica numa área em
     L. **Decisão do autor (18/11): opção 1, nota 1** (custo basal do Vista SAGA, padrão da classe FUNDO):
     área sem polígono e coluna vazia = atravessáveis com nota 1, sem resultado. Vale para as guias
     Vetorial (modelo contínuo) e Raster (modelo célula a célula). Substitui a regra da barreira (dev2).
  3. **Laço de refinamento com limite fixo (nível + 2 rodadas) terminava antes de estabilizar**: 70 pontas
     soltas na rede de fronteiras, regiões fundidas (Jardim Petrópolis com 1.306 ha), conferência com 25%
     de divergência. Laço agora vai até estabilizar: 0 pontas soltas, 0 divergências; áreas traçadas =
     modelo ponto a ponto (grade de 50 m) a ≤ 2 ha. Regiões multipartes são reais (enclaves do mosaico).
  4. Conferência final: carimbo das regiões na grade de amostras (GDAL) em vez de 100 mil testes de ponto
     em polígono (100 s → ~1 s).
  5. Progresso em porcentagem com marcos dentro das rodadas (máximo de 7 s sem atualização) e execução do
     vetor direto com atrito em `VoronoiVectorTask` (QgsTask, cancelável).
- Tempo com os dados reais: ~2 min (Com Atrito 111 s; Com Massa e Atrito 129 s), antes > 18 min sem fim.

## 18/11/2026 — resultados do teste da 1.4.0-dev4 recebidos

- `voronoi_vetorial_dev4.zip`. O autor testou nota 0 na coluna ATRITO: o processo foi bloqueado (como
  decidido) e ele rodou com 0,1 (coluna ATRITO2; inferido pelas áreas: 0,1 no polígono "Atrito medio").
- Coluna ATRITO (extensão de ~948 m): espaçamento automático 9,48 m, tolerância 0,474 m; regiões inteiras,
  partição exata, conferência 0 divergências, 99,52% (sem massa) e 99,60% (com massa) do Vista SAGA;
  diferença para a dev3 (1 cm): 2-5 cm médios.
- Coluna ATRITO2 (0,1 no leste): conferência 0 divergências; Com Atrito com a região C em 2 partes — a
  segunda (858 m²) é real: cunha de C no alto da faixa de atrito alto, separada do corpo de C pela
  região B (conferido no modelo ponto a ponto).
- **dev4 homologada pelo autor no QGIS 4.**
- **Próximo passo (decisão do autor):** teste da dev4 com dados reais do autor antes de fechar a 1.4.0
  (medir tempo com muitos polos/polígonos; geometrias irregulares, buracos e lascas). Dados reais não
  vão para o repositório. Sugestão anotada para o fechamento: registrar o tempo de cálculo no
  `_resumo.txt` do vetor direto (hoje só o raster com atrito o registra).

## 18/11/2026 — 1.4.0-dev4 implementada

- `voronoi_friction_continuous`: `default_tolerance` (0,5 m em metros, ≤ maior lado/2000) e
  `automatic_spacing` (maior lado/100, ≤ 1/4 da menor largura média 2A/P dos polígonos que tocam a
  extensão, ≥ √(área/100 mil) e ≥ 8 × tolerância); `friction_voronoi_polygons(spacing=None,
  tolerance=None, units_to_meters=...)`. A fração passou de 1/200 (proposta) para 1/100: mesmo
  resultado, 3,5× mais rápido no caso de teste (1,1 s × 3,8 s). No caso aleatório o limite pela largura
  domina (~10 s).
- `save_vector_voronoi(search_spacing=None, friction_tolerance_m=None)`; relatório com espaçamento e
  tolerância usados. Diálogo: campo de resolução oculto na guia Vetorial; `search_spacing=None`.
- Nota 0 recusada: `check_rating`, `FrictionSurface`, `validate_friction` (raster e polígonos
  rasterizados), `parse_class_notes`; mensagens en/es; testes ajustados (074, 083, 130, 140).
- Caso de teste automático: espaçamento 8 m, tolerância 0,4 m (extensão de 800 m), regiões inteiras,
  conferência 0 divergências, 99,60% / 99,52% do Vista SAGA. Pontos fora da região na amostra
  independente: todos a < 9 cm da fronteira (dentro da tolerância).
- Suítes: 453 (3 pulados) + 36. QGIS 3.34 offscreen: guia Vetorial sem o campo, 99,60% / 99,48%;
  Raster 99,69%; Com Massa 100%. ZIP `Vista_Saga_Plugin_QGIS4_v1.4.0-dev4.zip`.

## 18/11/2026 — resultados do teste da 1.4.0-dev3 recebidos

- O autor enviou `voronoi_vetorial_5m.zip` e `voronoi_vetorial_20m.zip` (QGIS 4).
- dev3, espaçamento 5 m: Simples 99,96% (2 empates), Com Massa 100%, Atrito 99,50%, Massa e Atrito
  99,60%; todas com 1 parte por região, partição exata, conferência automática 0 divergências (19.200
  pontos). Atrito também com 20 m: 99,50%, 1 parte por região, 0 divergências (1.200 pontos). Atrito
  5 m × 20 m: diferença média 0,13-0,18 cm.
- **`Massa_Atrito_03` (pasta de 20 m) não é da dev3:** relatório no formato da dev2 e malha de busca de
  1 m (não 20). Está correto (99,60%, 1 parte por região), mas o teste-chave (Massa e Atrito, dev3,
  20 m, o caso que partia a região A) ficou sem resultado. Pedido ao autor: repetir só esse caso na
  dev3 (na dev4 o espaçamento deixa de ser escolhido).
- **Teste-chave recebido (`voronoi_vetorial_dev3.zip`): Massa e Atrito, dev3, 20 m:** 1 parte por região
  (na dev2 a região A saía em 2), partição exata, 99,60% do Vista SAGA, conferência 0 divergências
  (1.200 pontos). Com Atrito 20 m repetido: idêntico ao anterior. **dev3 homologada pelo autor no
  QGIS 4.** Próximo passo: dev4 (espaçamento automático, tolerância 0,5 m, valores no relatório, nota 0
  bloqueada).

## 18/11/2026 — decisões pendentes da dev1 fechadas pelo autor

O autor acatou as três recomendações (entram na dev4, junto com o padrão automático e a tolerância de
0,5 m):

1. **Área sem polígono e coluna de atrito vazia = barreira** (sem resultado e sem passagem); o plugin
   não inventa nota; o relatório informa as feições com a coluna vazia. (Já é o comportamento atual.)
2. **Sem opção "legado 1.3"** na interface; resultados antigos se reproduzem com o ZIP/tag da 1.3.0.
   (Já é o comportamento atual; registrar nas notas da versão.)
3. **Nota de atrito 0 bloqueada:** exigir nota > 0 (raster, coluna vetorial e combinação de superfícies),
   com mensagem sugerindo um valor pequeno (ex.: 0,1) para "quase sem atrito". Motivo: custo zero cria
   empates resolvidos pela ordem dos pontos, e o comportamento do Vista SAGA com nota 0 não foi testado.
   **A implementar na dev4** (`check_rating`, `validate_friction`, `voronoi_friction_stack`, mensagens
   en/es, testes que hoje usam nota 0).

## 18/11/2026 — proposta para a 1.4.0-dev4: padrão automático, tolerância pela escala dos dados

- O autor questionou o campo "Espaçamento da busca" (parece raster) e propôs um padrão único, aceitando
  a área de influência como estimativa. Discussão: (1) incerteza das entradas domina: +10% numa nota
  ou massa muda 0,4-1% da área (0,2-0,5 ha no caso de teste); PEC Classe A (Decreto 89.817/1984) a
  1:10.000 = 5 m (EP 3 m); logo 1 cm de tolerância é falsa precisão; (2) mas os defeitos corrigidos na
  dev3 eram topológicos, sistemáticos, silenciosos e dependentes de parâmetro arbitrário: a conferência
  automática (topologia) fica inegociável.
- Escala dos polígonos de atrito do autor: **1:10.000**.
- Medição (caso de teste, espaçamento 10): tolerância 0,01 / 0,1 / 0,5 / 1 m → vértices 902 / 520 /
  385 / 371; 0,8 / 0,6 / 0,5 / 0,5 s; coincidência com o Vista SAGA 99,60% em todas; maior diferença de
  área frente a 1 cm: 0 / 16 / 27 / 72 m².
- **Aprovado pelo autor (18/11):** tolerância padrão 0,5 m e a ordem (primeiro o teste da dev3, depois a
  dev4). Plano da dev4: sem o campo; espaçamento automático (≈ 1/200 do maior
  lado da extensão, ≤ 1/4 da largura média do polígono de atrito mais estreito, teto de ~100 mil nós);
  tolerância padrão 0,5 m (1/6 do EP a 1:10.000), limitada a extensão/2000 em áreas pequenas; ambos
  no `_resumo.txt`; conferência de topologia mantida. **Próximo passo:** aguardar os resultados do
  teste da dev3 (de preferência com espaçamento de 20 m) e então implementar a dev4.

## 18/11/2026 — resultados do teste da 1.4.0-dev2 recebidos

- O autor enviou `Voronoi_Vetorial.zip` (QGIS 4, guia Vetorial, 4 modalidades). Partição exata nas 4;
  coincidência com o Vista SAGA: Simples 99,96% (2 empates), Com Massa 100%, Atrito 99,50% (espaçamento
  5), Massa e Atrito 99,60% (espaçamento 20). Áreas estáveis entre espaçamentos (0,1-0,4 cm médios).
- **Defeito achado no teste do autor:** Massa e Atrito com espaçamento 20 m: região A em 2 partes (um
  triângulo de 3 m² separado por um fio de C de 0,14 mm). Causa: lado de célula com duas trocas de
  região (C→A→fora) perto da borda; a junção caiu na célula errada. O autor notou que mudar o
  espaçamento faz o defeito sumir (coerente: depende de onde caem as células).
- Correções (não commitadas como versão; WIP na branch): (1) lado com duas trocas se denuncia pelo
  rótulo ao lado da troca achada ≠ rótulo da ponta → as duas células se dividem em 4, recursivamente;
  (2) faces-fio (largura média < 2 × tolerância) vão ao vizinho de maior fronteira comum; (3) corda
  conferida em 1/4, 1/2 e 3/4 (uma cunha fina de B de 5 m × 2 m no canto do corredor era cortada, com
  desvio de até 2 m), dividida no ponto do meio; busca da fronteira com alcance crescente.
  Resultado no caso: 1 parte por região em qualquer espaçamento (5-40 m); >99,9% dos pontos de
  fronteira a < 2 cm da verdadeira; pontas de cunhas encurtadas em até ~0,5 m (área desprezível).
  A afirmação "desvio máximo de 1 cm" foi corrigida para "tolerância de 1 cm" + ressalva (relatório,
  interface, notas).
- **Em aberto:** `test_random_polygons_partition_and_labels` falha: faixa estreita (~7 m) da região 2
  entre duas partes da região 4 atravessa o lado de uma célula de 15 m com as duas pontas iguais
  (4→2→4): troca dupla invisível, ~100 m² com rótulo errado. É a limitação declarada ("detalhes menores
  que o espaçamento"), mas silenciosa. Proposta: verificação automática das faces (amostras internas)
  com refinamento local, ou aviso ao usuário.
- **Decisão do autor (18/11): opção 1, verificação automática com correção** (conferir pontos dentro de
  cada célula/face; onde houver rótulo inesperado, subdividir e traçar de novo; relatar a conferência).
- **Implementado (dev3):** `trace()` em `friction_voronoi_polygons`: malha adaptativa (dict de células
  (i0, j0, tamanho)), conferência por célula com avaliação em lote (lados: 1/4, 1/2, 3/4 e cantos das
  vizinhas menores; interior: centro e quartos; lado duplo da bisseção), só das células novas e das
  vizinhas das divididas. Conferência final: 1 ponto por célula base (posição fixa 0,618/0,414), contra
  os polígonos; divergência a > 5 × tolerância da fronteira aprofunda a pré-divisão (8 × 8, 64 × 64)
  da célula e vizinhas e refaz o traçado (até 3 passadas; orçamento de 400 mil células). Rotulagem com
  uma passada por polo (poda exata conferida contra avaliação exaustiva). Relatório informa a
  conferência e avisa se restar divergência.
- Provas: caso aleatório 0 divergências e 0/6000 numa amostra independente (espaçamentos 15/30/60 m);
  com as conferências internas novas desligadas, a final achou e corrigiu a faixa estreita (30 m).
  Desligar a conferência dos lados quebra a coerência entre células grossas e refinadas (não é
  opcional). Tempo: caso de teste 0,5-3 s; caso aleatório (9 polos, 13 polígonos) ~4-5 s.
- Suítes: 450 (3 pulados) + 36. QGIS 3.34 offscreen: Vetorial 99,60% / 99,48%, Raster 99,69%.
- ZIP `Vista_Saga_Plugin_QGIS4_v1.4.0-dev3.zip`.

## 17/11/2026 (noite) — 1.4.0-dev2 implementada: vetor direto com atrito

- `geosaga/voronoi_friction_continuous.py` (novo): `FrictionSurface` (polígonos com nota, sobreposição
  = última feição, arestas com interior à esquerda, união = cobertura), custo exato
  A = D²·[Σ ±f·τ²/2 + f(x)/2] por cruzamentos (vetorizado, sem ordenar), barreira = sair da
  cobertura; polo deslocado 1 µm nos testes de cruzamento (o caso de teste tinha segmentos passando
  exatamente por cantos e dava paridade errada). `ContinuousModel.labels` com poda A >= f_mín·D²/2.
  `friction_voronoi_polygons`: malha deslocada (1/π, 1/e do espaçamento), bisseção diádica nos lados
  (pontos idênticos nas arestas comuns), refinamento local 8 × 8 das células com junção/sela,
  propagado quando um lado troca de rótulo mais de uma vez; junção por subdivisão; refinamento de
  corda até a tolerância; poligonização GEOS (noding por união com uma linha, GDAL < 3.7);
  recorte de cada face pelo domínio antes do rótulo, rótulo por pedaço; resíduos finos ao vizinho
  de maior fronteira comum.
- `save_vector_voronoi` aceita 'friction'/'mass_friction' (friction_features, search_spacing).
- Diálogo: guia Vetorial = vetor direto nas 4 modalidades; com atrito, só polígonos + "Coluna de
  atrito" + "Espaçamento da busca" (o campo de resolução, rotulado de novo). Saíram a tabela
  classe → nota e o controle de área sem polígono (barreira fixa). Corrigido: colunas vazias quando a
  camada já vinha selecionada.
- Resultados: caso validado 99,60% (com massa) / 99,52% (sem massa) no centro das células; partição
  exata; nota uniforme = Apolônio a < 1 cm (espaçamento 10-20 m; com 40 m, 6 cm: detalhe perdido).
  QGIS 3.34 offscreen: Vetorial 99,60% em 0,6 s; Raster com polígonos 99,69%. Suítes: 448 (3
  pulados) + 36.
- ZIP `Vista_Saga_Plugin_QGIS4_v1.4.0-dev2.zip`; teste com `caso_atrito_vetorial.gpkg` (coluna ATRITO).

Pendências:
- [ ] Autor testa a dev2 no QGIS 4: guia Vetorial (esperado 99,60% com massa; 99,48% sem) e Raster.
- [ ] Autor confirma: área sem polígono/coluna vazia = barreira; sem "legado 1.3"; nota 0 permitida.
- [ ] Desempenho com dados reais (muitos polos/polígonos) não medido; o custo cresce com
      polos × arestas × nós avaliados.

## 17/11/2026 (noite) — decisões para a 1.4.0-dev2: vetor direto com atrito

- O autor não quer o resultado com atrito obtido por poligonização de raster: **a guia Vetorial passa a
  usar o modelo contínuo** do atrito (A = ∫₀^D s·f(s) ds ao longo do segmento polo → ponto, f = nota
  do polígono atravessado; com massa, A/M), com fronteiras traçadas numericamente até uma tolerância
  declarada. Mostrado ao autor antes da decisão (figuras): no caso validado, o modelo contínuo
  coincide 99,50% (sem massa) e 99,60% (com massa) com o Vista SAGA, contra 99,67%/99,69% do modelo
  discreto da guia Raster; diferenças a menos de uma célula da fronteira. Guia Raster continua no
  modelo discreto do Vista SAGA.
- **Atribuição do atrito simplificada:** só pela **coluna de atrito** da camada de polígonos; sai a
  tabela classe → nota.
- Decisões do orientador, a confirmar com o autor: área sem polígono e feições com a coluna vazia =
  barreira (sem resultado e sem passagem), sem controle manual; na guia Vetorial, superfície de atrito
  só vetorial (polígonos).

## 17/11/2026 (noite) — 1.4.0-dev1 implementada

Decisões do autor (17/11): massa **M/d²**; **atrito vetorial** nas modalidades com atrito, com notas
por **classe** (tabela, como na Avaliação) **ou por coluna**; a **área sem polígono** recebe nota
informada (ou barreira); custo = **nota direta** (sem 1 + C). Sem modelo "legado 1.3" na interface:
quem precisar reproduzir resultados antigos usa o ZIP da versão antiga (decisão do orientador, a
confirmar com o autor).

Implementado na branch `feat/voronoi-atrito-fiel` (versão 1.4.0 no `metadata.txt`):

- `voronoi_core.assign_window('mass')`: d²/M. `voronoi_vector._apollonius_disk`: k = √(M_l/M_p).
- `voronoi_friction.py` reescrito: `_vista_saga_cost_batch` (Bresenham vetorizado, Σ d × nota ×
  passo), poda exata com limite nota_mín × lado² × n(n+1)/2, célula do polo sempre do polo, sem
  `baseline`. Reproduz exatamente os números da validação (16 e 15 células).
- `voronoi_friction_vector.py` (novo): notas por classe/coluna, área sem polígono (nota, barreira
  ou exigência de cobertura total), rasterização pelo centro da célula (MEM/"Memory" do OGR).
- Diálogo: "Tipo de superfície" (Raster/Vetorial), camada de polígonos, "Notas por", campo de
  classe + "Notas das classes…", coluna de atrito, "Área sem polígono" (“—”/nota + Barreira);
  grade da análise (extensão + resolução) também na guia Vetorial com atrito vetorial; o SRC da
  análise é o da camada de polígonos (pontos convertidos, como no atrito raster).
- Modalidades com atrito sem "(experimental)"; textos, metadados e `_resumo.txt` atualizados.
- Testes: 074/081/086 reescritos contra `geosaga/tests/friction_reference.py` (Python puro);
  `test_140_voronoi_vista_saga_case.py` (regressão do caso) e `test_140_friction_vector.py`.
  Suítes: 440 (3 pulados) + 36, verdes.
- Conferência de ponta a ponta em **QGIS 3.34 offscreen** (o do Ubuntu; não é o alvo): caso em
  polígonos → 99,69% (classes, com massa), 99,67% (coluna), 99,69% (guia Vetorial); mensagens de
  cobertura incompleta, polo sobre barreira e classe sem nota conferidas. `gui_monkey`: nenhuma
  exceção no Voronoi (só as do Processing, API exclusiva do QGIS 4).
- ZIP de teste: `Vista_Saga_Plugin_QGIS4_v1.4.0-dev1.zip` + `caso_atrito_vetorial.gpkg`
  (camadas `uso_atrito`, com CLASSE e ATRITO, e `pontos`, nos centros usados pelo Vista SAGA).

Pendências:
- [ ] Autor testa a dev1 no QGIS 4 com `caso_atrito_vetorial.gpkg` (esperado: 99,69% com massa e
      classes; 99,67% com atrito e coluna; Simples e Com Massa 100%, exceto empates).
- [x] Esclarecido pelo autor (17/11): o desenvolvimento do plugin é separado da tese, que fica fora
      destas sessões. Não perguntar sobre mapas da tese nas sessões do plugin; o autor chama quando
      voltar à tese. O rigor de método do `CLAUDE.md` continua valendo para o plugin.
- [ ] Autor confirma: sem opção "legado 1.3" na interface.
- [ ] Nota 0: permitida (custo zero), comportamento do Vista SAGA com nota 0 não testado.
- [ ] Leitura/gravação do arquivo de pontos do Vista SAGA (contagem a partir de 1): não feito.

## 17/11/2026 (noite) — decisões do autor para a 1.4.0

- **Massa: M/d²** (como o Vista SAGA), no raster e no vetor exato (discos de Apolônio com razão √M).
- **Atrito com superfície vetorial** nas modalidades Com Atrito e Com Massa e Atrito (pedido do autor).
- Perguntas sobre a tese (mapas da 1.3, significado da massa): fora do escopo destas sessões, por
  decisão do autor (ver entrada da dev1).

## 17/11/2026 (noite) — reteste no QGIS com os pontos corrigidos: Simples homologado

O autor refez o vetorial com `docs/caso_atrito/pontos_qgis.csv` (`Voronoi_Plugin_{Simples,Massa}_2.gpkg`).
`python3.12 scripts/comparar_vetor_plugin.py VS PLUGIN _2 qgis`:

- **Simples: 99,96% (2 células), e as 2 são empates exatos** entre B e C (células 45:23 e 55:26,
  equidistantes). Excluídos os empates, 100%. **Homologado pelo autor no QGIS 4.2.2.**
- **Desempate do Vista SAGA:** nas 4 células empatadas da grade (45:23, 55:26, 65:29, 75:32), vence o
  polo que vem **primeiro no arquivo** (B antes de C). É a mesma regra do raster do plugin (`<` estável
  em `assign_window`). No vetor, o empate é a própria fronteira; a rasterização pelo centro escolhe
  qualquer lado, o que não é erro do plugin.
- **Com Massa: 84,39% (749 células), exatamente o previsto** a partir do código; 100% contra o modelo do
  próprio plugin. Polo C: 512 células no Vista SAGA, 143 no plugin. Diagnóstico confirmado: a
  divergência é só o modelo (M/d × M/d²).

## 17/11/2026 (noite) — vetor do plugin (QGIS 4.2.2) × Vista SAGA

O autor rodou no QGIS o Voronoi **vetorial** Simples e Com Massa (`Voronoi_Plugin_{Simples,Massa}.gpkg`,
SIRGAS 2000 / UTM 25S, extensão igual à do mapa) com os pontos do `pontos_utm.txt`, que estão
**deslocados 1 célula** (+10 m em X, −10 m em Y) em relação ao Vista SAGA, por causa da contagem a
partir de 1. Comparação pelo centro das células: `python3.12 scripts/comparar_vetor_plugin.py VS PLUGIN`.

| | Simples | Com Massa |
|---|---|---|
| plugin × Vista SAGA, bruto | 97,67% (112) | 82,82% (824) |
| plugin × modelo do próprio plugin nos pontos usados | 99,98% (1, empate exato) | **100%** |
| modelo do plugin × Vista SAGA, nos pontos do Vista SAGA | **100%** | **84,39% (749)** |

- **A cadeia do plugin está correta**: camada → SRC → vetor exato reproduz o modelo do plugin. No
  Simples, a única diferença é a célula 46:24, equidistante de B e C (empate na bissetriz).
- **Simples:** a diferença bruta (112 células) vem **só** do deslocamento dos pontos; com os pontos no
  lugar, 100%.
- **Com Massa:** a diferença vem do **modelo** (M/d no plugin × M/d² no Vista SAGA). Polo C (M = 1):
  512 células no Vista SAGA, 143 no plugin; Polo A (M = 9): 2.693 × 3.518.
- Observações menores: no Simples o campo `MASSA` sai 1 para todos (massa ignorada, mas pode confundir);
  o metadado QGIS embutido no GPKG de saída tem SRC vazio (o SRC da camada está certo).
- Para refazer o teste da 1.4.0: usar `pontos_qgis.csv` (centros 500115/8900455, 500595/8900105,
  500715/8900505), gerado nesta sessão.

## 17/11/2026 (noite) — validação caixa-preta do Voronoi contra o Vista SAGA

Comparação célula a célula (`python scripts/comparar_caso_atrito.py PASTA`) das quatro saídas do
Vista SAGA com o caso de teste. Arquivos recebidos: `voronoi_saga_{simples,massa,atrito,massa_atrito}.rs2`
(R4, R3, R1, R2) e `pontos_saga.txt`, este **idêntico byte a byte** ao `pontos_pixel.txt`.

**Confirmado:**

1. **Arquivo de pontos:** `Nome;Massa;X:Y`, sem cabeçalho, CRLF, `[ATRITOS]` com uma nota por classe a
   partir da classe 0; X:Y = **coluna:linha contadas a partir de 1** (12:15 caiu na célula 11:14
   contada a partir de 0, nos quatro resultados).
2. **Saída:** classe 0 "Ponto" marca as células dos polos; classes 1..n = polos, na ordem do arquivo.
3. **Simples:** distância euclidiana entre centros, 100% (0 divergências).
4. **Com Massa (sem atrito): max M/d², não M/d.** min d/√M acerta 100%; o expoente é nítido (k = 0,48
   ou 0,52 já dá 26 e 35 divergências). Coincide com a fórmula do manual, FZ = M/(D × A), em que
   A cresce com D. **O plugin 1.3 usa M/d e diverge em 749 células (84,4%)**, inclusive no vetor
   exato (discos de Apolônio com razão M; a correção é usar √M).
5. **Atrito:** Σ (distância do polo à célula × nota × √2 nos passos diagonais) / M, na reta polo →
   célula: 99,67% (sem massa) e 99,69% (com massa). Era a leitura do executável; agora validada pela
   saída. O "efeito √M" é a mesma propriedade do item 4, presente também sem atrito.
6. Plugin 1.3 (código real, notas 1, 1, 3, 5 como C, basal 1): Atrito 96,73% (157), Massa + Atrito
   98,37% (78).

**Resíduo:** 10 a 16 células, **todas na fronteira entre regiões**, com margem de custo ≤ 10%: detalhe
do traçado (raios até a borda, regra de sobreposição, variante da reta). Raios até a borda com "último
raio vence" dão 10 divergências no Massa + Atrito, mas foram escolhidos entre 32 variantes **no mesmo
caso**: é ajuste, não validação. Decidir entre variantes exige um segundo caso, independente.

**Não testado:** notas 0, classes excluídas, mapas com FUNDO dentro da área, polos na borda.

## 17/11/2026 (noite) — resultados do teste perdidos em sessão bloqueada

- O autor **já rodou o caso de teste no Vista SAGA** e enviou os RS2 de saída numa sessão que foi
  bloqueada antes de qualquer registro; nada chegou ao repositório. É o **segundo bloqueio** (o
  primeiro foi o de 16/11). Causa desconhecida.
- Medidas combinadas: registrar o contexto **no início** da sessão e logo após cada achado (não só
  no fim); validação **caixa-preta** (entrada → saída do Vista SAGA), sem nova análise do executável;
  os RS2 de saída não vão para o repositório (regra do `CLAUDE.md`); só o script de comparação e os
  números resumidos.
- **Reenviado** (`teste_voronoi_atrito_2.zip`). Respostas do autor:
  - funcionou o `pontos_pixel.txt`: coordenadas do arquivo de pontos em **coluna:linha**;
  - notas de atrito exibidas como 1, 1, 3, 5 (lidas corretamente);
  - a versão do Vista SAGA usada **não oferece** a escolha entre M/(d + a) e M/(d × a);
  - não testou atrito igual a 0.

## 17/11/2026 (tarde) — 1.3.0 fechada; caso de teste do atrito

- **1.3.0 fechada e mesclada** (merge `87406de` na `main`). Tag `v1.3.0` pendente (autor).
- **Branch da 1.4.0:** `feat/voronoi-atrito-fiel` ("atrito fiel ao Vista SAGA"). Versão do
  `metadata.txt` ainda 1.3.0: muda junto com a primeira alteração de código.
- **Caso de teste enviado ao autor** (`teste_voronoi_atrito.zip`), reproduzível com
  `python scripts/gerar_caso_atrito.py PASTA` (gera arquivos idênticos byte a byte):
  - `teste_atrito.rs2`: 80 × 60 células de 10 m; bordas X 500000–500800, Y 8900000–8900600;
    classes 0 FUNDO (ausente do mapa), 1 Atrito baixo, 2 Atrito médio, 3 Atrito alto;
    faixa vertical de atrito alto (colunas 30–39) com corredor de atrito baixo (linhas 25–34) e
    bloco alto (linhas 5–19, colunas 55–69);
  - pontos (coluna, linha, a partir de 0): Polo A M=9 (12, 15); Polo B M=4 (60, 50);
    Polo C M=1 (72, 10); notas `[ATRITOS]` 1, 1, 3, 5;
  - `pontos_pixel.txt` (X:Y = coluna:linha) e `pontos_utm.txt` (X:Y = centro da célula), porque
    a unidade das coordenadas não foi confirmada.
- **Roteiro pedido ao autor:** abrir o RS2 e conferir com `mapa_previa.png`; carregar
  `pontos_pixel.txt` (se falhar, `pontos_utm.txt`; anotar qual funcionou e qualquer deslocamento);
  conferir as notas; rodar e salvar R1 atrito sem massa, R2 atrito com massa, R3 sem atrito com
  massa, R4 simples; salvar o arquivo de pontos pelo Vista SAGA (`pontos_salvo.txt`).
- **Próximo passo:** com os quatro RS2 e o `pontos_salvo.txt`, comparar pixel a pixel com a
  simulação da leitura do executável e fixar o modelo da 1.4.0.

## 17/11/2026 — recuperação do contexto da sessão de 16/11 (noite)

A sessão de 16/11 que produziu a 1.3.0 foi interrompida por bloqueio automático antes de registrar
o contexto. O resumo abaixo foi reconstruído a partir do histórico dela.

### Estado da versão 1.3.0

- **Branch:** `feat/voronoi-saida-vetorial`; **PR:**
  [ezrandrade/Vista-Saga-Plugin#12](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/12),
  sem merge.
- **Build de teste:** `Vista_Saga_Plugin_QGIS4_v1.3.0-dev3.zip` = commit `9476819`.
  O autor testou no QGIS e aprovou ("Deu certo").
- Conteúdo: ver `geosaga/NOTAS_DA_VERSAO_130.md` e `geosaga/CHANGELOG.md`.
- **Decisão do autor (17/11):** fechar a 1.3.0 como está e tratar o atrito na 1.4.0.

### Achado de método: o modelo de atrito do Voronoi

Modelo atual do plugin (experimental desde a 0.7.5):

> escore = D × Σ(1 + atrito de cada célula atravessada) / M

Testes com atrito zero, na sessão de 16/11:

1. **O custo depende da direção.** Segmentos de mesmo comprimento custaram 10.100 (0°),
   13.100 (22,5°) e 7.200 (45°), porque a soma conta células, não comprimento percorrido. Também
   depende da resolução.
2. **No modo Com Massa e Atrito, as massas valem como √M.** Como Σ cresce com D, o escore fica
   proporcional a D²/M. Com massas 1 e 9 e atrito zero, a área do centro leve foi de 4.016
   células, contra 401 no Com Massa; o modelo com √M dá 4.420 (98,3% de coincidência).

**Fonte primária da fórmula:** manual do Vista SAGA (texto enviado pelo autor; não vai para o
repositório por direitos autorais), que define

> FZ(Gi) = M(Gi) / [ D(x→Gi) × A(x→Gi) ], com A = Σ Cₖ sobre as células da trajetória reta.

O manual chama o procedimento de "exploratório". O expoente 1 em M/d vem do manual.

**Análise estática dos programas originais** (sem executar e sem copiar código; só o método).
As conclusões são **leituras do executável, ainda não validadas** com um mapa gerado pelo
Vista SAGA:

| | VORONOI.EXE (ancestral, 16 bits) | Vista SAGA (integrado, 32 bits) |
|---|---|---|
| Fórmula | escolha: M/(d + a), padrão, ou M/(d × a) | sem escolha |
| Percurso | reta de cada célula até cada polo | raios de cada polo até as células da borda |
| Atrito | nota por classe, por trecho de classe constante | nota por classe, célula a célula no raio |
| Acúmulo | soma: (D + Σ notas)/M; produto: Σ(L × nota)/M | Σ (distância do polo à célula × nota × √2 nos passos diagonais) / M |
| Classes excluídas | não | sim (atravessadas, sem resultado) |

- No **Vista SAGA integrado**, a referência da tese, o efeito √M **também existe** (simulação:
  99,8% de coincidência com o modelo √M). Logo, é propriedade do método original, a ser declarada
  na tese, e não erro do plugin.
- Diferenças restantes entre o plugin e o Vista SAGA:
  1. peso do atrito: o Vista SAGA pondera a nota pela distância da célula ao polo; o plugin soma
     células com peso igual e multiplica por D;
  2. custo basal: o plugin usa 1 + C; o Vista SAGA usa a nota direto (padrão 1);
  3. percurso: raios até a borda com √2 nas diagonais × reta célula-polo;
  4. classes excluídas: só no Vista SAGA.
- Não confirmados: a rotina final que preenche células não alcançadas pelos raios; o efeito da
  caixa de atrito desmarcada (provavelmente nota 1 em todas as classes).

**Proposta registrada para a 1.4.0 ("atrito fiel ao Vista SAGA"):**

1. Implementar o modelo do Vista SAGA como padrão; manter o atual como "legado 1.3" para
   reproduzir resultados já gerados.
2. **Validação obrigatória:** o autor roda no Vista SAGA um caso pequeno (RS2 com 3 ou 4 classes,
   3 pontos, massas e notas diferentes) e envia o RS2 de saída para comparação pixel a pixel.
   Sem isso, o modelo "fiel" não é conferido e não serve para a tese.
3. Atrito vetorial depois, convertido em grade (o cálculo do Vista SAGA é célula a célula).
4. Registrar a justificativa escrita da mudança de método (exigência do `CLAUDE.md`).

### Formato do arquivo de pontos do Voronoi

Lido no executável do Vista SAGA integrado (não confirmado com arquivo salvo pelo programa):

```
Nome;Massa;X:Y
Nome;Massa;X:Y
[ATRITOS]
nota da classe 0
nota da classe 1
```

- sem cabeçalho e sem aspas; separador `;`; massa inteira (`StrToInt`);
- coordenada `X:Y`, aparentemente **coluna:linha da matriz**, não metros, apesar do rótulo
  "Coordenada UTM"; não se sabe se começa em 0 ou em 1;
- provável CP1252 e CRLF; separador decimal das notas não verificado.

O arquivo de pontos de exemplo do autor (formato do ancestral: cabeçalho, aspas, sete colunas)
mostrou uma grade implícita de células de 700 m, com a relação exata Leste = origem + 700 × X e
Norte = origem − 700 × Y. Datum e fuso não podem ser deduzidos das coordenadas (regra de SRC do
`CLAUDE.md`): o autor precisa confirmá-los.

### Pendências abertas

- [x] 1.3.0 fechada em 17/11/2026 e PR 12 mesclado a pedido do autor. Tag `v1.3.0` pendente:
      usar o commit de merge do PR 12 na `main` (o autor cria pelo Codespaces).
- [x] Caso de teste gerado e enviado (17/11).
- [ ] Autor roda o caso de teste no Vista SAGA e envia R1–R4 e `pontos_salvo.txt`.
- [ ] Autor responde: o Vista SAGA que usa tem a escolha entre M/(d + a) e M/(d × a)?
- [ ] Autor responde: faixa de valores de atrito usada (há notas 0?).
- [ ] Conversão do arquivo de pontos do autor para o formato do Vista SAGA integrado: interrompida
      pelo bloqueio; o autor precisa reenviar o arquivo.
- [ ] Decidir se o plugin deve ler e gravar o formato de pontos do Vista SAGA (útil para a
      validação cruzada).
- [ ] Definir por escrito o critério de "plugin finalizado" (escopo fechado), proposto pelo
      orientador em 17/11.
