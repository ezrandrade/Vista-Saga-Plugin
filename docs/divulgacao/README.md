# Divulgação do Vista Saga Plugin 1.6.1

- `material/`: peças prontas (pt-BR) - carrossel de 10 cartões (PNG 1080x1350 e PDF para o LinkedIn), post de
  lançamento (1080x1080), capa de link (1200x627), vídeo vertical de 30 s (1080x1920, sem áudio) e o kit de textos
  em DOCX (legendas por rede, thread do X, post acadêmico, roteiro do vídeo, hashtags, calendário e conferência
  dos fatos).
- `PROMPT_REDES_SOCIAIS.md` e `imagens/`: prompt e imagens para gerar material com outra IA.

Para gerar de novo, na raiz do repositório:

```bash
node docs/divulgacao/build_pecas.js <trabalho>            # carrossel, post, capa e cenas do vídeo
bash docs/divulgacao/montar_video.sh <trabalho>           # vídeo vertical (ffmpeg)
SOFFICE_PY=<soffice.py> python3 docs/divulgacao/kit_textos.py <trabalho> <trabalho>/Kit_Divulgacao_Vista_Saga_Plugin_1.6.1.docx
```

Regras: só fatos do repositório (validação registrada no CHANGELOG); Vila Serena sempre como exemplo fictício;
nenhuma sugestão de vínculo com o Vista SAGA/UFRJ.
