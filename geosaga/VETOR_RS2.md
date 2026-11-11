# Vetor → RS2 (rasterização Vista SAGA) — em desenvolvimento

Sexta operação do **Conversor de formatos**. Converte uma camada vetorial
(GeoPackage, Shapefile, GeoJSON ou FlatGeobuf) diretamente para o formato RS2
do Vista SAGA, sem a etapa manual Vetor → GeoTIFF → RS2. As cinco operações
anteriores não foram alteradas.

> O RS2 é uma **matriz categórica**, não um formato vetorial. Esta operação é,
> portanto, uma **rasterização**: limites de feições passam a depender da
> resolução da grade, e não há conversão vetorial sem perda.

## Uso

1. Em **Converter**, escolher **Vetor → RS2 (rasterização Vista SAGA)**.
2. Selecionar o arquivo vetorial ou uma camada vetorial do projeto.
3. Escolher o **campo para rasterizar** (`CODIGO` é selecionado automaticamente quando existir).
4. Definir a grade:
   - **sem referência**: informar o **tamanho do pixel** (inteiro, nas unidades do SRC — metros em UTM);
   - **com referência** (*Opções avançadas → RS2 de referência (grade)*): a origem, a resolução e
     as dimensões de um RS2 existente são copiadas, e o tamanho do pixel é ignorado.
5. Opcionalmente, em *Opções avançadas*: **ALL_TOUCHED** e o **modo dos códigos RS2**.
6. Informar o arquivo `.rs2` de saída e executar.

## Regras e decisões metodológicas

| Tema | Regra adotada | Motivo |
| --- | --- | --- |
| SRC | Exige SRC **projetado**; SRC geográfico é recusado. **Não há reprojeção.** | O RS2 grava bordas como inteiros não negativos de 32 bits; graus perderiam a geometria. |
| Grade sem referência | Bordas alinhadas para fora a **múltiplos inteiros do pixel**; o pixel deve ser inteiro. | Garante coordenadas inteiras e que vetores rasterizados com a mesma resolução compartilhem a mesma malha. |
| Grade com referência | Cópia exata da grade do RS2 indicado; recusa se o vetor não intersectar a grade. | Permite cruzamento célula a célula com mapas existentes (por exemplo, GEOM, USO). O RS2 não registra SRC: a coerência de SRC é responsabilidade do usuário. |
| Campo inteiro — *Automático* | Preserva os códigos se todos estiverem entre 1 e 255; caso contrário, renumera para 1..n. | O RS2 exige categorias consecutivas 0..n; códigos esparsos inflariam a legenda com classes vazias. |
| Campo inteiro — *Preservar* | Mantém os códigos (até 32.768); recusa o código 0. | 0 é reservado ao FUNDO; uma classe 0 se confundiria com a ausência de dados. |
| Campo inteiro — *Renumerar* | Ordem crescente dos valores originais → 1..n. | Legenda compacta; a correspondência fica no `.rs2.json`. |
| Campo textual | Códigos 1..n em **ordem alfabética** do texto. | Resultado reprodutível, independente da ordem das feições no arquivo. |
| Campo decimal | **Recusado.** | O RS2 armazena apenas categorias; classifique antes. |
| Nomes e cores | `CLASSE` (campo inteiro) ou o próprio texto (campo textual) como nome; `COR_HEX` como cor; demais cores geradas de forma determinística. Nomes devem caber em CP1252. | Codificação do cabeçalho RS2 observado. |
| Sobreposição | Prevalece a última feição processada; o número de células sobrepostas é **contado e relatado**. | Evita um viés silencioso: corrija a topologia se as classes conflitarem. |
| Feições inválidas | Geometria vazia ou atributo nulo são ignorados e contados. | Transparência do processamento. |
| Classes sem células | Relatadas no final (feições menores que o pixel). | Alerta de perda de informação pela resolução. |

## Arquivo lateral `.rs2.json`

Além dos campos já usados pelas demais operações RS2 (grade, nomes e cores), registra em
`rasterization`: vetor e campo de origem, tipo do campo, modo de grade e RS2 de referência,
tamanho do pixel, ALL_TOUCHED, modo dos códigos, **tabela de correspondência**
`codigo_rs2 ↔ valor_original` com a contagem de células por classe, células sobrepostas e
feições ignoradas. O SRC da camada (`source_wkt`) fica **somente** neste arquivo.

## Limites

- No máximo 65.535 linhas ou colunas, 100 milhões de células e 32.768 classes além do FUNDO.
- Somente arquivo individual (sem lote) nesta versão.
- O prefixo de 11 bytes do cabeçalho usa o valor observado nas amostras autênticas;
  sua semântica completa permanece desconhecida.

## Verificação

- Testes unitários e de conversão real com GDAL/OGR: `geosaga/tests/test_vector_rs2.py`
  (células conferidas uma a uma pelo leitor independente `RS2Reader`).
- Ida e volta conferida com as operações existentes: RS2 → GeoTIFF devolve a mesma grade e as
  mesmas classes; RS2 → Vetor devolve polígonos com áreas idênticas às originais.
- Homologação no QGIS 4.x (núcleo e interface), no Console Python:

```python
from geosaga.tests.integration_vector_rs2_qgis import run
run()
```

- **Pendente e indispensável:** abrir no **Vista SAGA original** um RS2 gerado por esta operação
  e conferir classes, cores e posição. Os testes automatizados não substituem essa validação.
