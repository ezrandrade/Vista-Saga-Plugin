# Vista Saga Plugin

<p align="center"><img src="docs/assets/vista-saga-mark.png" width="160" alt="Vista Saga Plugin — mão sustentando o globo" /></p>

**Complemento independente de geoprocessamento para QGIS 4.x / Qt6**, desenvolvido por **Esdras Andrade (IGDEMA/UFAL)**. O projeto reúne procedimentos de análise geoespacial inspirados conceitualmente no Vista SAGA/UFRJ, **sem incorporar o código do software original** e sem vínculo oficial com seus desenvolvedores.

**Site oficial e apresentação do projeto:** [vistasagaplugin.wordpress.com](https://vistasagaplugin.wordpress.com/) · **Código-fonte:** [GitHub](https://github.com/ezrandrade/Vista-Saga-Plugin)

**Versão do código-fonte: `1.6.1` (20/11/2026): dicas em todos os botões, campos, caixas de marcar e listas dos sete módulos (1.6.0) e aprovação na varredura de segurança do catálogo do QGIS (1.6.1).** Versão `1.5.0` (20/11/2026): **Assinatura** refeita no modelo do Vista SAGA e validada contra o programa original; Conversor de Formatos com paleta e estilo `.qml` nos GeoTIFF; resultados temporários com o nome "Módulo - operação". Versões `1.4.x` (19/11/2026): **Voronoi fiel ao Vista SAGA** (M/d²; atrito pelo custo do Vista SAGA), validado célula a célula; rodapé padrão em todos os módulos. Histórico completo no [CHANGELOG](geosaga/CHANGELOG.md). A **versão publicada atualmente no catálogo oficial do QGIS ainda é a `1.0.4`**, até que a nova seja submetida e aprovada.

> **ZIP instalável:** gere-o com `python scripts/build_release.py` (cria `dist/Vista_Saga_Plugin_QGIS4_v<versão>.zip`). Não utilize **Code → Download ZIP** como se fosse o ZIP instalável. [Notas da versão 1.6.1](geosaga/NOTAS_DA_VERSAO_161.md) · [Testes](tests/README.md).

## Módulos

| Módulo | Finalidade |
| --- | --- |
| Assinatura | Do que é feita uma área selecionada num mapa de referência, em cada mapa da lista (modelo do Vista SAGA) |
| Monitoria | Comparação entre períodos, mudanças e permanências, relatórios e tendências quando estatisticamente apropriado |
| Avaliação | Análises multicritério por pesos e notas, em raster e vetor |
| Análises Voronoi | Simples, Massa, Atrito, Massa + Atrito e atrito integrado de várias superfícies ponderadas |
| Combinação de Mapas | Cruzamento de mapas categóricos raster e vetoriais |
| Conversor de Formatos | Interoperabilidade RS2 ↔ GeoTIFF e dados vetoriais, incluindo Vetor → RS2; rasterização e vetorização |
| Sequenciador de Mapas | Animações Raster, Vetorial e Mista; exportação GIF e quadros PNG |

## Requisitos e instalação

- **QGIS 4.x, Qt6 e Python 3.12 ou compatível com a distribuição QGIS utilizada**. O plugin não foi preparado para o QGIS 3.x.
- Bibliotecas PyQGIS, GDAL/OGR e NumPy do ambiente QGIS. SciPy pode ser usado para acelerar um caso do Voronoi, mas existe alternativa sem SciPy.
- No QGIS, acesse **Complementos → Gerenciar e Instalar Complementos → Instalar a partir de ZIP**, selecione o **ZIP instalável** e reinicie o programa.
- A interface segue o idioma do QGIS: **português, inglês ou espanhol** (nos demais idiomas, inglês). Os relatórios CSV/TXT são sempre gravados em português.
- Na versão 1.0.4 consolidada, o painel foi substituído por **um único botão Vista Saga Plugin com menu suspenso**, oferecendo acesso direto aos sete módulos (também disponível nos menus nativos do QGIS e na guia Complementos do QRibbonSkin). O menu suspenso mantém o indicador no canto inferior nesta versão, conforme homologado.

**Atenção:** a pasta Python instalável chama-se `geosaga` de propósito. Não a renomeie para `Vista-Saga-Plugin` ou `vista_saga_plugin`: isso quebraria importações e os identificadores históricos `geosaga:*` utilizados por modelos e projetos antigos.

O código-fonte está em [`geosaga/`](geosaga/); testes de unidade e integração estão em [`geosaga/tests/`](geosaga/tests/). O ZIP de instalação é menor e exclui testes e documentação de desenvolvimento.

## Ressalvas metodológicas

- **Voronoi com atrito:** modelo do Vista SAGA (soma, nas células da reta polo-célula, de distância ao polo × nota × passo; a nota é o próprio custo). Não é caminho de custo mínimo. Validação contra o Vista SAGA original: Simples e Com Massa 100% das células; com atrito, 99,4% a 99,7%, diferenças na fronteira entre regiões ([notas da 1.4.0](geosaga/NOTAS_DA_VERSAO_140.md)).
- **Assinatura:** validada contra o Vista SAGA original (mapa inteiro 100%; seleções parciais iguais, salvo células ligadas à classe só pela diagonal) ([notas da 1.5.0](geosaga/NOTAS_DA_VERSAO_150.md)).
- Mapas analisados em conjunto devem compartilhar SRC e, no raster, grade e resolução; para áreas, use SRC projetado em metros.
- Em conversões raster-vetor, os limites dependem da resolução da grade.
- Salve os resultados temporários antes de encerrar o QGIS.

## Desenvolvimento e testes

```bash
python -m compileall -q geosaga
python -m unittest discover -s geosaga/tests -p 'test_*.py'
python -m pytest -q tests/unit
```

Os testes de integração com QGIS instalado devem ser executados no ambiente PyQGIS. Não interprete os testes unitários automatizados como substitutos de validação funcional no QGIS. Há um roteiro em [`docs/TESTES_E_HOMOLOGACAO.md`](docs/TESTES_E_HOMOLOGACAO.md).

Para criar um ZIP instalável diretamente do código desta branch:

```bash
python scripts/build_release.py
```

## Histórico, suporte e licença

- [Notas da versão 1.6.1 (varredura de segurança do catálogo)](geosaga/NOTAS_DA_VERSAO_161.md)
- [Notas da versão 1.6.0 (dicas em todos os módulos)](geosaga/NOTAS_DA_VERSAO_160.md)
- [Notas da versão 1.5.0 (Assinatura no modelo do Vista SAGA)](geosaga/NOTAS_DA_VERSAO_150.md)
- [Notas da versão 1.4.2](geosaga/NOTAS_DA_VERSAO_142.md) · [1.4.1](geosaga/NOTAS_DA_VERSAO_141.md) · [1.4.0 (Voronoi fiel ao Vista SAGA)](geosaga/NOTAS_DA_VERSAO_140.md)
- [Notas da versão 1.3.0 (Voronoi com guias Raster e Vetorial; vetor exato Com Massa)](geosaga/NOTAS_DA_VERSAO_130.md)
- [Notas da versão 1.2.1 (correções de interface)](geosaga/NOTAS_DA_VERSAO_121.md)
- [Notas da versão 1.2.0 (Conversor de Formatos, Combinação, Sequenciador e Monitoria)](geosaga/NOTAS_DA_VERSAO_120.md)
- [Notas da versão 1.1.0 (Avaliação no padrão da guia Raster; interface em espanhol)](geosaga/NOTAS_DA_VERSAO_110.md)
- [Notas da versão 1.0.9 (ícone principal em alta qualidade)](geosaga/NOTAS_DA_VERSAO_109.md)
- [Notas da versão 1.0.8 (novos ícones)](geosaga/NOTAS_DA_VERSAO_108.md)
- [Notas da versão 1.0.6 (Vetor → RS2 e formato RS2)](geosaga/NOTAS_DA_VERSAO_106.md)
- [Notas da versão 1.0.5 (estabilidade)](geosaga/NOTAS_DA_VERSAO_105.md)
- [Notas da versão 1.0.4 (pacote consolidado)](geosaga/NOTAS_DA_VERSAO_104.md)
- [Notas da versão 1.0.3](geosaga/NOTAS_DA_VERSAO_103.md)
- [Histórico de alterações](geosaga/CHANGELOG.md)
- [Documentação dos módulos](geosaga/)
- [Reportar problema ou solicitar melhoria](https://github.com/ezrandrade/Vista-Saga-Plugin/issues)

Licença **GNU GPL-3.0-or-later**; consulte [`LICENSE`](LICENSE) e a cópia incluída no pacote do complemento. **Vista Saga Plugin** é uma implementação independente, não uma distribuição oficial do Vista SAGA/UFRJ.

---

*Independent QGIS 4.x plugin for geospatial evaluation, monitoring, signatures, thematic overlays, format conversion, weighted Voronoi analyses and animated raster/vector maps. The seven modules have been functionally tested on QGIS 4.2 for Windows and on Linux/Flatpak. Source version 1.2.0 renames the conversion module to "Format converter", loads Map combination and Monitoring results automatically, tolerates coordinate slivers and merges crossing residues in vector combination, lets Monitoring tables be copied to spreadsheets and removes the Mann-Kendall test for now (returning as a module in 2.0); version 1.1.0 reorganised the Evaluation module (vector tabs aligned with the Raster tab, results loaded automatically, reusable weights-and-scores file) and provides a complete Portuguese, English and Spanish interface. The installable ZIP is built with `python scripts/build_release.py`; GitHub Releases and submission to the official QGIS plugin repository will follow the final version.*
