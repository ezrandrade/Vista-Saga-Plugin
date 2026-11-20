// Gera o DOCX do manual a partir da especificação JSON de build_manual.py.
// Uso: node docs/manual/build_docx.js spec.json saida.docx
const fs = require('fs');
const {
  AlignmentType, BorderStyle, Document, Footer, Header, HeadingLevel, ImageRun, LevelFormat, LineRuleType, Packer,
  LeaderType, TabStopType,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow, TextRun,
  VerticalAlign, WidthType,
} = require('docx');

const spec = JSON.parse(fs.readFileSync(process.argv[2], 'utf-8'));
const UI = spec.ui;
const FONT = 'Calibri';
const BRAND = '1F5F8B';
const INK = '1B1B1B';
const INK2 = '52514E';
const PAGE_W = 11906, MARGIN = 1134;           // A4, margens de 2 cm
const CONTENT = PAGE_W - 2 * MARGIN;           // 9638 DXA
const COLORS = {
  tip: { fill: 'EAF2FA', border: '2A78D6' },
  warning: { fill: 'FFF4E0', border: 'EDA100' },
  hidden: { fill: 'E8F6EF', border: '1BAF7A' },
};

// **negrito** -> TextRuns
function runs(text, opts = {}) {
  const parts = String(text).split(/(\*\*[^*]+\*\*)/g).filter((s) => s.length);
  return parts.map((part) => {
    const bold = part.startsWith('**') && part.endsWith('**');
    return new TextRun({ text: bold ? part.slice(2, -2) : part, bold: bold || opts.bold, font: FONT,
      size: opts.size || 21, color: opts.color || INK, italics: opts.italics });
  });
}

const numberingConfigs = [{
  reference: 'bullets',
  levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 540, hanging: 280 } } } }],
}];
let stepLists = 0;
function newSteps() {
  stepLists += 1;
  const reference = `steps${stepLists}`;
  numberingConfigs.push({ reference, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.',
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } },
      run: { bold: true, color: BRAND } } }] });
  return reference;
}

let figureCount = 0;
function imageBlock(block) {
  figureCount += 1;
  const widthPx = Math.round(block.width_in * 96);
  const heightPx = Math.round(widthPx * block.ratio);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true,
      spacing: { before: 160, after: 60, line: 240, lineRule: LineRuleType.AUTO },
      children: [new ImageRun({ type: 'png', data: fs.readFileSync(block.path),
        transformation: { width: widthPx, height: heightPx },
        altText: { title: block.caption, description: block.caption, name: `fig${figureCount}` } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 220 },
      children: runs(`${UI.figure} ${figureCount} - ${block.caption}`, { size: 18, color: INK2, italics: true }) }),
  ];
}

const border = { style: BorderStyle.SINGLE, size: 4, color: 'D9D8D3' };
const borders = { top: border, bottom: border, left: border, right: border };

function cell(text, width, opts = {}) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: runs(text, { size: opts.size, bold: opts.bold,
      color: opts.color }) })],
  });
}

function tableBlock(block) {
  const widths = block.widths.map((f) => Math.round(f * CONTENT));
  widths[widths.length - 1] = CONTENT - widths.slice(0, -1).reduce((a, b) => a + b, 0);
  const size = block.small ? 17 : 19;
  const rows = [];
  if (block.header !== false) {
    rows.push(new TableRow({ tableHeader: true, children: block.cols.map((col, i) =>
      cell(col, widths[i], { fill: BRAND, bold: true, color: 'FFFFFF', size })) }));
  }
  let previous = null;
  block.rows.forEach((row, r) => {
    rows.push(new TableRow({ cantSplit: true, children: row.map((value, i) => {
      let text = value;
      if (block.merge_first && i === 0) {        // seção repetida: só na primeira linha do grupo
        text = value === previous ? '' : value;
      }
      return cell(text, widths[i], { size, fill: r % 2 ? 'F6F8FB' : undefined,
        bold: block.merge_first && i === 0, color: block.merge_first && i === 0 ? BRAND : undefined });
    }) }));
    previous = row[0];
  });
  return [new Table({ width: { size: CONTENT, type: WidthType.DXA }, columnWidths: widths, rows }),
    new Paragraph({ spacing: { after: 120 }, children: [] })];
}

function calloutBlock(block) {
  const color = COLORS[block.kind] || COLORS.tip;
  const children = [new Paragraph({ spacing: { after: 80 }, children: runs(block.title, { bold: true,
    color: color.border === 'EDA100' ? '8A5A00' : color.border === '1BAF7A' ? '0E6B47' : BRAND, size: 22 }) })];
  if (block.text) children.push(new Paragraph({ children: runs(block.text) }));
  (block.items || []).forEach((item) => children.push(new Paragraph({ numbering: { reference: 'bullets', level: 0 },
    spacing: { after: 60 }, children: runs(item) })));
  const side = { style: BorderStyle.SINGLE, size: 4, color: color.fill };
  return [new Table({ width: { size: CONTENT, type: WidthType.DXA }, columnWidths: [CONTENT],
    rows: [new TableRow({ cantSplit: false, children: [new TableCell({
      width: { size: CONTENT, type: WidthType.DXA },
      shading: { fill: color.fill, type: ShadingType.CLEAR, color: 'auto' },
      borders: { top: side, bottom: side, right: side,
        left: { style: BorderStyle.SINGLE, size: 24, color: color.border } },
      margins: { top: 140, bottom: 140, left: 220, right: 200 }, children })] })] }),
  new Paragraph({ spacing: { after: 160 }, children: [] })];
}

function coverBlock(block) {
  const out = [new Paragraph({ spacing: { before: 1400 }, children: [] })];
  if (fs.existsSync(block.logo)) {
    out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { line: 240, lineRule: LineRuleType.AUTO },
      children: [new ImageRun({ type: 'png',
      data: fs.readFileSync(block.logo), transformation: { width: 190, height: 190 },
      altText: { title: 'Vista Saga Plugin', description: 'Vista Saga Plugin', name: 'logo' } })] }));
  }
  out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 480, after: 120 },
    children: [new TextRun({ text: block.title, font: FONT, size: 64, bold: true, color: BRAND })] }));
  out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [new TextRun({ text: block.subtitle, font: FONT, size: 34, color: INK })] }));
  out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1600 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: BRAND, space: 12 } },
    children: [new TextRun({ text: block.tagline, font: FONT, size: 24, italics: true, color: INK2 })] }));
  out.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: block.author,
    font: FONT, size: 22, color: INK })] }));
  out.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: block.date,
    font: FONT, size: 22, color: INK2 })] }));
  out.push(new Paragraph({ children: [new PageBreak()] }));
  return out;
}

const body = [];
spec.blocks.forEach((block) => {
  switch (block.type) {
    case 'cover': body.push(...coverBlock(block)); break;
    case 'toc':
      // Sumário estático com as páginas reais (calculadas em duas passadas por build_manual.py): aparece igual
      // no Word, no LibreOffice e no Google Docs, sem depender de atualizar campos.
      body.push(new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun({ text: block.title })] }));
      (block.entries || []).forEach((entry) => body.push(new Paragraph({
        spacing: { before: entry.level === 1 ? 140 : 20, after: 20 },
        indent: { left: entry.level === 1 ? 0 : 360 },
        // Tabulação direita comum com pontilhado (o LibreOffice não desenha a tabulação posicional).
        tabStops: [{ type: TabStopType.RIGHT, position: CONTENT, leader: LeaderType.DOT }],
        children: [
          new TextRun({ text: entry.text, font: FONT, size: entry.level === 1 ? 22 : 20, bold: entry.level === 1,
            color: entry.level === 1 ? BRAND : INK }),
          new TextRun({ text: `\t${entry.page}`, font: FONT, size: entry.level === 1 ? 22 : 20,
            bold: entry.level === 1, color: INK2 }),
        ] })));
      break;
    case 'pagebreak': body.push(new Paragraph({ children: [new PageBreak()] })); break;
    case 'h1': body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(block.text)] })); break;
    case 'h2': body.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(block.text)] })); break;
    case 'h3': body.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(block.text)] })); break;
    case 'p': body.push(new Paragraph({ spacing: { after: 140 }, children: runs(block.text) })); break;
    case 'bullets':
      block.items.forEach((item) => body.push(new Paragraph({ numbering: { reference: 'bullets', level: 0 },
        spacing: { after: 80 }, children: runs(item) })));
      body.push(new Paragraph({ spacing: { after: 60 }, children: [] }));
      break;
    case 'steps': {
      const reference = newSteps();
      block.items.forEach((item) => body.push(new Paragraph({ numbering: { reference, level: 0 },
        spacing: { after: 100 }, children: runs(item) })));
      body.push(new Paragraph({ spacing: { after: 60 }, children: [] }));
      break;
    }
    case 'image': body.push(...imageBlock(block)); break;
    case 'table': body.push(...tableBlock(block)); break;
    case 'callout': body.push(...calloutBlock(block)); break;
    default: break;
  }
});

const doc = new Document({
  creator: 'Vista Saga Plugin', title: `${UI.doc_title} - ${UI.subtitle}`, description: UI.tagline,
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 21, color: INK }, paragraph: { spacing: { line: 288, lineRule: LineRuleType.AUTO } } } },
    paragraphStyles: [
      { id: 'Title', name: 'Title', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: 40, bold: true, color: BRAND },
        paragraph: { spacing: { before: 0, after: 240 }, keepNext: true } },
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: 38, bold: true, color: BRAND },
        paragraph: { spacing: { before: 120, after: 220 }, keepNext: true, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND, space: 6 } } } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: BRAND },
        paragraph: { spacing: { before: 300, after: 120 }, keepNext: true, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: 23, bold: true, color: INK },
        paragraph: { spacing: { before: 220, after: 100 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: { config: numberingConfigs },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 },
      margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN, header: 560, footer: 560 } },
      titlePage: true },
    headers: {
      default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: UI.subtitle, font: FONT, size: 16, color: INK2 })] })] }),
      first: new Header({ children: [new Paragraph({ children: [] })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: 'D9D8D3', space: 6 } },
        children: [new TextRun({ text: `${UI.footer}  |  ${UI.page} `, font: FONT, size: 16, color: INK2 }),
          new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: INK2 })] })] }),
      first: new Footer({ children: [new Paragraph({ children: [] })] }),
    },
    children: body,
  }],
});

Packer.toBuffer(doc).then((buffer) => fs.writeFileSync(process.argv[3], buffer));
