# Avaliação Espacial Vetorial — versão 0.3.10 (homologação)

A Avaliação Espacial passou a oferecer duas interfaces sem expor o usuário ao Processing:

- **Raster:** interface e procedimento mantidos integralmente, com projetos `.geosaga.json` legados.
- **Vetor por atributos:** primeira modalidade funcional para uma camada poligonal com vários campos temáticos. A avaliação por sobreposição de várias camadas poligonais independentes ainda não foi implementada.

## Uso

1. Carregue uma camada **poligonal** no projeto do QGIS. Salve as edições pendentes.
2. Abra `Painel de módulos → Avaliação Espacial → Avaliação vetorial por atributos…`.
3. Escolha a camada na lista nativa do QGIS e selecione um campo categórico.
4. Clique em `Adicionar campo`. Repita para cada critério de avaliação.
5. Ajuste os pesos (soma 100%) e selecione cada campo à esquerda para atribuir as notas a todas as suas categorias (0–10 ou 0–100), ou marque as categorias que serão excluídas.
6. Salve como GeoPackage. Clique em `Validar` e `Executar avaliação`.

O resultado conserva as geometrias e os atributos de entrada; adiciona `AVALIACAO` (nota final), `VALIDO` (1/0), `MOTIVO` (ausência de dado/exclusão) e `NOTA_01`, `NOTA_02`, ... (notas individuais por critério). A camada original não é modificada. Se houver classe excluída ou valor nulo em algum critério, a nota final da feição é nula, **sem redistribuição de pesos**. Registros sem avaliação não são apagados.

### Limitações deliberadas desta primeira modalidade

- A camada de entrada já deve possuir atributos categóricos. Campos numéricos contínuos com mais de 256 valores diferentes exigem reclassificação prévia; não há ainda classificação automática por intervalos dentro da Avaliação Espacial vetorial.
- A interface não salva um projeto de regras vetoriais próprio nesta versão; o formato legado de projeto raster permanece inalterado.
- Apenas **GeoPackage** é oferecido como saída da avaliação, permitindo evitar perdas de atributos. Caso precise de SHP/GeoJSON/FGB, exporte a camada pelo QGIS depois de conferir o resultado.
- As feições são avaliadas por seus próprios atributos; **não há interseção espacial de múltiplas camadas** nesta fase.
- Para bases muito grandes, o processamento roda na thread da interface com progresso/cancelamento, não como tarefa em background. A futura otimização deverá empregar execução em lotes e tarefas seguras para o PyQGIS.
- Se existir um GeoPackage de saída aberto no QGIS, remova-o do projeto antes de substituí-lo, especialmente em Windows (bloqueio de arquivo).

## Teste integrado no Console Python do QGIS 4.x

```python
from geosaga.tests.integration_vector_evaluation_qgis import run
run()
```

A validação aqui realizada é do **núcleo matemático e do pacote Python**, sem ambiente de execução PyQGIS 4.x. A janela, a gravação GeoPackage e a compatibilidade com Windows/Linux Flatpak precisam de testes no QGIS.
