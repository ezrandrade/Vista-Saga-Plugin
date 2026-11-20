"""Monta a especificação do manual (JSON) em cada idioma e chama o gerador DOCX (build_docx.js).

Uso, na raiz do repositório (depois de capture_windows.py e build_figures.py na mesma pasta de trabalho):
    python docs/manual/build_manual.py <pasta_de_trabalho> <pasta_de_saida>
"""
import importlib
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

ORDER = ['assinatura', 'monitoria', 'avaliacao', 'voronoi', 'combinacao', 'conversor', 'sequenciador']
FILE_NAMES = {'pt': 'Manual_Vista_Saga_Plugin_1.6.0_pt-BR.docx', 'en': 'User_Manual_Vista_Saga_Plugin_1.6.0_en.docx',
              'es': 'Manual_Usuario_Vista_Saga_Plugin_1.6.0_es.docx'}


def png_size(path):
    with open(path, 'rb') as stream:
        head = stream.read(24)
    width, height = struct.unpack('>II', head[16:24])
    return width, height


def image(path, width_in, caption):
    w, h = png_size(path)
    return {'type': 'image', 'path': path, 'width_in': width_in, 'ratio': h / w, 'caption': caption}


def build_spec(lang, work):
    c = importlib.import_module(f'content_{lang}')
    ui = c.UI
    fig = os.path.join(work, lang, 'figuras')
    win = os.path.join(work, lang, 'janelas')
    with open(os.path.join(work, lang, 'campos.json'), encoding='utf-8') as stream:
        fields = json.load(stream)
    blocks = [{'type': 'cover', 'title': ui['doc_title'], 'subtitle': ui['subtitle'], 'tagline': ui['tagline'],
               'author': ui['author'], 'date': ui['date'], 'logo': os.path.join(ROOT, 'docs', 'assets',
                                                                                  'vista-saga-mark.png')},
              {'type': 'toc', 'title': ui['toc']}, {'type': 'pagebreak'}]
    chapter = 0

    def h1(text):
        nonlocal chapter
        chapter += 1
        blocks.append({'type': 'h1', 'text': f'{chapter}. {text}'})

    # 1. Apresentação
    h1(c.INTRO['title'])
    blocks += [{'type': 'p', 'text': p} for p in c.INTRO['paras']]
    blocks.append(image(os.path.join(fig, 'panorama.png'), 6.3, c.UI['subtitle']))
    blocks.append({'type': 'h2', 'text': c.INTRO['audience_title']})
    blocks.append({'type': 'bullets', 'items': c.INTRO['audience']})
    blocks.append({'type': 'h2', 'text': c.INTRO['principles_title']})
    blocks.append({'type': 'bullets', 'items': c.INTRO['principles']})
    blocks.append({'type': 'h2', 'text': c.QUICK['title']})
    blocks.append({'type': 'table', 'cols': c.QUICK['cols'], 'rows': [list(r) for r in c.QUICK['rows']],
                   'widths': [0.38, 0.27, 0.35]})
    blocks.append({'type': 'pagebreak'})

    # 2. Instalação e primeiros passos
    h1(c.INSTALL['title'])
    blocks.append({'type': 'h2', 'text': c.INSTALL['steps_title']})
    blocks.append({'type': 'steps', 'items': c.INSTALL['steps']})
    blocks.append({'type': 'callout', 'kind': 'warning', 'title': ui['warning'], 'text': c.INSTALL['warning']})
    blocks.append({'type': 'h2', 'text': c.INSTALL['common_title']})
    blocks.append(image(os.path.join(fig, 'fluxo.png'), 6.3, c.INSTALL['common_title']))
    blocks.append({'type': 'bullets', 'items': c.INSTALL['common']})
    blocks.append({'type': 'callout', 'kind': 'warning', 'title': ui['warning'], 'text': c.INSTALL['temp_warning']})
    blocks.append({'type': 'pagebreak'})

    # 3. Conceitos
    h1(c.CONCEPTS['title'])
    blocks.append({'type': 'table', 'cols': ['', ''], 'header': False,
                   'rows': [[f'**{a}**', b] for a, b in c.CONCEPTS['items']], 'widths': [0.27, 0.73]})
    blocks.append({'type': 'pagebreak'})

    # 4 a 10. Módulos
    kinds = ui['kinds']
    for key in ORDER:
        m = c.MODULES[key]
        h1(m['title'])
        blocks.append({'type': 'h2', 'text': ui['concept']})
        blocks += [{'type': 'p', 'text': p} for p in m['concept']]
        name, caption = m['figure']
        blocks.append(image(os.path.join(fig, f'{name}.png'), 6.4, caption))
        blocks.append({'type': 'h2', 'text': ui['compare']})
        blocks.append({'type': 'table', 'cols': ui['compare_cols'], 'rows': [list(r) for r in m['compare']],
                       'widths': [0.32, 0.68]})
        blocks.append({'type': 'h2', 'text': ui['ease']})
        blocks.append({'type': 'bullets', 'items': m['ease']})
        blocks.append({'type': 'h2', 'text': ui['window']})
        for shot, shot_caption in m['windows']:
            blocks.append(image(os.path.join(win, f'{shot}.png'), 5.6, shot_caption))
        blocks.append({'type': 'h3', 'text': ui['fields_title']})
        rows = []
        for row in fields[key]:
            label = ui['close_label'] if row['label'] == 'Close' else row['label']
            rows.append([row['section'], label, kinds.get(row['kind'], row['kind']), row['tip']])
        blocks.append({'type': 'table', 'cols': ui['fields_cols'], 'rows': rows, 'widths': [0.2, 0.22, 0.13, 0.45],
                       'small': True, 'merge_first': True})
        blocks.append({'type': 'h2', 'text': ui['routine']})
        blocks.append({'type': 'steps', 'items': m['routine']})
        blocks.append({'type': 'h2', 'text': ui['results']})
        blocks.append({'type': 'table', 'cols': ui['results_cols'], 'rows': [list(r) for r in m['results']],
                       'widths': [0.26, 0.74]})
        blocks.append({'type': 'callout', 'kind': 'hidden', 'title': ui['hidden'], 'items': m['hidden']})
        blocks.append({'type': 'h2', 'text': ui['pitfalls']})
        blocks.append({'type': 'bullets', 'items': m['pitfalls']})
        blocks.append({'type': 'pagebreak'})

    # 11. Validação
    h1(c.VALIDATION['title'])
    blocks += [{'type': 'p', 'text': p} for p in c.VALIDATION['paras']]
    name, caption = c.VALIDATION['figure']
    blocks.append(image(os.path.join(fig, f'{name}.png'), 6.3, caption))
    blocks.append({'type': 'pagebreak'})

    # 12. Solução de problemas
    h1(c.FAQ['title'])
    for question, answer in c.FAQ['items']:
        blocks.append({'type': 'h3', 'text': question})
        blocks.append({'type': 'p', 'text': answer})

    # 13. Glossário
    h1(c.GLOSSARY['title'])
    blocks.append({'type': 'table', 'cols': ['', ''], 'header': False,
                   'rows': [[f'**{a}**', b] for a, b in c.GLOSSARY['items']], 'widths': [0.27, 0.73]})
    return {'lang': lang, 'ui': ui, 'blocks': blocks}


SOFFICE = os.environ.get('SOFFICE_PY', '')


def _render(spec, work, target):
    spec_path = os.path.join(work, f"spec_{spec['lang']}.json")
    with open(spec_path, 'w', encoding='utf-8') as stream:
        json.dump(spec, stream, ensure_ascii=False)
    subprocess.run(['node', os.path.join(HERE, 'build_docx.js'), spec_path, target], check=True)


def _pdf_pages(docx, work):
    """Texto de cada página do DOCX convertido em PDF pelo LibreOffice (para achar as páginas dos títulos)."""
    folder = os.path.join(work, 'pdf')
    os.makedirs(folder, exist_ok=True)
    command = (['python3', SOFFICE] if SOFFICE else ['soffice']) + ['--headless', '--convert-to', 'pdf',
                                                                    '--outdir', folder, docx]
    subprocess.run(command, check=True, capture_output=True, timeout=600)
    pdf = os.path.join(folder, os.path.splitext(os.path.basename(docx))[0] + '.pdf')
    text = subprocess.run(['pdftotext', '-layout', pdf, '-'], check=True, capture_output=True,
                          text=True).stdout
    return [' '.join(page.split()) for page in text.split('\f')]


def _toc_entries(spec):
    return [{'level': 1 if b['type'] == 'h1' else 2, 'text': b['text'], 'page': '00'}
            for b in spec['blocks'] if b['type'] in ('h1', 'h2')]


def main(work, out, languages=('pt', 'en', 'es')):
    os.makedirs(out, exist_ok=True)
    for lang in languages:
        spec = build_spec(lang, work)
        toc = next(b for b in spec['blocks'] if b['type'] == 'toc')
        toc['entries'] = _toc_entries(spec)
        target = os.path.join(out, FILE_NAMES[lang])
        _render(spec, work, target)                 # 1ª passada: páginas provisórias
        pages = _pdf_pages(target, work)
        # Os títulos também aparecem no próprio sumário: buscar só depois das páginas do sumário.
        texts = [' '.join(e['text'].split()) for e in toc['entries']]
        cursor = next(i for i, page in enumerate(pages) if toc['title'] in page)
        while cursor + 1 < len(pages) and sum(t in pages[cursor + 1] for t in texts) >= 10:
            cursor += 1                             # páginas seguintes do sumário
        cursor += 1
        for entry in toc['entries']:
            needle = ' '.join(entry['text'].split())
            for index in range(cursor, len(pages)):
                if needle in pages[index]:
                    entry['page'] = index + 1
                    cursor = index
                    break
        _render(spec, work, target)                 # 2ª passada: páginas reais
        missing = [e['text'] for e in toc['entries'] if e['page'] == '00']
        print(target, f'({len(pages) - 1} páginas; títulos sem página: {missing})')


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), sys.argv[3:] or ('pt', 'en', 'es'))
