# Vista Saga Plugin - mudanças por módulo, da 1.0.4 à 1.6.1

Resumo das mudanças desde a **1.0.4** (versão publicada no catálogo oficial do QGIS em 31/10/2026) até a
**1.6.1** (20/11/2026), agrupadas por módulo. Entre colchetes, a versão em que cada mudança entrou. O histórico
completo, versão a versão, está em [`geosaga/CHANGELOG.md`](../geosaga/CHANGELOG.md). A 1.0.7 foi só um pacote
interno de teste.

**Cálculos alterados nesse período (decisões de método):** Análises Voronoi [1.4.0] e Combinação de Mapas
vetorial [1.2.0]. A Assinatura foi refeita [1.5.0], com validação contra o Vista SAGA original. Nos demais
módulos, só interface e robustez.

---

## Assinatura

- **Refeita no modelo do Vista SAGA** [1.5.0]:
  - lista de mapas com a **referência no topo**; a seleção feita na referência é o limite da análise;
  - **todos os mapas da lista são assinados**, inclusive a referência;
  - resultado da **união da seleção** e, opcionalmente, **por feição**;
  - colunas do Vista SAGA: área total, área assinada, **% Área Asn.** e **% Categoria**; FUNDO e NoData contam
    como classe.
- **Guia Raster** [1.5.0]: formatos do GDAL e **RS2**; mesmo SRC projetado em metros e mesma grade obrigatórios
  (o plugin não reprojeta); seleção por lista de classes ("Marcar todas" = assinar o mapa inteiro); nomes das
  classes do arquivo ou do estilo da camada no QGIS. **Validada contra o Vista SAGA original**: mapa inteiro
  100%; seleções parciais iguais, salvo células ligadas à classe só pela diagonal.
- **Guia Vetorial** [1.5.0]: interseção exata; seleção pelas ferramentas do QGIS ("Selecionar no mapa",
  "Selecionar todas", "Desselecionar todas"); linhas "Sem classe" e "Sobreposição excluída"; lascas com largura
  média menor que 1 cm toleradas e registradas.
- **Saídas** [1.5.0]: relatórios TXT e CSV; botão "Remover todas". O algoritmo Processing `geosaga:assinatura`
  fica obsoleto e oculto (modelos antigos continuam funcionando). Corrigida a reprojeção silenciosa do módulo
  antigo.
- Reprojeção pelo contexto da execução e mensagens claras em falhas (algoritmo Processing) [1.0.5].

## Monitoria

- **Resultado no padrão do plugin** [1.2.0]: campo "Salvar em" vazio gera resultado temporário (raster em
  arquivo, vetor em memória); preenchido, salva. Sempre carregado no QGIS. Mesmos rótulos nas guias Raster e
  Vetorial.
- **Aviso de feições sem classe** na guia Vetorial, com o número de feições ignoradas e o campo [1.2.0].
- **Tabelas de resultado copiáveis para planilhas** (Ctrl+A, Ctrl+C), com o separador decimal do idioma [1.2.0].
- **Mann–Kendall retirado por enquanto** [1.2.0]: volta como módulo próprio na 2.0. Transições, matriz e áreas
  não mudaram.
- Rodapé padrão e progresso só durante a execução [1.4.1]; dicas em todos os controles [1.6.0].

## Avaliação

- **Guias "Vetorial (Atributos)" e "Vetorial (Sobreposição)" com o leiaute da guia Raster** [1.1.0]: projeto
  (Novo, Abrir, Salvar), escala das notas, critérios e pesos, classes, resultado.
- **Projeto de pesos e notas reutilizável** [1.1.0]: cada execução grava `*_pesos_notas.geosaga.json`, que
  "Abrir projeto…" reaplica.
- **Classes sem nota em evidência** [1.1.0]: destacadas e contadas; "Validar" lista todas as pendências; a nota
  "—" continua bloqueando a execução (o plugin nunca supõe nota 0).
- **Pesos novos em branco**; divisão igual só pelo botão "Distribuir pesos igualmente" [1.1.0].
- Ordenação das classes pelo cabeçalho; Tab salta entre pesos e entre notas; "Classes" e "Não avaliar" como
  terminologia; números à direita [1.1.0].
- Resultado sempre carregado no QGIS ("Salvar em" vazio = temporário) [1.1.0].
- Guia Raster sem os campos Título e Autor [1.1.0].
- Rodapé padrão com [Validar] [Executar] [Fechar] [1.4.1]; dicas em todos os controles [1.6.0].

## Análises Voronoi

- **Fiel ao Vista SAGA, validado célula a célula** [1.4.0] (mudança de método):
  - **Com Massa: maior M/d²** (antes, M/d);
  - **atrito pelo custo do Vista SAGA**: soma de distância ao polo × nota × passo na reta polo-célula; a nota é o
    próprio custo (sai o 1 + C);
  - Simples e Com Massa: 100% das células; com atrito: 99,4% a 99,7% (guia Raster) e 99,1% a 99,6% (guia
    Vetorial), diferenças na fronteira entre regiões;
  - modalidades com atrito deixam de ser experimentais.
- **Superfície de atrito vetorial** (polígonos com a nota numa coluna) [1.4.0]; área sem polígono, coluna vazia
  e NoData do raster de atrito ficam sem resultado e são atravessados com nota 1.
- **Guia Vetorial direta, sem rasterizar** nas quatro modalidades [1.4.0], com conferência automática do
  traçado; execução em segundo plano com progresso e cancelamento.
- **Guias Raster e Vetorial** e campo "Salvar em" [1.3.0]; formatos vetoriais GeoPackage, Shapefile, GeoJSON e
  FlatGeobuf pelo "Salvar como…" [1.3.0].
- **Fronteiras exatas na Com Massa** (arcos de círculos de Apolônio) [1.3.0].
- Nota de atrito 0 recusada (use 0,1 para "quase sem atrito") [1.4.0].
- Recorte pela área de estudo quando a extensão vem de camada poligonal [1.4.0].
- Rótulos da extensão manual traduzidos [1.6.0]; dicas em todos os controles [1.6.0].

## Combinação de Mapas

- **Guias "Raster" e "Vetorial"**, "Adicionar camada selecionada" e "Mover para cima/baixo" [1.2.0].
- **Resultado sempre carregado no QGIS** ("Salvar em" vazio = temporário) [1.2.0].
- **Tolerância de lascas** (decisão de método) [1.2.0]: sobreposições internas com largura média menor que
  1 cm são tratadas como imprecisão de coordenadas e registradas; acima disso, a combinação para e lista os
  pares.
- **Resíduos de cruzamento incorporados ao vizinho** de maior fronteira comum (decisão de método) [1.2.0]:
  somem as combinações falsas, sem mudar a área total.
- **Campos renomeados** de `C01`/`L01` para `COD_01`/`LEG_01` [1.2.0].
- Campo de classe editável para qualquer camada da lista; aviso de camada repetida mais claro [1.2.0].
- Leitura de RS2 por código da classe (códigos não consecutivos) [1.0.6]; dicas em todos os controles [1.6.0].

## Conversor de Formatos

- **Nova operação Vetor → RS2** (rasterização no formato do Vista SAGA), com grade de um RS2 de referência ou
  alinhada ao pixel [1.0.6].
- **Formato RS2 corrigido** [1.0.6]: legendas com códigos não consecutivos (como grava o Vista SAGA), cabeçalho
  com a quantidade de classes em 2 bytes, RS2 de avaliação (FUNDO com código 11) aceitos.
- **SRC nas conversões a partir de RS2** [1.0.6]: último SRC lembrado; SRC do `.rs2.json` usado
  automaticamente; converter sem SRC exige confirmação.
- **Novo nome** "Conversor de Formatos" (antes "Conversão de Formatos") e aparência igual à dos demais
  módulos [1.2.0].
- **Vetor → GeoTIFF grava sempre a paleta**, e Vetor → GeoTIFF e RS2 → GeoTIFF gravam um estilo `.qml` só com
  as classes reais [1.5.0].
- Vetor → RS2 não deixa pastas temporárias no Windows [1.5.0]; pastas temporárias limpas corretamente na
  rasterização [1.0.5].
- "Propriedades RS2…" ao lado do arquivo de entrada [1.4.1]; texto no botão de opções avançadas [1.2.1].
- Estilo `.qml` gravado sem importar `xml.sax`, com escape idêntico [1.6.1]; dicas em todos os controles [1.6.0].

## Sequenciador de Mapas

- **Guias Raster, Vetorial e Mista com a mesma altura**; textos explicativos das guias viraram dicas [1.4.2].
- "Mover para cima" e "Mover para baixo" no lugar de "Subir" e "Descer" [1.2.0].
- Textos da lista de quadros e da exportação traduzidos ("Sem data", "sobre", "GIF salvo em") [1.2.1].
- Rodapé padrão [Executar] [Fechar] [1.4.1]; dicas em todos os controles [1.6.0].

---

## Geral (todos os módulos)

- **Dicas** (caixas amarelas do QGIS) em todos os botões, campos, caixas de marcar e listas dos sete módulos,
  em português, inglês e espanhol [1.6.0].
- **Rodapé padrão** [Executar] [Fechar] ([Validar] só na Avaliação), fora das guias; progresso e Cancelar
  numa janela só durante a execução; desfecho na barra de mensagens do QGIS [1.4.1].
- **Nomes dos resultados**: temporário "Módulo - operação"; salvo, com o nome do arquivo [1.5.0].
- **Espanhol completo** em todo o plugin [1.1.0]; mensagens de erro e avisos traduzidos [1.0.5].
- **Traço simples no lugar do travessão** nos textos de interface e relatórios [1.1.0]; mesmo fundo de guia em
  todas as janelas [1.1.0].
- **Ícones**: novo ícone principal e ícones SVG dos sete módulos no menu [1.0.8, 1.0.9].
- **Robustez** [1.0.5]: exceções do GDAL só com escopo local (não afetam o QGIS nem outros complementos);
  compatibilidade com GDAL 3.11 ou mais novo e com Qt6; falhas inesperadas registradas na aba "Vista Saga
  Plugin" do painel de mensagens.
- **Catálogo do QGIS** [1.6.1]: `metadata.txt` lido sem erro pelo catálogo e código aprovado na varredura de
  segurança (Bandit e detect-secrets); defeito latente corrigido numa função reservada da Monitoria.
