# Vista Saga Plugin — versão 1.0.4

Complemento independente para **QGIS 4.x / Qt6**, desenvolvido por **Esdras Andrade (IGDEMA/UFAL)**. O programa moderniza procedimentos de análise geoespacial inspirados conceitualmente no Vista SAGA/UFRJ, sem incorporar o código deste. Não há vínculo institucional com os desenvolvedores do Vista SAGA/UFRJ original.

> **Versão 1.0.4:** os sete módulos estão homologados funcionalmente em português e inglês na rc4. A compatibilidade com Windows 11 e Linux/Flatpak foi testada e aprovada pelo responsável. Na interface clássica, o botão suspenso está na barra própria **Vista Saga Plugin**, com ícone limitado a 24 px; se ocultada, reative em **Exibir → Barras de ferramentas → Vista Saga Plugin**. No **QRibbonSkin**, utilize **Complementos → Vista Saga Plugin**: o botão visual com ícone e menu é criado a partir da mesma ação nativa do QGIS. Se o QRibbonSkin já estava ativado durante a instalação/atualização, volte à interface clássica e ative a Ribbon novamente para que ela reconstruia a guia de complementos.

## Sete módulos

1. **Assinatura** — distribuição de classes temáticas dentro de polígonos de interesse.
2. **Monitoria** — mudanças e permanências entre períodos, mapas, matrizes e relatórios; séries temporais maiores permitem análise de tendências quando atendidas as condições estatísticas.
3. **Avaliação** — classificação multicritério com pesos e notas, em raster ou vetores.
4. **Análises Voronoi** — Simples, Massa, Atrito e Massa + Atrito; atrito único ou composição de múltiplos rasters com pesos e notas por classe.
5. **Combinação de Mapas** — cruzamento categórico e cálculo de áreas, em raster ou vetor.
6. **Conversão de Formatos** — RS2/GeoTIFF/vetor, incluindo vetorização e rasterização.
7. **Sequenciador de Mapas** — três abas Raster/Vetorial/Misto, ordenação temporal, GIF animado e PNGs opcionais, preservando as camadas de origem.

## Instalação e compatibilidade

1. No QGIS 4.x, abra **Complementos → Gerenciar e instalar complementos → Instalar a partir de ZIP**.
2. Selecione o ZIP de **instalação** (não o pacote de código-fonte), instale e reinicie o QGIS.
3. Acesse **Raster → Vista Saga Plugin → [módulo]**, ou clique no botão do Vista Saga Plugin na barra de complementos para abrir o menu suspenso de módulos.

O complemento usa PyQGIS/Qt6, GDAL/OGR, NumPy e bibliotecas disponibilizadas pela instalação do QGIS; SciPy pode acelerar um caso específico do Voronoi, mas há alternativa de cálculo sem SciPy. Não são distribuídos executáveis nem bibliotecas compiladas no ZIP. A execução em Linux/Flatpak já foi testada e aprovada pelo responsável pelo projeto. Esta versão exige QGIS 4.x e não foi preparada para QGIS 3.x.

O diretório interno `geosaga` e identificadores Processing `geosaga:*` são **intencionalmente mantidos** para preservar a compatibilidade com projetos e scripts anteriores. **Não** renomeie manualmente essa pasta para `vista_saga_plugin`.

## Atenção à metodologia

- Para **Atrito** e **Massa + Atrito**, o motor percorre trajetórias retas no raster de resistência; **não** calcula caminhos de menor custo acumulado em rede.
- O custo experimental por célula é `1 + atrito_integrado`; a influência considera distância e massa conforme a modalidade. A equivalência numérica com as rotinas originais Vista SAGA/UFRJ **não foi demonstrada**.
- A composição de múltiplas superfícies requer grades com mesmo SRC, resolução e alinhamento. Os pesos são normalizados pela soma; as notas por classe usam, por exemplo, `1=2;2=8`. Para rasters contínuos, recomenda-se padronizar primeiro a resistência para uma escala comum.
- Em operações raster, resultados vetoriais de poligonização são dependentes da resolução das células. Trabalhe em SRC projetado apropriado para medidas métricas.
- Resultados temporários devem ser salvos permanentemente antes de encerrar o QGIS.

## Verificações adicionais recomendadas

- Instalar em **perfil QGIS 4.x limpo**, sem outros complementos de terceiros.
- Abrir cada módulo, carregar e processar amostras pequenas, salvar/reabrir o projeto, desativar e reativar o complemento.
- Reconfirmar a instalação limpa e a iconografia em diferentes distribuições do QGIS; Windows e Linux/Flatpak já foram testados e aprovados pelo responsável.
- Comparar dados e resultados contra software histórico, quando disponível, para estabelecer o grau de equivalência da metodologia Voronoi com atrito.
- Verificar os links `homepage`, `repository` e `tracker` no `metadata.txt` antes de submeter ao repositório oficial de complementos QGIS.

## Licença e atribuição

O código deste complemento é distribuído sob **GNU GPL-3.0-or-later**; o texto integral está no arquivo [`LICENSE`](LICENSE). Autoria do complemento: **Esdras Andrade**. Documentação e resultados desta implementação não representam certificação pelo Vista SAGA/UFRJ ou pela Universidade Federal do Rio de Janeiro.

Para histórico completo de evolução, ensaios e testes de desenvolvimento, consulte o **pacote de código-fonte**, distribuído separadamente.


### Integração QRibbonSkin (rc9)

A guia Raster e o menu nativo de Complementos apresentam **uma única ação**
com ícone próprio e submenu com os sete módulos. Na interface Ribbon, abra
**Raster → Vista Saga Plugin** ou **Complementos → Vista Saga Plugin**; não
há mais sete botões distribuídos em três comandos e “Outras ferramentas”.
Na interface padrão, a barra exclusiva mantém o mesmo botão com ícone de
24 pixels. Ao atualizar o ZIP, reinicie o QGIS e reative a Ribbon, pois o
QRibbonSkin monta os controles a partir dos menus nativos ao ser ativado.


### Integração visual com QRibbonSkin (rc10)

A ação principal aparece somente como **Vista Saga Plugin** (português e inglês),
com o menu suspenso nativo dos sete módulos. O QMenu continua sob o controle
do QGIS/Qt, e o QRibbonSkin utiliza seus próprios controles para renderizá-lo
em seu padrão visual. A imagem do ícone tem uma versão otimizada em 19 × 19 px,
resolução usada pelo QRibbonSkin v1.1.44 nos botões principais. Na interface
clássica, conserva-se o ícone de 24 × 24 px.

Não há dependência de importação do QRibbonSkin, personalização global de tema
nem mudança no processamento. Após a instalação, reinicie o QGIS e reative a
Ribbon para garantir a reconstrução dos menus.


## Site oficial

[Vista Saga Plugin — página WordPress](https://vistasagaplugin.wordpress.com/) · [Código-fonte e colaboração no GitHub](https://github.com/ezrandrade/Vista-Saga-Plugin).
