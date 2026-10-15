# Monitoria Ambiental — versão 0.4.2

## Mudanças de interface

A Monitoria tem duas abas: **Configuração** (dois mapas lado a lado, parâmetros principais e saída) e **Resultados** (resumo e tabela das transições). O painel avançado da Configuração fica inicialmente recolhido e contém escolha da legenda, CSV de equivalência temática e série temporal para Mann–Kendall.

A execução permanece em segundo plano, com progresso e cancelamento; a conclusão seleciona a aba Resultados. O núcleo raster de comparação entre períodos não foi modificado.

## Vetorização da saída de Monitoria

Após produzir `mudancas.tif`, utilize **Conversão de formatos → GeoTIFF → Vetor**. O conversor procura `mudancas_transicoes.csv` na mesma pasta. Nas saídas novas, a Monitoria também grava a relação das classes como metadado da banda raster quando o volume não exceder 512 KiB. Isso possibilita manter a legenda caso o TIFF seja copiado sem o CSV. Se o CSV estiver presente, ele tem precedência.

O vetor recebe os campos habituais (`CODIGO`, `CLASSE`, `COR_HEX`), além de:

- `ID_TRANS`: ID codificado no raster de transições;
- `COD_INI`, `COD_FIM`: códigos temáticos dos períodos inicial e final;
- `SITUACAO`: permanência ou mudança;
- `DEIXOU_SER`, `TORNOU_SE`: descritores das mudanças (em branco nas permanências);
- `AREA_M2`, `AREA_HA`, `PCT_AREA`: área da feição e participação percentual em relação à soma das áreas das feições vetorizadas.

A simbologia de vetor gerado pelo conversor usa `COR_HEX` e a descrição da transição, limitada a até 256 categorias para manter legibilidade. Os campos de área também passam a existir para outros GeoTIFFs vetorizados.

### Regras de áreas

Para SRC projetado, a área geométrica é convertida para metros quadrados utilizando as unidades lineares indicadas pelo SRC. Para SRC geográfico, a área geodésica será calculada se disponível na versão do GDAL/OGR. Para um SRC ausente ou sem função de área confiável, os campos de área são deixados nulos: o plugin **não considera graus quadrados como hectares**. Percentuais são derivados das áreas efetivamente vetorizadas, excluindo NoData/fundo conforme a configuração da conversão.

Não é realizada reprojeção ou alteração dos pixels da Monitoria. A conversão continua suportando GeoPackage, SHP, GeoJSON e FlatGeobuf.

## Próxima modalidade: Monitoria vetorial

A comparação direta de duas camadas poligonais é viável, mas ainda não foi implementada nesta versão. Ela requer interseção geométrica, correspondência dos atributos temáticos, tratamento de sobreposições/ausências de cobertura e relatório de áreas por transição. Não confundir essa função futura com a **vetorização do resultado raster**, já disponível.

## Teste no QGIS 4.x

No Console Python, execute:

```python
from geosaga.tests.integration_monitoring_vector_qgis import run
run()
```

O teste deve confirmar a legenda, os campos de auditoria, a área de 600 m² e a soma percentual de 100% numa grade sintética de seis células de 10 × 10 metros.
