# Vista Saga Plugin 1.0.6 — notas da versão

Inclui todas as correções de estabilidade da 1.0.5 ([notas](NOTAS_DA_VERSAO_105.md)).

## Novidades

- **Vetor → RS2 (rasterização Vista SAGA)** no Conversor de formatos: GeoPackage, Shapefile,
  GeoJSON ou FlatGeobuf diretamente para RS2. Grade de um RS2 de referência ou alinhada a
  múltiplos inteiros do pixel; SRC projetado obrigatório, sem reprojeção; códigos originais
  preservados; legenda apenas com as classes presentes; `.rs2.json` com SRC e correspondência
  de códigos. Detalhes e regras metodológicas em `VETOR_RS2.md` (no repositório).

## Correções

- **Formato RS2:** legendas com códigos não consecutivos, como as gravadas pelo próprio Vista SAGA,
  passam a ser lidas e gravadas corretamente (antes eram recusadas). A paleta é localizada pelo
  fim da matriz, e bytes residuais no fim do arquivo são tolerados. Afeta todas as operações RS2,
  a Monitoria e a Combinação de Mapas, que agora associam nomes e cores pelo código.
- **RS2 do módulo de avaliação do Vista SAGA:** deixam de ser recusados ("Quantidade de classes
  RS2 inválida"). O cabeçalho guarda o código de cada classe, inclusive a primeira, e o FUNDO pode
  ter código diferente de 0 (por exemplo, 11, após as notas 1–10); ele é tratado como NoData.

## Verificação

- Testes automatizados com GDAL real; ida e volta RS2 → GeoTIFF → RS2 idêntica byte a byte a um
  arquivo gravado pelo Vista SAGA.
- Conversão Vetor → RS2 validada pelo responsável no Vista SAGA original (builds de teste).
- **Pendente:** homologação do pacote 1.0.6 completo no QGIS 4.x (Windows) e no Vista SAGA.

Algoritmos numéricos dos demais módulos e identificadores `geosaga:*` inalterados.
