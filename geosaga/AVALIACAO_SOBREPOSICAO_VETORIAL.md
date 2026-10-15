# Avaliação Espacial — sobreposição de camadas vetoriais (0.3.11)

## Para que serve

A modalidade **por atributos** (introduzida na versão 0.3.10) avalia vários campos de uma única camada poligonal, preservando suas feições. A modalidade **por sobreposição** permite **empilhar duas ou mais camadas de polígonos diferentes**, usando um campo de classificação de cada uma e atribuindo pesos/notas independentes por mapa.

A interface de sobreposição é acessível em **Painel de módulos → Avaliação Espacial → Avaliação vetorial por sobreposição…**, ou a partir do botão **Empilhar camadas vetoriais independentes…** da janela de avaliação por atributos.

## Como utilizar

1. Carregue as camadas poligonais no QGIS e confira se estão com o **mesmo SRC**. O plugin não reprojeta automaticamente os dados.
2. Selecione a primeira camada e seu campo temático. Clique em **Adicionar camada**. Ela aparecerá na tabela **Camadas empilhadas e pesos**.
3. Escolha outra camada no seletor, escolha seu campo e clique em **Adicionar camada**. A primeira permanece na tabela. Repita conforme necessário.
4. Selecione cada mapa da tabela para preencher **notas por categoria** e/ou marcar **Excluir**. Ajuste os **pesos** para somarem 100%.
5. Indique um novo GeoPackage de saída e execute. O arquivo original de cada camada não é alterado.

## Regra geométrica e matemática

As camadas são intersectadas sucessivamente (`native:intersection`). Cada combinação espacial de categorias recebe um polígono resultante. **São consideradas apenas as áreas cobertas simultaneamente por TODAS as camadas**. Áreas sem cobertura comum não aparecem no arquivo final. A soma ponderada segue o mesmo núcleo que a modalidade por atributos:

`AVALIACAO = Σ(peso_i × nota_i) / Σ(peso_i)`.

As classes marcadas como *Excluir* e os valores nulos deixam a feição com `AVALIACAO` nulo, `VALIDO=0` e um campo `MOTIVO` explicativo, sem retirar a geometria da área comum. Os campos `C01`, `C02`, etc. registram os códigos originais usados por cada tema; `NOTA_01`, `NOTA_02`, etc. registram as notas atribuídas.

## Condições e limites da versão inicial

- Entrada exclusivamente **polígonos** e **um campo categórico por camada**. Para vários campos de uma única camada, utilize **Avaliação vetorial por atributos**.
- Geometrias inválidas são recusadas e devem ser tratadas com **Corrigir geometrias** no QGIS. Não há simplificação, tolerância de snap nem reprojeção automática.
- As camadas devem compartilhar o mesmo SRC e possuir **área de interseção comum**.
- É recomendável que cada camada temática não contenha feições com **sobreposição interna**, pois isso pode gerar multiplicação de regiões resultantes.
- Valores contínuos com muitas categorias devem ser previamente reclassificados; há limite operacional de 256 classes distintas por critério.
- A sobreposição pode consumir tempo e espaço de armazenamento elevados quando as camadas são extensas e fragmentadas. Intermediários são processados em arquivos temporários na pasta de saída.
- Esta versão não inclui união de cobertura total; apenas interseção de áreas comuns. A união poderá ser avaliada separadamente.
- A execução real da interface e do algoritmo precisa ser homologada no QGIS 4.x. Os testes automatizados locais não substituem essa validação.

## Teste integrado

No Console Python do QGIS, execute:

```python
from geosaga.tests.integration_vector_overlay_qgis import run
print(run())
```

Esse teste cria duas pequenas camadas temporárias, calcula a interseção de 50 unidades quadradas e valida a nota ponderada 5,6 (pesos 40/60 e notas 2/8). Não modifica nenhum arquivo do usuário.
