"""Kit de textos da divulgação do Vista Saga Plugin 1.6.1 (pt-BR), em DOCX.

Uso, na raiz do repositório:
    SOFFICE_PY=<soffice.py> python3 docs/divulgacao/kit_textos.py <pasta_de_trabalho> <saida.docx>
Só fatos conferidos no repositório (validação, módulos, licença). Os números de Vila Serena são de um exemplo
fictício do tutorial e vêm identificados como tal.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'docs', 'manual'))

import build_manual as bm  # noqa: E402

SITE = 'https://vistasagaplugin.wordpress.com/'
GITHUB = 'https://github.com/ezrandrade/Vista-Saga-Plugin'
UI = {'doc_title': 'Kit de divulgação', 'subtitle': 'Vista Saga Plugin 1.6.1 para QGIS 4',
      'tagline': 'Textos para redes sociais, carrossel, vídeo curto e calendário de publicação',
      'author': 'Esdras Andrade (IGDEMA/UFAL)', 'date': 'Novembro de 2026', 'toc': 'Sumário', 'figure': 'Figura',
      'footer': 'Vista Saga Plugin 1.6.1 - Kit de divulgação', 'page': 'Página'}

THREAD = [
    '🧵 Saiu a versão 1.6.1 do Vista Saga Plugin, complemento gratuito para o QGIS 4 que traz sete procedimentos de '
    'análise ambiental inspirados no Vista SAGA (tradição do SAGA/UFRJ). O que ele faz, em 7 mensagens 👇',
    '1/ Assinatura: selecione bairros, bacias ou unidades num mapa de referência e veja quanto ocupa cada classe de '
    'uso do solo, solo ou relevo, em vários mapas de uma vez. Relatórios em TXT e CSV.',
    '2/ Monitoria: compare dois mapas de datas diferentes e receba o mapa de transições e a matriz de transição, com '
    'áreas em hectares. Avaliação: combine mapas com pesos e notas e gere cartas de aptidão.',
    '3/ Análises Voronoi: áreas de influência por distância, por porte (massa) e por dificuldade de deslocamento '
    '(atrito). Combinação de Mapas: cada associação de classes recebe um código, com área e percentual.',
    '4/ Conversor de Formatos: leve dados entre RS2 (formato do Vista SAGA), GeoTIFF e vetor, preservando códigos, '
    'nomes e cores. Sequenciador de Mapas: transforme mapas em ordem num GIF animado.',
    '5/ Validação: comparado célula a célula com o Vista SAGA original, com os mesmos dados. Voronoi Simples e Com '
    'Massa: 100% das células iguais. Com atrito: 99,1% a 99,7%. Assinatura do mapa inteiro: 100%.',
    '6/ Na 1.6.1: dicas em todos os botões e campos, Assinatura refeita no modelo do Vista SAGA e a mesma lógica em '
    'todos os módulos. Gratuito, GPL-3.0, em português, inglês e espanhol.',
    f'7/ Manual, tutorial passo a passo e dados de exemplo: {SITE} Código-fonte: {GITHUB} #QGIS #Geoprocessamento',
]


def build(work):
    car = os.path.join(work, 'carrossel')
    B = []
    chapter = [0]

    def h1(t):
        chapter[0] += 1
        B.append({'type': 'h1', 'text': f'{chapter[0]}. {t}'})

    def h2(t): B.append({'type': 'h2', 'text': t})
    def h3(t): B.append({'type': 'h3', 'text': t})
    def p(*ts): B.extend({'type': 'p', 'text': t} for t in ts)
    def bullets(items): B.append({'type': 'bullets', 'items': items})
    def table(cols, rows, widths, header=True, small=False):
        B.append({'type': 'table', 'cols': cols, 'rows': rows, 'widths': widths, 'header': header, 'small': small})
    def tip(title, text=None, items=None, kind='tip'):
        B.append({'type': 'callout', 'kind': kind, 'title': title, 'text': text, 'items': items})
    def brk(): B.append({'type': 'pagebreak'})

    B.append({'type': 'cover', 'title': UI['doc_title'], 'subtitle': UI['subtitle'], 'tagline': UI['tagline'],
              'author': UI['author'], 'date': UI['date'], 'logo': os.path.join(ROOT, 'docs', 'assets', 'vista-saga-mark.png')})
    B.append({'type': 'toc', 'title': UI['toc']})
    brk()

    # -----------------------------------------------------------------------------------------------
    h1('Como usar este kit')
    p('Este kit traz as peças visuais prontas e os textos para divulgar a versão 1.6.1 do Vista Saga Plugin. Tudo foi '
      'escrito a partir do repositório do projeto: os números da validação são os registrados nos testes contra o '
      'Vista SAGA original, e os números de Vila Serena vêm de um exemplo fictício do tutorial (sempre identificado '
      'como tal).')
    table(['Peça', 'Arquivo', 'Formato', 'Onde usar'], [
        ['Carrossel (10 cartões)', 'carrossel/01.png a 10.png', '1080 × 1350 (4:5)', 'Instagram, LinkedIn (como documento ou imagens), Facebook'],
        ['Post de lançamento', 'post_lancamento.png', '1080 × 1080 (1:1)', 'Instagram, Facebook, LinkedIn, X'],
        ['Capa de link', 'capa_link.png', '1200 × 627', 'LinkedIn, Facebook e X ao compartilhar o site; capa de artigo'],
        ['Vídeo vertical (30 s)', 'video_vertical_vista_saga_1.6.1.mp4', '1080 × 1920, sem áudio', 'Reels, Shorts, TikTok, Stories'],
    ], [0.22, 0.32, 0.18, 0.28], small=True)
    image = lambda name, cap, w=4.6: B.append(bm.image(os.path.join(work, name), w, cap))  # noqa: E731
    image('post_lancamento.png', 'Post de lançamento (1080 × 1080)', 3.6)
    tip('Antes de publicar', items=[
        'Status no catálogo do QGIS: enquanto a 1.6.1 estiver em análise, use a frase "instale pelo ZIP do site '
        'oficial". Depois da aprovação, troque por "disponível em Complementos > Gerenciar e instalar complementos".',
        'O vídeo não tem áudio: acrescente uma trilha livre de direitos (por exemplo, a biblioteca de áudio do YouTube '
        'ou do Instagram) ou grave a narração opcional da seção 7.',
        'No LinkedIn, o carrossel rende mais publicado como documento (PDF): junte os 10 PNG num PDF na ordem.',
        'Não marque a UFRJ nem o QGIS como parceiros: o plugin é uma implementação independente.'], kind='warning')
    brk()

    # -----------------------------------------------------------------------------------------------
    h1('Posts de lançamento')
    h2('LinkedIn (imagem: capa de link ou carrossel)')
    p('🌎 **Saiu a versão 1.6.1 do Vista Saga Plugin para QGIS 4.**',
      'O Vista Saga Plugin é um complemento gratuito e de código aberto que traz para o QGIS sete procedimentos de '
      'análise ambiental e territorial inspirados no Vista SAGA, o sistema de análise geoambiental da tradição do '
      'SAGA/UFRJ.',
      'Com ele, você responde no QGIS, com os dados que já usa:',
      '▸ de que é feita uma área (Assinatura);',
      '▸ o que mudou entre duas datas (Monitoria);',
      '▸ onde é mais adequado ou mais crítico, por pesos e notas (Avaliação);',
      '▸ qual a área de influência de cada ponto, por distância, porte ou atrito (Análises Voronoi);',
      '▸ que associações de classes existem (Combinação de Mapas);',
      '▸ como trazer dados do Vista SAGA (Conversor de Formatos) e como mostrar a evolução no tempo '
      '(Sequenciador de Mapas).',
      '**Validado contra o Vista SAGA original**, célula a célula: 100% das células iguais nas Análises Voronoi Simples '
      'e Com Massa, de 99,1% a 99,7% com atrito, e 100% na Assinatura do mapa inteiro.',
      'Novidades da 1.6.1: dicas em todos os botões e campos, Assinatura refeita no modelo do Vista SAGA e a mesma '
      'lógica de uso em todos os módulos. Interface em português, inglês e espanhol; licença GPL-3.0.',
      f'📘 Manual, tutorial passo a passo e dados de exemplo: {SITE}',
      f'💻 Código-fonte: {GITHUB}',
      '#QGIS #Geoprocessamento #SIG #AnáliseAmbiental #PlanejamentoUrbano #SoftwareLivre #OpenSource')
    h2('Instagram (legenda do carrossel)')
    p('Análise ambiental no QGIS, com o método do Vista SAGA 🌎',
      'A versão 1.6.1 do Vista Saga Plugin chegou: sete módulos para diagnóstico, monitoramento e planejamento do '
      'território, gratuitos e de código aberto. Arraste para conhecer cada um 👉',
      '✅ Análises Voronoi e Assinatura validadas contra o Vista SAGA original',
      '✅ Dicas em todos os botões e campos',
      '✅ Raster e vetor, com relatórios em TXT e CSV',
      '✅ Português, inglês e espanhol',
      '🔗 Manual, tutorial e dados de exemplo no link da bio (vistasagaplugin.wordpress.com)',
      '#QGIS #Geoprocessamento #SIG #GIS #AnáliseAmbiental #Geografia #PlanejamentoUrbano #SoftwareLivre '
      '#Cartografia #MeioAmbiente')
    h2('Facebook (imagem: post de lançamento)')
    p('🌎 Nova versão do Vista Saga Plugin para QGIS 4!',
      'Sete procedimentos de análise ambiental inspirados no Vista SAGA, agora no QGIS e de graça: Assinatura, '
      'Monitoria, Avaliação, Análises Voronoi, Combinação de Mapas, Conversor de Formatos e Sequenciador de Mapas.',
      'Na 1.6.1, cada botão e campo explica o que faz, e a Assinatura foi refeita no modelo do Vista SAGA. Os '
      'resultados das Análises Voronoi e da Assinatura foram comparados com o programa original, célula a célula.',
      f'Manual, tutorial passo a passo e dados de exemplo: {SITE}')
    h2('X (post único, imagem: post de lançamento)')
    p(f'Saiu o Vista Saga Plugin 1.6.1 para QGIS 4: sete módulos de análise ambiental inspirados no Vista SAGA, '
      f'gratuitos e de código aberto. Voronoi e Assinatura validados contra o original. {SITE} #QGIS #SIG')
    brk()

    # -----------------------------------------------------------------------------------------------
    h1('Carrossel: cartões e textos alternativos')
    p('Os cartões estão prontos em PNG. A tabela traz o texto alternativo de cada um (campo "Texto alternativo" ou '
      '"Descrição da imagem" das redes), para leitores de tela.')
    B.append(bm.image(os.path.join(car, '01.png'), 2.6, 'Cartão 1 (capa)'))
    alts = [
        'Capa: Vista Saga Plugin, nova versão 1.6.1 para QGIS 4. Análise ambiental no QGIS, com o método do Vista SAGA. '
        'Sete módulos para diagnóstico, monitoramento e planejamento do território, gratuitos e de código aberto.',
        'Assinatura: de que é feita esta área? Infográfico da seleção num mapa de referência recortando outros mapas e '
        'gráfico com o percentual de cada classe.',
        'Monitoria: o que mudou entre duas datas? Mapa de transições de 2000 a 2020 da cidade fictícia de Vila Serena e '
        'gráfico da área de cada classe nas duas datas.',
        'Avaliação: onde é mais adequado? Carta de aptidão à expansão urbana da cidade fictícia de Vila Serena e '
        'gráfico da área por nota.',
        'Análises Voronoi: qual a área de influência de cada ponto? Áreas de influência de seis escolas da cidade '
        'fictícia de Vila Serena nas modalidades Simples, Com Massa e Com Atrito.',
        'Combinação de Mapas: que associações existem e quanto ocupam? Dois mapas cruzados geram um mapa com um código '
        'para cada associação de classes.',
        'Conversor de Formatos: como aproveitar as bases do Vista SAGA? Diagrama das seis conversões entre RS2, GeoTIFF '
        'e vetor.',
        'Sequenciador de Mapas: como mostrar a evolução no tempo? Três mapas de uso do solo da cidade fictícia de Vila '
        'Serena, em 2000, 2010 e 2020, mostrando a mancha urbana crescer.',
        'Validado contra o Vista SAGA original: 100% das células iguais nas Análises Voronoi Simples e Com Massa; de '
        '99,1% a 99,7% no Voronoi com atrito; 100% de coincidência na Assinatura do mapa inteiro.',
        'Experimente agora: manual, tutorial e dados de exemplo em vistasagaplugin.wordpress.com. Gratuito, licença '
        'GPL-3.0, para QGIS 4, em português, inglês e espanhol.',
    ]
    table(['Cartão', 'Texto alternativo'], [[str(i + 1), a] for i, a in enumerate(alts)], [0.1, 0.9], small=True)
    brk()

    # -----------------------------------------------------------------------------------------------
    h1('Série de posts por módulo')
    p('Sete posts curtos, um por módulo, para publicar ao longo das duas semanas. Imagem sugerida: o cartão do módulo '
      'no carrossel (ou a janela correspondente em imagens/1_janelas).')
    series = [
        ('Assinatura (cartão 2)', 'De que é feita esta área? 🗺️ Na Assinatura do Vista Saga Plugin, você seleciona '
         'bairros, bacias ou unidades num mapa de referência e vê quanto ocupa cada classe de uso do solo, solo ou '
         'relevo, em vários mapas de uma vez. Duas porcentagens do Vista SAGA: de que é feito o lugar e quanto da classe '
         'está ali. Relatórios em TXT e CSV.'),
        ('Monitoria (cartão 3)', 'O que mudou entre duas datas? 🔄 A Monitoria compara dois mapas e entrega o mapa de '
         'transições, a tabela e a matriz de transição, com áreas em hectares. No exemplo fictício do tutorial, a mancha '
         'urbana de Vila Serena passou de 32,5 ha para 109,7 ha entre 2000 e 2020.'),
        ('Avaliação (cartão 4)', 'Onde é mais adequado? ⚖️ A Avaliação combina mapas com pesos e notas (análise '
         'multicritério) e gera cartas de aptidão, suscetibilidade ou prioridade. Nenhuma classe entra na conta sem '
         'decisão sua: o plugin nunca supõe nota zero. Pesos e notas ficam gravados para reutilizar.'),
        ('Análises Voronoi (cartão 5)', 'Qual escola atende cada parte da cidade? 🏫 As Análises Voronoi delimitam '
         'áreas de influência pela distância, pelo porte (massa) e pela dificuldade de deslocamento (atrito), em raster '
         'ou vetor. Validadas contra o Vista SAGA original: 100% das células iguais na Simples e na Com Massa.'),
        ('Combinação de Mapas (cartão 6)', 'Que associações existem e quanto ocupam? 🧩 A Combinação de Mapas cruza '
         'dois ou mais mapas e dá um código para cada associação de classes, com área e percentual. No exemplo fictício '
         'do tutorial, ela revela 17,9 ha de cidade sobre solo de várzea.'),
        ('Conversor de Formatos (cartão 7)', 'Tem bases antigas do Vista SAGA? 💾 O Conversor de Formatos leva dados '
         'entre RS2, GeoTIFF e vetor, preservando códigos, nomes e cores das classes, e registra o sistema de '
         'coordenadas que o RS2 não guarda. Converte vários arquivos de uma vez.'),
        ('Sequenciador de Mapas (cartão 8 ou vídeo)', 'Como mostrar a evolução no tempo? 🎞️ O Sequenciador de Mapas '
         'transforma mapas em ordem num GIF animado (e em quadros PNG), com data e legenda, usando a simbologia que você '
         'já definiu no QGIS.'),
    ]
    for title, text in series:
        h3(title)
        p(text + f' Saiba mais: {SITE}')
    brk()

    # -----------------------------------------------------------------------------------------------
    h1('Thread para o X')
    p('Oito mensagens, todas dentro do limite de 280 caracteres (conferido automaticamente; links contam como 23).')
    rows = []
    for i, msg in enumerate(THREAD, 1):
        rows.append([str(i), msg, str(_x_len(msg))])
    table(['#', 'Mensagem', 'Caract.'], rows, [0.06, 0.82, 0.12], small=True)
    brk()

    # -----------------------------------------------------------------------------------------------
    h1('Post para grupos e listas acadêmicas')
    p('**Assunto (e-mail ou lista):** Vista Saga Plugin 1.6.1: análise geoambiental no QGIS 4, validada contra o '
      'Vista SAGA',
      'Prezados colegas,',
      'Compartilho a versão 1.6.1 do Vista Saga Plugin, complemento livre (GPL-3.0) para o QGIS 4 que reimplementa, de '
      'forma independente, sete procedimentos de análise geoambiental inspirados no Vista SAGA: Assinatura, Monitoria, '
      'Avaliação por pesos e notas, Análises Voronoi (simples, com massa e com atrito), Combinação de Mapas, '
      'Conversor de Formatos (RS2, GeoTIFF e vetor) e Sequenciador de Mapas.',
      'Os módulos com resultados comparáveis foram validados contra o Vista SAGA original, com os mesmos dados de '
      'entrada e comparação célula a célula: nas Análises Voronoi, 100% das células iguais nas modalidades Simples e '
      'Com Massa e de 99,1% a 99,7% nas modalidades com atrito (diferenças concentradas na fronteira entre regiões); '
      'na Assinatura, 100% de coincidência no mapa inteiro. Os scripts de comparação estão no repositório, para quem '
      'quiser repetir os testes com os próprios dados.',
      'Todos os resultados geram relatórios em TXT e CSV, e o plugin não reprojeta mapas sem avisar nem supõe notas: '
      'características importantes para análises auditáveis em pesquisa e no ensino. O site oficial traz manual, '
      'tutorial passo a passo com dados sintéticos e material para aulas.',
      f'Site: {SITE} | Código-fonte: {GITHUB}',
      'Relatos de uso, comparações de resultados e sugestões são muito bem-vindos.',
      'Atenciosamente,', 'Esdras Andrade')
    tip('Atenção', 'O plugin é uma implementação independente: não use expressões como "versão oficial", "parceria" ou '
        '"apoio da UFRJ".', kind='warning')
    brk()

    # -----------------------------------------------------------------------------------------------
    h1('Vídeo vertical (30 segundos)')
    p('O vídeo está pronto, sem áudio. A tabela mostra as cenas e uma narração opcional (cerca de 70 palavras, para '
      'ritmo calmo).')
    table(['Tempo', 'Cena (texto na tela)', 'Narração opcional'], [
        ['0:00', 'Análise ambiental completa, direto no QGIS?', 'Análise ambiental completa, direto no QGIS?'],
        ['0:03', 'Vista Saga Plugin - nova versão 1.6.1', 'Conheça o Vista Saga Plugin.'],
        ['0:05', 'Sete módulos, uma só lógica', 'Sete módulos inspirados no Vista SAGA, todos com a mesma lógica de uso.'],
        ['0:10', 'O que mudou no território? (Vila Serena 2000, 2010, 2020)', 'Veja o que mudou no território e transforme a série em animação.'],
        ['0:15', 'Quem atende quem, considerando o porte e as barreiras', 'Delimite áreas de influência pela distância, pelo porte e pelas barreiras.'],
        ['0:19', 'Validado contra o Vista SAGA original: 100% e 99,1-99,7%', 'Resultados validados contra o Vista SAGA original, célula a célula.'],
        ['0:23', 'Uma dica em cada botão', 'Cada botão explica o que faz, em português, inglês e espanhol.'],
        ['0:27', 'Gratuito e de código aberto - vistasagaplugin.wordpress.com', 'Gratuito e de código aberto. Manual e tutorial no site oficial.'],
    ], [0.1, 0.45, 0.45], small=True)
    h3('Legenda para Reels, Shorts e TikTok')
    p('20 anos de expansão urbana em 3 segundos, sete módulos de análise ambiental e validação contra o Vista SAGA '
      'original. Tudo dentro do QGIS, de graça. 🌎 Link na bio: vistasagaplugin.wordpress.com '
      '#QGIS #Geoprocessamento #SIG #Geografia #MeioAmbiente')
    brk()

    # -----------------------------------------------------------------------------------------------
    h1('Hashtags por rede')
    table(['Rede', 'Hashtags (até 10)'], [
        ['Instagram', '#QGIS #Geoprocessamento #SIG #GIS #AnáliseAmbiental #Geografia #PlanejamentoUrbano #SoftwareLivre #Cartografia #MeioAmbiente'],
        ['LinkedIn', '#QGIS #Geoprocessamento #SIG #AnáliseAmbiental #PlanejamentoUrbano #SoftwareLivre #OpenSource'],
        ['X', '#QGIS #SIG #Geoprocessamento (no máximo 2 ou 3 por mensagem)'],
        ['Facebook', '#QGIS #Geoprocessamento #SIG #AnáliseAmbiental'],
        ['TikTok / Reels / Shorts', '#QGIS #Geoprocessamento #SIG #Geografia #MeioAmbiente #Mapas'],
    ], [0.22, 0.78], small=True)
    h1('Calendário sugerido (duas semanas)')
    table(['Dia', 'Rede', 'Peça'], [
        ['Seg (semana 1)', 'LinkedIn, Instagram, Facebook, X', 'Lançamento: post de lançamento + carrossel (Instagram/LinkedIn) + post único (X)'],
        ['Ter', 'X', 'Thread completa (8 mensagens)'],
        ['Qua', 'Instagram, Facebook, TikTok', 'Vídeo vertical (Reels, Shorts, TikTok)'],
        ['Qui', 'LinkedIn, Instagram', 'Série: Análises Voronoi (cartão 5)'],
        ['Sex', 'Grupos e listas acadêmicas', 'Post para grupos e listas'],
        ['Seg (semana 2)', 'LinkedIn, Instagram', 'Série: Assinatura (cartão 2)'],
        ['Ter', 'Instagram, Facebook', 'Série: Monitoria (cartão 3)'],
        ['Qua', 'LinkedIn, Instagram', 'Série: Avaliação (cartão 4)'],
        ['Qui', 'Instagram, Facebook', 'Série: Combinação de Mapas (cartão 6) e Conversor de Formatos (cartão 7)'],
        ['Sex', 'Todas', 'Série: Sequenciador de Mapas (cartão 8 ou vídeo) + cartão 10 (chamada final)'],
    ], [0.18, 0.3, 0.52], small=True)
    brk()

    # -----------------------------------------------------------------------------------------------
    h1('Conferência dos fatos')
    table(['Afirmação usada', 'Fonte no repositório'], [
        ['Versão 1.6.1, QGIS 4, gratuito, GPL-3.0, PT/EN/ES', 'geosaga/metadata.txt; LICENSE; README.md'],
        ['Voronoi Simples e Com Massa: 100% das células', 'CHANGELOG 1.4.0; NOTAS_DA_VERSAO_140.md'],
        ['Voronoi com atrito: 99,1% a 99,7% das células', 'CHANGELOG 1.4.0 (guia Raster 99,4-99,7%; guia Vetorial 99,1-99,6%)'],
        ['Assinatura do mapa inteiro: 100%', 'CHANGELOG 1.5.0; NOTAS_DA_VERSAO_150.md'],
        ['Dicas em todos os botões e campos', 'CHANGELOG 1.6.0'],
        ['Vila Serena: 32,5 → 109,7 ha; 17,9 ha de cidade em várzea', 'Tutorial (exemplo fictício, dados sintéticos)'],
        ['Implementação independente, sem vínculo com o Vista SAGA/UFRJ', 'README.md; metadata.txt (about)'],
    ], [0.55, 0.45], small=True)
    p('Não foram usados números de downloads, usuários, depoimentos nem parcerias.')
    return {'lang': 'pt', 'ui': UI, 'blocks': B}


def _x_len(text):
    """Comprimento no X: cada link conta 23 caracteres; emojis contam 2."""
    import re
    links = re.findall(r'https?://\S+', text)
    rest = re.sub(r'https?://\S+', '', text)
    emoji = sum(1 for ch in rest if ord(ch) > 0x2600)
    return len(rest) + emoji + 23 * len(links)


def main(work, target):
    for msg in THREAD:
        assert _x_len(msg) <= 280, (len(msg), msg[:40])
    spec = build(work)
    toc = next(b for b in spec['blocks'] if b['type'] == 'toc')
    toc['entries'] = bm._toc_entries(spec)
    bm._render(spec, work, target)
    pages = bm._pdf_pages(target, work)
    cursor = next(i for i, page in enumerate(pages) if toc['title'] in page) + 1
    for entry in toc['entries']:
        needle = ' '.join(entry['text'].split())
        for index in range(cursor, len(pages)):
            if needle in pages[index]:
                entry['page'] = index + 1
                cursor = index
                break
    bm._render(spec, work, target)
    print(target, f'({len(pages) - 1} páginas)')


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
