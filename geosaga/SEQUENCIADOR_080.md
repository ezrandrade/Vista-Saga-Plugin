# Sequenciador de Imagens — Vista Saga Plugin 0.8.0

O sequenciador aceita dois ou mais rasters (GeoTIFFs e imagens aceitas pelo QGIS) e gera uma animação GIF89a, sem FFmpeg ou bibliotecas Python extras.

## Operação

1. Abra **Painel de módulos → Sequenciador de Imagens**.
2. Selecione um ou vários mapas do projeto ou do computador.
3. Organize a sequência manualmente ou por data extraída do nome do mapa. Cada item aceita edição do período, incluindo datas não numéricas.
4. Configure tamanho dos quadros, duração de cada quadro, rótulos e legenda temática opcional (para camadas com paleta categórica).
5. Escolha o caminho de um arquivo `.gif`, clique **Gerar GIF** e confira a prévia animada.

## Garantias e limitações

- A exportação usa o renderizador atual de cada camada no QGIS; todos os quadros usam uma extensão espacial comum e o SRC do projeto, sem modificar os rasters originais.
- Quando o conjunto da animação tem até 256 cores RGB diferentes, a paleta GIF preserva todas exatamente. Quadros com mais de 256 cores são quantizados para uma paleta fixa 3-3-2. A quantização pode alterar cores de legendas e imagens fotográficas, por isso compare visualmente antes de utilizar a animação em publicação.
- A inclusão de texto antialiasing poderá aumentar o número de cores acima de 256, acionando quantização.
- O módulo exporta apenas GIF (não MP4), com controle de duração e repetição infinita.
- Limite inicial de até 30 milhões de pixels acumulados em todas as imagens (dimensões do quadro × quadros) para proteção de RAM.
- A escala espacial é fixa visualmente, mas mapas sem georreferenciamento não são suportados. O GIF não contém georreferenciamento e não substitui o processamento estatístico da Monitoria.
- A renderização ocorre pela API do QGIS na thread principal; pode demorar em muitos rasters/quadros. Suporte de cancelamento entre quadros.
- A interface e o renderizador ainda requerem testes no QGIS 4.2.2/Qt6 em Windows e Linux/Flatpak.

## Verificação integrada no QGIS

Abra o Console Python e execute:

```python
from geosaga.tests.integration_image_sequence_qgis import run
run()
```

O comando produz dois rasters sintéticos e um GIF no diretório temporário, sem modificar o projeto existente.
