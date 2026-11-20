# Manual do usuário (DOCX)

Manual do Vista Saga Plugin em português do Brasil, inglês e espanhol. Os arquivos prontos ficam em `saida/`.

## Como gerar de novo

Na raiz do repositório, com QGIS (PyQGIS) em `python3.12`, LibreOffice, `pdftotext` e o pacote npm `docx`:

```bash
M=/caminho/de/trabalho
QT_QPA_PLATFORM=offscreen python3.12 docs/manual/capture_windows.py $M   # capturas e campos.json (dados sintéticos)
QT_QPA_PLATFORM=offscreen python3.12 docs/manual/build_figures.py $M     # infográficos
python3 docs/manual/build_manual.py $M docs/manual/saida pt en es       # DOCX com sumário em duas passadas
```

- `content_pt.py`, `content_en.py` e `content_es.py` têm o texto, com a mesma estrutura.
- As tabelas de campos vêm das dicas reais da interface (`campos.json`): ao mudar uma dica, gere o manual de novo.
- Nenhum dado do autor entra aqui: capturas e figuras usam dados sintéticos.
