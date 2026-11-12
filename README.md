# Vista Saga Plugin

<p align="center"><img src="docs/assets/vista-saga-mark.png" width="160" alt="Vista Saga Plugin — mão sustentando o globo" /></p>

**Complemento independente de geoprocessamento para QGIS 4.x / Qt6**, desenvolvido por **Esdras Andrade (IGDEMA/UFAL)**. O projeto reúne procedimentos de análise geoespacial inspirados conceitualmente no Vista SAGA/UFRJ, **sem incorporar o código do software original** e sem vínculo oficial com seus desenvolvedores.

**Site oficial e apresentação do projeto:** [vistasagaplugin.wordpress.com](https://vistasagaplugin.wordpress.com/) · **Código-fonte:** [GitHub](https://github.com/ezrandrade/Vista-Saga-Plugin)

**Versão do código-fonte: `1.1.0` (12/11/2026).** Módulo Avaliação reorganizado: as guias Vetorial (Atributos) e Vetorial (Sobreposição) seguem o padrão da guia Raster, o resultado é carregado automaticamente no QGIS e cada execução grava um arquivo de pesos e notas reaproveitável; interface completa em **português, inglês e espanhol**. Inclui o ícone principal da 1.0.9, a conversão **Vetor → RS2** e as correções do formato RS2 da 1.0.6 e as correções de estabilidade da 1.0.5. A **versão publicada atualmente no catálogo oficial do QGIS ainda é a `1.0.3`**, até que a nova seja submetida e aprovada.

> **ZIP instalável:** gere-o com `python scripts/build_release.py` (cria `dist/Vista_Saga_Plugin_QGIS4_v<versão>.zip`). Não utilize **Code → Download ZIP** como se fosse o ZIP instalável. [Notas da versão 1.1.0](geosaga/NOTAS_DA_VERSAO_110.md) · [Testes](tests/README.md).

## Módulos

| Módulo | Finalidade |
| --- | --- |
| Assinatura | Distribuição de classes temáticas em unidades espaciais de interesse |
| Monitoria | Comparação entre períodos, mudanças e permanências, relatórios e tendências quando estatisticamente apropriado |
| Avaliação | Análises multicritério por pesos e notas, em raster e vetor |
| Análises Voronoi | Simples, Massa, Atrito, Massa + Atrito e atrito integrado de várias superfícies ponderadas |
| Combinação de Mapas | Cruzamento de mapas categóricos raster e vetoriais |
| Conversão de Formatos | Interoperabilidade RS2 ↔ GeoTIFF e dados vetoriais, incluindo Vetor → RS2; rasterização e vetorização |
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

- As modalidades com atrito usam **trajetórias retas** sobre uma superfície raster de resistência; **não** calculam caminhos de custo mínimo.
- Cada célula atravessada contribui com a convenção experimental `1 + atrito_integrado`. A equivalência matemática integral com o **Vista SAGA/UFRJ original não foi demonstrada**.
- Em análises com múltiplas superfícies, mapas devem compartilhar SRC, grade e resolução. Os pesos são normalizados pela soma; notas por classe podem ser informadas como `1=2;2=8` e requerem correspondência para todas as classes representadas.
- Em conversões raster-vetor, os limites dependem da resolução da grade. Para cálculos métricos e de área, utilize CRS projetado apropriado.
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

*Independent QGIS 4.x plugin for geospatial evaluation, monitoring, signatures, thematic overlays, format conversion, weighted Voronoi analyses and animated raster/vector maps. The seven modules have been functionally tested on QGIS 4.2 for Windows and on Linux/Flatpak. Source version 1.1.0 reorganises the Evaluation module (vector tabs aligned with the Raster tab, results loaded automatically, reusable weights-and-scores file) and provides a complete Portuguese, English and Spanish interface. The installable ZIP is built with `python scripts/build_release.py`; GitHub Releases and submission to the official QGIS plugin repository will follow the final version.*
