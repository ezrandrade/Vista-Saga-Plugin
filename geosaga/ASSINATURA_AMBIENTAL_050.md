# Assinatura Ambiental — versão 0.5.0

**Escopo:** composição temática de um mapa raster categórico ou de um mapa vetorial poligonal em uma ou mais áreas poligonais de análise.

## Procedimento
1. Instalar ZIP e reiniciar o QGIS 4.x.
2. Painel de módulos → Assinatura Ambiental.
3. Selecionar modalidade Raster ou Vetor; selecionar mapa temático do projeto ou do disco.
4. Selecionar camada de polígonos com as áreas de análise. Campo com nome da área é opcional.
5. Para o modo Vetor, escolher campo de classe e, opcionalmente, nome da classe.
6. Selecionar CSV de destino, calcular e conferir as abas Resultados e os arquivos de saída.

## Saídas
- `base.csv` — ID_AREA, NOME_AREA, CODIGO, CLASSE, PIXELS, AREA_HA, PCT_CLASSE, AREA_AOI_HA, AREA_ANALISADA_HA, COBERTURA_PCT;
- `base_resumo.txt` — estatísticas de cada área, cobertura e predominância;
- `base_areas.gpkg` — `assinatura_areas` com áreas originais e respectivos campos AREA_ID, AREA_NOME, AREA_AOI_HA, AREA_ANAL_HA, COBERT_PCT, CLASSES_N e PREDOMINA.

Os valores de cobertura percentual podem exceder ligeiramente 100% apenas no modo raster por aproximação no limite do pixel. O modo vetorial utiliza interseção geométrica e dissolve automaticamente polígonos da mesma classe. Caso classes diferentes se sobreponham, o usuário pode excluir apenas a região ambígua (padrão), cuja área será documentada, ou interromper a análise (modo estrito).

**Critérios de qualidade:** somente CRS válido; raster monobanda e georreferenciado; vetores poligonais com geometria válida; não sobrescrever fonte. Saídas existentes são confirmadas antes de substituir. Conjuntos são publicados com mecanismo de restauração.

**Limites:** a saída não é um mapa raster novo: o produto espacial é um GeoPackage de áreas enriquecidas; percentuais raster são apurados por pixels válidos, hectares raster apenas para SRC projetado; não executa dissolução de áreas sobrepostas.

**Teste no QGIS** (Console Python):
```python
from geosaga.tests.integration_signature_qgis import run
run()
```

**Legado**: `geosaga:assinatura` permanece disponível para scripts e Processing.

## Ajuste da versão 0.5.1

No modo vetorial foi incluído o grupo **Sobreposição entre classes** com duas opções: excluir área ambígua ou interromper a análise. Se for escolhida a exclusão, a superfície comum a classes distintas não pertence a nenhuma categoria no resultado. As áreas excluídas constam no CSV/TXT e no GPKG (`AREA_CONF_HA`, `PCT_CONF`). O usuário pode corrigir a topologia dos dados originais e repetir a operação, caso precise de cobertura temática completa.
