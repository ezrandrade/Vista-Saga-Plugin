# Monitoria Ambiental — modalidade vetorial direta (0.4.3)

A versão 0.4.3 acrescenta a comparação **direta entre duas camadas poligonais**,
sem rasterização. A Monitoria raster 0.4.2, incluindo relatórios, legendas e
Mann–Kendall opcional, permanece disponível sem alterações no algoritmo.

## Como abrir

1. Abra **Painel de módulos → Monitoria Ambiental**.
2. Na aba **Configuração**, clique em **Abrir Monitoria vetorial…**.
3. Selecione uma camada poligonal inicial e uma final, já carregadas no QGIS,
   ou indique os respectivos arquivos. Para GeoPackages com várias subcamadas,
   carregue a subcamada desejada no QGIS e selecione-a no menu.
4. Para cada camada, escolha o **campo de classe** e, opcionalmente, um
   **campo de legenda**. Campos de texto podem ser utilizados diretamente
   como categorias; códigos numéricos precisam ser semanticamente equivalentes
   nos períodos caso não sejam fornecidas as legendas.
5. Informe os períodos e o caminho de saída `.gpkg`. Execute a monitoria.

## Método

O plugin verifica SRCs, geometria poligonal, campos e disponibilidade das
camadas. Feições de classe ausente ou geometria vazia são desconsideradas,
com contagem no resumo. **Geometrias inválidas são recusadas:** utilize
*Corrigir geometrias* do QGIS antes de executar.

A sobreposição utiliza `native:intersection` (motor QGIS) e preserva a área
**comum aos dois mapas**. Polígonos de limites diferentes são subdivididos.
A permanência é decidida pela igualdade de nomes temáticos quando os dois
mapas têm legendas explícitas; caso contrário, pela igualdade dos códigos.
Logo, é indispensável conferir a compatibilidade das classificações.

A área é calculada em m² com fator de unidade linear do SRC projetado ou
cálculo elipsoidal com SRC geográfico, conforme a rotina de áreas já presente
na Avaliação Espacial. Os percentuais são relativos à soma das áreas dos
polígonos resultantes da interseção, **não** ao número de feições.

**Importante:** feições sobrepostas dentro da mesma camada podem duplicar
áreas no resultado; confira topologia e inexistência de sobreposição interna
antes da Monitoria. Áreas existentes apenas em um dos períodos não recebem
classificação de transição nesta modalidade. O plugin não realiza correção
geométrica, dissolução nem generalização automáticas.

## Arquivos de saída

- `<nome>.gpkg`: geometrias com `COD_INI`, `NOME_INI`, `COD_FIM`, `NOME_FIM`,
  `ID_TRANS`, `SITUACAO`, `LEGENDA`, `DEIXOU_SER`, `TORNOU_SE`,
  `AREA_M2`, `AREA_HA` e `PCT_AREA`.
- `<nome>_transicoes.csv`: tabela de combinações, áreas (m² e ha) e percentuais.
- `<nome>_matriz.csv`: matriz inicial × final **em hectares**, diferente da
  matriz de contagens de pixels da Monitoria raster.
- `<nome>_resumo.txt`: síntese de permanências e mudanças, área comum,
  percentuais, ressalvas e feições desconsideradas.

Os quatro arquivos são publicados em conjunto e, se necessário, substituem
os arquivos anteriores com restauração em caso de falha. Entradas não são
modificadas. Uma análise com somente dois períodos **não permite inferência
estatística por Mann–Kendall**; tal análise permanece disponível apenas no
fluxo raster com série temporal de mapas adicionais.

## Teste no Console Python do QGIS 4.x

```python
from geosaga.tests.integration_vector_monitoring_qgis import run
run()
```

O teste sintetiza camadas poligonais com 200 m² comuns: 50 m² de permanência
(25%) e 150 m² de mudança (75%), verifica campos e soma das áreas, matriz e
CSV. A interface real e a execução do Processing devem ser homologadas no
QGIS 4.x em Windows e Linux/Flatpak.
