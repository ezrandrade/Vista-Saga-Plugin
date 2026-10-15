## 1.0.1 — Correção de exceções silenciosas identificadas pelo Bandit

- Removidos dois `except Exception: pass` de `geosaga/rs2_dialog.py` na aplicação opcional de simbologia vetorial RS2 e GeoTIFF.
- Falhas de renderização agora são registradas como avisos no `QgsMessageLog` (canal Vista Saga Plugin), sem invalidar os arquivos exportados.
- A matemática dos módulos e os IDs históricos permanecem inalterados.

## 1.0.0 — Padronização final da interface pública

- Ordem do menu do QGIS e do painel: Assinatura, Monitoria, Avaliação, Análises Voronoi, Combinação de Mapas, Conversão de Formatos e Sequenciador de Mapas.
- Removido “Espacial” dos nomes públicos de Assinatura, Monitoria e Avaliação, inclusive títulos de janelas e tarefas; sem alterar IDs legados `geosaga:*`.
- Nenhuma alteração na matemática dos algoritmos e nos arquivos dos motores de análise.
- Sete módulos homologados funcionalmente no QGIS 4.2.2 para Windows; Linux/Flatpak e comparação numérica com o Vista SAGA/UFRJ continuam sem validação independente.

## 0.8.7 — Sequenciador de Mapas: raster, vetor e misto (candidata a homologação)

- Renomeado o módulo **Sequenciador de Imagens** para **Sequenciador de Mapas**.
- Três abas independentes: Raster (preservado), Vetorial (múltiplas camadas ou período em atributo) e Misto (raster sob vetor ou raster fixo com atributos temporais).
- Suporte a filtro temporal por período ou acumulação, preservando a camada original com materialização temporária e estilo copiado.
- Exportação em GIF com PNGs individuais opcionais, sem FFmpeg/Pillow em produção.
- Grade comum, cores/simbologia do QGIS, título/ano, legenda categórica limitada e prévia.
- Os motores de Voronoi, avaliação, monitoria, assinatura, conversão e combinação não foram modificados.
- Homologação gráfica no QGIS 4.2.2 Windows e Linux/Flatpak pendente.

## 0.8.6 — Otimização verificada e diagnóstico de desempenho

- Nas modalidades Com Atrito e Com Massa e Atrito, os trajetos são interrompidos antecipadamente quando o custo acumulado, que não pode diminuir, já ultrapassou o limite que permitiria vencer o melhor centro. Mantém empates, NoData, pesos de massa e interpretação das células.
- Relatório TXT e metadados GeoTIFF informam tempo do cálculo matricial, trajetórias avaliadas, trajetórias interrompidas durante o percurso, visitas a células e descarte prévio de pares centro–célula.
- Benchmarks sintéticos controlados e testes de equivalência com o procedimento exaustivo; ganhos de tempo não garantidos para todas as bases.
- Interface do Sequenciador de Imagens não alterada; mantida a necessidade de homologação gráfica no QGIS 4.2.2. `geosaga` permanece como identificador técnico. Não é versão 1.0 nem validação matemática com Vista SAGA/UFRJ.

## 0.8.5 — Restauração do nome público

- Nome público **Vista Saga Plugin** restaurado nos metadados, menu Raster, painel, diálogos e provedor Processing.
- Módulo **Análises Voronoi** e interfaces de atrito múltiplo mantidos.
- Sem alterações nos cálculos; pacote Python `geosaga` e IDs de algoritmos preservados.
- Teste funcional no QGIS 4.x permanece recomendado.

## 0.8.4 — Correção da interface de atrito múltiplo

- Seleção e edição das superfícies movidas para uma janela própria de tamanho adequado; acessível pelo botão **Selecionar e configurar superfícies…**.
- Ao marcar o modo de atrito múltiplo, a janela de seleção se abre automaticamente na primeira utilização.
- Inclusão múltipla de rasters do projeto ou arquivos GeoTIFF, remoção múltipla, pesos e notas por classe editáveis em tabela.
- Janela principal com rolagem e resumo da quantidade de superfícies configuradas.
- Motores matemáticos e saídas dos demais módulos preservados.
- Teste gráfico Qt6/QGIS 4.x ainda necessário.

## 0.8.3 — Padronização e superfícies múltiplas (experimental)
- Nome público: VistaSagaPlugin. Módulo: Análises Voronoi.
- No Voronoi com atrito, combinação de até 12 superfícies com pesos e notas por categoria, validando SRC e grade; NoData vira barreira.
- Relatório TXT e metadados raster registram composição, pesos e fórmula. Sem mudança dos algoritmos de avaliação raster/vetorial e das modalidades de Voronoi simples/massa.
- `geosaga` (diretório e IDs Processing) preservado para compatibilidade.
- Métodos com atrito seguem experimentais até comparação quantitativa com Vista SAGA/UFRJ.

## 0.8.2 — Correção de progresso Voronoi no Qt6

- `QgsTask.progressChanged` agora chega a um `@pyqtSlot(float)` na thread da interface,
  que converte e limita os valores para `int` antes de chamar `QProgressDialog.setValue`.
- Ignora notificações de progresso pendentes após o término/cancelamento.
- Nenhuma alteração nos motores de cálculo das quatro modalidades de Voronoi,
  nos cinco módulos anteriores ou no Sequenciador de Imagens.
- O Voronoi com Atrito e com Massa e Atrito continuam experimentais.

## 0.8.0 — Sequenciador de Imagens (GIF) — candidata de homologação

- Sétimo módulo acessível no Painel e no menu Raster: sequenciamento de mapas georreferenciados em GIF animado.
- Exportação sem dependências de FFmpeg/Pillow, prévia Qt, ordenação dos mapas, datas, extensão e SRC comuns, simbologia dos rasters, legendas opcionais.
- Código GIF com preservação exata das cores quando a sequência usa <=256 cores; quantização 3-3-2 em demais casos.
- Mantida a quarta modalidade de Voronoi com Massa e Atrito introduzida na 0.7.5, experimental e aguardando validação contra o software original.
- Sem mudanças intencionais nos algoritmos de Avaliação, Monitoria, Assinatura, Combinação e Conversão.

## 0.7.5 — Voronoi com Massa e Atrito (experimental)

- Quarta modalidade integrada; campo de massa e superfície de atrito habilitados em conjunto.
- Ponderação do índice de atrito acumulado por massa positiva, em tarefa do QGIS.
- Corrigida variável de referência não inicializada em saída permanente da modalidade de atrito.
- 273 testes automatizados; falta homologação com PyQGIS/Qt6 e comparação numérica ao Vista SAGA original.

## 0.7.4 — Voronoi com Atrito (experimental)

- Novo processamento em grade de atrito ao longo de segmentos retos (DDA), custo basal explícito, NoData como barreira, raster/GeoPackage e relatórios.
- Seleção do raster de atrito na interface, herança de extensão, resolução e SRC.
- Modelo limitado em custo computacional; não reivindica equivalência com o executável original até validação comparativa.
- Mantidas as rotinas anteriores, inclusive tarefas assíncronas QgsTask.

# 0.7.2 — Otimização e correção do Voronoi raster

- Remove o bloqueio artificial de 300 milhões de comparações.
- Processa em janelas de aproximadamente 200 mil pixels.
- Aceleração espacial opcional (SciPy cKDTree) no Voronoi Simples, com fallback NumPy.
- Mantém todas as funcionalidades 0.7.1; atrito permanece futuro.

## 0.7.1 — Voronoi (ajuste de fluxo)

Voronoi Simples não exige massa nem raster de referência. Permite extensão pelo mapa, por camada poligonal, manual ou pontos + margem. Saída GeoPackage vetorial direta, sem rasterização; saída GeoTIFF e poligonização continuam disponíveis. Voronoi com Massa permanece raster nesta etapa. Os modos com atrito continuam reservados.

## 0.7.0 — Voronoi Espacial (etapa I)

- Novo cartão e menu Voronoi Espacial no painel.
- Cálculo simples e ponderado por massa (maior M/d), com grade raster e GeoPackage opcional.
- Campo de massa, pontos geradores, raster de referência opcional e saídas temporárias.
- Relatórios quantitativos TXT/CSV e legenda categorizada.
- Atrito e massa+atrito explicitamente reservados a 0.7.1 / 0.7.2.
- Equivalência matemática com o Vista SAGA original ainda NÃO certificada por mapas de referência.
- Preserva motores de avaliação, monitoria, assinatura, combinação e conversão.

## 0.6.5 — Padronização visual das abas da Assinatura Espacial

- `QTabBar.setExpanding(False)` aplicado exclusivamente às abas Raster e Vetorial da Assinatura Espacial; agora permanecem compactas e alinhadas à esquerda, como nos demais módulos.
- Formulários, indicadores, algoritmos, relatórios, conversões e demais janelas permanecem iguais aos da 0.6.4.
- Registrado teste automatizado de regressão para a apresentação compacta das abas.
- Correção de código verificada localmente; a inspeção gráfica final deve ser feita no QGIS 4.x.

## 0.6.4 — Correção pontual do erro de interface

- Removida a importação local redundante de `QPushButton` em `VectorOverlayEvaluationDialog._build()`, que provocava `UnboundLocalError` ao abrir a aba de sobreposição.
- Mantidas a interface e as rotinas de cálculo da versão 0.6.3.
- Incluído teste de regressão estática para detectar retorno do mesmo erro.

## 0.6.3 — Correção de abas e painel

- Formulários vetoriais de Avaliação e Monitoria corrigidos como QWidget embutidos em QScrollArea.
- Diagnóstico de falhas de montagem exibido no formulário e no log do QGIS.
- Descrições dos cinco cartões restauradas; informação de autoria, filiação IGDEMA/UFAL e independência no rodapé.
- Motores de cálculo preservados.

## 0.6.2 — Usabilidade e coerência das abas

- A **Avaliação Espacial** passa a mostrar os controles completos de atributos e sobreposição nas próprias abas. A lógica de pesos, categorias, notas, exclusões, relatórios e saídas vetoriais é a mesma da 0.6.1.
- A **Monitoria Espacial** mostra os dois períodos vetoriais, campos de classes e legendas, execução e destino diretamente na aba Vetorial; os resultados raster/vetorial são acessíveis na aba Resultados. Os motores raster e vetorial são preservados.
- O painel de módulos agora tem **cinco cartões iguais**: Avaliação, Monitoria, Assinatura, Combinação e Conversão. O texto exibido abaixo do título passa a ser apenas: “Escolha um módulo para começar. Uma nova janela será aberta para cada módulo.”
- **Assinatura Espacial** e **Combinação de Mapas** não sofreram alterações em suas interfaces ou cálculos.
- Os formulários vetoriais são criados somente quando a aba respectiva for selecionada; não há instanciação de processamento adicional ao abrir o painel.
- Testes automatizados de núcleo e verificações estruturais não substituem testes de uso da interface real em QGIS 4.x.

## 0.6.1

- Abas Raster/Vetorial, seleção múltipla e saídas temporárias; veja INTERFACE_SAIDAS_TEMPORARIAS_061.md.
- Núcleos analíticos da versão 0.6.0 preservados.

## 0.6.0 — Combinação de Mapas

- Novo módulo com interface gráfica e acesso pelo painel e menu Raster.
- Combinação categórica raster por tuplas, GeoTIFF Int32, CSV e TXT, sem pesos ou notas.
- Combinação vetorial por interseção de duas ou mais camadas poligonais, com GeoPackage, atributos e áreas.
- Legendas de combinação recuperáveis na conversão do GeoTIFF combinado em vetores.
- Validação de origem, SRC, alinhamento, NoData, conflitos geométricos e substituição de saídas.
- Módulos da versão 0.5.2 preservados. Consulte COMBINACAO_MAPAS_060.md.

## 0.5.2 — Padronização de interfaces e terminologia

- Painel preservado com Avaliação Espacial, Monitoria Espacial e Assinatura Espacial.
- Botão **Fechar** na avaliação raster, avaliação vetorial por atributos, avaliação por sobreposição e monitoria raster; fechamento bloqueado enquanto houver tarefa em execução.
- Os botões de fechar do Conversor, Assinatura e Monitoria vetorial permanecem como na versão anterior.
- Títulos de relatórios TXT atualizados para terminologia espacial, mantendo estrutura e campos de saída.
- Identificadores de algoritmos `geosaga:*`, estrutura dos projetos e cálculos não sofreram alterações.

## 0.5.1 — Assinatura vetorial: tratamento de sobreposições

- Polígonos temáticos da mesma categoria são dissolvidos dentro de cada área de análise; não duplicam área.
- Interseções reais entre classes diferentes podem ser excluídas da distribuição (padrão) ou impedir a análise (modo estrito, escolhido no formulário). Nunca existe atribuição arbitrária de uma área a duas classes.
- O CSV e o TXT incluem área em conflito (ha) e porcentagem sobre a área de análise; o GeoPackage recebe `AREA_CONF_HA` e `PCT_CONF`.
- Os percentuais por classe mantêm como denominador somente a área validamente atribuída a uma classe. Interseções conflitantes não entram nesse denominador.
- Raster, Avaliação Espacial, Monitoria, conversor e as saídas anteriormente homologadas permanecem inalterados.
- Teste funcional com PyQGIS/GDAL no QGIS 4.x permanece necessário.

## 0.5.0 — Assinatura Ambiental interativa

- Interface própria no painel de módulos e no menu Raster; menus Processing da Assinatura retirados do fluxo operacional, com `geosaga:assinatura` mantido no provedor para compatibilidade.
- Assinatura de raster categórico monobanda dentro de cada área poligonal, por centro de pixel, com exclusão de NoData e nomes do raster quando conhecidos.
- Assinatura de polígonos temáticos por interseção exata com áreas de análise. Recusa sobreposição geométrica dos polígonos temáticos na mesma área para evitar duplicidade de superfície.
- Relatórios UTF-8 CSV/TXT de classes e percentuais por área, com GeoPackage de polígonos contendo área total, área temática coberta, cobertura percentual, número de classes e classe predominante.
- Validação de SRC e geometrias, progressão, cancelamento e publicação coordenada dos três arquivos.
- **Limite:** em raster geográfico não estima hectares dos pixels; usa contagens e percentuais. Os vetores usam cálculo elipsoidal ou unidades projetadas.
- Base: versão 0.4.3 homologada, sem alteração dos motores anteriores.

## 0.4.3 — Monitoria vetorial direta

- Comparação entre duas camadas poligonais por `native:intersection`, sem rasterizar.
- Interface compacta acessível pela Configuração da Monitoria, com campos
  de classes e de legendas para os dois períodos.
- GeoPackage com transições categóricas, campos descritivos e áreas m²/ha/%.
- CSV de transições, matriz em hectares e relatório TXT com ressalvas metodológicas.
- Mantidos o painel e todos os procedimentos raster da versão 0.4.2.

## 0.4.2 — Monitoria compacta e atributos vetoriais

- Janela da Monitoria com abas Configuração/Resultados e opções avançadas inicialmente recolhidas.
- Mapa de transições inclui metadados de legenda, quando pequenos o suficiente; o CSV associado é lido na vetorização.
- GeoTIFF → Vetor: transferência de classes inicial/final, situação, legendas de mudança e permanência; campos AREA_M2, AREA_HA e PCT_AREA.
- Simbologia categorizada na abertura do vetor exportado.
- Mantidos os cálculos de monitoria raster, suas matrizes e o teste MK.
- Monitoria diretamente entre vetores fica em avaliação para versão futura.

## 0.4.1 — Legendas descritivas e tendências temporais

- Legendas `Permaneceu` e `Deixou de ser ... | Tornou-se ...` no QGIS e no CSV/TXT; opção de códigos mantida.
- Importação opcional de nomes de classes por tabela CSV distinta para períodos inicial e final.
- Seleção opcional de mapas adicionais por ano; séries de 5 ou mais datas geram estatísticas Mann–Kendall por porcentagem de ocupação, inclinação de Sen e correção FDR BH; com 2 datas, informa claramente `NAO_APLICAVEL` e não gera p fictício.
- Saída adicional `_tendencias_mk.csv`, proteção do conjunto de arquivos, tolerância a deslocamento inferior a 0,000005 pixel.
- Avaliação Espacial, Conversor e Assinatura sem alterações.

## 0.4.0 — Monitoria Ambiental interativa

- Painel e menu abrem a janela de Monitoria sem exigir Processing. Algoritmo `geosaga:monitoria` continua registrado para projetos existentes.
- Seleção de dois rasters categóricos locais, carregados no QGIS ou por caminho; rótulos dos períodos e título do estudo.
- Verificação de dimensões, geotransformação e SRC; máscaras NoData e NaN; sem reprojeção ou reamostragem implícita.
- Mapa GeoTIFF categórico de transições (IDs estáveis), matriz de contingência CSV, CSV detalhado e resumo TXT.
- Cálculos de pixels/percentuais por transição e permanência/mudança; área em ha apenas quando o SRC é projetado e as unidades são conhecidas.
- Execução por QgsTask, indicador de progresso e cancelamento; resultados anteriores preservados caso haja falha.
- Sem alterações nos módulos de Avaliação Espacial, conversor, Assinatura, nem nas bibliotecas legadas.

## 0.3.12 — Relatórios de Avaliação Espacial e áreas (14/10/2026)

- Novo relatório de combinações por nota final em TXT e CSV, seguindo a organização do exemplo histórico do Vista SAGA fornecido pelo usuário.
- Para raster: registro das combinações de classes durante a própria avaliação, sem releitura; contagens de pixels, notas, pesos, produtos, percentuais, áreas quando SRC projetado e metragem linear conhecida; área em hectares não é inventada para graus geográficos.
- A classificação da nota final nos relatórios usa arredondamento half-up; o GeoTIFF mantém notas ponderadas decimais sem alteração.
- Para vetores por atributos e por sobreposição: novos campos AREA_M2, AREA_HA e PCT_AREA, além dos campos de nota e auditoria; relatórios de combinações e áreas por classe final.
- SRC geográfico em vetores: área elipsoidal com QgsDistanceArea; CRS projetado: área planar convertida para m² pelas unidades lineares WKT.
- Relatórios TXT/CSV opcionais, habilitados por padrão; publicação coordenada dos três arquivos vetoriais com possibilidade de restauração em falhas.
- Demais operações do conversor RS2/GeoTIFF/Vetor e módulos Monitoria/Assinatura preservados.
- A interface e a gravação espacial reais requerem homologação em QGIS 4.x no Windows e Linux/Flatpak.

## 0.3.10
- Avaliação Espacial vetorial por atributos em camada poligonal com pesos, notas, exclusões e GeoPackage; campo de pontuação e notas individuais.
- Acesso pela interface Avaliação Espacial; painel de módulos e núcleo raster preservados.
- Teste unitário independente do QGIS e teste integrado para executar no QGIS 4.x.
- Sobrescrita protegida por geração temporária; projeto de regras vetoriais e sobreposição espacial ficam para a próxima etapa.

## 0.3.9 — Vetorização de rasters contínuos (14/10/2026)

- GeoTIFF Float32/Float64 de Avaliação Espacial aceito em GeoTIFF → Vetor.
- Divisão do intervalo de valores em 2 a 20 classes de igual amplitude (5 padrão), configuráveis nas opções avançadas.
- Geração dos atributos `CODIGO`, `CLASSE`, `COR_HEX`, `VALOR_MIN` e `VALOR_MAX` para resultados contínuos.
- NoData, NaN e infinito omitidos; valor 0 permanece quando válido. GeoTIFF original não modificado.
- Demais rotinas e módulos preservados; vetorização testável no QGIS 4.x.

# 0.3.8 — Rasterização de vetores

- Quinta operação **Vetor → GeoTIFF** no mesmo conversor, sem substituir os quatro modos anteriores.
- Arquivos vetoriais locais em GPKG, SHP, GeoJSON e FGB; seleção de camadas carregadas no QGIS.
- Campo de entrada e tamanho do pixel configuráveis; preservação do SRC projetado original.
- Campos inteiros/decimais preservados; campos de texto codificados como classes.
- Legendas e cores HEX dos atributos são incorporadas quando disponíveis; fundo categórico = 0.
- Configuração avançada ALL_TOUCHED, progresso/cancelamento, publicação transacional e carregamento da saída.
- Testes unitários e script de integração QGIS acrescentados; homologação no QGIS ainda necessária.

# 0.3.7 — Consolidação funcional e Avaliação Espacial

- Versão 0.3.6 homologada e adotada como base funcional para o projeto.
- Painel de módulos confirmado como componente permanente até a versão 1.0.
- Nomenclatura do módulo alterada para **Avaliação Espacial**, mantendo o cálculo raster intacto.
- Acesso redundante de Avaliação pelo Processing removido do menu Raster;
  o algoritmo registrado `geosaga:avaliacao` permanece disponível para retrocompatibilidade.
- Preservados os projetos `.geosaga.json` e os IDs internos dos algoritmos.
- Modalidade vetorial avaliada tecnicamente e documentada; não implementada nesta versão.
- Nenhuma modificação na rotina RS2 ↔ GeoTIFF nem nas vetorizacões RS2/TIFF.

# 0.3.6 — GeoTIFF → Vetor (inclusão pontual)

- Quarta operação no conversor: GeoTIFF → polígonos em GPKG, SHP, GeoJSON e FlatGeobuf.
- GeoTIFF monobanda categórico: preserva o código inteiro dos pixels, legendas/paleta ou metadados `.tif.rs2.json`, SRC e geometria.
- TIFF RGB/RGBA classificado: códigos criados por cor HEX (não são códigos históricos), com limites de cores; evita interpretar a banda vermelha como classe.
- Reutiliza opções vetoriais existentes (FUNDO, 4/8 vizinhos, seleção de camadas QGIS, lote, progresso, sobrescrita segura).
- Demais módulos e funções da 0.3.5 preservados sem mudança em seu processamento.
- Regressões e teste de integração QGIS adicionais; validação na instalação real do QGIS 4.x ainda necessária.

# 0.3.5 — Interface reorganizada e vetorização RS2

- Layout próximo às ferramentas Processing do QGIS: Operação, Entrada, Saída, sistema de referência e opções avançadas recolhíveis.
- RS2 → GPKG, SHP, GeoJSON e FlatGeobuf via GDAL/OGR Polygonize, com campos CODIGO, CLASSE e COR_HEX.
- Processamento em lote para conversões vetoriais, com máscara opcional para FUNDO e 4/8 vizinhos.
- Backup/restauração da família de arquivos vetoriais ao substituir saídas; evita sobrescrever camadas abertas no projeto.
- Preserve integralmente o núcleo RS2 ↔ GeoTIFF homologado na 0.3.4.
- Teste adicional de integração no próprio QGIS e documentação RS2_VETORIZACAO.md.

## 0.3.4 — Interoperabilidade, SRC nativo e conversão em lote

- Seletor `QgsProjectionSelectionWidget` com opção SRC não definido.
- TIFFs locais carregados no projeto podem ser escolhidos via `QgsMapLayerComboBox`.
- Conversão em lote: mesmas dimensões/resolução, aviso para grades deslocadas.
- Substituição transacional de TIFF, JSON, XML, TFW/TIFW e preservação de metadados externos.
- Atualização de documentação após confirmação externa de RS2 no Vista SAGA.
- Testes de segurança e regressão.

## 0.3.3 — Entrada detectada automaticamente e RGB sem referência

- Corrigido encaminhamento de entrada `.rs2` ao GDAL (quando modo TIFF → RS2
  permanecia selecionado); direção agora deriva da extensão da entrada.
- RS2 → GeoTIFF e GeoTIFF categórico → RS2 sem arquivos de referência.
- TIFF RGB também pode ser convertido sem RS2 auxiliar, mas os códigos são
  NOVOS e criados a partir das cores, sem herdar semântica dos mapas antigos.
- TIFF sem coordenadas: opção de inserir extensão manual comprovada.
- Evita reaproveitamento silencioso de referências antigas entre mapas.
- Cinco testes adicionais de lógica/mapeamento/validação (34 ao todo);
  cinco ida-e-voltas categóricas RS2 → TIFF → RS2 idênticas byte a byte;
  quatro TIFFs RGB legados importados sem referência mediante extensão manual.
- Nenhuma alteração na matemática dos módulos ambientais.

## 0.3.2 — Compatibilidade TIFF RGB → RS2

- Recuperação por correspondência exata das cores RGB/RGBA para códigos categóricos,
  usando um RS2 original fornecido explicitamente como referência.
- Tratamento seguro de TIFF sem georreferenciamento a partir de grade/legenda do RS2
  correspondente; validação de dimensão e georreferenciamento divergentes.
- Proteção contra paletas ambíguas, cores desconhecidas e substituição do RS2 de referência.
- Sugestões de nomes de saída que preservam arquivos originais.
- Quatro testes reais de ida e volta RGB → RS2 idênticos byte a byte;
  seis novos testes unitários de mapeamento RGB.
- Nenhuma alteração nas rotinas matemáticas dos três módulos ambientais.

## 0.3.1 — RS2 e GeoTIFF categórico

- Leitura integral da variante RS2 observada em cinco mapas de referência,
  com RLE, coordenadas, legendas CP1252 e paleta RGB.
- Conversão para GeoTIFF de banda única, com opção de atribuir EPSG
  confirmado pelo usuário; não atribui zona/datum sem evidência.
- Escrita RS2 experimental de rasters categóricos de banda única.
- Diálogo integrado ao menu Raster e ao painel inicial.
- Testes de regressão para leitor/gravador; documentação de limitações.
- Manutenção integral dos três módulos ambientais da versão 0.3.0.

# Histórico do Vista Saga Plugin

## 0.3.0 — primeira etapa da continuidade incremental

- Nome comercial alterado de GeoSAGA Ambiental para Vista Saga Plugin.
- Preservada a pasta interna `geosaga` e todos os IDs do Processing para permitir atualização em lugar e compatibilidade com projetos de avaliação v0.2.
- Implementado painel de entrada para Avaliação, Monitoria e Assinatura.
- Corrigida importação de `QAction` exigida pelo Qt6.
- Mantido editor existente de Avaliação; Monitoria e Assinatura permanecem no Processing.
- Adicionados testes NumPy/unittest e conferência de registro de algoritmos no QGIS.
- Sem alterações nas fórmulas matemáticas de cálculo do núcleo v0.2.0.

## 0.2.0 — base preservada

- Editor visual de pesos, notas e categorias de Avaliação Ambiental.
- Projetos `.geosaga.json`, resultado GeoTIFF e relatório CSV.
- Algoritmos experimentais de Monitoria e Assinatura Ambiental.

## 0.3.11 — Avaliação Espacial por sobreposição vetorial

- Permite empilhar duas ou mais camadas poligonais independentes na interface gráfica.
- Campo categórico, notas por classe e peso próprios para cada camada.
- Interseção geométrica sucessiva das camadas, validações e resultado em GeoPackage.
- Preserva inteiramente a modalidade por atributos, a avaliação raster, o painel e as cinco operações de conversão.
- Inclui testes de planejamento e um teste funcional sintético para executar no QGIS.
