// Renders report_spec.json into CCA1_Report_FirstAid_Assistant.docx (US Letter, single column).
// Each figure is 4.2 in tall: with its caption it takes half of the text area, two per page.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, BorderStyle, LevelFormat, Footer, PageNumber,
} = require("docx");

const spec = JSON.parse(fs.readFileSync(path.join(__dirname, "report_spec.json"), "utf8"));
const FIG_H_IN = 4.2;
const MAX_W_IN = 6.5;
const NAVY = "1F3864";

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const cellBorders = { top: border, bottom: border, left: border, right: border };

function table(block) {
  const total = block.widths.reduce((a, b) => a + b, 0);
  const size = block.small ? 17 : 19;
  const mkCell = (text, i, header) =>
    new TableCell({
      width: { size: block.widths[i], type: WidthType.DXA },
      borders: cellBorders,
      shading: header ? { type: ShadingType.CLEAR, color: "auto", fill: "E7EBF2" } : undefined,
      margins: { top: 50, bottom: 50, left: 90, right: 90 },
      children: [new Paragraph({ children: [new TextRun({ text, bold: header, size, font: "Calibri" })] })],
    });
  const rows = [new TableRow({ tableHeader: true, children: block.header.map((t, i) => mkCell(t, i, true)) })]
    .concat(block.rows.map((r) => new TableRow({ cantSplit: true, children: r.map((t, i) => mkCell(t, i, false)) })));
  const out = [new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: block.widths, rows })];
  if (block.caption) out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 200 }, children: [new TextRun({ text: block.caption, italics: true, size: 19 })] }));
  else out.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
  return out;
}

const children = [];
for (const b of spec) {
  if (b.type === "title") {
    children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text: b.text, bold: true, size: 36, color: NAVY })] }));
  } else if (b.type === "subtitle") {
    children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: b.text, size: 20, color: "595959" })] }));
  } else if (b.type === "h") {
    const lvl = { 1: HeadingLevel.HEADING_1, 2: HeadingLevel.HEADING_2, 3: HeadingLevel.HEADING_3 }[b.level];
    children.push(new Paragraph({ heading: lvl, keepNext: true, children: [new TextRun(b.level === 1 ? b.text.toUpperCase() : b.text)] }));
  } else if (b.type === "p") {
    const runs = [];
    if (b.lead) runs.push(new TextRun({ text: b.lead + " ", bold: true }));
    runs.push(new TextRun(b.text));
    children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 120 }, children: runs }));
  } else if (b.type === "notes") {
    const shade = { type: ShadingType.CLEAR, color: "auto", fill: "FFF4CC" };
    const left = { left: { style: BorderStyle.SINGLE, size: 18, color: "C9A227", space: 6 } };
    children.push(new Paragraph({ shading: shade, border: left, keepNext: true, spacing: { before: 80, after: 0 },
      children: [new TextRun({ text: "Write in your own words: ", bold: true, size: 19, color: "7A5C00" }), new TextRun({ text: b.title, bold: true, size: 19 })] }));
    b.items.forEach((it, i) => {
      children.push(new Paragraph({ shading: shade, border: left, numbering: { reference: "notes", level: 0 },
        spacing: { after: i === b.items.length - 1 ? 160 : 0 }, keepNext: i < b.items.length - 1,
        children: [new TextRun({ text: it, size: 19 })] }));
    });
  } else if (b.type === "figure") {
    const { w, h, data } = pngSize(b.path);
    let hIn = FIG_H_IN;
    let wIn = (hIn * w) / h;
    if (wIn > MAX_W_IN) { wIn = MAX_W_IN; hIn = (wIn * h) / w; }
    children.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 40 },
      children: [new ImageRun({ type: "png", data, transformation: { width: Math.round(wIn * 96), height: Math.round(hIn * 96) },
        altText: { title: b.caption, description: b.caption, name: path.basename(b.path) } })] }));
    children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
      children: [new TextRun({ text: b.caption, bold: true, size: 19 })] }));
  } else if (b.type === "table") {
    children.push(...table(b));
  } else if (b.type === "ref") {
    children.push(new Paragraph({ indent: { left: 720, hanging: 720 }, spacing: { after: 100 }, children: [new TextRun({ text: b.text, size: 20 })] }));
  }
}

const doc = new Document({
  creator: "CCNLP team",
  title: "CCA1 Report: Multilingual First Aid Assistant",
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: NAVY, font: "Calibri" }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: NAVY, font: "Calibri" }, paragraph: { spacing: { before: 220, after: 100 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, italics: true, color: "404040", font: "Calibri" }, paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [{ reference: "notes", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 460, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, bottom: 1080, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "7F7F7F" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "CCA1_Report_FirstAid_Assistant.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out);
});
