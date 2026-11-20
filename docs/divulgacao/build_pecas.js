// Peças visuais da divulgação do Vista Saga Plugin 1.6.1 (pt-BR), renderizadas pelo Chromium (Playwright).
// Uso, na raiz do repositório:  node docs/divulgacao/build_pecas.js <pasta_de_saida>
// Saída: carrossel/01..10.png (1080x1350), post_lancamento.png (1080x1080), capa_link.png (1200x627) e
// video/cena_NN.png (1080x1920, cenas do vídeo vertical montado por montar_video.sh).
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
const IMG = path.join(ROOT, 'docs', 'divulgacao', 'imagens');
const ICONS = path.join(ROOT, 'geosaga', 'icons', 'modulos');
const LOGO = path.join(ROOT, 'docs', 'assets', 'vista-saga-mark.png');
const OUT = path.resolve(process.argv[2] || path.join(ROOT, 'dist', 'divulgacao'));
const url = (p) => 'file://' + p;

const MODULES = [
  ['assinatura_espacial', 'Assinatura'], ['monitoria_espacial', 'Monitoria'], ['avaliacao_espacial', 'Avaliação'],
  ['analises_voronoi', 'Análises Voronoi'], ['combinacao_mapas', 'Combinação de Mapas'],
  ['conversor', 'Conversor de Formatos'], ['sequenciador_mapas', 'Sequenciador de Mapas'],
];
const icon = (key) => url(path.join(ICONS, `${key}.svg`));

const CSS = `
:root{--navy:#0B2540;--navy2:#123B63;--blue:#2F7FD1;--brand:#1F5F8B;--green:#3DBE8B;--peach:#F6A97C;
--ink:#0F1E2E;--ink2:#4A5B6C;--paper:#F4F7FA;--line:#DCE4EC}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;color:var(--ink);-webkit-font-smoothing:antialiased;overflow:hidden}
.dark{background:radial-gradient(120% 90% at 85% 0%,#1B4F80 0%,var(--navy2) 38%,var(--navy) 100%);color:#fff}
.light{background:var(--paper)}
.kicker{font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:26px}
.chip{display:inline-flex;align-items:center;gap:10px;padding:12px 20px;border-radius:999px;font-weight:600;font-size:23px}
.brandline{display:flex;align-items:center;gap:18px}
.brandline img{width:64px;height:64px}
.brandline span{font-weight:800;font-size:30px;letter-spacing:-.01em}
.pager{font-weight:600;font-size:24px;opacity:.7}
`;

function page(w, h, cls, body) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>${CSS}
  body{width:${w}px;height:${h}px}</style></head><body class="${cls}">${body}</body></html>`;
}

function footer(n, dark) {
  const color = dark ? 'rgba(255,255,255,.75)' : 'var(--ink2)';
  return `<div style="position:absolute;left:72px;right:72px;bottom:56px;display:flex;justify-content:space-between;
    align-items:center;color:${color}">
    <div class="brandline"><img src="${url(LOGO)}" style="width:48px;height:48px"><span style="font-size:24px">Vista Saga Plugin</span></div>
    <div class="pager">${n} / 10</div></div>`;
}

function cover() {
  const icons = MODULES.map(([k, n]) => `<div style="display:flex;flex-direction:column;align-items:center;gap:12px;width:120px">
      <div style="width:100px;height:100px;border-radius:26px;background:rgba(255,255,255,.95);display:grid;place-items:center;
      box-shadow:0 10px 30px rgba(0,0,0,.25)"><img src="${icon(k)}" style="width:72px;height:72px"></div>
      <div style="font-size:19px;font-weight:600;text-align:center;line-height:1.2;opacity:.9">${n}</div></div>`).join('');
  return page(1080, 1350, 'dark', `
  <div style="position:absolute;right:-120px;top:-60px;width:620px;height:620px;opacity:.16">
    <img src="${url(LOGO)}" style="width:100%"></div>
  <div style="position:absolute;left:72px;right:72px;top:96px">
    <div class="brandline"><img src="${url(LOGO)}"><span>Vista Saga Plugin</span></div>
    <div class="kicker" style="color:var(--peach);margin-top:120px">Nova versão 1.6.1 · QGIS 4</div>
    <h1 style="font-size:84px;line-height:1.04;font-weight:800;letter-spacing:-.025em;margin-top:28px">
      Análise ambiental no QGIS, com o método do <span style="color:var(--green)">Vista SAGA</span></h1>
    <p style="font-size:34px;line-height:1.4;margin-top:36px;color:rgba(255,255,255,.85);max-width:880px">
      Sete módulos para diagnóstico, monitoramento e planejamento do território. Gratuito e de código aberto.</p>
    <div style="display:flex;gap:12px;margin-top:64px">${icons}</div>
  </div>
  <div style="position:absolute;left:72px;bottom:56px;display:flex;gap:12px">
    <div class="chip" style="background:rgba(255,255,255,.12)">Português · Inglês · Espanhol</div></div>
  <div style="position:absolute;right:72px;bottom:66px" class="pager">1 / 10  →</div>`);
}

function moduleCard(n, key, name, question, text, chips, visual, note) {
  const chipHtml = chips.map((c) => `<div class="chip" style="background:#fff;border:2px solid var(--line);color:var(--brand)">
      <span style="width:12px;height:12px;border-radius:50%;background:var(--green)"></span>${c}</div>`).join('');
  return page(1080, 1350, 'light', `
  <div style="position:absolute;left:0;top:0;right:0;height:14px;background:linear-gradient(90deg,var(--blue),var(--green))"></div>
  <div style="position:absolute;left:72px;right:72px;top:84px">
    <div style="display:flex;align-items:center;gap:24px">
      <div style="width:96px;height:96px;border-radius:26px;background:#fff;display:grid;place-items:center;
        box-shadow:0 8px 24px rgba(15,30,46,.12)"><img src="${icon(key)}" style="width:68px;height:68px"></div>
      <div class="kicker" style="color:var(--brand);font-size:28px">${name}</div></div>
    <h2 style="font-size:66px;line-height:1.08;font-weight:800;letter-spacing:-.02em;margin-top:40px">${question}</h2>
    <p style="font-size:31px;line-height:1.45;color:var(--ink2);margin-top:26px">${text}</p>
  </div>
  <div style="position:absolute;left:56px;right:56px;top:610px;height:440px;border-radius:28px;background:#fff;
    box-shadow:0 18px 50px rgba(15,30,46,.14);display:grid;place-items:center;overflow:hidden;padding:24px">${visual}</div>
  ${note ? `<div style="position:absolute;left:72px;right:72px;top:1066px;font-size:21px;color:var(--ink2);font-style:italic">${note}</div>` : ''}
  <div style="position:absolute;left:72px;right:72px;top:1110px;display:flex;flex-wrap:wrap;gap:12px">${chipHtml}</div>
  ${footer(n, false)}`);
}

const fit = (file) => `<img src="${url(file)}" style="max-width:100%;max-height:100%;object-fit:contain">`;
const frames = () => `<div style="display:flex;gap:18px;align-items:center">${[1, 2, 3].map((i) =>
  `<img src="${url(path.join(IMG, '3_vila_serena', `quadro_00${i}_${['2000', '2010', '2020'][i - 1]}.png`))}"
   style="width:262px;height:262px;border-radius:14px;box-shadow:0 6px 18px rgba(0,0,0,.15)">`).join('<div style="font-size:40px;color:var(--ink2)">›</div>')}</div>`;

function validation() {
  const stat = (big, label, color) => `<div style="padding:28px 40px;border-radius:26px;background:rgba(255,255,255,.08);
      border:1px solid rgba(255,255,255,.14)">
      <div style="font-size:92px;font-weight:800;letter-spacing:-.03em;line-height:1;color:${color}">${big}</div>
      <div style="font-size:28px;line-height:1.35;margin-top:10px;color:rgba(255,255,255,.88)">${label}</div></div>`;
  return page(1080, 1350, 'dark', `
  <div style="position:absolute;left:72px;right:72px;top:96px">
    <div class="kicker" style="color:var(--peach)">Diferencial</div>
    <h2 style="font-size:68px;line-height:1.06;font-weight:800;letter-spacing:-.02em;margin-top:22px">
      Validado contra o Vista SAGA original</h2>
    <p style="font-size:30px;line-height:1.4;margin-top:22px;color:rgba(255,255,255,.8)">
      Comparação célula a célula, com os mesmos dados de entrada, nos casos de teste do projeto.</p>
    <div style="display:flex;flex-direction:column;gap:20px;margin-top:40px">
      ${stat('100%', 'das células iguais nas Análises Voronoi Simples e Com Massa', 'var(--green)')}
      ${stat('99,1–99,7%', 'das células iguais no Voronoi com atrito, com as diferenças concentradas na fronteira entre regiões', '#8CC8FF')}
      ${stat('100%', 'de coincidência na Assinatura do mapa inteiro', 'var(--peach)')}
    </div></div>
  ${footer(9, true)}`);
}

function cta() {
  const badge = (t) => `<div class="chip" style="background:rgba(255,255,255,.12);font-size:27px">${t}</div>`;
  return page(1080, 1350, 'dark', `
  <div style="position:absolute;left:72px;right:72px;top:150px;text-align:center">
    <img src="${url(LOGO)}" style="width:220px;height:220px">
    <h2 style="font-size:80px;font-weight:800;letter-spacing:-.02em;margin-top:30px">Experimente agora</h2>
    <p style="font-size:33px;line-height:1.45;margin-top:22px;color:rgba(255,255,255,.85)">
      Manual, tutorial passo a passo e dados de exemplo no site oficial</p>
    <div style="margin:46px auto 0;display:inline-block;padding:30px 44px;border-radius:24px;background:#fff;color:var(--navy);
      font-size:40px;font-weight:800;letter-spacing:-.01em;box-shadow:0 18px 50px rgba(0,0,0,.3)">vistasagaplugin.wordpress.com</div>
    <p style="font-size:27px;margin-top:34px;color:rgba(255,255,255,.75)">Código-fonte: github.com/ezrandrade/Vista-Saga-Plugin</p>
    <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:14px;margin-top:46px">
      ${badge('Gratuito')}${badge('GPL-3.0')}${badge('QGIS 4')}${badge('PT · EN · ES')}</div>
  </div>
  <div style="position:absolute;left:72px;right:72px;bottom:120px;text-align:center;font-size:21px;color:rgba(255,255,255,.55)">
    Implementação independente, sem vínculo institucional com o Vista SAGA ou a UFRJ.</div>
  ${footer(10, true)}`);
}

function launchPost() {
  const icons = MODULES.map(([k]) => `<div style="width:92px;height:92px;border-radius:24px;background:rgba(255,255,255,.95);
      display:grid;place-items:center"><img src="${icon(k)}" style="width:64px;height:64px"></div>`).join('');
  const item = (t) => `<div style="display:flex;gap:18px;align-items:flex-start;font-size:33px;line-height:1.35">
      <span style="flex:none;width:16px;height:16px;border-radius:50%;background:var(--green);margin-top:14px"></span>${t}</div>`;
  return page(1080, 1080, 'dark', `
  <div style="position:absolute;right:-90px;top:-70px;width:480px;opacity:.14"><img src="${url(LOGO)}" style="width:100%"></div>
  <div style="position:absolute;left:72px;right:72px;top:80px">
    <div class="brandline"><img src="${url(LOGO)}"><span>Vista Saga Plugin</span></div>
    <div class="kicker" style="color:var(--peach);margin-top:70px">Nova versão</div>
    <h1 style="font-size:150px;font-weight:800;letter-spacing:-.04em;line-height:1;margin-top:8px">1.6.1</h1>
    <div style="display:flex;flex-direction:column;gap:18px;margin-top:44px">
      ${item('Dicas em todos os botões e campos dos sete módulos')}
      ${item('Assinatura refeita no modelo do Vista SAGA')}
      ${item('Análises Voronoi validadas célula a célula')}</div>
    <div style="display:flex;gap:14px;margin-top:54px">${icons}</div>
  </div>
  <div style="position:absolute;left:72px;bottom:56px;font-size:28px;font-weight:700;color:rgba(255,255,255,.9)">
    vistasagaplugin.wordpress.com</div>
  <div style="position:absolute;right:72px;bottom:56px;font-size:24px;color:rgba(255,255,255,.65)">Para QGIS 4 · Gratuito</div>`);
}

function linkCover() {
  return page(1200, 627, 'dark', `
  <div style="position:absolute;left:64px;top:70px;width:560px">
    <div class="brandline"><img src="${url(LOGO)}" style="width:56px;height:56px"><span style="font-size:26px">Vista Saga Plugin</span></div>
    <div class="kicker" style="color:var(--peach);font-size:20px;margin-top:46px">Nova versão 1.6.1 · QGIS 4</div>
    <h1 style="font-size:52px;line-height:1.08;font-weight:800;letter-spacing:-.02em;margin-top:16px">
      Análise ambiental no QGIS, com o método do <span style="color:var(--green)">Vista SAGA</span></h1>
    <p style="font-size:23px;line-height:1.4;margin-top:20px;color:rgba(255,255,255,.82)">
      Sete módulos; Voronoi e Assinatura validados contra o programa original. Gratuito e de código aberto.</p>
  </div>
  <img src="${url(path.join(IMG, '1_janelas', '04_analises_voronoi.png'))}" style="position:absolute;right:250px;top:96px;width:330px;
    border-radius:12px;box-shadow:0 20px 50px rgba(0,0,0,.45);transform:rotate(-4deg)">
  <img src="${url(path.join(IMG, '1_janelas', '01_assinatura.png'))}" style="position:absolute;right:36px;top:150px;width:360px;
    border-radius:12px;box-shadow:0 24px 60px rgba(0,0,0,.5);transform:rotate(3deg)">`);
}

// ---- cenas do vídeo vertical (1080x1920) ----
function scene(body, cls = 'dark') { return page(1080, 1920, cls, body); }
const big = (t, size = 96) => `<h1 style="font-size:${size}px;line-height:1.06;font-weight:800;letter-spacing:-.025em">${t}</h1>`;
const SCENES = [
  () => scene(`<div style="position:absolute;left:80px;right:80px;top:640px">
      <div class="kicker" style="color:var(--peach)">Para quem trabalha com território</div>
      <div style="margin-top:30px">${big('Análise ambiental completa, direto no QGIS?', 104)}</div></div>`),
  () => scene(`<div style="position:absolute;left:0;right:0;top:520px;text-align:center">
      <img src="${url(LOGO)}" style="width:360px">
      <div style="margin-top:40px">${big('Vista Saga Plugin', 100)}</div>
      <div class="kicker" style="color:var(--peach);margin-top:28px">Nova versão 1.6.1</div></div>`),
  () => scene(`<div style="position:absolute;left:80px;right:80px;top:300px">
      ${big('Sete módulos, uma só lógica', 88)}
      <div style="display:flex;flex-direction:column;gap:22px;margin-top:70px">${MODULES.map(([k, n]) => `
        <div style="display:flex;align-items:center;gap:30px;padding:18px 24px;border-radius:26px;background:rgba(255,255,255,.08)">
          <div style="width:110px;height:110px;border-radius:28px;background:#fff;display:grid;place-items:center">
          <img src="${icon(k)}" style="width:76px"></div><div style="font-size:46px;font-weight:700">${n}</div></div>`).join('')}</div></div>`),
  ...['2000', '2010', '2020'].map((year, i) => () => scene(`<div style="position:absolute;left:80px;right:80px;top:260px">
      <div class="kicker" style="color:var(--peach)">Sequenciador e Monitoria</div>
      ${big('O que mudou no território?', 84)}
      <img src="${url(path.join(IMG, '3_vila_serena', `quadro_00${i + 1}_${year}.png`))}" style="width:920px;height:920px;margin-top:70px;
        border-radius:30px;box-shadow:0 30px 80px rgba(0,0,0,.45)">
      <div style="font-size:30px;margin-top:34px;color:rgba(255,255,255,.7)">Cidade fictícia de Vila Serena (dados do tutorial)</div></div>`)),
  () => scene(`<div style="position:absolute;left:80px;right:80px;top:470px">
      <div class="kicker" style="color:var(--peach)">Análises Voronoi</div>
      ${big('Quem atende quem, considerando o porte e as barreiras', 80)}
      <div style="margin-top:80px;background:#fff;border-radius:30px;padding:28px">
        <img src="${url(path.join(IMG, '3_vila_serena', 'vila_serena_voronoi.png'))}" style="width:100%"></div>
      <div style="font-size:30px;margin-top:34px;color:rgba(255,255,255,.7)">Simples · Com Massa · Com Atrito (exemplo fictício)</div></div>`),
  () => scene(`<div style="position:absolute;left:80px;right:80px;top:380px">
      <div class="kicker" style="color:var(--peach)">Validação</div>
      ${big('Validado contra o Vista SAGA original', 88)}
      <div style="margin-top:80px;display:flex;flex-direction:column;gap:34px">
        <div><div style="font-size:150px;font-weight:800;color:var(--green);line-height:1">100%</div>
          <div style="font-size:40px;color:rgba(255,255,255,.85)">das células no Voronoi Simples e Com Massa</div></div>
        <div><div style="font-size:150px;font-weight:800;color:#8CC8FF;line-height:1">99,1–99,7%</div>
          <div style="font-size:40px;color:rgba(255,255,255,.85)">no Voronoi com atrito</div></div></div></div>`),
  () => scene(`<div style="position:absolute;left:80px;right:80px;top:300px">
      <div class="kicker" style="color:var(--brand)">Facilidade de uso</div>
      <h1 style="font-size:88px;line-height:1.06;font-weight:800;letter-spacing:-.025em;color:var(--ink)">Uma dica em cada botão</h1>
      <div style="margin-top:60px;background:#fff;border-radius:30px;padding:24px;box-shadow:0 24px 70px rgba(15,30,46,.18)">
        <img src="${url(path.join(IMG, '1_janelas', '03_avaliacao.png'))}" style="width:100%;border-radius:12px"></div>
      <div style="font-size:38px;line-height:1.4;margin-top:50px;color:var(--ink2)">
        [Executar] e [Fechar] em todos os módulos. Relatórios em TXT e CSV. Português, inglês e espanhol.</div></div>`, 'light'),
  () => scene(`<div style="position:absolute;left:80px;right:80px;top:560px;text-align:center">
      <img src="${url(LOGO)}" style="width:260px">
      <div style="margin-top:40px">${big('Gratuito e de código aberto', 90)}</div>
      <div style="margin:60px auto 0;display:inline-block;padding:34px 46px;border-radius:26px;background:#fff;color:var(--navy);
        font-size:52px;font-weight:800">vistasagaplugin.wordpress.com</div>
      <div style="font-size:34px;margin-top:40px;color:rgba(255,255,255,.75)">Manual, tutorial e dados de exemplo</div></div>`),
];

(async () => {
  for (const d of ['carrossel', 'video', 'html']) fs.mkdirSync(path.join(OUT, d), { recursive: true });
  const C = [
    cover(),
    moduleCard(2, 'assinatura_espacial', 'Assinatura', 'De que é feita esta área?',
      'Selecione bairros, bacias ou unidades num mapa de referência e veja quanto ocupa cada classe de uso do solo, solo ou relevo, em vários mapas de uma vez.',
      ['% da área e % da categoria', 'Raster e vetor', 'Relatórios TXT e CSV'],
      fit(path.join(IMG, '2_resultados', '01_assinatura_resultado.png'))),
    moduleCard(3, 'monitoria_espacial', 'Monitoria', 'O que mudou entre duas datas?',
      'Compare dois mapas e obtenha o mapa de transições, a tabela e a matriz de transição, com áreas em hectares.',
      ['Permanências e mudanças', 'Matriz de transição', 'Raster e vetor'],
      fit(path.join(IMG, '3_vila_serena', 'vila_serena_transicoes.png')), 'Exemplo fictício do tutorial: cidade de Vila Serena, 2000 a 2020.'),
    moduleCard(4, 'avaliacao_espacial', 'Avaliação', 'Onde é mais adequado?',
      'Combine mapas com pesos e notas e gere a carta de aptidão, suscetibilidade ou prioridade (análise multicritério).',
      ['Pesos e notas', 'Nenhuma classe sem decisão', 'Projeto reutilizável'],
      fit(path.join(IMG, '3_vila_serena', 'vila_serena_aptidao.png')), 'Exemplo fictício do tutorial: aptidão à expansão urbana de Vila Serena.'),
    moduleCard(5, 'analises_voronoi', 'Análises Voronoi', 'Qual a área de influência de cada ponto?',
      'Delimite áreas de atendimento pela distância, pelo porte (massa) e pela dificuldade de deslocamento (atrito).',
      ['4 modalidades', 'Atrito raster ou poligonal', 'Saída raster ou vetorial'],
      fit(path.join(IMG, '3_vila_serena', 'vila_serena_voronoi.png')), 'Exemplo fictício do tutorial: escolas de Vila Serena e o rio.'),
    moduleCard(6, 'combinacao_mapas', 'Combinação de Mapas', 'Que associações existem e quanto ocupam?',
      'Cruze dois ou mais mapas e receba um código para cada associação de classes, com área e percentual.',
      ['Sem pesos nem notas', 'Tolera lascas abaixo de 1 cm', 'Raster e vetor'],
      fit(path.join(IMG, '2_resultados', '05_combinacao_resultado.png'))),
    moduleCard(7, 'conversor', 'Conversor de Formatos', 'Como aproveitar as bases do Vista SAGA?',
      'Converta entre RS2, GeoTIFF e vetor preservando códigos, nomes e cores das classes.',
      ['6 conversões', 'Vários arquivos em lote', 'SRC registrado'],
      fit(path.join(IMG, '2_resultados', '06_conversor_resultado.png'))),
    moduleCard(8, 'sequenciador_mapas', 'Sequenciador de Mapas', 'Como mostrar a evolução no tempo?',
      'Transforme mapas em ordem num GIF animado, com data e legenda, usando a simbologia que você já definiu no QGIS.',
      ['GIF e PNG', 'Raster, vetor ou misto', 'Modo acumulativo'], frames(), 'Exemplo fictício do tutorial: Vila Serena em 2000, 2010 e 2020.'),
    validation(),
    cta(),
  ];
  const jobs = C.map((html, i) => [`carrossel/${String(i + 1).padStart(2, '0')}.png`, html, 1080, 1350]);
  jobs.push(['post_lancamento.png', launchPost(), 1080, 1080], ['capa_link.png', linkCover(), 1200, 627]);
  SCENES.forEach((s, i) => jobs.push([`video/cena_${String(i + 1).padStart(2, '0')}.png`, s(), 1080, 1920]));
  const browser = await chromium.launch();
  for (const [file, html, w, h] of jobs) {
    const htmlPath = path.join(OUT, 'html', file.replace(/[\/]/g, '_') + '.html');
    fs.writeFileSync(htmlPath, html);
    const p = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto(url(htmlPath));
    await p.waitForLoadState('networkidle');
    await p.screenshot({ path: path.join(OUT, file) });
    await p.close();
  }
  await browser.close();
  console.log(`${jobs.length} peças em ${OUT}`);
})();
