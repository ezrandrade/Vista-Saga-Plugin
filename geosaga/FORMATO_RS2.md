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
| total de categorias | uint32 | inclui categoria 0 / FUNDO |
| nome categoria zero | CP1252 + `0x00` | sem código precedente |
| nome demais categorias | uint16 + CP1252 + `0x00` | códigos sequenciais começando em 1 |
| início de cada linha | uint32 | número da linha (inicia em 1) |
| bloco RLE | repetidos `(uint16 comprimento, uint16 categoria)` | blocos somam a largura |
| terminador da linha | byte `0x00` | depois do último bloco |
| paleta no final | 32.769 × 4 bytes | vermelho, verde, azul e quarto byte reservado |

A grade é norte-acima: transformada geográfica resultante = `(xmin, dx, 0, ymax, 0, -dy)`.
Em todos os arquivos: `dx=dy=10`. Os campos de coordenadas não identificam
inequivocamente datum, sistema geodésico ou zona UTM. **Nunca atribuir EPSG
por inferência automática**. Confirmar com documentação/cartografia original.

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
