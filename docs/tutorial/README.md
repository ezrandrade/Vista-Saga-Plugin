# Tutorial passo a passo (Vila Serena)

Exercício guiado pelos sete módulos, sobre a cidade fictícia de Vila Serena (dados sintéticos, semente fixa).
O texto cita os números que os motores do plugin realmente produzem com esses dados.

- `saida/Tutorial_Vista_Saga_Plugin_1.6.0_pt-BR.docx`: o tutorial.
- `dados/dados_tutorial_vila_serena_<pt|en|es>.zip`: dados para download (mesmos números; nomes de classes,
  bairros e critérios no idioma).

## Como gerar de novo (na raiz do repositório)

```bash
W=/home/usuario/VilaSerena   # pasta de nome legível: aparece nas capturas
python3.12 docs/tutorial/executar_tutorial.py $W                     # dados + os 7 módulos + numeros.json
QT_SCALE_FACTOR=2 QT_QPA_PLATFORM=offscreen python3.12 docs/tutorial/capturar_tutorial.py $W pt   # janelas + GIF
python3.12 docs/tutorial/figuras_tutorial.py $W pt                   # figuras a partir dos resultados
SOFFICE_PY=<soffice.py> python3 docs/tutorial/build_tutorial.py $W docs/tutorial/saida/Tutorial_Vista_Saga_Plugin_1.6.0_pt-BR.docx
python3.12 docs/tutorial/empacotar_dados.py $W                       # pacotes de dados pt/en/es
```

Mudou um motor? Rode `executar_tutorial.py` de novo e confira se os números do tutorial e dos roteiros mudaram.
