#!/usr/bin/env python3
"""Build the timesheet template and its print layout from the company Excel record.

Usage:
    python3 tools/build_template.py "<company timesheet workbook>.xlsx" "<sheet name>"

Writes:
    templates/form.xlsx                   one clean sheet, logo and letterhead kept, data cells blank
    templates/form.layout.json            column widths, row heights, borders, fixed texts, logo and
                                          letterhead positions, used by the app to draw the PDF
    templates/logo.jpeg                   the logo image from the sheet

The app fills the template cell by cell (Excel output) and draws the PDF from the layout, so both
outputs follow the same sheet. Run this again if the company changes the Excel form.
"""
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import openpyxl
from openpyxl.utils import get_column_letter

if len(sys.argv) < 3:
    raise SystemExit(__doc__)
SRC = Path(sys.argv[1])
SHEET = sys.argv[2]
OUT = Path(__file__).resolve().parent.parent / "templates"
OUT.mkdir(exist_ok=True)

MAX_COL, MAX_ROW = 37, 41  # A..AK, rows 1..41 (the print area)
EMU_PT = 12700.0
MDW = 7  # max digit width of Arial 10 (workbook default font) in px

# Cells the app writes. They are blanked in the template and left out of the fixed texts.
DYNAMIC = {"A12", "A15", "O15", "V15", "AD15", "AJ15"}
for r in range(25, 41):
    for c in range(23, 38):
        DYNAMIC.add(f"{get_column_letter(c)}{r}")
for r in range(16, 23):
    for c in range(2, 38):
        if r == 16 and c < 5:
            continue  # NO / Stage Code / Time Code / 0 headings stay fixed
        if r >= 17 and c == 3:
            continue  # time codes 1..5 stay fixed
        if r == 16 and c >= 36:
            continue  # Total Hour / Remarks headings stay fixed
        DYNAMIC.add(f"{get_column_letter(c)}{r}")


def col_px(width):
    return int(width * MDW + 0.5)


# ---------------------------------------------------------------- layout (openpyxl, resolved styles)
wb = openpyxl.load_workbook(SRC)
ws = wb[SHEET]
default_w = ws.sheet_format.defaultColWidth or 8.43
default_h = ws.sheet_format.defaultRowHeight or 12.75

# column widths: <cols> ranges are not always expanded by openpyxl, so read them from the XML too
z = zipfile.ZipFile(SRC)
wbxml = z.read("xl/workbook.xml").decode()
rels = z.read("xl/_rels/workbook.xml.rels").decode()
rid = re.search(r'<sheet name="%s" sheetId="\d+" r:id="(rId\d+)"' % re.escape(SHEET), wbxml).group(1)
sheet_path = "xl/" + re.search(r'Id="%s" [^>]*Target="([^"]+)"' % rid, rels).group(1)
if not re.search(r'Id="%s"' % rid, rels):
    raise SystemExit("sheet relation not found")
sxml = z.read(sheet_path).decode()
widths = [default_w] * (MAX_COL + 1)
for m in re.finditer(r'<col min="(\d+)" max="(\d+)" width="([\d.]+)"', sxml):
    a, b, w = int(m.group(1)), int(m.group(2)), float(m.group(3))
    for c in range(a, min(b, MAX_COL) + 1):
        widths[c] = w
cols_pt = [col_px(widths[c]) * 0.75 for c in range(1, MAX_COL + 1)]
rows_pt = []
for r in range(1, MAX_ROW + 1):
    h = ws.row_dimensions[r].height if r in ws.row_dimensions else None
    rows_pt.append(float(h) if h else float(default_h))

xs = [0.0]
for w in cols_pt:
    xs.append(xs[-1] + w)
ys = [0.0]
for h in rows_pt:
    ys.append(ys[-1] + h)

segs = set()
texts = []


def rgb(color):
    if color is None:
        return "000000"
    if color.type == "rgb" and color.rgb and isinstance(color.rgb, str):
        return color.rgb[-6:]
    return "000000"


for r in range(1, MAX_ROW + 1):
    for c in range(1, MAX_COL + 1):
        cell = ws.cell(r, c)
        b = cell.border
        x0, x1, y0, y1 = xs[c - 1], xs[c], ys[r - 1], ys[r]
        if b.left and b.left.style:
            segs.add((x0, y0, x0, y1))
        if b.right and b.right.style:
            segs.add((x1, y0, x1, y1))
        if b.top and b.top.style:
            segs.add((x0, y0, x1, y0))
        if b.bottom and b.bottom.style:
            segs.add((x0, y1, x1, y1))
        if cell.value is None or cell.coordinate in DYNAMIC:
            continue
        v = cell.value
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        f, al = cell.font, cell.alignment
        texts.append({
            "c": cell.coordinate, "t": str(v), "num": isinstance(v, (int, float)),
            "sz": float(f.sz or 10), "b": bool(f.b), "u": bool(f.u), "color": rgb(f.color),
            "h": al.horizontal or "general", "v": al.vertical or "bottom",
            "wrap": bool(al.wrap_text), "rot": int(al.text_rotation or 0),
        })

# merge collinear segments to keep the PDF small
def merge(segments):
    hor, ver = {}, {}
    for x1, y1, x2, y2 in segments:
        if y1 == y2:
            hor.setdefault(round(y1, 3), []).append((x1, x2))
        else:
            ver.setdefault(round(x1, 3), []).append((y1, y2))
    out = []
    for y, spans in hor.items():
        spans.sort()
        a, b = spans[0]
        for s, e in spans[1:]:
            if s <= b + 0.01:
                b = max(b, e)
            else:
                out.append([round(a, 2), y, round(b, 2), y]); a, b = s, e
        out.append([round(a, 2), y, round(b, 2), y])
    for x, spans in ver.items():
        spans.sort()
        a, b = spans[0]
        for s, e in spans[1:]:
            if s <= b + 0.01:
                b = max(b, e)
            else:
                out.append([x, round(a, 2), x, round(b, 2)]); a, b = s, e
        out.append([x, round(a, 2), x, round(b, 2)])
    return out


# drawing: picture + text box
srels = z.read(sheet_path.replace("worksheets/", "worksheets/_rels/") + ".rels").decode()
drawing_path = "xl/" + re.search(r'Type="[^"]+/drawing" Target="\.\./([^"]+)"', srels).group(1)
dxml = z.read(drawing_path).decode()
drels = z.read(drawing_path.replace("drawings/", "drawings/_rels/") + ".rels").decode()
image_path = "xl/" + re.search(r'Target="\.\./([^"]+)"', drels).group(1)


def anchor_pt(block, tag):
    m = re.search(r"<xdr:%s><xdr:col>(\d+)</xdr:col><xdr:colOff>(\d+)</xdr:colOff><xdr:row>(\d+)</xdr:row><xdr:rowOff>(\d+)</xdr:rowOff></xdr:%s>" % (tag, tag), block)
    c, co, r, ro = (int(g) for g in m.groups())
    return xs[c] + co / EMU_PT, ys[r] + ro / EMU_PT


images, shapes = [], []
for block in re.findall(r"<xdr:twoCellAnchor.*?</xdr:twoCellAnchor>", dxml, re.S):
    (x0, y0), (x1, y1) = anchor_pt(block, "from"), anchor_pt(block, "to")
    box = {"x": round(x0, 2), "y": round(y0, 2), "w": round(x1 - x0, 2), "h": round(y1 - y0, 2)}
    if "<xdr:pic>" in block:
        images.append(dict(box, src="templates/logo.jpeg"))
    elif "<xdr:sp" in block:
        paras = []
        for p in re.findall(r"<a:p>(.*?)</a:p>", block, re.S):
            runs = []
            for rr in re.findall(r"<a:r>(.*?)</a:r>", p, re.S):
                t = re.search(r"<a:t>(.*?)</a:t>", rr, re.S)
                sz = re.search(r' sz="(\d+)"', rr)
                col = re.search(r'srgbClr val="(\w+)"', rr)
                bold = re.search(r' b="1"', rr)
                runs.append({"t": t.group(1) if t else "", "sz": int(sz.group(1)) / 100 if sz else 10,
                             "b": bool(bold), "color": col.group(1) if col else "000000"})
            paras.append(runs)
        ins = {k: int(v) / EMU_PT for k, v in re.findall(r'(lIns|tIns|rIns|bIns)="(\d+)"', block)}
        shapes.append(dict(box, paras=paras, inset=[round(ins.get("lIns", 91440 / EMU_PT), 2), round(ins.get("tIns", 45720 / EMU_PT), 2)]))

ps, pm = ws.page_setup, ws.page_margins
layout = {
    "source": "company timesheet form",
    "cols": [round(w, 2) for w in cols_pt],
    "rows": [round(h, 2) for h in rows_pt],
    "merged": [str(m) for m in ws.merged_cells.ranges],
    "page": {"paper": "A4", "orientation": ps.orientation or "landscape", "scale": (ps.scale or 100) / 100,
             "margins": {"l": pm.left * 72, "r": pm.right * 72, "t": pm.top * 72, "b": pm.bottom * 72},
             "hCenter": bool(ws.print_options.horizontalCentered)},
    "lines": merge(segs),
    "texts": texts,
    "images": images,
    "shapes": shapes,
}
(OUT / "form.layout.json").write_text(json.dumps(layout, indent=1))
(OUT / "logo.jpeg").write_bytes(z.read(image_path))

# ---------------------------------------------------------------- template xlsx (raw XML, keeps the drawing)
sst = re.findall(r"<si>(.*?)</si>", z.read("xl/sharedStrings.xml").decode(), re.S)


def inline(si_body):
    return "<is>%s</is>" % si_body


def cell_ref(tag):
    return re.search(r'r="([A-Z]+\d+)"', tag).group(1)


def rewrite_cell(m):
    full = m.group(0)
    ref = cell_ref(full)
    s = re.search(r' s="(\d+)"', full)
    s_attr = f' s="{s.group(1)}"' if s else ""
    if ref in DYNAMIC:
        return f'<c r="{ref}"{s_attr}/>'
    if ' t="s"' in full:
        idx = int(re.search(r"<v>(\d+)</v>", full).group(1))
        return f'<c r="{ref}"{s_attr} t="inlineStr">{inline(sst[idx])}</c>'
    return full


sheet = re.sub(r'<c r="[A-Z]+\d+"[^>]*?(?:/>|>.*?</c>)', rewrite_cell, sxml, flags=re.S)
sheet = re.sub(r' tabSelected="1"', "", sheet)
sheet = re.sub(r'<selection [^>]*/>', '<selection activeCell="A1" sqref="A1"/>', sheet)
sheet = re.sub(r'<pageSetup ([^>]*?) r:id="rId\d+"', r"<pageSetup \1", sheet)
sheet = re.sub(r'horizontalDpi="\d+" ?', "", sheet)
sheet = re.sub(r'<drawing r:id="rId\d+"/>', '<drawing r:id="rId1"/>', sheet)
sheet = sheet.replace('view="pageBreakPreview" ', "")

# two extra cell formats for the name block under the employee signature (black, centred, no border)
styles = z.read("xl/styles.xml").decode()
m = re.search(r'<cellXfs count="(\d+)">(.*?)</cellXfs>', styles, re.S)
n = int(m.group(1))
fonts_m = re.search(r'<fonts count="(\d+)"([^>]*)>(.*?)</fonts>', styles, re.S)
nf = int(fonts_m.group(1))
new_fonts = ('<font><b/><sz val="9"/><name val="Arial"/><family val="2"/></font>'
             '<font><sz val="9"/><name val="Arial"/><family val="2"/></font>')
styles = styles.replace(fonts_m.group(0), f'<fonts count="{nf + 2}"{fonts_m.group(2)}>{fonts_m.group(3)}{new_fonts}</fonts>')
m = re.search(r'<cellXfs count="(\d+)">(.*?)</cellXfs>', styles, re.S)
xfs = (f'<xf numFmtId="0" fontId="{nf}" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment horizontal="center"/></xf>'
       f'<xf numFmtId="0" fontId="{nf + 1}" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment horizontal="center"/></xf>'
       f'<xf numFmtId="0" fontId="{nf}" fillId="0" borderId="0" xfId="0" applyFont="1"/>')
styles = styles.replace(m.group(0), f'<cellXfs count="{n + 3}">{m.group(2)}{xfs}</cellXfs>')
STYLE_NAME_BOLD, STYLE_NAME, STYLE_SIGN_BOLD = n, n + 1, n + 2

content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="jpeg" ContentType="image/jpeg"/><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/><Override PartName="/xl/drawings/drawing1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>"""
root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>"""
workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><workbookPr defaultThemeVersion="124226"/><bookViews><workbookView xWindow="0" yWindow="0" windowWidth="25000" windowHeight="13000"/></bookViews><sheets><sheet name="Timesheet" sheetId="1" r:id="rId1"/></sheets><definedNames><definedName name="_xlnm.Print_Area" localSheetId="0">'Timesheet'!$A$1:$AK$41</definedName></definedNames><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>"""
wb_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>"""
sheet_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>"""
drawing_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image1.jpeg"/></Relationships>"""
core = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>Time Sheet</dc:title><dc:creator>Timesheet</dc:creator></cp:coreProperties>"""
app = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Microsoft Excel</Application></Properties>"""

drawing = re.sub(r'r:embed="rId\d+"', 'r:embed="rId1"', dxml)
with zipfile.ZipFile(OUT / "form.xlsx", "w", zipfile.ZIP_DEFLATED) as o:
    o.writestr("[Content_Types].xml", content_types)
    o.writestr("_rels/.rels", root_rels)
    o.writestr("docProps/core.xml", core)
    o.writestr("docProps/app.xml", app)
    o.writestr("xl/workbook.xml", workbook)
    o.writestr("xl/_rels/workbook.xml.rels", wb_rels)
    o.writestr("xl/styles.xml", styles)
    o.writestr("xl/theme/theme1.xml", z.read("xl/theme/theme1.xml"))
    o.writestr("xl/worksheets/sheet1.xml", sheet)
    o.writestr("xl/worksheets/_rels/sheet1.xml.rels", sheet_rels)
    o.writestr("xl/drawings/drawing1.xml", drawing)
    o.writestr("xl/drawings/_rels/drawing1.xml.rels", drawing_rels)
    o.writestr("xl/media/image1.jpeg", z.read(image_path))

# style ids the app needs, read from the source sheet so they follow the form
def style_of(ref):
    mm = re.search(r'<c r="%s" s="(\d+)"' % ref, sxml)
    return int(mm.group(1)) if mm else 0

ids = {
    "nameBold": STYLE_NAME_BOLD, "name": STYLE_NAME, "signBold": STYLE_SIGN_BOLD,
    "title": style_of("A12"), "label": style_of("A15"), "value": style_of("O15"),
    "month": style_of("AD15"), "year": style_of("AJ15"),
    "dayHead": style_of("E16"), "dayHeadBold": style_of("J16") if style_of("J16") != style_of("E16") else style_of("E16"),
    "stage": style_of("B17"), "num": style_of("E17"), "code": style_of("J17"),
    "remark": style_of("AK18"), "sign": style_of("Z28"),
}
layout["styles"] = ids
(OUT / "form.layout.json").write_text(json.dumps(layout, indent=1))
print("ok", ids, len(layout["lines"]), "lines", len(texts), "texts")
