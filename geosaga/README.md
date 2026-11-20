# Vista Saga Plugin — versão 1.6.0

Complemento independente para **QGIS 4.x / Qt6**, desenvolvido por **Esdras Andrade (IGDEMA/UFAL)**. O programa moderniza procedimentos de análise geoespacial inspirados conceitualmente no Vista SAGA/UFRJ, sem incorporar o código deste. Não há vínculo institucional com os desenvolvedores do Vista SAGA/UFRJ original.

> **Versão 1.6.0:** dicas (caixas amarelas do QGIS) em todos os botões, campos, caixas de marcar e listas dos sete módulos. **Versão 1.5.0:** Assinatura refeita no modelo do Vista SAGA (mapa de referência, seleção como limite, todos os mapas assinados, união e por feição), validada contra o programa original; Conversor de Formatos com paleta e estilo `.qml` nos GeoTIFF de classes; resultados temporários com o nome "Módulo - operação". **Versão 1.4.x:** Voronoi fiel ao Vista SAGA (Com Massa = M/d²; atrito pelo custo do Vista SAGA), validado célula a célula; rodapé padrão [Executar] [Fechar] em todos os módulos. Histórico completo em `CHANGELOG.md`. A interface segue o idioma do QGIS (português, inglês ou espanhol); relatórios CSV/TXT sempre em português. Na interface clássica, o botão suspenso está na barra própria **Vista Saga Plugin**; se ocultada, reative em **Exibir → Barras de ferramentas → Vista Saga Plugin**.

## Sete módulos

1. **Assinatura** — do que é feita uma área selecionada num mapa de referência, em cada mapa da lista (modelo do Vista SAGA).
2. **Monitoria** — mudanças e permanências entre períodos, mapas, matrizes e relatórios; séries temporais maiores permitem análise de tendências quando atendidas as condições estatísticas.
3. **Avaliação** — classificação multicritério com pesos e notas, em raster ou vetores.
4. **Análises Voronoi** — Simples, Massa, Atrito e Massa + Atrito; atrito único ou composição de múltiplos rasters com pesos e notas por classe.
5. **Combinação de Mapas** — cruzamento categórico e cálculo de áreas, em raster ou vetor.
6. **Conversor de Formatos** — RS2/GeoTIFF/vetor, incluindo vetorização e rasterização.
7. **Sequenciador de Mapas** — três abas Raster/Vetorial/Misto, ordenação temporal, GIF animado e PNGs opcionais, preservando as camadas de origem.

## Instalação e compatibilidade

1. No QGIS 4.x, abra **Complementos → Gerenciar e instalar complementos → Instalar a partir de ZIP**.
2. Selecione o ZIP de **instalação** (não o pacote de código-fonte), instale e reinicie o QGIS.
3. Acesse **Raster → Vista Saga Plugin → [módulo]**, ou clique no botão do Vista Saga Plugin na barra de complementos para abrir o menu suspenso de módulos.

O complemento usa PyQGIS/Qt6, GDAL/OGR, NumPy e bibliotecas disponibilizadas pela instalação do QGIS; SciPy pode acelerar um caso específico do Voronoi, mas há alternativa de cálculo sem SciPy. Não são distribuídos executáveis nem bibliotecas compiladas no ZIP. A execução em Linux/Flatpak já foi testada e aprovada pelo responsável pelo projeto. Esta versão exige QGIS 4.x e não foi preparada para QGIS 3.x.

O diretório interno `geosaga` e identificadores Processing `geosaga:*` são **intencionalmente mantidos** para preservar a compatibilidade com projetos e scripts anteriores. **Não** renomeie manualmente essa pasta para `vista_saga_plugin`.

## Atenção à metodologia

- **Voronoi com atrito** segue o modelo do Vista SAGA: custo = soma, nas células da reta entre o polo e a célula, de distância ao polo × nota × passo (a nota é o próprio custo; nota 1 = custo basal). **Não** é caminho de custo mínimo. Validado contra o Vista SAGA original: Simples e Com Massa 100% das células; com atrito, 99,4% a 99,7% (diferenças na fronteira entre regiões).
- **Assinatura** validada contra o Vista SAGA original em três casos: mapa inteiro 100%; seleções parciais iguais, salvo células da classe ligadas só pela diagonal (o balde do Vista SAGA as exclui; o plugin marca a classe inteira).
- Mapas analisados em conjunto devem ter o mesmo SRC (projetado, em metros, para áreas) e, no raster, a mesma grade; o plugin não reprojeta sem avisar.
- Em operações raster, limites e áreas dependem da resolução das células.
- Resultados temporários devem ser salvos antes de encerrar o QGIS.

## Verificações adicionais recomendadas

- Instalar em **perfil QGIS 4.x limpo**, sem outros complementos de terceiros.
- Abrir cada módulo, carregar e processar amostras pequenas, salvar/reabrir o projeto, desativar e reativar o complemento.
- Reconfirmar a instalação limpa e a iconografia em diferentes distribuições do QGIS; Windows e Linux/Flatpak já foram testados e aprovados pelo responsável.
- Para repetir as validações contra o Vista SAGA original, use os scripts do repositório (`scripts/comparar_caso_bacia.py` e `scripts/comparar_assinatura_vista_saga.py`).
- Verificar os links `homepage`, `repository` e `tracker` no `metadata.txt` antes de submeter ao repositório oficial de complementos QGIS.

## Licença e atribuição

O código deste complemento é distribuído sob **GNU GPL-3.0-or-later**; o texto integral está no arquivo [`LICENSE`](LICENSE); a nota de independência do projeto está em [`NOTICE.md`](NOTICE.md). Autoria do complemento: **Esdras Andrade**. Documentação e resultados desta implementação não representam certificação pelo Vista SAGA/UFRJ ou pela Universidade Federal do Rio de Janeiro.

Para histórico completo de evolução, ensaios e testes de desenvolvimento, consulte o **pacote de código-fonte**, distribuído separadamente.



## Integração com QRibbonSkin

Os menus Raster e Complementos apresentam **uma única ação** com ícone e submenu dos sete módulos. O QMenu permanece sob controle do QGIS/Qt; o QRibbonSkin o renderiza em seu próprio padrão visual. Há versões do ícone em 19 × 19 px (botões principais do QRibbonSkin) e 24 × 24 px (interface clássica). Não há dependência de importação do QRibbonSkin nem personalização global de tema.

## Diagnóstico de falhas

Falhas inesperadas exibem uma mensagem curta e registram o traceback completo em **Exibir → Painéis → Mensagens de log**, aba **Vista Saga Plugin**. Anexe esse texto ao relatar problemas no [rastreador do projeto](https://github.com/ezrandrade/Vista-Saga-Plugin/issues).

## Site oficial

[Vista Saga Plugin — página WordPress](https://vistasagaplugin.wordpress.com/) · [Código-fonte e colaboração no GitHub](https://github.com/ezrandrade/Vista-Saga-Plugin).
