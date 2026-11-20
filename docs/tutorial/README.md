# Tutorial passo a passo (Vila Serena)

Exercício guiado pelos sete módulos, sobre a cidade fictícia de Vila Serena (dados sintéticos, semente fixa).
O texto cita os números que os motores do plugin realmente produzem com esses dados.

- `saida/Tutorial_Vista_Saga_Plugin_1.6.0_<pt-BR|en|es>.docx`: o tutorial nos três idiomas (texto em
  `tutorial_<idioma>.py`; capturas com a interface e os nomes das classes no idioma).
- `dados/dados_tutorial_vila_serena_<pt|en|es>.zip`: dados para download (mesmos números; nomes de classes,
  bairros e critérios no idioma).

## Como gerar de novo (na raiz do repositório)

```bash
# Um idioma por pasta de trabalho (o caminho aparece nas capturas): pt /home/usuario/VilaSerena,
# en /home/user/Documents/VilaSerena, es /home/usuario/Documentos/VilaSerena
L=pt; W=/home/usuario/VilaSerena
python3.12 docs/tutorial/executar_tutorial.py $W $L                  # dados + os 7 módulos + numeros.json
QT_SCALE_FACTOR=2 QT_QPA_PLATFORM=offscreen python3.12 docs/tutorial/capturar_tutorial.py $W $L   # janelas + GIF
python3.12 docs/tutorial/figuras_tutorial.py $W $L                   # figuras a partir dos resultados
SOFFICE_PY=<soffice.py> python3 docs/tutorial/build_tutorial.py $W docs/tutorial/saida/Tutorial_Vista_Saga_Plugin_1.6.0_pt-BR.docx $L
python3.12 docs/tutorial/empacotar_dados.py $W                       # pacotes de dados pt/en/es
```

Mudou um motor? Rode `executar_tutorial.py` de novo e confira se os números do tutorial e dos roteiros mudaram.
