"""Tutorial passo a passo do Vista Saga Plugin 1.6.0 em DOCX (pt-BR, en, es), com os números reais da execução.

Uso, na raiz do repositório, depois de executar_tutorial.py, capturar_tutorial.py e figuras_tutorial.py
(na mesma pasta de trabalho e no mesmo idioma):
    SOFFICE_PY=<soffice.py> python3 docs/tutorial/build_tutorial.py <trabalho> <saida.docx> [pt|en|es]
O texto de cada idioma fica em tutorial_<idioma>.py.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'docs', 'manual'))

import build_manual as bm  # noqa: E402

def main(work, target, lang='pt'):
    spec = importlib.import_module(f'tutorial_{lang}').build(work)
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
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else 'pt')
