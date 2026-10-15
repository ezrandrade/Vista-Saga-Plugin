# Vista Saga Plugin — QGIS 4.x

Nome público e identidade do projeto: **Vista Saga Plugin**. As antigas referências a GeoSAGA Ambiental designam versões históricas de origem. A pasta interna Python `geosaga` e os identificadores `geosaga:*` são preservados intencionalmente para permitir atualização sobre o plugin existente e manter projetos/modelos antigos. **Não instale uma segunda cópia em outra pasta**.

## Atualização 0.8.6 — Desempenho e verificações

Os modos de atrito preservam a combinação de múltiplas superfícies e usam um limite de custo acumulado para interromper trajetórias que não podem vencer a atribuição atual. A otimização é exata sob o modelo adotado (custos `1+C_k` não negativos) e está coberta por testes contra a referência exaustiva. Os resultados podem ser mais rápidos, mas dependem do raster, da resolução e dos centros. O TXT informa o esforço computacional e o tempo do cálculo matricial. **O Sequenciador de Mapas 0.8.7 (Raster, Vetorial e Misto) requer homologação gráfica no QGIS 4.x.** Consulte `SEQUENCIADOR_087.md`.

## Atualização 0.8.5 — Nome público

O nome exibido do complemento volta a ser **Vista Saga Plugin**. O módulo mantém o título **Análises Voronoi**. A pasta interna Python `geosaga`, os identificadores do Processing e os algoritmos anteriores não mudaram.

## Atualização 0.8.4 — Seleção de atrito múltiplo

Em **Análises Voronoi**, selecione **Com Atrito** ou **Com Massa e Atrito** e marque **Combinar múltiplas superfícies**. Uma janela será aberta para adicionar rasters do QGIS ou arquivos GeoTIFF. Os pesos e as notas por classe podem ser editados com duplo clique na tabela. Use **Fechar** para retornar. Também existe um botão permanente de edição na seção **Superfícies integradas**.

## Atualização 0.8.3 — Análises Voronoi

Quatro modalidades: Simples, com Massa, com Atrito e com Massa e Atrito. As duas que utilizam atrito são experimentais, embora tenham funcionado nos testes informados pelo usuário. A equivalência numérica com Vista SAGA/UFRJ permanece pendente.

Para atrito, selecione **superfície única** ou marque **Combinar múltiplas superfícies de atrito**. No modo múltiplo, adicione de 1 a 12 rasters do projeto em uma só seleção; edite o peso positivo de cada camada e, opcionalmente, as notas por classe no formato `1=2;2=8`. Deixe vazio para usar valores de resistência já padronizados na camada. Todos os rasters precisam ter mesmo SRC, grade, resolução e extensão. NoData em qualquer camada invalida a célula. Não são feitos reprojeção ou reamostragem automáticos. Os pesos são normalizados pela soma e as resistências são combinadas por média ponderada. O modelo ao longo dos segmentos retos permanece `D * soma(1 + atrito_integrado)` ou `D * soma(1 + atrito_integrado) / massa`.

CUIDADO: antes de ponderar, padronize os fatores para uma escala comum de resistência, com valores mais altos representando maior dificuldade. Para um raster contínuo, o campo de notas deve ficar vazio somente se os valores já estiverem adequadamente padronizados. Para um raster categórico, informe as notas de **todas** as categorias válidas. Códigos sem nota geram erro para evitar interpretações indevidas.

Os metadados do GeoTIFF e o TXT informam a composição de atrito. Os tempos podem variar fortemente de acordo com a eficácia da poda de centros; a aceleração observada com massa não é garantida em todas as bases. Em mapas grandes, comece por um recorte.

## Novidades da versão 0.8.0 (candidata a homologação)

- Voronoi Espacial: quatro modalidades (Simples, Massa, Atrito experimental e Massa + Atrito experimental).
- Sequenciador de Mapas: raster/vetor/misto com GIF e PNGs opcionais, incluindo atributo temporal (`SEQUENCIADOR_087.md`).
- Conversão, Avaliação, Monitoria, Assinatura e Combinação preservadas.

**Atenção:** as modalidades com atrito ainda não foram comparadas numericamente com os resultados do Vista SAGA/UFRJ e o sequenciador requer teste gráfico no QGIS 4.x. Não declarar equivalência científica ou homologação definitiva antes dessa validação.

## Versão 0.7.0 — Voronoi Espacial (etapa I)

O painel de módulos inclui **Voronoi Espacial**, com quatro modalidades previstas.
Nesta versão as modalidades **Simples** e **Com Massa** estão operacionais;
**Com Atrito** e **Com Massa e Atrito** aparecem desabilitadas, respectivamente
previstas para as versões 0.7.1 e 0.7.2. O modelo de massa utiliza M/d;
equivalência com a rotina original depende de testes comparativos.

Selecione uma camada vetorial de pontos do QGIS. No modelo Com Massa, indique
um campo numérico positivo. Opcionalmente selecione um raster de referência
para a grade de saída; sem referência, informe resolução em unidades do SRC.
As análises exigem CRS projetado. Serão gerados GeoTIFF de identificação dos
centros, relatórios TXT/CSV e GeoPackage de polígonos, se solicitado.
Resultados temporários são adicionados ao QGIS, mas precisam ser salvos para
persistir além da sessão. Consulte `VORONOI_070.md` e teste a instalação com
`from geosaga.tests.integration_voronoi_qgis import run; run()`.

> Versão 0.6.5: padronização visual das abas Raster/Vetorial da Assinatura Espacial; demais funcionalidades preservadas.

## Atualização 0.6.1 — ergonomia e saídas temporárias

As interfaces dos módulos oferecem navegação Raster/Vetorial, seleção múltipla
onde a metodologia admite empilhamento e resultados temporários carregados
no projeto QGIS. O resultado temporário pode ser exportado pela opção nativa
do QGIS; relatórios em TXT/CSV também são gravados junto ao arquivo temporário.
Consulte `INTERFACE_SAIDAS_TEMPORARIAS_061.md` antes de fechar o QGIS.

> Versão 0.5.2: módulos Avaliação Espacial, Monitoria Espacial e Assinatura Espacial; botão Fechar padronizado nas interfaces.

## Assinatura Espacial 0.5.0

Abra o Painel de módulos → Assinatura Espacial. Escolha GeoTIFF categórico monobanda ou mapa vetorial de polígonos, e informe os polígonos das áreas de análise. Para mapas vetoriais, selecione um campo de classificação e, se houver, outro com a legenda. É possível selecionar camadas do projeto ou arquivos locais.

Escolha o CSV de saída. O plugin criará no mesmo diretório: `exemplo.csv` (uma linha por classe e área), `exemplo_resumo.txt` (relatório legível com os totais e percentuais) e `exemplo_areas.gpkg` (geometrias das áreas de análise com `AREA_AOI_HA`, `AREA_ANAL_HA`, `COBERT_PCT`, `CLASSES_N`, `PREDOMINA`). As fontes não são modificadas.

Em raster, contabiliza pixels cujo centro está no polígono. Ignora NoData. Caso o raster não possua SRC projetado com unidade linear válida, não calcula hectares por pixel. Em vetor, computa interseções exatas e reprojeta temporariamente os polígonos de análise para o SRC do mapa temático; geometrias temáticas sobrepostas são rejeitadas para não duplicar áreas. Os percentuais usam como denominador a área temática válida dentro de cada polígono, não o polígono completo. Polígonos de análise sobrepostos têm relatórios independentes.

A assinatura histórica no Processing continua acessível pelo ID `geosaga:assinatura` para automações existentes.

### Versão 0.4.3 — Monitoria vetorial direta

Agora, em **Monitoria Espacial → Configuração → Abrir Monitoria vetorial…**, é
possível comparar diretamente dois mapas poligonais com campo categórico,
produzindo GeoPackage, matriz de áreas em hectares, CSV de transições e TXT.
A Monitoria raster da 0.4.2 é preservada. Consulte
[`MONITORIA_VETORIAL_043.md`](MONITORIA_VETORIAL_043.md) para uso e limitações.

> **Monitoria 0.4.2:** interface mais compacta em abas. Ao vetorizar o GeoTIFF da Monitoria, o conversor recupera as legendas de transição a partir do CSV associado ou dos metadados embutidos, quando disponíveis, e acrescenta campos de área. Consulte `MONITORIA_042.md`.

# Vista Saga Plugin — Monitoria Espacial 0.4.1

Nova opção de legendas descritivas e análise temporal de classes com Mann–Kendall mediante série de pelo menos cinco datas. Para dois mapas, apresenta apenas a análise descritiva; teste MK marcado como não aplicável. Consulte `MONITORIA_041.md` para exemplos e ressalvas.

---

# Vista Saga Plugin — Monitoria Espacial 0.4.0

A partir da versão 0.4.0, **Painel de módulos → Monitoria Espacial** abre uma interface gráfica própria. Selecione dois mapas categóricos (inicial/final) e indique a saída `.tif`. O programa cria automaticamente:

- `monitoria.tif` — mapa de transições de classes. Cada pixel contém o `ID_TRANS` da tabela; NoData é -9999.
- `monitoria_transicoes.csv` — classe inicial, classe final, situação, pixels, percentual da área avaliada e hectares quando disponíveis.
- `monitoria_matriz.csv` — tabela cruzada (linhas = classes iniciais; colunas = finais), em quantidade de pixels.
- `monitoria_resumo.txt` — síntese de permanências, mudanças e exclusões NoData.

**Condições:** dois rasters locais monobanda com mesmo SRC, extensão, grade e resolução; mapas RS2 devem antes ser convertidos no módulo Conversão de formatos. Não há alinhamento automático, reclassificação, reprojeção ou cálculo de área em hectares para coordenadas geográficas. Percentuais usam somente pixels válidos em ambos os períodos. A classe 0 é legítima quando não estiver marcada como NoData. A matriz segue os códigos reais; o GeoTIFF de transições guarda IDs correspondentes à tabela, não os códigos originais.

**Homologação:** executar o teste do Console Python do QGIS `from geosaga.tests.integration_monitoring_qgis import run; run()`; conferir uma matriz pequena manualmente e testar dados reais no Windows e no Linux/Flatpak. O algoritmo histórico `geosaga:monitoria` permanece registrado para compatibilidade, mas não é mais a interface principal.

---

# Vista Saga Plugin 0.3.10 — Avaliação Espacial vetorial (homologação)

Nova modalidade de avaliação vetorial **por atributos de uma camada poligonal**, acessível da janela Avaliação Espacial, com saída GeoPackage e testes matemáticos. **Todos os cinco conversores da versão 0.3.9 e a avaliação raster permanecem inalterados.** Veja `AVALIACAO_VETORIAL_GUIA.md`.

---

# Vista Saga Plugin 0.3.8 — QGIS 4.x

## Inclusão pontual: Vetor → GeoTIFF

Quinta operação do conversor: rasterizar camada vetorial local por campo de
atributos, definindo resolução e utilizando o SRC projetado existente. Arquivos
GPKG (inclusive seleção de camada), SHP, GeoJSON e FGB são aceitos. Campos
numéricos preservam valores; campos textuais recebem códigos categóricos e
legendas; `CODIGO`/`CLASSE`/`COR_HEX` podem reconstruir a categorização.
Opções avançadas incluem `ALL_TOUCHED`. A seleção de vetor carregado no projeto
está disponível. Veja `INSTRUCOES_VETOR_TIFF.md`.

As quatro operações anteriores, a Avaliação Espacial e o painel permanecem
inalterados. O lote da nova quinta operação ainda não é oferecido; os lotes
das demais operações continuam disponíveis.

---

# Histórico: Vista Saga Plugin 0.3.7 — QGIS 4.x

## Marco de consolidação: Avaliação Espacial e painel permanente

Esta versão consolida a 0.3.6 homologada pelo usuário. O painel de módulos é
uma interface permanente. O módulo anteriormente denominado **Avaliação Ambiental**
passa a ser **Avaliação Espacial**, pois os pesos e notas são aplicáveis também
a contextos sociais, territoriais e locacionais. Não houve alteração no cálculo
raster, no conversor ou nos demais módulos.

A Avaliação Espacial é aberta diretamente pela interface gráfica, sem atalho
redundante de Processing no menu Raster. O algoritmo `geosaga:avaliacao` segue
registrado para compatibilidade retroativa com scripts/modelos, assim como
os projetos `.geosaga.json` e seus identificadores históricos. Monitoria e
Assinatura continuam temporariamente com acesso via Processing, até que suas
interfaces próprias sejam implementadas.

A futura **Avaliação Espacial vetorial** está especificada em
`AVALIACAO_ESPACIAL_VETORIAL.md`; nesta versão, ela ainda não está implementada.

---

# Histórico: Vista Saga Plugin 0.3.6 — QGIS 4.x

## Inclusão: GeoTIFF → formatos vetoriais

A versão 0.3.6 acrescenta **GeoTIFF → Vetor (polígonos)** como quarta
operação no conversor, **sem modificar as três opções previamente homologadas**.
Oferece GeoPackage, Shapefile, GeoJSON e FlatGeobuf, via GDAL/OGR Polygonize.
GeoTIFFs categóricos de **uma banda inteira** são vetorizados diretamente,
preservando os códigos dos pixels em `CODIGO`; `CLASSE` e `COR_HEX` vêm da
legenda ou tabela de cores existente e, quando disponível, dos metadados
`.tif.rs2.json`. Sem legenda, cria o rótulo genérico `Classe N` e deixa
`COR_HEX` vazio se a cor não estiver armazenada.

GeoTIFFs **RGB/RGBA classificados** também são suportados: são detectadas
as cores únicas e criados novos códigos por cor, com nome `Cor #RRGGBB`.
Uma imagem fotográfica ou com gradiente de muitas cores **não é adequada**
para esta vetorização; nesse caso o conversor recusa paletas excessivas.
O código de uma cor RGB não é um código temático original. Ao excluir FUNDO,
se não existir branco/transparência no RGB, a classe de código 0 **não é
excluída automaticamente**, por poder representar informação válida.

São mantidos **seleção de TIFF do projeto QGIS**, SRC com widget nativo,
processamento em lote de mapas de mesma dimensão/resolução, inclusão opcional
da classe 0, contiguidade de 4/8 vizinhos, carregamento vetorial no QGIS,
progresso, cancelamento e substituição coordenada de saídas. O SRC é lido
do GeoTIFF; selecionar outro EPSG só altera a **atribuição de referência**,
não reprojeta os dados. Sem georreferenciamento, informe a extensão manual.

Teste integrado a executar no Console Python do QGIS 4.x:

```python
from geosaga.tests.integration_tiff_vector_qgis import run
run()
```

Esta versão passou por testes unitários sem QGIS. A integração GDAL/OGR e
a interface Qt6 ainda precisam ser homologadas numa instalação real do QGIS.

---

# Histórico: Vista Saga Plugin 0.3.5 — QGIS 4.x

## Interface simplificada e vetorização direta de RS2

O conversor foi reorganizado em **Operação**, **Entrada** e **Saída**, seguindo
formulários de processamento do QGIS. Controles opcionais ficam recolhidos em
**Opções avançadas**. O seletor de SRC usa a janela nativa do QGIS e permite
não definir o SRC quando o datum/zona dos mapas antigos não é conhecido.

Além de RS2 → GeoTIFF e GeoTIFF → RS2, esta versão oferece **RS2 → Vetor
(polígonos)** nos formatos GeoPackage, Shapefile, GeoJSON e FlatGeobuf. A
vetorização usa códigos categóricos RS2, cria uma feição por região contígua
e grava os campos `CODIGO`, `CLASSE` e `COR_HEX` (a cor `#RRGGBB`). Por padrão,
exclui a classe 0 (FUNDO), com opção de incluí-la e de utilizar 4 ou 8 vizinhos.
Se o resultado for carregado no projeto, o complemento tentará aplicar
simbologia categorizada com as cores RS2. A representação também permanece nos
campos de atributos, mesmo que o estilo não seja aplicado.

O processamento em lote continua disponível, com verificação de resolução e
dimensões iguais; desalinhamentos espaciais produzem aviso. No modo vetorial,
o resultado pode ser adicionado diretamente ao QGIS. A conversão emprega
GeoTIFF e GeoPackage temporários de modo transparente, sem criar etapas
manuais nem alterar o arquivo RS2 original. **Formatos altamente fragmentados
podem gerar muitas feições e exigir tempo/espaço de armazenamento**.

A documentação detalhada e o teste integrado estão em
[`RS2_VETORIZACAO.md`](RS2_VETORIZACAO.md). Os testes de interface gráfica
e da vetorização no GDAL do QGIS 4.x ainda exigem homologação em Windows e
Linux/Flatpak; o ambiente de desenvolvimento apenas executou testes unitários
independentes de PyQGIS e dos bindings GDAL/OGR.

---

## Histórico: funcionalidades da 0.3.4
### Aperfeiçoamentos de usabilidade e conversão em lote

Esta versão reorganiza o conversor RS2 ↔ GeoTIFF da 0.3.4 e adiciona vetorização RS2, sem alterar a
codificação de categorias e cores HEX e sem modificar os três módulos
ambientais existentes.

1. **SRC padrão do QGIS**: o campo de EPSG foi substituído por
   `QgsProjectionSelectionWidget`. A opção inicial é **Não definido**.
   O RS2 armazena coordenadas, mas não identifica datum e zona UTM de modo
   inequívoco: escolha somente um sistema projetado confirmado.
2. **Raster TIFF carregado no QGIS**: selecione pelo menu de camadas e clique
   **Usar como entrada**. Camadas não-TIFF, remotas ou virtuais devem ser
   previamente exportadas para GeoTIFF no disco.
3. **Conversão em lote**: marque a caixa correspondente, adicione múltiplos
   arquivos pelo disco ou pelo menu de camadas do QGIS, e indique uma pasta
   de saída. Todos os mapas devem ter iguais **dimensões de matriz e resolução**.
   Grades com origem/extensão diferentes são **aceitas com aviso**, pois a
   operação é uma conversão independente de cada arquivo, sem alinhamento
   automático, interpolação, reprojeção ou alteração de pixels.
4. **Substituição de GeoTIFF**: o TIFF e seus arquivos auxiliares conhecidos
   (`.tif.rs2.json`, `.tif.aux.xml`, `.tif.xml`, `.tfw`, `.tifw`) são
   substituídos/removidos juntos. Um backup temporário na pasta de saída
   permite restaurar o conjunto anterior quando a publicação falhar.
   O conversor escreve um arquivo de georreferenciamento `.tfw` atualizado.
   Um `.xml` genérico de outra origem (`<nome>.xml`) não é apagado.
   Se o GeoTIFF de destino estiver carregado no QGIS, remova a camada
   temporariamente antes de sobrescrevê-lo em Windows.
5. **Tratamento de erros**: verificação prévia de entradas e grade do lote,
   confirmação única antes de sobrescrever saídas, indicador de progresso e
   relatório por arquivo. TIFF RGB sem referência continua criando códigos
   temáticos novos por cor; com referência recupera os códigos originais.

### Exemplo de lote com os arquivos fornecidos

`GEOM.rs2`, `COTA.rs2`, `USO.rs2`, `LITO.rs2` e `DECL.rs2` possuem
3.507 × 4.455 células e resolução de 10 m, portanto podem ser convertidos
juntos. Todavia, `COTA` tem deslocamento de +20 m em Y e `DECL` apresenta
+10 m em X e +11 m em Y em relação a `GEOM`, `USO` e `LITO`.
O conversor mostrará aviso e não modificará esses valores. As grades
precisam de avaliação específica antes de operações cruzadas nos módulos
científicos (Avaliação, Monitoria e Assinatura Espacial).

### Validação

Testes automatizados independentes de QGIS executados no desenvolvimento,
incluindo simulação da escrita GDAL, reversão de sobrescrita e lotes.
Interface PyQGIS/Qt6 ainda requer homologação de execução no QGIS 4.x
(Windows e Linux/Flatpak); testes sintéticos não substituem essa verificação.
A compatibilidade de RS2 de saída com o Vista SAGA original foi confirmada
pelo usuário na versão 0.3.3.

---

# Vista Saga Plugin 0.3.3 — QGIS 4.x

## Correção de seleção do formato e conversão RGB independente

O tipo de arquivo de **entrada** agora determina automaticamente a operação:
`.rs2` abre no leitor RS2 e produz GeoTIFF categórico; `.tif`/`.tiff` abre
no GDAL e produz RS2. Isso impede o erro do GDAL
`not recognized as being in a supported file format` ao tentar abrir um
RS2 como TIFF. A seleção de entrada não preenche automaticamente o campo
de referência e sugere saída com outro nome.

- **RS2 → TIFF**: códigos, grade, legendas e cores vêm do próprio `.rs2`.
  Nenhum RS2 adicional deve ser indicado como referência.
- **TIFF de uma banda → RS2**: lê os códigos do próprio TIFF e, se existir,
  seu arquivo complementar `.tif.rs2.json` (gerado por este conversor).
  Referência `.rs2` não é necessária.
- **TIFF RGB/RGBA → RS2 (com referência)**: lê os pixels do TIFF e usa
  os códigos, nomes, cores e coordenadas do RS2 de referência para uma
  reprodução fiel, exigindo correspondência exata de cores e dimensões.
- **TIFF RGB/RGBA → RS2 (sem referência)**: gera códigos **novos**, um por
  cor exata e nomes genéricos `Cor #RRGGBB`; a cor branca (ou transparência)
  representa o código 0 quando presente. A escolha de código 0 e as
  classes resultantes devem ser revistas antes de análise ambiental.
  É impossível recuperar os códigos/nome originais perdidos a partir
  de valores RGB apenas.

Se o TIFF **não tem georreferenciamento**, só é possível converter para
RS2 fornecendo uma extensão comprovada no campo **Extensão manual**
(`xmin, ymin, xmax, ymax`, inteiros, na unidade projetada do mapa), ou
um RS2 de referência correspondente para o modo RGB. Não atribuímos
coordenadas automaticamente por semelhança do nome do arquivo.
O RS2 continua sem identificação inequívoca do datum/zona UTM no
próprio cabeçalho. O teste de compatibilidade de escrita no Vista SAGA
original permanece pendente.

Para arquivos fornecidos pelo usuário, a opção mais segura continua sendo
`USO.rs2` → `USO_categorias.tif` → `USO_reconstruido.rs2`:
**nenhuma referência é necessária nas duas operações**. A ida e volta
foi validada como idêntica byte a byte nas cinco amostras, usando
adaptador rasterio para simular a leitura de GDAL no ambiente de testes.
A interface Qt6 e a execução com GDAL do QGIS ainda precisam de validação
no Windows e Linux/Flatpak.

---

# Histórico: Vista Saga Plugin 0.3.2 — QGIS 4.x

## Correção do TIFF RGB → RS2

A versão 0.3.1 rejeitava TIFF RGB de 3/4 bandas porque reconhecia apenas
GeoTIFF categórico com uma banda. A versão 0.3.2 suporta ambos os casos:

1. **Uma banda de códigos inteiros:** mantém a conversão anterior e, quando
   disponível, recupera metadados do `<tif>.rs2.json`.
2. **TIFF RGB/RGBA de 8 bits:** requer o arquivo `.rs2` original
   correspondente em **RS2 de referência (para RGB)**. O plugin interpreta
   cada cor pela paleta RS2, restaura os códigos/nomes/cores e usa as
   coordenadas do arquivo original (inclusive com TIFF RGB sem SRC).

O programa **não** usa o canal vermelho isolado como código de classe.
Cores desconhecidas, paletas ambíguas, dimensões diferentes ou
extensão espacial conflitante provocam erro explicativo, evitando
conversões com categorias incorretas. Arquivos RGB colorizados ou editados
que perderam suas cores exatas não podem ser reconstruídos dessa forma.

Ao escolher TIFF como entrada, a saída sugerida é `<nome>_convertido.rs2`,
para evitar sobrescrever o arquivo original. O programa proíbe usar o
RS2 de referência como destino da conversão RGB.

**Teste recomendado com os arquivos enviados:** Entrada `GEOM.tif`;
referência `GEOM.rs2`; saída `GEOM_convertido.rs2`. Depois, abrir no
Vista SAGA original para homologar leitura do arquivo produzido.

A variante RS2 não declara de maneira inequívoca o EPSG. O TIFF RGB sem
georreferenciamento só pode adquirir extensão e resolução de um RS2
correspondente explicitamente selecionado. A escrita segue experimental
até ser testada em instalação real do Vista SAGA e do QGIS 4.x.

---

# Vista Saga Plugin 0.3.1 — QGIS 4.x

**Novo: conversor experimental Vista SAGA `.rs2` ↔ GeoTIFF categórico**.

O módulo **Raster → Vista Saga Plugin → Conversor RS2 ↔ GeoTIFF (experimental)**
permite importar mapas RS2 do Vista SAGA original, sem transformar seus códigos
numéricos em simples imagens RGB. A legenda temática e as cores são preservadas
no GeoTIFF (banda única) e no arquivo `.rs2.json` ao lado da saída.

Informe o **EPSG confirmado** ao importar RS2 caso conheça o SRC. Os limites
em coordenadas projetadas estão no RS2, mas o datum e a zona UTM não são
identificados inequivocamente pela variante examinada. Deixar EPSG vazio
mantém coordenadas sem atribuir um SRC por suposição.

A partir da versão 0.3.2, a exportação admite também TIFFs RGB com
um arquivo RS2 original de referência selecionado pelo usuário. A escrita RS2 é
experimental e ainda requer conferência no programa Vista SAGA original.

Consulte [FORMATO_RS2.md](FORMATO_RS2.md) para documentação e testes.

---

# Vista Saga Plugin — versão 0.3.0 (QGIS 4.x)

**Complemento experimental para QGIS 4.x**, desenvolvido incrementalmente a partir do GeoSAGA Ambiental **0.2.0**. O plugin reúne Avaliação Ambiental, Monitoria Espacial e Assinatura Espacial, inspirado na facilidade operacional e nos procedimentos do Vista SAGA/UFRJ.

**Independência:** implementação original e independente; não é a reprodução ou uma portabilidade do executável Delphi do Vista SAGA, não recupera seu código-fonte e não representa uma distribuição oficial da UFRJ. A equivalência quantitativa com o software original **ainda não foi demonstrada**.

## O que mudou na versão 0.3.0

- Novo nome de exibição **Vista Saga Plugin** e novo painel de abertura dos três módulos, acessível pelo menu **Raster → Vista Saga Plugin → Painel de módulos** e pelo botão da barra de ferramentas.
- Correção da importação `QAction` para Qt6 (`qgis.PyQt.QtGui`).
- Preservação integral das operações de Avaliação Ambiental, incluindo projetos `.geosaga.json` v1, relatórios CSV, pesos e notas, processamento em segundo plano via `QgsTask` e raster GeoTIFF.
- Monitoria e Assinatura continuam disponíveis via **Processing**, sem promessa de interface específica nesta etapa.
- Identificadores de algoritmos **`geosaga:avaliacao`**, **`geosaga:monitoria`** e **`geosaga:assinatura`** mantidos para compatibilidade com scripts/modelos existentes.
- Testes de regressão do núcleo com NumPy e script de conferência dos algoritmos no QGIS.

## Instalação / atualização

1. No QGIS 4.x, abra **Complementos → Gerenciar e Instalar Complementos → Instalar a partir de ZIP**.
2. Selecione `Vista_Saga_Plugin_QGIS4_v0.3.0.zip` e habilite **Vista Saga Plugin**.
3. A pasta interna permanece **`geosaga`** intencionalmente: é uma **atualização do GeoSAGA Ambiental 0.2.0**, e não um segundo plugin independente. Se o QGIS mantiver a versão anterior carregada, desabilite-a e reinicie o aplicativo após a substituição. Não instale uma segunda pasta com outro nome ao lado de `geosaga`.
4. Use o menu **Raster → Vista Saga Plugin** ou o botão da barra de ferramentas.

Requer PyQGIS, NumPy e GDAL/OGR instalados **no próprio ambiente do QGIS**. Não exige dependências Python externas. O código visa **QGIS 4.x + Qt6**, em Windows e Linux/Flatpak, mas ainda precisa de homologação funcional nos dois ambientes; a validação de sintaxe e lógica independente não equivale a um teste real do QGIS.

## 1. Avaliação Ambiental (interface própria)

1. Adicione mapas raster categóricos do projeto QGIS, ou carregue GeoTIFFs locais pelo botão **Arquivo…**.
2. Revise a banda 1 e as classes detectadas (máximo de 300 classes distintas por mapa).
3. Defina pesos positivos, cuja soma deve ser 100%.
4. Atribua notas a todas as classes entre 0 e 10 ou entre 0 e 100; notas ausentes impedem a execução. Classes marcadas **Não avaliar** transformam em NoData o pixel final.
5. Valide o alinhamento de grades e SRC; selecione o destino `.tif` e execute. Opcionalmente gere CSV e carregue o resultado no QGIS.
6. Salve as configurações em `.geosaga.json`. O formato legado `.ava` do Vista SAGA não é suportado.

A operação por pixel é uma **média ponderada das notas**, com propagação de NoData e sem redistribuição de pesos quando uma classe é bloqueada. Dados de entrada devem possuir mesmo SRC, extensão, resolução, dimensões e alinhamento.

## 2. Monitoria Espacial — algoritmo legado (Processing)

Compare dois rasters categóricos do mesmo grid e gere um GeoTIFF Int32 com IDs de transição e uma tabela CSV com as classes inicial/final, pixels, porcentagem e área (ha quando o SRC é projetado). O módulo realiza duas passagens por blocos e não reamostra os rasters automaticamente.

## 3. Assinatura Espacial — algoritmo legado do Processing

Forneça um raster categórico e uma camada de polígonos. O algoritmo histórico, mantido para compatibilidade, contabiliza, dentro da **união espacial das áreas selecionadas**, as classes, os pixels, os percentuais e as áreas. Polígonos sobrepostos não são contados duas vezes. A saída é CSV. A nova interface 0.5.0, descrita no início deste documento, acrescenta estatísticas individuais por feição e relatórios CSV/TXT/GPKG. O desenho de novos polígonos diretamente no canvas ainda não está implementado.

## Limitações e precauções

- Somente raster categórico em arquivo local (preferencialmente GeoTIFF), banda 1.
- O formato `.rs2` tem conversor experimental; `.rst`, `.ava`, `.mon` e `.asn` continuam sem suporte.
- Não há alinhamento automático geral nem comprovação de equivalência completa entre os resultados do plugin e do software original; Monitoria e Assinatura já possuem interface própria.
- Para sistemas em graus, o plugin não apresenta hectares obtidos por área planar dos pixels.
- Não substitua resultados já validados sem conferir arquivos, sistema de referência e regras numéricas.
- A versão permanece **experimental** e não deve ser submetida ao repositório público antes dos testes manuais e preenchimento dos metadados complementares.

## Como testar

**Testes Python/NumPy**, no diretório acima da pasta `geosaga`:

```bash
python -m unittest discover -s geosaga/tests -p 'test_*.py' -v
```

**Teste do registro no QGIS**, após instalar e ativar o plugin, no Console Python:

```python
from geosaga.tests.smoke_qgis import check
check()
```

**Teste geoespacial automatizado dentro do QGIS**, com dados raster e poligonal sintéticos (pasta temporária):

```python
from geosaga.tests.integration_qgis import run
run()
```

**Teste manual mínimo no QGIS:** abrir o painel e os três módulos; no Avaliação, carregar dois rasters categóricos alinhados, distribuir pesos, definir notas, executar, verificar o GeoTIFF e conferir pelo menos duas células de saída contra a média ponderada calculada manualmente; repetir no Windows e Linux/Flatpak. Em Monitoria, verificar contagens de transição e soma dos pixels; em Assinatura, validar contagem em uma área de geometria simples.

O cronograma e os critérios de aceite da evolução estão em `PLANO_DE_EVOLUCAO.md`.

## Licenciamento

GPL-3.0-or-later. Ver `LICENSE` e `LICENSE.md`. O código-fonte não incorpora componentes do executável original Vista SAGA.

### GeoTIFF contínuo para vetor (0.3.9)

GeoTIFFs `Float32`/`Float64`, como o resultado da Avaliação Espacial, são classificados em intervalos de igual amplitude antes da poligonização. Em **Conversão de formatos → GeoTIFF → Vetor → Opções avançadas**, escolha de 2 a 20 classes (5 padrão). Saídas incluem `CODIGO`, `CLASSE`, `COR_HEX` (vazio quando não há cores), `VALOR_MIN` e `VALOR_MAX`. Essa classificação **não conserva o valor decimal de cada célula individual** no vetor: preserva os limites dos intervalos. Raster de origem inalterado; NoData, NaN e infinitos não são vetorizados, enquanto zero válido é mantido. Para preservar resultados quantitativos, conserve o GeoTIFF original.

## 0.3.11 — Empilhamento de mapas vetoriais

A **Avaliação Espacial** agora oferece dois modos para vetores: avaliação por atributos de uma única camada (sem alteração) e **avaliação por sobreposição de duas ou mais camadas de polígonos**. A nova janela permite selecionar sucessivamente o mapa, seu campo categórico, pesos e notas. A interseção espacial calcula a carta apenas nas áreas comuns a todos os mapas. Veja [AVALIACAO_SOBREPOSICAO_VETORIAL.md](AVALIACAO_SOBREPOSICAO_VETORIAL.md) para instruções e limites metodológicos.


## Combinação de Mapas (0.6.0)

O painel inclui a ferramenta **Combinação de Mapas**, para rasters temáticos (GeoTIFF) e polígonos vetoriais. Consulte `COMBINACAO_MAPAS_060.md` para opções, limitações e testes no QGIS.


**0.7.1:** Voronoi Simples com campo de massa oculto, raster de referência opcional e saída GeoPackage direta.
