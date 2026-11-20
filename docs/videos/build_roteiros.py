"""Roteiros de vídeo em DOCX (um documento por idioma), com o mesmo gerador do manual.

Uso, na raiz do repositório:
    SOFFICE_PY=<soffice.py> python3 docs/videos/build_roteiros.py <pasta_de_trabalho> <pasta_de_saida> [pt en es]
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'docs', 'manual'))

import build_manual as bm  # noqa: E402

FILE_NAMES = {'pt': 'Roteiros_Videos_Vista_Saga_Plugin_1.6.0_pt-BR.docx',
              'en': 'Video_Scripts_Vista_Saga_Plugin_1.6.0_en.docx',
              'es': 'Guiones_Videos_Vista_Saga_Plugin_1.6.0_es.docx'}


def build_spec(lang):
    c = importlib.import_module(f'roteiros_{lang}')
    ui = c.UI
    blocks = [{'type': 'cover', 'title': ui['doc_title'], 'subtitle': ui['subtitle'], 'tagline': ui['tagline'],
               'author': ui['author'], 'date': ui['date'],
               'logo': os.path.join(ROOT, 'docs', 'assets', 'vista-saga-mark.png')},
              {'type': 'toc', 'title': ui['toc']}, {'type': 'pagebreak'}]
    g = c.GUIDE
    blocks.append({'type': 'h1', 'text': g['title']})
    blocks += [{'type': 'p', 'text': p} for p in g['paras']]
    blocks.append({'type': 'h2', 'text': g['production_title']})
    blocks.append({'type': 'bullets', 'items': g['production']})
    blocks.append({'type': 'h2', 'text': g['series_title']})
    blocks.append({'type': 'bullets', 'items': g['series']})
    blocks.append({'type': 'p', 'text': g['series_note']})
    for video in c.VIDEOS:
        blocks.append({'type': 'pagebreak'})
        blocks.append({'type': 'h1', 'text': video['title']})
        blocks.append({'type': 'h2', 'text': ui['sheet']})
        blocks.append({'type': 'table', 'cols': ui['sheet_cols'], 'header': False,
                       'rows': [[f'**{k}**', v] for k, v in zip(ui['fields'], video['sheet'])], 'widths': [0.25, 0.75]})
        blocks.append({'type': 'h2', 'text': ui['scenes']})
        blocks.append({'type': 'table', 'cols': ui['cols'], 'rows': [list(s) for s in video['scenes']],
                       'widths': [0.08, 0.27, 0.47, 0.18], 'small': True})
        blocks.append({'type': 'h2', 'text': ui['youtube']})
        blocks.append({'type': 'h3', 'text': ui['description']})
        blocks.append({'type': 'p', 'text': video['description']})
        blocks.append({'type': 'h3', 'text': ui['chapters']})
        blocks.append({'type': 'bullets', 'items': video['chapters']})
        blocks.append({'type': 'h3', 'text': ui['tags']})
        blocks.append({'type': 'p', 'text': video['tags']})
    return {'lang': lang, 'ui': ui, 'blocks': blocks}


def main(work, out, languages):
    os.makedirs(out, exist_ok=True)
    for lang in languages:
        spec = build_spec(lang)
        toc = next(b for b in spec['blocks'] if b['type'] == 'toc')
        toc['entries'] = bm._toc_entries(spec)
        target = os.path.join(out, FILE_NAMES[lang])
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
        print(target, f'({len(pages) - 1} páginas; sem página: {[e["text"] for e in toc["entries"] if e["page"] == "00"]})')


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), sys.argv[3:] or ['pt', 'en', 'es'])
