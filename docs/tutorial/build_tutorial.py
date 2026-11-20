"""Tutorial passo a passo do Vista Saga Plugin 1.6.0 (pt-BR), em DOCX, com os números reais da execução.

Uso, na raiz do repositório, depois de executar_tutorial.py, capturar_tutorial.py e figuras_tutorial.py:
    SOFFICE_PY=<soffice.py> python3 docs/tutorial/build_tutorial.py <trabalho> <saida.docx>
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'docs', 'manual'))

import build_manual as bm  # noqa: E402  (renderização e sumário em duas passadas)

UI = {
    'doc_title': 'Tutorial passo a passo', 'subtitle': 'Vista Saga Plugin 1.6.0 para QGIS 4',
    'tagline': 'Vila Serena: do dado ao diagnóstico, nos sete módulos', 'author': 'Esdras Andrade (IGDEMA/UFAL)',
    'date': 'Novembro de 2026', 'toc': 'Sumário', 'figure': 'Figura', 'footer': 'Vista Saga Plugin 1.6.0 - Tutorial',
    'page': 'Página',
}


def f(value, places=2):
    """Número no formato brasileiro (vírgula decimal, ponto de milhar)."""
    text = f'{value:,.{places}f}'
    return text.replace(',', 'X').replace('.', ',').replace('X', '.')


def build(work):
    n = json.load(open(os.path.join(work, 'numeros.json'), encoding='utf-8'))
    fig = lambda name: os.path.join(work, 'figuras_pt', f'{name}.png')  # noqa: E731
    win = lambda name: os.path.join(work, 'janelas_pt', f'{name}.png')  # noqa: E731
    B = []
    chapter = [0]

    def h1(text):
        chapter[0] += 1
        B.append({'type': 'h1', 'text': f'{chapter[0]}. {text}'})

    def h2(text): B.append({'type': 'h2', 'text': text})
    def h3(text): B.append({'type': 'h3', 'text': text})
    def p(*texts): B.extend({'type': 'p', 'text': t} for t in texts)
    def bullets(items): B.append({'type': 'bullets', 'items': items})
    def steps(items): B.append({'type': 'steps', 'items': items})
    def table(cols, rows, widths, header=True): B.append({'type': 'table', 'cols': cols, 'rows': rows,
                                                          'widths': widths, 'header': header})
    def tip(title, text=None, items=None, kind='tip'):
        B.append({'type': 'callout', 'kind': kind, 'title': title, 'text': text, 'items': items})
    def image(path, caption, width=6.3): B.append(bm.image(path, width, caption))
    def brk(): B.append({'type': 'pagebreak'})

    sig = n['assinatura']
    union = sig['União da seleção']
    centro = next(v for k, v in sig.items() if 'Centro' in k and k != 'União da seleção')
    beira = next(v for k, v in sig.items() if 'Beira' in k)
    mon = n['monitoria']
    ev = n['avaliacao']
    vor = n['voronoi']
    conv = n['conversor']

    B.append({'type': 'cover', 'title': UI['doc_title'], 'subtitle': UI['subtitle'], 'tagline': UI['tagline'],
              'author': UI['author'], 'date': UI['date'],
              'logo': os.path.join(ROOT, 'docs', 'assets', 'vista-saga-mark.png')})
    B.append({'type': 'toc', 'title': UI['toc']})
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Antes de começar')
    p('Este tutorial é um **exercício guiado**: você vai fazer, do começo ao fim, um diagnóstico territorial '
      'completo de uma cidade fictícia, **Vila Serena**, usando os sete módulos do Vista Saga Plugin. Cada passo diz '
      'o que clicar, o que preencher e **qual resultado você deve obter**. Se o seu número bater com o do texto, você '
      'fez certo.',
      'O manual do usuário explica cada campo e cada conceito. Este tutorial faz o caminho inverso: parte de uma '
      'pergunta real e mostra como os módulos se encadeiam para respondê-la.')
    h2('A pergunta de Vila Serena')
    p('Vila Serena é uma cidade de 400 hectares (2 km × 2 km), cortada por um rio de norte a sul, com uma serra a '
      'leste. Entre 2000 e 2020, a mancha urbana triplicou. A prefeitura quer saber:')
    steps(['**De que são feitos** os bairros Centro e Beira-Rio hoje? (Assinatura)',
           '**O que mudou** entre 2000 e 2020, e às custas de quê? (Monitoria)',
           '**Que associações** de uso do solo e solo existem, e onde há cidade sobre solo de várzea? (Combinação)',
           '**Onde a cidade pode crescer** com menos conflito? (Avaliação)',
           '**Qual escola atende cada parte** da cidade, considerando o tamanho das escolas e o rio? (Voronoi)',
           '**Como mostrar** a expansão em uma animação para a audiência pública? (Sequenciador)'])
    p('O Conversor de Formatos aparece primeiro, porque prepara um dos mapas e porque é a ponte com o Vista SAGA.')
    h2('O que você precisa')
    table(['Item', 'Detalhe'], [
        ['QGIS', 'Versão 4.x (Windows ou Linux).'],
        ['Vista Saga Plugin', 'Versão 1.6.0 instalada (Complementos > Gerenciar e instalar > Instalar a partir do ZIP).'],
        ['Dados do tutorial', '**dados_tutorial_vila_serena_pt.zip** (dados sintéticos, livres para uso). Descompacte numa '
                              'pasta sem acentos no caminho, por exemplo C:\\VilaSerena\\dados.'],
        ['Tempo', 'Cerca de 2 horas para tudo; cada lição tem 10 a 20 minutos e pode ser feita sozinha.'],
    ], [0.25, 0.75])
    h2('O que tem na pasta de dados')
    table(['Arquivo', 'Conteúdo'], [
        ['uso_solo_2000.tif, uso_solo_2010.tif, uso_solo_2020.tif', 'Uso do solo em três datas: 1 Área urbana, 2 Vegetação '
                                                                    'nativa, 3 Agricultura, 4 Pastagem, 5 Água.'],
        ['solos.tif', '1 Argissolo, 2 Latossolo, 3 Neossolo flúvico (solo de várzea, sujeito a inundação).'],
        ['declividade.tif', '1 Plano (0-3%), 2 Suave ondulado (3-8%), 3 Ondulado (8-20%), 4 Forte ondulado (> 20%).'],
        ['atrito.tif', 'Nota de atrito para o Voronoi: área urbana 1, pastagem e agricultura 2, vegetação 4, água 10.'],
        ['bairros.gpkg', '6 bairros (campos CODIGO e NOME).'],
        ['escolas.gpkg', '6 escolas (campos NOME e MATRICULAS).'],
        ['aptidao_expansao.geosaga.json', 'Projeto pronto da Avaliação (pesos e notas da lição 5).'],
    ], [0.38, 0.62])
    p('Todos os rasters têm a **mesma grade**: 200 × 200 células de 10 m, no SRC **SIRGAS 2000 / UTM 25S '
      '(EPSG:31985)**. Isso não é acaso: vários módulos comparam mapas célula por célula e exigem a mesma grade.')
    tip('Os dados são sintéticos',
        'Vila Serena não existe. Os mapas foram gerados por um script com semente fixa '
        '(docs/tutorial/gerar_dados.py, no repositório), de modo que todos obtêm exatamente os mesmos números. '
        'Os pesos e as notas usados nas lições são escolhas didáticas, não recomendações de método.', kind='warning')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Preparação do projeto')
    steps(['Abra o QGIS 4 e crie um projeto novo (**Projeto > Novo**).',
           'Defina o SRC do projeto: **Projeto > Propriedades > SRC**, procure **31985** e escolha '
           '**SIRGAS 2000 / UTM zone 25S**. Clique em **OK**.',
           'Arraste para o painel de camadas os arquivos da pasta **dados**: os três **uso_solo**, **solos**, '
           '**declividade**, **atrito**, **bairros.gpkg** e **escolas.gpkg**.',
           'Confira a legenda dos rasters categóricos: o QGIS deve mostrar os **nomes das classes** (Área urbana, '
           'Vegetação nativa…), porque eles estão gravados nos GeoTIFFs.',
           'Salve o projeto na pasta do tutorial (**Projeto > Salvar como…**, por exemplo vila_serena.qgz).',
           'Crie uma pasta **resultados** ao lado da pasta **dados**: todos os resultados das lições vão para lá.'])
    image(fig('f01_dados'), 'Os mapas de Vila Serena: uso do solo em 2000 e 2020, solos e declividade')
    image(fig('f02_bairros_escolas'), 'Bairros e escolas (entre parênteses, o número de matrículas)', 4.2)
    tip('Por que o SRC importa tanto',
        'O plugin **nunca reprojeta sem avisar** e **nunca adivinha o SRC** pelas coordenadas. Mapas em SRCs '
        'diferentes são recusados com uma mensagem clara. Em trabalhos reais, padronize o SRC (projetado, em metros) '
        'antes de começar: é o passo que mais evita retrabalho.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lição 1 - Conversor de Formatos: preparar e trocar dados')
    p('**Objetivo:** transformar os bairros (vetor) num raster na mesma grade dos demais mapas, para usá-lo como '
      'referência na Assinatura; e exportar o uso do solo para o formato RS2, do Vista SAGA.')
    h2('1.1 Bairros: de vetor para GeoTIFF')
    steps(['Abra **Vista Saga Plugin > Conversor de Formatos**.',
           'Em **Converter**, escolha **Vetor → GeoTIFF (rasterização)**.',
           'Em **Camada vetorial do projeto**, escolha **Bairros** e clique em **Selecionar**.',
           'Em **Campo para rasterizar**, escolha **CODIGO**; em **Tamanho do pixel**, **10**.',
           'Em **Arquivo de saída**, indique resultados\\bairros.tif. Clique em **Executar**.'])
    image(win('t01_conversor_vetor_geotiff'), 'Conversor de Formatos: bairros.gpkg para GeoTIFF', 5.4)
    p(f"**Resultado esperado:** bairros.tif com **{conv['bairros_tif'][0]} × {conv['bairros_tif'][1]} células de "
      f"{f(conv['bairros_tif'][2], 0)} m**, exatamente a grade dos outros mapas, porque os bairros cobrem toda a "
      'área de estudo. O raster é carregado com um estilo (.qml) que mostra só as classes reais.')
    image(fig('f03_conversor'), 'O mesmo mapa antes (vetor) e depois (raster) da conversão')
    h2('1.2 Dar nome às classes do raster')
    p('O GeoTIFF gerado guarda os **códigos** (1 a 6), e o QGIS mostra "Classe 1", "Classe 2"… A Assinatura usa os '
      'nomes do estilo da camada no QGIS; então, dê nome às classes agora:')
    steps(['Clique duas vezes na camada **bairros** (raster) e abra **Simbologia**.',
           'Na coluna **Rótulo**, troque: 1 Beira-Rio, 2 Centro, 3 Alto da Serra, 4 Porto, 5 Jardim Novo, 6 Vila Verde.',
           'Clique em **OK**. Para guardar os nomes junto do arquivo: **Estilo > Salvar como padrão**.'])
    tip('Dica que só o tutorial conta',
        'A tabela de correspondência código → nome está no próprio bairros.gpkg (campos CODIGO e NOME). Abra a tabela '
        'de atributos ao lado da Simbologia e copie os nomes; em mapas com dezenas de classes, isso evita erro.')
    h2('1.3 Uso do solo 2020: de GeoTIFF para RS2 (e de volta)')
    steps(['No Conversor, escolha **GeoTIFF → RS2 (formato Vista SAGA)**.',
           'Em **Arquivo de entrada**, indique dados\\uso_solo_2020.tif; em **Arquivo de saída**, '
           'resultados\\uso_solo_2020.rs2. Clique em **Executar**.',
           'Para conferir, faça o caminho de volta: **RS2 → GeoTIFF**, entrada uso_solo_2020.rs2, saída '
           'uso_solo_2020_de_volta.tif. Confira o SRC: o plugin o lê do arquivo .rs2.json gravado no passo anterior '
           '(**EPSG:31985**).'])
    image(win('t02_conversor_geotiff_rs2'), 'Conversor de Formatos: GeoTIFF para RS2', 5.4)
    p(f"**Resultado esperado:** um arquivo RS2 de {f(conv['rs2_bytes'], 0)} bytes, mais o arquivo lateral "
      '**uso_solo_2020.rs2.rs2.json**, que guarda o SRC, a legenda e a correspondência dos códigos. O GeoTIFF de volta '
      f"é **{'idêntico célula a célula' if conv['ida_e_volta_identico'] else 'diferente'}** ao original, com os mesmos "
      'nomes e cores.')
    tip('Atenção', 'O RS2 **não guarda o SRC**. Ao levar um RS2 para outra pasta ou outra pessoa, leve também o '
        '.rs2.json; sem ele, o plugin pedirá que você confirme o SRC.', kind='warning')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lição 2 - Assinatura: de que são feitos Centro e Beira-Rio?')
    p('**Objetivo:** medir, dentro dos bairros Centro e Beira-Rio, quanto ocupa cada classe de uso do solo, de solo '
      'e de declividade.')
    steps(['Abra **Vista Saga Plugin > Assinatura**, guia **Raster**.',
           'Em **1. Mapas**, adicione **primeiro** o raster **bairros** (ele será a referência) e depois '
           '**Uso do solo 2020**, **Solos** e **Declividade** (Camada no QGIS + **Adicionar camada selecionada**).',
           'Em **2. Seleção na referência**, marque **1 - Beira-Rio** e **2 - Centro**.',
           'Em **3. Opções**, deixe **Resultado por feição** ligado (um bloco para cada bairro, além da união).',
           'Em **4. Resultado**, escreva o título "Centro e Beira-Rio" e escolha resultados\\assinatura.csv '
           '(o TXT é gravado ao lado). Clique em **Executar**.'])
    image(win('t03_assinatura_configuracao'), 'Assinatura: bairros como referência, Centro e Beira-Rio marcados', 5.2)
    image(win('t04_assinatura_resultados'), 'Assinatura, guia Resultados: a tabela da união da seleção', 5.8)
    h2('Resultado esperado')
    u_uso = union['uso_solo_2020.tif']
    p(f"A união dos dois bairros tem **{f(union['bairros.tif']['1 - Beira-Rio'][0] + union['bairros.tif']['2 - Centro'][0])} ha** "
      f"(Beira-Rio {f(union['bairros.tif']['1 - Beira-Rio'][0])} ha + Centro {f(union['bairros.tif']['2 - Centro'][0])} ha). "
      'Para o uso do solo de 2020:')
    table(['Classe', 'Área assinada (ha)', '% Área Asn.', '% Categoria'],
          [[k.split(' - ', 1)[1], f(v[0]), f(v[1]), f(v[2])] for k, v in u_uso.items() if not k.startswith('0 ')],
          [0.34, 0.22, 0.22, 0.22])
    h2('Como ler')
    bullets([f"**% Área Asn.** responde \"de que é feito o lugar\": {f(u_uso['1 - Área urbana'][1])}% da área dos dois "
             'bairros é urbana. Essa coluna soma 100% em cada mapa.',
             f"**% Categoria** responde \"quanto da classe está aqui\": {f(u_uso['1 - Área urbana'][2])}% de toda a área "
             f"urbana de Vila Serena está nesses dois bairros, e {f(u_uso['5 - Água'][2])}% da água. Essa coluna **não** "
             'soma 100%.',
             f"Por bairro, o contraste é forte: o Centro é {f(centro['uso_solo_2020.tif']['1 - Área urbana'][1])}% urbano; "
             f"a Beira-Rio, só {f(beira['uso_solo_2020.tif']['1 - Área urbana'][1])}%, com "
             f"{f(beira['uso_solo_2020.tif']['4 - Pastagem'][1])}% de pastagem.",
             f"No Centro, {f(centro['solos.tif']['3 - Neossolo flúvico'][1])}% da área é Neossolo flúvico, solo de várzea: "
             'uma pista que a Combinação e a Avaliação vão confirmar.'])
    image(fig('f04_assinatura'), 'Uso do solo 2020 em cada recorte: Centro, Beira-Rio e a cidade inteira')
    tip('Dicas que só o tutorial conta', items=[
        'A tabela da própria referência (bairros) mostra 100% nas classes marcadas: é a conferência do tamanho exato '
        'do limite. Se não der 100%, a seleção não é a que você pensa.',
        'Não some os blocos por bairro para obter a união: use o bloco "União da seleção".',
        'No CSV, filtre a coluna RECORTE (UNIAO ou FEICAO) e monte uma tabela dinâmica por MAPA e CLASSE.'])
    p('**Exercício:** assine sozinho o bairro **Jardim Novo**, a fronteira de expansão da cidade. Qual a % de área '
      'urbana? E de vegetação nativa?')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lição 3 - Monitoria: o que mudou entre 2000 e 2020?')
    steps(['Abra **Vista Saga Plugin > Monitoria**, guia **Raster**.',
           'Em **Mapa inicial**, escolha **Uso do solo 2000** e escreva **2000** em Período.',
           'Em **Mapa final**, escolha **Uso do solo 2020** e escreva **2020** em Período.',
           'Em **Título do estudo**, "Uso do solo 2000 - 2020"; em **Salvar em**, resultados\\transicoes_2000_2020.tif.',
           'Clique em **Executar**.'])
    image(win('t05_monitoria'), 'Monitoria: os dois períodos e o resultado', 5.4)
    h2('Resultado esperado')
    p(f"Das {f(mon['validos'], 0)} células ({f(mon['area_valida_ha'], 0)} ha), **{f(mon['pct_permanencia'])}% "
      f"permaneceram** na mesma classe ({f(mon['permanencias'] * 0.01)} ha) e **{f(mon['pct_mudanca'])}% mudaram** "
      f"({f(mon['mudancas'] * 0.01)} ha). As maiores mudanças:")
    import csv
    with open(os.path.join(work, 'resultados', 'transicoes_2000_2020_transicoes.csv'), encoding='utf-8-sig') as stream:
        changes = [r for r in csv.DictReader(stream, delimiter=';') if r['SITUACAO'] == 'Mudança']
    changes.sort(key=lambda r: -float(r['AREA_HA']))
    table(['Transição', 'Área (ha)', '% da área'],
          [[f"{r['DEIXOU_DE_SER']} → {r['TORNOU_SE']}", f(float(r['AREA_HA'])), f(float(r['PCT_VALIDOS']))]
           for r in changes[:5]], [0.5, 0.25, 0.25])
    image(fig('f05_monitoria'), 'O mapa de transições (permanência em cinza) e a área de cada classe nas duas datas')
    h2('Como ler')
    bullets(['A área urbana passou de **32,49 ha para 109,70 ha** (3,4 vezes). Quase metade do crescimento veio de '
             'pastagem (46,98 ha) e um quarto, de vegetação nativa (21,85 ha).',
             'A vegetação nativa caiu de **120,52 ha para 52,34 ha** (-56,6%): perdeu área para a cidade, para a '
             'pastagem e para a agricultura.',
             'A água (12,80 ha) não mudou: é um bom controle de qualidade. Se a água "mudasse", desconfie dos mapas.',
             'Na matriz (_matriz.csv), leia **por linha**: cada linha mostra para onde foi cada classe de 2000.'])
    tip('Dica que só o tutorial conta',
        'Abra o _transicoes.csv no Excel ou no LibreOffice e ordene pela coluna AREA_HA: as cinco primeiras linhas de '
        'mudança contam a história do período. A coluna LEGENDA já vem em linguagem de relatório ("Deixou de ser: '
        'Pastagem | Tornou-se: Área urbana").')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lição 4 - Combinação de Mapas: cidade sobre solo de várzea?')
    steps(['Abra **Vista Saga Plugin > Combinação de Mapas**, guia **Raster**.',
           'Adicione **Uso do solo 2020** e depois **Solos** (a ordem define a ordem das colunas na tabela).',
           'Em **Salvar em**, indique resultados\\uso2020_x_solos.tif e clique em **Executar**.'])
    image(win('t06_combinacao'), 'Combinação de Mapas: uso do solo 2020 e solos', 5.4)
    h2('Resultado esperado')
    p(f"**{n['combinacao']['combinacoes']} combinações** observadas, em {f(n['combinacao']['area_ha'], 0)} ha. "
      'A maior é **Pastagem | Argissolo** (98,07 ha, 24,52%). A que interessa à prefeitura é '
      '**Área urbana | Neossolo flúvico: 17,89 ha (4,47%)**: cidade construída sobre solo de várzea, sujeito a '
      'inundação.')
    image(fig('f06_combinacao'), 'Área de cada combinação de uso do solo e solo')
    tip('Dica que só o tutorial conta',
        'No QGIS, use a ferramenta **Identificar** sobre o mapa combinado: o código da célula corresponde ao ID_COMB do '
        '_combinacoes.csv. Para destacar só as áreas urbanas em várzea, abra a Simbologia e desmarque as demais '
        'combinações.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lição 5 - Avaliação: onde a cidade pode crescer?')
    p('**Objetivo:** produzir uma carta de aptidão à expansão urbana pela média ponderada de três critérios. Os '
      'pesos e as notas abaixo são **didáticos**: num estudo real, eles precisam ser justificados (literatura, '
      'consulta a especialistas, legislação).')
    table(['Critério (peso)', 'Notas (0 a 10)'], [
        ['Declividade (40%)', 'Plano 10; Suave ondulado 8; Ondulado 4; Forte ondulado 1'],
        ['Solos (25%)', 'Argissolo 7; Latossolo 9; Neossolo flúvico 2 (várzea, inundável)'],
        ['Uso do solo 2020 (35%)', 'Área urbana 8; Vegetação nativa 1; Agricultura 6; Pastagem 9; Água: Não avaliar'],
    ], [0.3, 0.7])
    h2('Montagem passo a passo')
    steps(['Abra **Vista Saga Plugin > Avaliação**, guia **Raster**. Escala das notas: **0 a 10**.',
           'Adicione **Declividade**, **Solos** e **Uso do solo 2020**. Os pesos entram em branco, de propósito.',
           'Digite os pesos 40, 25 e 35 (a tecla **Tab** salta de peso em peso). A linha abaixo da tabela deve dizer '
           '"Pesos: 100,00% - distribuição válida".',
           'Selecione cada mapa e digite as notas das classes. Em **Água**, marque **Não avaliar**.',
           'Clique em **Validar**: não pode restar nenhuma classe com nota "—".',
           'Em **Salvar em**, indique resultados\\aptidao_expansao.tif, mantenha os dois relatórios marcados e clique '
           'em **Executar**.'])
    tip('Atalho', 'Em vez de digitar tudo, clique em **Abrir projeto…** e escolha dados\\aptidao_expansao.geosaga.json: '
        'os três mapas, os pesos e as notas são carregados de uma vez. É assim que você reaproveita uma avaliação.')
    image(win('t07_avaliacao'), 'Avaliação: pesos, notas e Água em "Não avaliar"', 5.8)
    h2('Resultado esperado')
    per = ev['area_por_nota_ha']
    p(f"**{f(ev['pixels_validos'], 0)} células avaliadas** ({f(ev['pixels_validos'] * 0.01, 1)} ha) e "
      f"{f(ev['pixels_sem_avaliacao'], 0)} sem avaliação (a água, {f(ev['pixels_sem_avaliacao'] * 0.01, 1)} ha). Nota "
      f"mínima **{f(ev['minimo'], 1)}**, máxima **{f(ev['maximo'], 1)}**, média **{f(ev['media'])}**. Área por nota final "
      '(como no relatório):')
    table(['Nota final'] + sorted(per, key=int), [['Área (ha)'] + [f(per[k]) for k in sorted(per, key=int)]],
          [0.2] + [0.8 / len(per)] * len(per))
    image(fig('f07_avaliacao'), 'Carta de aptidão à expansão urbana e área por nota final')
    h2('Como ler')
    bullets([f"As notas **8 e 9** ({f(per.get('8', 0) + per.get('9', 0))} ha) são as áreas mais aptas: quase todas em "
             'relevo plano ou suave ondulado, sobre argissolo, ocupadas por pastagem ou já urbanas.',
             f"A nota **3** ({f(per.get('3', 0))} ha) junta o pior de tudo: vegetação nativa em encosta forte.",
             'Um resultado que ensina: o **Latossolo**, apesar da nota 9, tem a menor nota média (5,51), porque fica na '
             'serra, em declividade alta. A declividade (40%) pesa mais que o solo (25%) e domina. Já a várzea (Neossolo '
             'flúvico, nota 2) fica com média 6,18: é plana, e o solo a penaliza só em parte. Se a prefeitura quiser '
             'excluir a várzea de vez, não basta nota baixa: marque a classe como **Não avaliar**.'])
    tip('Dicas que só o tutorial conta', items=[
        'A nota "—" bloqueia a execução: o plugin **nunca supõe nota 0**. Isso é proposital, para que nenhuma classe '
        'entre na conta sem decisão sua.',
        'Cada execução grava *_pesos_notas.geosaga.json ao lado da carta: é o registro exato do que você usou. '
        'Guarde-o junto do relatório do estudo.',
        'Teste a sensibilidade: troque os pesos para 50/20/30 e compare as cartas. Se o mapa mudar muito, a decisão '
        'sobre os pesos é crítica e precisa de justificativa forte.'])
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lição 6 - Análises Voronoi: qual escola atende cada parte da cidade?')
    p('Três versões da mesma pergunta: pela distância pura (**Simples**), pelo porte da escola (**Com Massa**, '
      'matrículas) e pela dificuldade de deslocamento (**Com Atrito**, o rio custa caro para atravessar).')
    h2('6.1 Com Massa')
    steps(['Abra **Vista Saga Plugin > Análises Voronoi**, guia **Raster**.',
           'Em **Modalidade**, escolha **Com Massa**.',
           'Em **Pontos geradores**, **Escolas**; em **Identificação do ponto**, **NOME**; em **Campo de massa**, '
           '**MATRICULAS**.',
           'Em **Extensão da análise**, escolha **Grade de raster de referência** e, em **Raster de referência**, '
           '**Atrito**: assim o resultado cai exatamente na grade dos outros mapas.',
           'Em **Salvar em**, resultados\\voronoi_com_massa.tif. Clique em **Executar**.'])
    image(win('t09_voronoi_massa'), 'Análises Voronoi, Com Massa: matrículas como massa, grade do raster de atrito', 5.4)
    h2('6.2 Com Atrito')
    steps(['Troque a **Modalidade** para **Com Atrito**.',
           'Em **Tipo de superfície**, **Raster**; em **Superfície de atrito**, **Atrito**.',
           'Mantenha a grade do raster de referência; em **Salvar em**, resultados\\voronoi_com_atrito.tif. '
           'Clique em **Executar**.',
           'Para comparar, rode também a modalidade **Simples** (resultados\\voronoi_simples.tif).'])
    image(win('t08_voronoi_atrito'), 'Análises Voronoi, Com Atrito: superfície de atrito raster', 5.4)
    h2('Resultado esperado')
    names = list(vor['simples'])
    table(['Escola (matrículas)', 'Simples (ha)', 'Com Massa (ha)', 'Com Atrito (ha)'],
          [[f"{k} ({f(vor['simples'][k]['MASSA'], 0)})", f(vor['simples'][k]['AREA_HA']),
            f(vor['com_massa'][k]['AREA_HA']), f(vor['com_atrito'][k]['AREA_HA'])] for k in names],
          [0.4, 0.2, 0.2, 0.2])
    image(fig('f08_voronoi'), 'As regiões de influência nas três modalidades (na modalidade Com Massa, o tamanho do '
          'ponto é proporcional às matrículas)')
    h2('Como ler')
    bullets([f"**Com Massa**, a E. E. Darcy Ribeiro (1.200 matrículas) passa de {f(vor['simples']['E. E. Darcy Ribeiro']['AREA_HA'])} "
             f"para **{f(vor['com_massa']['E. E. Darcy Ribeiro']['AREA_HA'])} ha**; a E. M. Cora Coralina (250) cai de "
             f"{f(vor['simples']['E. M. Cora Coralina']['AREA_HA'])} para {f(vor['com_massa']['E. M. Cora Coralina']['AREA_HA'])} ha. "
             'O critério é M/d²: uma escola com massa 4 vezes maior alcança o dobro da distância, não o quádruplo.',
             f"**Com Atrito**, a E. M. Monteiro Lobato, junto ao rio, perde área ({f(vor['simples']['E. M. Monteiro Lobato']['AREA_HA'])} → "
             f"{f(vor['com_atrito']['E. M. Monteiro Lobato']['AREA_HA'])} ha): atravessar a água custa 10 vezes mais que andar "
             'na cidade. A E. E. Cecília Meireles ganha '
             f"({f(vor['simples']['E. E. Cecília Meireles']['AREA_HA'])} → {f(vor['com_atrito']['E. E. Cecília Meireles']['AREA_HA'])} ha).",
             'O custo é medido na **reta** entre a escola e cada lugar, como no Vista SAGA: não é o caminho de menor custo '
             '(r.cost do GRASS). A reta "paga" o rio; não o contorna.'])
    tip('Dicas que só o tutorial conta', items=[
        'Nota de atrito 0 é recusada; para "quase sem atrito", use 0,1.',
        'Em caso de empate exato, ganha o primeiro ponto da camada.',
        'O _centros.csv traz a área e a % de cada escola: cole-o ao lado da tabela de matrículas e calcule '
        'matrículas por hectare atendido.'])
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Lição 7 - Sequenciador de Mapas: a expansão em animação')
    steps(['Abra **Vista Saga Plugin > Sequenciador de Mapas**, guia **Raster**.',
           'Adicione, nesta ordem, **Uso do solo 2000**, **Uso do solo 2010** e **Uso do solo 2020** '
           '(o plugin lê o ano no nome; use **Ordenar por data** se precisar).',
           'Em **2. Dimensões e composição**: largura e altura **600**, duração **1000 ms / quadro**, '
           '**Exibir data/período sobre o mapa** ligado.',
           'Em **3. Saídas e prévia**, indique resultados\\vila_serena_2000_2020.gif e marque a exportação dos '
           'quadros em PNG. Clique em **Executar**.'])
    image(win('t10_sequenciador'), 'Sequenciador de Mapas: três quadros, 600 × 600 pixels', 5.2)
    p('**Resultado esperado:** um GIF de 3 quadros (2000, 2010, 2020) com o ano no canto, e uma pasta com os três PNGs '
      '(quadro_001_2000.png…). Os quadros usam a simbologia que está no QGIS.')
    image(fig('f09_sequenciador'), 'Os três quadros gerados pelo Sequenciador')
    tip('Dica que só o tutorial conta',
        'O GIF tem no máximo 256 cores. Para uma apresentação de slides, use os PNGs: as cores ficam exatas e você '
        'controla o tempo de cada quadro no próprio programa de apresentação.')
    brk()

    # ------------------------------------------------------------------------------------------------
    h1('Fechamento: o diagnóstico de Vila Serena')
    p('Juntando as lições, a resposta à prefeitura cabe em cinco frases:')
    steps([f"O Centro já é {f(centro['uso_solo_2020.tif']['1 - Área urbana'][1], 1)}% urbano, e um terço dele está "
           'sobre solo de várzea (Assinatura).',
           'Em 20 anos, a cidade triplicou, principalmente sobre pastagem, e a vegetação nativa perdeu mais da metade da '
           'área (Monitoria).',
           'Há 17,89 ha de cidade sobre Neossolo flúvico, prioridade para drenagem e controle de cheias (Combinação).',
           f"As áreas mais aptas para crescer (notas 8 e 9, {f(per.get('8', 0) + per.get('9', 0))} ha) ficam em relevo "
           'plano ou suave, quase todas fora da várzea (Avaliação).',
           'O rio redesenha o atendimento escolar: considerar a travessia muda a área atendida da maioria das escolas '
           '(Voronoi).'])
    h2('Lista de conferência')
    table(['Lição', 'Arquivo esperado em resultados', 'Número-chave'], [
        ['1', 'bairros.tif, uso_solo_2020.rs2 (+ .rs2.json)', '200 × 200 células; ida e volta idêntica'],
        ['2', 'assinatura.csv, assinatura.txt', f"Área urbana na união: {f(u_uso['1 - Área urbana'][0])} ha ({f(u_uso['1 - Área urbana'][1])}%)"],
        ['3', 'transicoes_2000_2020.tif + _transicoes.csv, _matriz.csv, _resumo.txt', f"Mudança: {f(mon['pct_mudanca'])}%"],
        ['4', 'uso2020_x_solos.tif + _combinacoes.csv, _resumo.txt', f"{n['combinacao']['combinacoes']} combinações"],
        ['5', 'aptidao_expansao.tif + relatórios CSV e TXT + _pesos_notas.geosaga.json', f"Média {f(ev['media'])}"],
        ['6', 'voronoi_*.tif + _centros.csv, _resumo.txt', f"Darcy Ribeiro Com Massa: {f(vor['com_massa']['E. E. Darcy Ribeiro']['AREA_HA'])} ha"],
        ['7', 'vila_serena_2000_2020.gif + pasta de PNGs', '3 quadros'],
    ], [0.08, 0.52, 0.4])
    h2('Se o seu número não bateu')
    bullets(['Confira se usou os mapas certos (2000 e 2020, não 2010) e a ordem certa na lista.',
             'Confira o SRC do projeto e das camadas (EPSG:31985).',
             'Na Avaliação, confira pesos e notas com o projeto pronto (aptidao_expansao.geosaga.json).',
             'No Voronoi, confira a extensão: com "Extensão visível no QGIS", a área total muda com o zoom e as áreas '
             'não batem; use a grade do raster de referência.'])
    h2('Próximos passos')
    bullets(['Repita as lições com os seus dados: o roteiro é o mesmo.',
             'Consulte o **Manual do Usuário** para todos os campos, opções avançadas e dicas de cada módulo.',
             'Assista aos vídeos de cada módulo no canal do projeto (links no site oficial).'])
    return {'lang': 'pt', 'ui': UI, 'blocks': B}


def main(work, target):
    spec = build(work)
    toc = next(b for b in spec['blocks'] if b['type'] == 'toc')
    toc['entries'] = bm._toc_entries(spec)
    bm._render(spec, work, target)
    pages = bm._pdf_pages(target, work)
    texts = [' '.join(e['text'].split()) for e in toc['entries']]
    cursor = next(i for i, page in enumerate(pages) if toc['title'] in page)
    while cursor + 1 < len(pages) and sum(t in pages[cursor + 1] for t in texts) >= 10:
        cursor += 1
    cursor += 1
    for entry in toc['entries']:
        needle = ' '.join(entry['text'].split())
        for index in range(cursor, len(pages)):
            if needle in pages[index]:
                entry['page'] = index + 1
                cursor = index
                break
    bm._render(spec, work, target)
    print(target, f'({len(pages) - 1} páginas; sem página: {[e["text"] for e in toc["entries"] if e["page"] == "00"]})')


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
