# Imagens do site oficial

Imagens para substituir as capturas antigas de https://vistasagaplugin.wordpress.com/ (versão 1.6.0, dados sintéticos).

- `janelas/`: uma janela por módulo, na ordem da página inicial (substituem as 7 capturas de 30/10/2026).
- `resultados/`: infográficos calculados pelos motores do plugin (os mesmos do manual), para a seção
  "Documentação visual": panorama dos módulos, resultado de cada módulo e painel de validação.

Para gerar de novo, na raiz do repositório:

```bash
VSP_MANUAL_DATA=/home/usuario/Projeto QT_SCALE_FACTOR=2 QT_QPA_PLATFORM=offscreen python3.12 docs/manual/capture_windows.py <trabalho> pt
python3 docs/manual/build_site_images.py <trabalho>/pt/janelas docs/site/janelas
```
