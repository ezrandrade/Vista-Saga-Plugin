# Contexto entre sessões

Registro das decisões, achados e pendências que ficaram fora do código. Serve para que uma nova
sessão do Claude (ou o próprio autor) retome o trabalho sem depender do histórico de conversas.
Atualize ao fim de cada sessão de trabalho. As entradas mais recentes ficam no topo.

---

## 17/11/2026 (tarde) — 1.3.0 fechada; caso de teste do atrito

- **1.3.0 fechada e mesclada** (merge `87406de` na `main`). Tag `v1.3.0` pendente (autor).
- **Branch da 1.4.0:** `feat/voronoi-atrito-fiel` ("atrito fiel ao Vista SAGA"). Versão do
  `metadata.txt` ainda 1.3.0: muda junto com a primeira alteração de código.
- **Caso de teste enviado ao autor** (`teste_voronoi_atrito.zip`), reproduzível com
  `python scripts/gerar_caso_atrito.py PASTA` (gera arquivos idênticos byte a byte):
  - `teste_atrito.rs2`: 80 × 60 células de 10 m; bordas X 500000–500800, Y 8900000–8900600;
    classes 0 FUNDO (ausente do mapa), 1 Atrito baixo, 2 Atrito médio, 3 Atrito alto;
    faixa vertical de atrito alto (colunas 30–39) com corredor de atrito baixo (linhas 25–34) e
    bloco alto (linhas 5–19, colunas 55–69);
  - pontos (coluna, linha, a partir de 0): Polo A M=9 (12, 15); Polo B M=4 (60, 50);
    Polo C M=1 (72, 10); notas `[ATRITOS]` 1, 1, 3, 5;
  - `pontos_pixel.txt` (X:Y = coluna:linha) e `pontos_utm.txt` (X:Y = centro da célula), porque
    a unidade das coordenadas não foi confirmada.
- **Roteiro pedido ao autor:** abrir o RS2 e conferir com `mapa_previa.png`; carregar
  `pontos_pixel.txt` (se falhar, `pontos_utm.txt`; anotar qual funcionou e qualquer deslocamento);
  conferir as notas; rodar e salvar R1 atrito sem massa, R2 atrito com massa, R3 sem atrito com
  massa, R4 simples; salvar o arquivo de pontos pelo Vista SAGA (`pontos_salvo.txt`).
- **Próximo passo:** com os quatro RS2 e o `pontos_salvo.txt`, comparar pixel a pixel com a
  simulação da leitura do executável e fixar o modelo da 1.4.0.

## 17/11/2026 — recuperação do contexto da sessão de 16/11 (noite)

A sessão de 16/11 que produziu a 1.3.0 foi interrompida por bloqueio automático antes de registrar
o contexto. O resumo abaixo foi reconstruído a partir do histórico dela.

### Estado da versão 1.3.0

- **Branch:** `feat/voronoi-saida-vetorial`; **PR:**
  [ezrandrade/Vista-Saga-Plugin#12](https://github.com/ezrandrade/Vista-Saga-Plugin/pull/12),
  sem merge.
- **Build de teste:** `Vista_Saga_Plugin_QGIS4_v1.3.0-dev3.zip` = commit `9476819`.
  O autor testou no QGIS e aprovou ("Deu certo").
- Conteúdo: ver `geosaga/NOTAS_DA_VERSAO_130.md` e `geosaga/CHANGELOG.md`.
- **Decisão do autor (17/11):** fechar a 1.3.0 como está e tratar o atrito na 1.4.0.

### Achado de método: o modelo de atrito do Voronoi

Modelo atual do plugin (experimental desde a 0.7.5):

> escore = D × Σ(1 + atrito de cada célula atravessada) / M

Testes com atrito zero, na sessão de 16/11:

1. **O custo depende da direção.** Segmentos de mesmo comprimento custaram 10.100 (0°),
   13.100 (22,5°) e 7.200 (45°), porque a soma conta células, não comprimento percorrido. Também
   depende da resolução.
2. **No modo Com Massa e Atrito, as massas valem como √M.** Como Σ cresce com D, o escore fica
   proporcional a D²/M. Com massas 1 e 9 e atrito zero, a área do centro leve foi de 4.016
   células, contra 401 no Com Massa; o modelo com √M dá 4.420 (98,3% de coincidência).

**Fonte primária da fórmula:** manual do Vista SAGA (texto enviado pelo autor; não vai para o
repositório por direitos autorais), que define

> FZ(Gi) = M(Gi) / [ D(x→Gi) × A(x→Gi) ], com A = Σ Cₖ sobre as células da trajetória reta.

O manual chama o procedimento de "exploratório". O expoente 1 em M/d vem do manual.

**Análise estática dos programas originais** (sem executar e sem copiar código; só o método).
As conclusões são **leituras do executável, ainda não validadas** com um mapa gerado pelo
Vista SAGA:

| | VORONOI.EXE (ancestral, 16 bits) | Vista SAGA (integrado, 32 bits) |
|---|---|---|
| Fórmula | escolha: M/(d + a), padrão, ou M/(d × a) | sem escolha |
| Percurso | reta de cada célula até cada polo | raios de cada polo até as células da borda |
| Atrito | nota por classe, por trecho de classe constante | nota por classe, célula a célula no raio |
| Acúmulo | soma: (D + Σ notas)/M; produto: Σ(L × nota)/M | Σ (distância do polo à célula × nota × √2 nos passos diagonais) / M |
| Classes excluídas | não | sim (atravessadas, sem resultado) |

- No **Vista SAGA integrado**, a referência da tese, o efeito √M **também existe** (simulação:
  99,8% de coincidência com o modelo √M). Logo, é propriedade do método original, a ser declarada
  na tese, e não erro do plugin.
- Diferenças restantes entre o plugin e o Vista SAGA:
  1. peso do atrito: o Vista SAGA pondera a nota pela distância da célula ao polo; o plugin soma
     células com peso igual e multiplica por D;
  2. custo basal: o plugin usa 1 + C; o Vista SAGA usa a nota direto (padrão 1);
  3. percurso: raios até a borda com √2 nas diagonais × reta célula-polo;
  4. classes excluídas: só no Vista SAGA.
- Não confirmados: a rotina final que preenche células não alcançadas pelos raios; o efeito da
  caixa de atrito desmarcada (provavelmente nota 1 em todas as classes).

**Proposta registrada para a 1.4.0 ("atrito fiel ao Vista SAGA"):**

1. Implementar o modelo do Vista SAGA como padrão; manter o atual como "legado 1.3" para
   reproduzir resultados já gerados.
2. **Validação obrigatória:** o autor roda no Vista SAGA um caso pequeno (RS2 com 3 ou 4 classes,
   3 pontos, massas e notas diferentes) e envia o RS2 de saída para comparação pixel a pixel.
   Sem isso, o modelo "fiel" não é conferido e não serve para a tese.
3. Atrito vetorial depois, convertido em grade (o cálculo do Vista SAGA é célula a célula).
4. Registrar a justificativa escrita da mudança de método (exigência do `CLAUDE.md`).

### Formato do arquivo de pontos do Voronoi

Lido no executável do Vista SAGA integrado (não confirmado com arquivo salvo pelo programa):

```
Nome;Massa;X:Y
Nome;Massa;X:Y
[ATRITOS]
nota da classe 0
nota da classe 1
```

- sem cabeçalho e sem aspas; separador `;`; massa inteira (`StrToInt`);
- coordenada `X:Y`, aparentemente **coluna:linha da matriz**, não metros, apesar do rótulo
  "Coordenada UTM"; não se sabe se começa em 0 ou em 1;
- provável CP1252 e CRLF; separador decimal das notas não verificado.

O arquivo de pontos de exemplo do autor (formato do ancestral: cabeçalho, aspas, sete colunas)
mostrou uma grade implícita de células de 700 m, com a relação exata Leste = origem + 700 × X e
Norte = origem − 700 × Y. Datum e fuso não podem ser deduzidos das coordenadas (regra de SRC do
`CLAUDE.md`): o autor precisa confirmá-los.

### Pendências abertas

- [x] 1.3.0 fechada em 17/11/2026 e PR 12 mesclado a pedido do autor. Tag `v1.3.0` pendente:
      usar o commit de merge do PR 12 na `main` (o autor cria pelo Codespaces).
- [x] Caso de teste gerado e enviado (17/11).
- [ ] Autor roda o caso de teste no Vista SAGA e envia R1–R4 e `pontos_salvo.txt`.
- [ ] Autor responde: o Vista SAGA que usa tem a escolha entre M/(d + a) e M/(d × a)?
- [ ] Autor responde: faixa de valores de atrito usada (há notas 0?).
- [ ] Conversão do arquivo de pontos do autor para o formato do Vista SAGA integrado: interrompida
      pelo bloqueio; o autor precisa reenviar o arquivo.
- [ ] Decidir se o plugin deve ler e gravar o formato de pontos do Vista SAGA (útil para a
      validação cruzada).
- [ ] Definir por escrito o critério de "plugin finalizado" (escopo fechado), proposto pelo
      orientador em 17/11.
