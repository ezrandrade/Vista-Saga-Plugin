# Vista Saga Plugin 1.0.4-rc3 — correções de internacionalização

Versão **experimental**, preparada a partir da versão candidata 1.0.4-rc2.
Não substitui a versão oficial homologada 1.0.3 para fins de publicação.

## Correções feitas com base nas capturas enviadas pelo usuário

- Conversão de Formatos: modalidades RS2/GeoTIFF, descrição variável da operação, seleção de SRC e legendas dos controles.
- Assinatura: opções de identificação dos polígonos, legendas e política de sobreposição vetorial.
- Monitoria: modalidades de legenda de transição, textos padrão Inicial/Final e campos de legenda vetorial.
- Avaliação raster e vetorial: botões gerados por funções auxiliares, escalas de notas, mensagens de pesos e controles de avaliação.
- Análises Voronoi: tipos de influência, opções de extensão, identificador dos pontos e unidade de resolução.
- Combinação de Mapas: nomes de abas raster/vetorial e opção de legenda por classe.
- Sequenciador de Mapas: controles da lista, ações de adicionar, unidades de duração e mensagens de estado.
- Diálogos de progresso: rótulos de operação e botão Cancelar em inglês.

O catálogo inglês contém 650 entradas; o espanhol permanece parcial com 135 entradas.
O módulo respeita o idioma definido na interface do QGIS; idiomas sem tradução dedicada recorrem ao inglês.

## Segurança e compatibilidade

Os identificadores 9geosaga:*9, chaves de parâmetros, campos de dados e métodos de processamento
são preservados. A tradução das opções de combos não muda seus valores internos.
Os relatórios e mensagens dinâmicas ainda podem incluir expressões em português.
Não foi possível executar testes gráficos no QGIS 4.x/Qt6 neste ambiente; o teste é somente estático.

## Instalação

1. Faça backup do complemento 1.0.3 e dos seus projetos.
2. QGIS → Complementos → Gerenciar e Instalar → Instalar a partir de ZIP.
3. Escolha o ZIP 1.0.4-rc3. Configure inglês nas preferências de idioma do QGIS e reinicie-o.
4. Revise as telas que aparecem nas capturas e execute análises simples.
5. Compare os resultados com a versão oficial 1.0.3 antes de homologar.
