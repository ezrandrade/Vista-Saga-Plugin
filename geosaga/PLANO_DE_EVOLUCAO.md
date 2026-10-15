## Plano do Voronoi Espacial (0.7.x)

- **0.7.0:** Voronoi Simples e Voronoi com Massa (grade raster, GeoPackage opcional, estatísticas). Homologação com QGIS 4.x e comparação com resultados do Vista SAGA original ainda necessárias.
- **0.7.1:** Voronoi com Atrito; testar acumulação ao longo da trajetória em mapas raster, sem confundir com custo mínimo acumulado.
- **0.7.2:** Voronoi com Massa e Atrito, testes de comparação sistemática pixel a pixel com arquivos de referência da versão original.
- **0.8.0:** Sequenciador temporal de imagens, com GIF animado como formato principal, minimizando dependências de codecs externos.

- **0.4.3 — Monitoria vetorial direta:** implementação inicial em caráter
  experimental; interseção de dois mapas poligonais, atributos temáticos e de
  áreas, CSV/matriz/TXT; depende de homologação no QGIS 4.x.
## Implementado em 0.4.0 — Monitoria Ambiental
Interface própria com mapa de transições, matriz de contingência e relatórios CSV/TXT, mantendo `geosaga:monitoria` para scripts legados. Próxima fase: homologação funcional no QGIS 4.x e interface de Assinatura Ambiental.

## Marco 0.3.7 — Consolidação e revisão conceitual

- [x] Versão 0.3.6 consolidada como linha de base homologada.
- [x] Painel de módulos permanente.
- [x] Nome de exibição **Avaliação Espacial**; projetos/IDs legados preservados.
- [x] Remoção do atalho visível para avaliação via Processing no menu Raster.
- [x] Especificação da Avaliação Espacial Vetorial (documento dedicado).
- [x] Implementação inicial da avaliação vetorial por atributos, versão 0.3.10.
- [ ] Teste integrado no QGIS 4.x, Windows e Linux/Flatpak.
- [ ] Avaliação espacial por sobreposição de múltiplas camadas poligonais.

## Marco 0.3.4 — Homologação da interface e processamento em lote

- SRC do QGIS, seleção de rasters do projeto, sobrescrita de auxiliares e processamento em lote.
- Validar em QGIS 4.x Windows e Linux/Flatpak antes de avançar a 0.4.0.
- A operação em lote converte, mas não alinha grades deslocadas automaticamente.

## Correção de interoperabilidade (0.3.2)

- TIFF RGB com referência `.rs2` para categorias, legendas e coordenadas;
- proteção contra perda de dados por substituição do arquivo de referência;
- testes de classificação e escrita com os mapas fornecidos;
- homologação pendente no QGIS 4.x Windows/Linux e Vista SAGA original.

## Fase de interoperabilidade (0.3.1)

Implementado leitor e gravador RS2 legado, com conversão experimental
RS2 ↔ GeoTIFF categórico e documentação da variante do formato.
Foram feitos testes estruturais de cinco arquivos, comparação exata das
cores dos 62.494.740 pixels de quatro pares RS2/TIFF e regravação idêntica
byte a byte das cinco amostras. **Ainda falta homologar GDAL + Qt6 no QGIS
4.x Windows/Linux Flatpak e abrir arquivos de saída no Vista SAGA original.**

A evolução 0.4.0 de Monitoria Ambiental deve preservar a estrutura atual e
permitir a seleção direta de RS2, recorrendo ao conversor intermediário.

---

# Plano incremental — Vista Saga Plugin

## Princípios

1. Nunca reescrever um procedimento funcional sem testes de equivalência e motivo documentado.
2. Manter arquivos `.geosaga.json` e IDs `geosaga:*` até existir migração versionada, testada e documentada.
3. Separar interface (Qt/PyQGIS), núcleo matemático (NumPy) e processamento raster (GDAL).
4. Garantir que as opções de exclusão, NoData, unidades, classes e SRC sejam explícitas e rastreáveis.
5. Homologar em QGIS 4.x no Windows e Linux/Flatpak com dados sintéticos e reais, antes de declarar estabilidade.

## Marco 0.3.0 — integração inicial

- [x] Preservação das funcionalidades da versão 0.2.0.
- [x] Marca Vista Saga Plugin e menu/painel dos três módulos.
- [x] Correção de importação Qt6 para QAction.
- [x] Testes básicos matemáticos independentes de PyQGIS.
- [x] Script de testes integrados sintéticos para executar no QGIS.
- [ ] Execução dos testes QGIS em Windows 4.x.
- [ ] Execução dos testes QGIS em Linux/Flatpak 4.x.

## Marco 0.4.0 — Monitoria Ambiental interativa

- Editor próprio para selecionar mapas anterior/posterior no projeto QGIS.
- Legendas de classe com tabela de transições, classes permanentes e alteradas.
- Pré-validação de SRC/grade e escolhas explícitas de alinhamento.
- Indicadores de áreas e percentuais com tratamento correto do tipo de projeção.
- Exportação auditável CSV e GeoTIFF; cancelamento seguro em tarefas.
- Testes de transições sintéticas, NoData e soma das contagens.

**Critério de aceite:** uma operação completa de monitoria deve ser realizada sem editar JSON nem usar a caixa de ferramentas Processing.

## Marco 0.5.0 — Assinatura Ambiental interativa (implementada parcialmente; homologação pendente)

- Definição da área por camada poligonal (implementada); desenho direto no canvas do QGIS fica para uma fase posterior.
- Tabela de classes por área (implementada); histograma gráfico opcional fica para fase posterior.
- Exportação de relatórios CSV/TXT e GeoPackage resumido (implementada); gráficos opcionais ficam para fase posterior.
- Controle de feições múltiplas, sobreposição, NoData e seleção por centro de pixel.
- Testes em polígonos sintéticos, incluindo geometrias sobrepostas.

**Critério de aceite da versão 0.5.0:** selecionar polígonos existentes no projeto ou no disco e gerar assinaturas sem abrir Processing; desenho direto no canvas é melhoria posterior.

## Marco 0.6.0 — interoperabilidade e robustez

- Estratégias explícitas de alinhamento/resampling, com preservação de classes inteiras.
- Visualização e validação de pesos e notas antes do processamento.
- Projetos e relatórios reprodutíveis; mensagens de diagnóstico mais completas.
- Testes de carga com rasters extensos, cancelamento e atomicidade de saída.
- Comparação quantitativa com casos de referência documentados (e, quando disponíveis, saídas do Vista SAGA original).

## Marco 1.0.0 — distribuição pública

- Auditoria de dependências/API QGIS 4.x, licença, metadados, ícone, README e changelog.
- CI e testes em ambientes QGIS 4.x suportados.
- Estudos de casos reais e aferição de resultados numéricos.
- Versionamento, repositório público, documentação de suporte e submissão ao repositório oficial.

**Nota metodológica:** nomes iguais aos do Vista SAGA não são prova de equivalência. Cada fórmula, opção de NoData e regime de contagem deve ser comparado a documentação/casos de controle.

## Avaliação Espacial vetorial por sobreposição — protótipo 0.3.11

Implementada a modalidade de interseção entre diferentes mapas poligonais, com interface independente. Homologação no QGIS 4.x pendente. Próximas extensões possíveis: união com cobertura total, regras para ausência de dados e controle de sobreposições internas.

## Etapas posteriores a 0.4.2

- Monitoria vetorial direta (duas camadas poligonais por sobreposição, comparação de categorias e áreas); implementação e homologação pendentes.
