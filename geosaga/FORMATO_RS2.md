> Situação 0.3.4: o usuário confirmou abertura bem-sucedida de RS2 criado pelo conversor no Vista SAGA original; a interface em QGIS 4.x e a conversão em lote ainda precisam de testes de homologação.

# RS2 do Vista SAGA — especificação experimental identificada

## Amostras e alcance

O formato foi deduzido de cinco arquivos RS2 autênticos fornecidos pelo usuário:
`GEOM`, `USO`, `COTA`, `DECL` e `LITO`. Os quatro mapas com GeoTIFF RGB de
referência (`GEOM`, `USO`, `DECL`, `LITO`) tiveram todas as suas 62.494.740
células comparadas com a cor esperada na paleta do RS2: **zero divergências**.
Cada arquivo também passou por reconstrução RS2 → pixels → RS2 **idêntica
byte a byte**. O TIFF correspondente a COTA não foi fornecido, mas os dados
RLE e cabeçalhos foram percorridos e validados integralmente.

## Layout observado

A variante tem ordem de bytes little-endian e a seguinte organização:

| Campo | Tipo | Observação |
| --- | --- | --- |
| Prefixo legado | 11 bytes | significado integral ainda não determinado; deve ser preservado |
| ymin, xmin, ymax, xmax | 4 × uint32 | coordenadas de borda (unidade projetada, provavelmente metros) |
| linhas, colunas | 2 × uint16 | todas as amostras 4.455 × 3.507 |
| total de categorias | **uint16** | correção 1.0.6: antes lido como uint32 |
| categorias | n × (uint16 código + CP1252 + `0x00`) | **inclusive a primeira**; códigos únicos, não necessariamente consecutivos (1.0.5) nem iniciados em 0 (1.0.6) |
| início de cada linha | uint32 | número da linha (inicia em 1) |
| bloco RLE | repetidos `(uint16 comprimento, uint16 categoria)` | blocos somam a largura |
| terminador da linha | byte `0x00` | depois do último bloco |
| paleta | 32.769 × 4 bytes | indexada pelo **código**; vem logo após a matriz; vermelho, verde, azul e quarto byte reservado |

A grade é norte-acima: transformada geográfica resultante = `(xmin, dx, 0, ymax, 0, -dy)`.
Em todos os arquivos: `dx=dy=10`. Os campos de coordenadas não identificam
inequivocamente datum, sistema geodésico ou zona UTM. **Nunca atribuir EPSG
por inferência automática**. Confirmar com documentação/cartografia original.

## Correção 1.0.5 — evidência de um RS2 gravado pelo próprio Vista SAGA

Um mapa de pluviometria rasterizado pelo plugin com os códigos 125 e 158 declarava
159 classes (0..158). O módulo de **visualização** do Vista SAGA mostrava as 2 classes,
mas o módulo de **avaliação** listava todas as 159. O usuário salvou uma cópia pelo
módulo de visualização, e a comparação byte a byte mostrou:

1. **Legenda esparsa:** o Vista SAGA gravou `n = 3` e a legenda `0 FUNDO`, `125`, `158`.
   Os códigos não precisam ser consecutivos; os pares RLE usam os próprios códigos
   (matriz RLE idêntica à do plugin). A dedução anterior ("códigos sequenciais a partir
   de 1") vinha apenas de amostras que, por acaso, eram consecutivas.
2. **Paleta indexada pelo código**, gravada imediatamente após a matriz.
3. **Bytes residuais:** a cópia terminava com 1.920 bytes nulos após a paleta, a mesma
   quantidade que a legenda encolheu; o arquivo foi aparentemente regravado sem
   truncamento. O leitor localiza a paleta pelo fim da matriz e ignora o resíduo.
4. **Prefixo (hipótese, não confirmada):** os bytes 3–5 passaram de `12 0c 13` para
   `0b 0b 1a`, compatível com a data de gravação (dia, mês, ano − 2000): 18/12/2019 nas
   amostras e 11/11/2026 na cópia. O plugin continua gravando o prefixo das amostras.

Regravado pelo plugin, o arquivo do Vista SAGA é reproduzido **byte a byte** (sem o
resíduo). Arquivos com legenda consecutiva continuam idênticos aos de antes.

## Correção 1.0.6 — RS2 gerado pelo módulo de avaliação do Vista SAGA

Um RS2 de avaliação (notas 1 a 10) era recusado com "Quantidade de classes RS2 inválida":
os 4 bytes lidos como quantidade valiam `0b 00 01 00` = 65.547. Na verdade são **dois campos
uint16**: a quantidade (11) e o **código da primeira classe** (1). Cada classe, inclusive a
primeira, é precedida do seu código. Nas amostras anteriores, a primeira classe era o FUNDO com
código 0, e os bytes `00 00` passavam despercebidos como parte alta de um uint32.

No arquivo da avaliação, as notas usam os códigos 1–10 e o **FUNDO é o código 11, gravado por
último**; não há código 0. O plugin passa a tratar como FUNDO o código 0, quando existe, ou a
classe chamada FUNDO; esse código vira NoData no GeoTIFF e é omitido na vetorização. Os bytes
6–9 do prefixo diferem nesse arquivo (`05 00 17 00`, contra `0a 00 19 00` nos demais); seu
significado continua desconhecido. Os bytes 3–5 voltaram a coincidir com a data de gravação.

A gravação é idêntica byte a byte à anterior quando a primeira classe tem código 0; os três
arquivos de teste (amostra regravada pelo Vista SAGA, saída do plugin e avaliação) são
reproduzidos byte a byte.

## Convenções do conversor

- **RS2 → GeoTIFF**: produz banda única com códigos inteiros das categorias,
  compressão DEFLATE, nomes das classes e tabela de cores, além do arquivo
  lateral `<arquivo>.tif.rs2.json`. O fundo 0 pode ser gravado como NoData
  no GeoTIFF, sem alterar os valores efetivos dos pixels.
- **GeoTIFF → RS2**: aceita raster categórico de banda única, norte-acima,
  não rotacionado, com limites inteiros e valores inteiros de categorias
  suportados. Na versão 0.3.3, aceita também RGB/RGBA de 8 bits, **com**
  RS2 original correspondente para recuperar exatamente os códigos legados,
  ou **sem** referência, criando uma nova codificação a partir das cores.
  O TIFF sem coordenadas exige extensão espacial informada manualmente
  (ou referência RS2 correspondente).
- Os nomes das classes devem caber na página CP1252. O `.rs2.json` armazena
  os nomes, cores, limite espacial e uma versão comprimida da paleta original
  para reversibilidade de arquivos provenientes do RS2.
- A escrita da variante RS2 foi validada byte a byte nas cinco amostras,
  **mas a abertura por instalações do Vista SAGA original ainda precisa ser testada**.
- Os metadados do EPSG ficam **fora** do RS2, no arquivo `.rs2.json` da saída.

## Restrições conhecidas

1. RGB com referência exige cores exatas e paleta RS2 sem duplicatas. RGB sem referência cria novos códigos por cor (sem recuperar nomes antigos), limitado a 32.769 cores distintas, e requer georreferenciamento no TIFF ou coordenadas manuais. Coordenadas fracionárias continuam não suportadas na escrita.
2. A semântica do prefixo de 11 bytes não foi integralmente determinada.
3. A variante ainda não foi testada com exemplares RS2 externos ao conjunto
   fornecido, incluindo arquivos de alta profundidade radiométrica ou de
   dimensões extremas. Outros subtipos poderão exigir novos leitores.
4. A interface QGIS/Qt6 e as chamadas GDAL devem ser homologadas no
   QGIS 4.x em Windows e Linux/Flatpak antes de publicação.
5. Preservar a classe 0 como fundo/NoData pode afetar análises que precisem
   explicitamente contabilizá-la: habilite ou desabilite NoData conforme o estudo.

## Testes locais

A partir da pasta pai de `geosaga`, executar:

```bash
python -m unittest discover -s geosaga/tests -p 'test_*.py' -v
```

Para testar a integração gráfica, instale o ZIP pelo Gerenciador de Complementos
e acesse **Raster → Vista Saga Plugin → Conversor RS2 ↔ GeoTIFF**.

## Teste de regressão adicional RGB (0.3.2)

As quatro imagens RGB fornecidas foram convertidas com as respectivas
paletas RS2: os quatro arquivos reconstruídos foram **idênticos byte por
byte** aos originais. Testado com leitura matricial independente (rasterio)
e núcleo de escrita RS2, sem depender da interface QGIS. A chamada GDAL e
a interface do QGIS ainda precisam de homologação nas instalações-alvo.
