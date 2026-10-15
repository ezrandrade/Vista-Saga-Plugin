# Vista Saga Plugin 0.8.1 — ajuste experimental de desempenho do Voronoi por atrito

## Motivação

O bloqueio da versão 0.7.4 (“O cálculo exato de atrito em segmentos retos é muito extenso...”) ocorria antes de executar o cálculo, quando a estimativa `altura × largura × centros × (altura + largura) / 4` ultrapassava 700 milhões. Esse indicador parte da hipótese de executar todas as trajetórias para todos os pontos geradores e não é uma medição da carga efetiva de trabalho.

## Otimização conservadora

Para cada célula e centro, calcula-se um **limite inferior matematicamente seguro** para o escore de atrito. Com custo basal `b > 0` e resistência não negativa, a quantidade de células percorridas é ao menos `1 + max(|Δcol|, |Δlin|)` e o escore possível é pelo menos `D × b × número_mínimo / massa` (quando aplicável). Os centros são avaliados em ordem crescente desse limite inferior. Quando o limite inferior de um centro supera o melhor escore exato conhecido, ele é descartado **sem calcular o percurso**, pois não pode vencer. Empates continuam respeitando a ordem original dos centros.

O algoritmo **não interpola** o atrito, **não reprojeta** o raster e **não muda** o modelo `D × Σ(1 + C_k)`, ou `D × Σ(1 + C_k) / M` na quarta modalidade. A convenção de custo basal 1 continua experimental e não representa comprovação de fidelidade ao Vista SAGA/UFRJ.

## Limitações que permanecem

- A otimização reduz a quantidade de percursos, mas **não garante execução rápida** para grandes grades, muitos pontos ou altos níveis de atrito. O pior caso pode continuar exigindo muitas trajetórias e a conclusão pode levar muito tempo.
- Permanecem as proteções de **8 milhões de células** e **500 centros**, a validação de SRC/grade, o tratamento de NoData e a execução como `QgsTask` cancelável.
- A versão 0.8.1 foi verificada por testes matemáticos com superfícies sintéticas. **Ainda não foi homologada no QGIS 4.2.2** com os dados reais que produziram o aviso.
- Para comprovar equivalência com o Vista SAGA original, serão necessários pontos, raster de atrito e resultados de referência do executável histórico. Nenhum modelo de custo mínimo foi substituído pelo traçado direto sem consentimento do usuário.

## Teste recomendado

1. Instale a 0.8.1 e reinicie completamente o QGIS.
2. Execute primeiro uma grade pequena (recorte do raster de declividade com os pontos na área), conferindo se o resultado diferencia corretamente as áreas de atrito.
3. Repita a grade completa, observando o progresso e usando Cancelar se o tempo for excessivo.
4. Registre dimensões da grade, resolução, quantidade de pontos, tempo decorrido e eventual erro para calibrarmos desempenho.
