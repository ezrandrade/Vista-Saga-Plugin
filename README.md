# Vista Saga Plugin

**Complemento independente de geoprocessamento para QGIS 4.x / Qt6**, desenvolvido por **Esdras Andrade (IGDEMA/UFAL)**. O projeto reúne procedimentos de análise geoespacial inspirados conceitualmente no Vista SAGA/UFRJ, **sem incorporar o código do software original** e sem vínculo oficial com seus desenvolvedores.

**Versão:** `1.0.0`. Os sete módulos foram homologados funcionalmente no QGIS 4.2.2 (Windows). A validação Linux/Flatpak, a verificação de instalação limpa e a comparação metodológica com o Vista SAGA/UFRJ permanecem pendentes. O complemento ainda não foi submetido ao repositório oficial do QGIS.

## Módulos

| Módulo | Finalidade |
| --- | --- |
| Assinatura | Distribuição de classes temáticas em unidades espaciais de interesse |
| Monitoria | Comparação entre períodos, mudanças e permanências, relatórios e tendências quando estatisticamente apropriado |
| Avaliação | Análises multicritério por pesos e notas, em raster e vetor |
| Análises Voronoi | Simples, Massa, Atrito, Massa + Atrito e atrito integrado de várias superfícies ponderadas |
| Combinação de Mapas | Cruzamento de mapas categóricos raster e vetoriais |
| Conversão de Formatos | Interoperabilidade RS2 ↔ GeoTIFF e dados vetoriais; rasterização e vetorização |
| Sequenciador de Mapas | Animações Raster, Vetorial e Mista; exportação GIF e quadros PNG |

## Requisitos e instalação

- **QGIS 4.x, Qt6 e Python 3.12 ou compatível com a distribuição QGIS utilizada**. O plugin não foi preparado para o QGIS 3.x.
- Bibliotecas PyQGIS, GDAL/OGR e NumPy do ambiente QGIS. SciPy pode ser usado para acelerar um caso do Voronoi, mas existe alternativa sem SciPy.
- No QGIS, acesse **Complementos → Gerenciar e Instalar Complementos → Instalar a partir de ZIP**, selecione o **ZIP instalável** e reinicie o programa.
- Abra **Raster → Vista Saga Plugin → Painel de módulos** ou use a barra de ferramentas do complemento.

**Atenção:** a pasta Python instalável chama-se `geosaga` de propósito. Não a renomeie para `Vista-Saga-Plugin` ou `vista_saga_plugin`: isso quebraria importações e os identificadores históricos `geosaga:*` utilizados por modelos e projetos antigos.

O código-fonte está em [`geosaga/`](geosaga/); testes de unidade e integração estão em [`geosaga/tests/`](geosaga/tests/). O ZIP de instalação é menor e exclui testes e documentação de desenvolvimento.

## Ressalvas metodológicas

- As modalidades com atrito usam **trajetórias retas** sobre uma superfície raster de resistência; **não** calculam caminhos de custo mínimo.
- Cada célula atravessada contribui com a convenção experimental `1 + atrito_integrado`. A equivalência matemática integral com o **Vista SAGA/UFRJ original não foi demonstrada**.
- Em análises com múltiplas superfícies, mapas devem compartilhar SRC, grade e resolução. Os pesos são normalizados pela soma; notas por classe podem ser informadas como `1=2;2=8` e requerem correspondência para todas as classes representadas.
- Em conversões raster-vetor, os limites dependem da resolução da grade. Para cálculos métricos e de área, utilize CRS projetado apropriado.
- Salve os resultados temporários antes de encerrar o QGIS.

## Desenvolvimento e testes

```bash
python -m compileall -q geosaga
python -m unittest discover -s geosaga/tests -p 'test_*.py'
```

Os testes de integração com QGIS instalado devem ser executados no ambiente PyQGIS. Não interprete os testes unitários automatizados como substitutos de validação funcional no QGIS. Há um roteiro em [`docs/TESTES_E_HOMOLOGACAO.md`](docs/TESTES_E_HOMOLOGACAO.md).

Para criar um ZIP instalável diretamente do código desta branch:

```bash
python scripts/build_release.py
```

## Histórico, suporte e licença

- [Notas da versão 1.0.0](geosaga/NOTAS_DA_VERSAO_100.md)
- [Histórico de alterações](geosaga/CHANGELOG.md)
- [Documentação dos módulos](geosaga/)
- [Reportar problema ou solicitar melhoria](https://github.com/ezrandrade/Vista-Saga-Plugin/issues)

Licença **GNU GPL-3.0-or-later**; consulte [`LICENSE`](LICENSE) e a cópia incluída no pacote do complemento. **Vista Saga Plugin** é uma implementação independente, não uma distribuição oficial do Vista SAGA/UFRJ.

---

*Independent QGIS 4.x plugin for geospatial evaluation, monitoring, signatures, thematic overlays, format conversion, weighted Voronoi analyses and animated raster/vector maps. The seven modules have been functionally tested on QGIS 4.2.2 for Windows; final release validation remains pending.*
