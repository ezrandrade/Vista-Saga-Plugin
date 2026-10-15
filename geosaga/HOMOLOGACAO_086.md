# Protocolo de homologação — Vista Saga Plugin 0.8.6

## Compatibilidade e instalação

Instalar pelo ZIP, sem criar uma pasta paralela ao complemento `geosaga` que já existe no QGIS. Reiniciar o QGIS 4.2.2. Conferir se o nome público exibido é **Vista Saga Plugin** e se o cartão do módulo se chama **Análises Voronoi**. Reiniciar novamente e verificar a abertura de um projeto salvo (preferencialmente uma cópia de teste).

## Análises Voronoi — desempenho e consistência

Executar Com Atrito e Com Massa e Atrito com os mesmos pontos e a mesma superfície (pode ser uma superfície integrada de duas camadas); manter a resolução de 10 m e a mesma extensão de seu teste anterior. Usar caminhos de saída diferentes e não sobrescrever resultados homologados.

Verificar nos arquivos `*_resumo.txt`: `Tempo do cálculo matricial (s)`, `Trajetórias calculadas`, `Trajetórias interrompidas durante o cálculo`, `Células atravessadas e avaliadas`, `Pares descartados`. Comparar tempos e examinar os mapas resultantes: os centros e as áreas de influência devem permanecer coerentes com a versão anterior. NoData é barreira; os valores zero permanecem válidos. Como a poda é matematicamente exata, a classificação obtida para entradas idênticas deve ser a mesma da versão 0.8.5 (exceto diferenças não determinísticas fora do núcleo testado). A otimização não deve ser tomada como prova de equivalência com Vista SAGA/UFRJ.

## Sequenciador de Imagens — homologação pendente

Abrir **Sequenciador de Imagens** e adicionar ao menos três GeoTIFFs, por exemplo, mapas temáticos de anos diferentes. Ajustar a ordem e as datas, habilitar rótulo temporal e nome do mapa e selecionar saída GIF. Testar 800 × 450 pixels e 1000 ms/quadro. Verificar no arquivo final que todos os quadros têm o mesmo recorte, são apresentados na ordem prevista e que as cores/legendas permanecem legíveis. GIF com mais de 256 cores é quantizado e pode ter cores alteradas; comparar visualmente os quadros no GIF com a visualização do QGIS. Fechar e reabrir a janela para verificar estabilidade.

Testes com dados sintéticos no Console Python do QGIS (não modificam fontes dos projetos):

```python
from geosaga.tests.integration_image_sequence_qgis import run
run()
```

```python
from geosaga.tests.integration_voronoi_stack_qgis import run
run()
```

A aprovação desses testes integrados ainda depende de execução efetiva em QGIS 4.2.2/Qt6 Windows ou ambiente compatível. Se ocorrer uma exceção, enviar a mensagem e o traceback completo.

## Condições para candidatura 1.0

Exigir homologação visual e de exportação do GIF, teste de estabilidade com projetos salvos, comparação do Atrito com resultados de referência do Vista SAGA/UFRJ ou documentação metodológica equivalente e checagem final das exigências do repositório QGIS (metadados, licença, arquivo de ícone e dependências). Enquanto isso, manter a marcação de versão experimental.
