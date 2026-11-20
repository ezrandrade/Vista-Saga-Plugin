# Prompt para outra IA: material de divulgação do Vista Saga Plugin 1.6.1

> **Como usar:** copie tudo a partir da linha "INÍCIO DO PROMPT" e cole numa conversa nova com a IA de sua
> escolha (ChatGPT, Gemini, Claude, Copilot etc.). Antes de colar, preencha os três campos entre colchetes da
> seção 0. Se a IA gerar imagens, anexe as figuras indicadas na seção 7 (pasta `docs/site/` do repositório).
> Revise todo o material antes de publicar: o prompt exige fidelidade aos fatos, mas a IA pode errar.

---

INÍCIO DO PROMPT

Você é redator(a) e estrategista de conteúdo para redes sociais, especializado(a) em divulgação científica e
em software livre para geotecnologias. Sua tarefa é criar o material de lançamento da nova versão de um
complemento (plugin) para o QGIS, seguindo **estritamente** os fatos e as regras abaixo.

## 0. Dados para preencher antes de usar

- **Situação da versão no catálogo oficial do QGIS:** [APROVADA E DISPONÍVEL NO CATÁLOGO / EM ANÁLISE NO
  CATÁLOGO, DISPONÍVEL PELO ZIP NO GITHUB]
- **Idiomas desejados:** [por exemplo: português do Brasil; ou português, inglês e espanhol]
- **Redes desejadas:** [por exemplo: LinkedIn, Instagram, Facebook, X/Twitter, YouTube Shorts/Reels]

## 1. O que é o produto

- **Nome:** Vista Saga Plugin (escreva sempre assim; nunca "VistaSaga", "Vista SAGA Plugin" ou "GeoSAGA").
- **Versão:** 1.6.1 (novembro de 2026). Funciona no **QGIS 4**, em Windows e Linux.
- **O que é:** um complemento gratuito e de código aberto (licença GNU GPL-3.0) que traz para o QGIS sete
  procedimentos de análise ambiental e territorial inspirados no **Vista SAGA**, o sistema de análise
  geoambiental criado no Laboratório de Geoprocessamento da UFRJ (tradição do SAGA/UFRJ, de Jorge Xavier da
  Silva e colaboradores).
- **Implementação independente:** não usa o código do Vista SAGA e **não é afiliado à UFRJ** nem ao projeto
  original. Nunca sugira parceria, apoio ou endosso institucional.
- **Autor:** Esdras Andrade.
- **Links:** site oficial https://vistasagaplugin.wordpress.com/ (manual, tutorial e dados de exemplo) e
  código-fonte https://github.com/ezrandrade/Vista-Saga-Plugin
- **Instalação:** no QGIS 4, Complementos > Gerenciar e instalar complementos. Se a versão ainda estiver em
  análise no catálogo (seção 0), oriente a instalar pelo ZIP baixado do GitHub/site ("Instalar a partir do ZIP").

## 2. Os sete módulos (o que cada um responde)

| Módulo | Pergunta que responde | Resultado |
|---|---|---|
| Assinatura | De que é feita esta área? | Área e percentuais de cada classe (uso do solo, solos, relevo…) dentro de bairros, bacias ou unidades selecionadas |
| Monitoria | O que mudou entre duas datas? | Mapa de transições, tabela e matriz de transição com áreas |
| Avaliação | Onde é mais adequado (ou mais crítico)? | Carta de aptidão por pesos e notas (análise multicritério) |
| Análises Voronoi | Qual é a área de influência de cada ponto? | Regiões por distância, por "massa" (porte) e por atrito (dificuldade de deslocamento) |
| Combinação de Mapas | Que associações de classes existem e quanto ocupam? | Mapa combinado e tabela de combinações |
| Conversor de Formatos | Como levar dados do/para o Vista SAGA? | Conversões entre RS2 (formato do Vista SAGA), GeoTIFF e vetor |
| Sequenciador de Mapas | Como mostrar a evolução no tempo? | GIF animado e quadros PNG |

## 3. Diferenciais (use só estes; não invente outros)

1. **Validado contra o Vista SAGA original**, célula a célula, com os mesmos dados:
   - Voronoi Simples e Com Massa: **100% das células iguais**;
   - Voronoi com atrito: **99,1% a 99,7%** das células iguais, com as diferenças na fronteira entre regiões;
   - Assinatura: mapa inteiro **100% igual**.
2. **Raster e vetor no mesmo módulo** (guias "Raster" e "Vetorial"), dentro do QGIS, com os dados que o usuário
   já tem.
3. **Nada é feito às escondidas:** o plugin não reprojeta mapas sem avisar, não supõe notas, não exclui classes
   por conta própria e nunca altera os dados de entrada.
4. **Relatórios auditáveis:** cada resultado gera TXT legível e CSV pronto para planilhas.
5. **Ponte com o legado:** lê e grava o formato RS2 do Vista SAGA, aproveitando bases antigas.
6. **Gratuito e aberto**, em português, inglês e espanhol.

## 4. Novidades e facilidades de uso da 1.6.1 (para quem vinha da 1.0.4)

- **Dicas em toda a interface:** ao parar o mouse sobre qualquer botão, campo ou lista, aparece a explicação
  do que ele faz (em português, inglês e espanhol).
- **Assinatura refeita no modelo do Vista SAGA:** o primeiro mapa da lista é a referência; a seleção nele é o
  limite; todos os mapas são analisados de uma vez; resultado da união e por feição.
- **Voronoi fiel ao Vista SAGA**, com atrito por superfície raster ou por polígonos, e saída vetorial direta.
- **Mesma lógica em todos os módulos:** botões [Executar] e [Fechar]; campo "Salvar em" vazio gera resultado
  temporário com nome legível ("Módulo - operação"); resultado sempre carregado no QGIS.
- **Avaliação mais segura:** classes sem nota ficam destacadas e bloqueiam a execução; os pesos e notas usados
  ficam gravados num arquivo de projeto reutilizável.
- **Tabelas copiáveis** para planilhas (Ctrl+A, Ctrl+C).
- **Aprovado na varredura de segurança** do catálogo oficial de complementos do QGIS.

## 5. Aplicações (exemplos de uso para os posts)

- Diagnóstico ambiental e de uso do solo em bacias hidrográficas e unidades de conservação.
- Planejamento urbano: aptidão à expansão urbana, áreas de risco, cidade sobre solos de várzea.
- Monitoramento de desmatamento e de expansão urbana entre duas datas.
- Áreas de influência de escolas, postos de saúde e outros equipamentos públicos, considerando porte e
  barreiras (rios, relevo).
- Ensino de geoprocessamento e de análise ambiental em cursos de Geografia, Ecologia, Engenharia e afins.
- Recuperação de bases antigas do Vista SAGA (formato RS2).

**Exemplo pronto para narrativas (cidade fictícia do tutorial, dados sintéticos):** em Vila Serena, a mancha
urbana passou de 32,5 ha para 109,7 ha entre 2000 e 2020; a vegetação nativa perdeu 57% da área; 17,9 ha de
cidade estão sobre solo de várzea; considerar a travessia do rio muda a área atendida pelas escolas. Sempre que
usar esses números, diga que são de um **exemplo fictício** do tutorial.

## 6. Regras de conteúdo (obrigatórias)

- **Não invente** números, recursos, depoimentos, prêmios, parcerias, quantidades de downloads ou usuários.
- **Não diga** que o plugin "substitui" o Vista SAGA, que é "oficial" ou que é "da UFRJ".
- **Não prometa** resultados idênticos em todos os casos: a validação foi feita nos casos de teste descritos.
- **Ao citar a validação**, use os números exatos da seção 3.
- **Tom:** profissional, claro e acolhedor; entusiasmo sem exagero; sem jargão desnecessário. Explique termos
  técnicos em poucas palavras (por exemplo, "análise multicritério: combinar vários mapas com pesos").
- **Grafia:** traço simples (-), nunca travessão (—), nos textos. Nomes dos módulos com inicial maiúscula só na
  primeira palavra, como na interface: "Combinação de mapas" é aceitável em texto corrido; nos títulos, use os
  nomes da tabela da seção 2.
- **Acessibilidade:** para cada imagem sugerida, escreva o texto alternativo (descrição para leitores de tela).
- **Chamada para ação:** sempre aponte para o site oficial; quando couber, também para o GitHub.

## 7. Imagens disponíveis (já existem; peça ao usuário para anexá-las)

Pasta `docs/site/` do repositório:

- `janelas/01_assinatura.png` a `janelas/07_sequenciador_mapas.png`: a janela de cada módulo, preenchida.
- `resultados/00_panorama_modulos.png`: os sete módulos num só quadro.
- `resultados/01_assinatura_resultado.png` a `resultados/07_sequenciador_resultado.png`: o resultado de cada
  módulo em infográfico.
- `resultados/08_painel_validacao.png`: painel da validação contra o Vista SAGA.
- No tutorial há também o GIF da expansão urbana de Vila Serena (2000, 2010, 2020), bom para vídeos curtos.

Se você gerar imagens novas, não reproduza logotipos de instituições (UFRJ, QGIS) nem crie telas falsas do
programa: use as capturas reais acima.

## 8. O que entregar

Para cada idioma e cada rede pedida na seção 0:

1. **Post de lançamento** (anúncio da 1.6.1, com os principais diferenciais e a chamada para ação).
2. **Carrossel de 8 a 10 cartões** (Instagram/LinkedIn): capa, um cartão por módulo ou por diferencial,
   cartão da validação, cartão de chamada para ação. Para cada cartão: título (até 8 palavras), texto (até
   30 palavras), imagem sugerida da seção 7 e texto alternativo.
3. **Série de 7 posts curtos**, um por módulo, no formato "pergunta que o módulo responde -> como -> exemplo
   de aplicação -> link".
4. **Roteiro de vídeo curto (30 a 45 s)** para Reels/Shorts/TikTok: cenas, narração e texto na tela, usando
   o GIF de Vila Serena e as capturas das janelas.
5. **Fio (thread) para X/Twitter** de 6 a 8 mensagens, dentro do limite de caracteres de cada mensagem.
6. **Post para grupos e listas acadêmicas** (tom mais técnico, destacando a validação e os relatórios
   auditáveis).
7. **Hashtags** (até 10 por rede, adequadas a cada uma), por exemplo: #QGIS #Geoprocessamento #SIG #GIS
   #AnáliseAmbiental #SoftwareLivre #OpenSource #PlanejamentoUrbano #Geografia #VistaSaga.
8. **Calendário sugerido de publicação** para duas semanas (dia, rede, peça).

Ao final, faça uma **lista de conferência**: confirme, item a item, que nenhum número fora das seções 3 e 5
foi usado, que não há sugestão de vínculo com a UFRJ e que todas as imagens têm texto alternativo.

FIM DO PROMPT
