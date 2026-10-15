# Vista Saga Plugin 0.6.1 — Organização da interface e saídas temporárias

Esta versão **não modifica os núcleos analíticos** da Avaliação, Monitoria,
Assinatura, Combinação de Mapas e Conversão de Formatos.

## Interface

- Combinação de Mapas: abas Raster/Vetorial já disponíveis, com seleção múltipla
  de camadas existentes no QGIS, seleção de arquivos múltiplos e remoção múltipla.
- Avaliação Espacial: aba Raster e abas de acesso às interfaces vetoriais por
  atributos e por sobreposição (que ainda abrem suas janelas próprias).
- Monitoria Espacial: aba Raster, aba de acesso à janela da Monitoria vetorial,
  e aba Resultados.
- Assinatura Espacial: abas seletoras Raster/Vetorial, mantendo
  Configuração/Resultados como páginas de trabalho.
- Avaliação raster: adição simultânea de múltiplos rasters do QGIS ou do disco.
- Avaliação vetorial por sobreposição: adição de várias camadas do projeto,
  com seleção de campo por mapa. As listas de avaliação permitem remoção múltipla.
- Conversor: adição simultânea de rasters do projeto nos lotes e remoção múltipla.

## Saídas

Nos procedimentos que produzem GeoTIFF, GeoPackage ou relatórios, a opção de
resultado temporário utiliza o diretório temporário do **QGIS Processing**.
O arquivo é adicionado ao projeto após execução e o usuário pode salvá-lo
posteriormente usando as funções nativas de exportação do QGIS.
Desmarque o modo temporário e escolha um caminho para salvar permanentemente.

Importante: a saída temporária **não fica inteiramente em RAM**. Rasteres e
GeoPackages podem ser grandes, por isso usam arquivos de trabalho temporários.
Essa alternativa reduz consumo de memória. O QGIS pode limpar esses arquivos ao
encerrar: exporte o resultado e relatórios para local permanente se quiser
preservá-los. Não confundir camadas temporárias com arquivos permanentes
referenciados por um projeto QGIS salvo.

**Exceção intencional:** GeoTIFF → RS2 requer arquivo de saída permanente, já que
RS2 é formato legado não reconhecido como camada nativa do QGIS.

A Assinatura oferece agora a seleção múltipla de camadas poligonais de áreas
carregadas no projeto. Essas áreas são reunidas em uma camada em memória
**apenas para análise**, identificando `VS_ORIGEM` e `VS_NOME`, sem dissolver
polígonos distintos. Todas devem ter SRC idêntico, geometrias válidas e não
estar em edição. Regiões sobrepostas das diferentes camadas são analisadas
individualmente; não some seus hectares como se fossem territórios únicos.

A Monitoria continua comparando exatamente dois períodos por análise.

## Homologação

Esta versão exige verificação gráfica no QGIS 4.x/Qt6 em Windows e Linux/Flatpak.
Teste os fluxos com resultados temporários e persistentes e confira os relatórios
correspondentes antes de utilizar a nova distribuição em produção.
