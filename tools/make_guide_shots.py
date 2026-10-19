#!/usr/bin/env python3
"""Make the screenshots for GUIDE.md (guide/*.png) with a sample person and a placeholder letterhead.

    python3 -m http.server 8765 &
    python3 tools/make_guide_shots.py

Nothing real appears in the pictures: the company letterhead, logo and project title are replaced
with placeholders, and the names are made up.
"""
import base64
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "guide"
OUT.mkdir(exist_ok=True)
TMP = Path(tempfile.mkdtemp())
URL = "http://localhost:8765/index.html?p=OTHER"
B64 = "const buf = new Uint8Array(await b.arrayBuffer()); let s=''; for (let i=0;i<buf.length;i+=8192) s += String.fromCharCode(...buf.subarray(i,i+8192)); return btoa(s);"

PLACEHOLDER = """() => {
  LAYOUT.shapes[0].paras[0][0].t = 'COMPANY NAME SDN BHD'; LAYOUT.shapes[0].paras[0][1].t = ' (000000-X)';
  LAYOUT.shapes[0].paras[1][0].t = 'CONSULTING ENGINEERS'; LAYOUT.images = []; delete EMBED.bin['templates/logo.jpeg']; LOGO_DATAURL = ''; logoDataURL = async () => '';
  PK.company = 'COMPANY NAME SDN BHD'; PK.submitTo = 'HQ'; PK.name = 'Sample road upgrading project';
  PK.signLabels = Object.assign({}, PK.signLabels, { verify1: 'VERIFIED BY (RE)' });
  const o = S.over[S.pkg] = S.over[S.pkg] || {};
  o.projectTitle = 'SAMPLE ROAD UPGRADING PROJECT (PACKAGE 1)'; o.signCompany = 'COMPANY NAME S/B';
  save(); render();
}"""


def shot(pg, name, el=None, full=False):
    path = OUT / f"{name}.png"
    if el:
        pg.locator(el).screenshot(path=str(path))
    else:
        pg.screenshot(path=str(path), full_page=full)
    im = Image.open(path)
    if im.width > 720:
        im.thumbnail((720, 4000))
    im.save(path, optimize=True)
    print("guide/" + path.name, im.size)


def save_blob(pg, js, path):
    data = pg.evaluate("async () => { const b = await (async () => {" + js + "})(); " + B64 + " }")
    Path(path).write_bytes(base64.b64decode(data))


def desk_photo(pdf, out_jpg):
    """A phone photo of the printed sheet on a desk: tilted, shaded."""
    subprocess.run(["pdftoppm", "-r", "110", "-png", "-f", "1", "-l", "1", str(pdf), str(TMP / "page")], check=True)
    page = Image.open(next(TMP.glob("page*.png"))).convert("RGB")
    W, H = 1600, 1200
    bg = Image.new("RGB", (W, H), (70, 58, 46))
    d = ImageDraw.Draw(bg)
    for i in range(0, H, 6):
        d.line([(0, i), (W, i + 30)], fill=(76 + i % 9, 62, 50))
    sheet = page.resize((1240, int(1240 * page.height / page.width)))
    sheet = sheet.rotate(6, expand=True, fillcolor=(0, 0, 0))
    mask = Image.new("L", sheet.size, 0)
    mask.paste(255, (0, 0, sheet.width, sheet.height))
    mask = page.resize((1240, int(1240 * page.height / page.width))).convert("L").point(lambda v: 255).rotate(6, expand=True)
    bg.paste(sheet, ((W - sheet.width) // 2, (H - sheet.height) // 2), mask)
    shade = Image.new("L", (W, H))
    for x in range(W):
        ImageDraw.Draw(shade).line([(x, 0), (x, H)], fill=int(60 * x / W))
    bg = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), bg, shade)
    bg.filter(ImageFilter.GaussianBlur(0.6)).save(out_jpg, quality=88)


with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())
    pg.goto(URL)
    pg.wait_for_selector("#w-name")
    pg.evaluate(PLACEHOLDER)
    pg.fill("#w-name", "Ts. Adam Lee Chee Wai")
    pg.fill("#w-status", "Assistant Resident Engineer")
    pg.click('#w-code [data-c="F"]')
    pg.wait_for_timeout(300)
    shot(pg, "01_welcome")
    pg.click("#w-go")
    pg.evaluate("() => { S.ui.y = 2026; S.ui.m = 8; save(); render(); }")
    pg.wait_for_timeout(3500)                     # let the toast go
    shot(pg, "02_new_month")
    pg.click("#btn-fill"); pg.wait_for_timeout(3500)
    shot(pg, "03_filled")
    pg.click("#btn-select")
    pg.click('[data-day="8"]'); pg.click('[data-day="9"]')
    pg.locator("#bulkbar").scroll_into_view_if_needed()
    pg.evaluate("() => window.scrollBy(0, -60)")
    pg.wait_for_timeout(200)
    shot(pg, "04_select_days")
    pg.click('#bulk-codes [data-setsel="AL"]'); pg.click("#bulk-done"); pg.wait_for_timeout(3300)
    pg.click('[data-day="20"]')
    pg.fill("#ot-2", "4"); pg.dispatch_event("#ot-2", "change")
    pg.fill("#day-note", "Concrete pour, Sunday")
    pg.wait_for_timeout(200)
    shot(pg, "05_day")
    pg.click("#sh-day [data-close]")
    pg.evaluate("() => document.querySelector('#h-sum').scrollIntoView({block: 'start'})")
    pg.wait_for_timeout(200)
    shot(pg, "06_summary", el="#h-sum >> xpath=ancestor::section[1]")
    pg.click("#dock-go"); pg.wait_for_timeout(600)
    shot(pg, "07_print")
    pg.evaluate("() => document.querySelector('#sh-out .sheet-b').scrollTop = 520"); pg.wait_for_timeout(200)
    shot(pg, "08_print_actions")
    pg.click("#btn-showqr"); pg.wait_for_timeout(400)
    shot(pg, "09_show_qr")
    pg.click("#sh-gen [data-close]")
    # a printable PDF for the desk photo
    save_blob(pg, "return await makePDF([sheetFor(2026, 8)], 't');", TMP / "sheet.pdf")
    pg.click("#sh-out [data-close]")
    desk_photo(TMP / "sheet.pdf", TMP / "desk.jpg")
    # scan the signed copy (no camera here, so the phone's camera app path is used)
    pg.evaluate("() => document.querySelector('#h-sign').scrollIntoView({block: 'start'})")
    pg.wait_for_timeout(200)
    with pg.expect_file_chooser() as fc:
        pg.click("#btn-scan-signed")
    fc.value.set_files(str(TMP / "desk.jpg"))
    pg.wait_for_timeout(1500)
    shot(pg, "10_scan_corners")
    pg.click("#sc-next"); pg.wait_for_timeout(2500)
    shot(pg, "11_scan_clean")
    pg.click("#sc-keep"); pg.wait_for_timeout(2500)
    pg.evaluate("() => document.querySelector('#h-sign').scrollIntoView({block: 'start'})")
    pg.wait_for_timeout(3400)
    shot(pg, "12_signed_copy", el="#h-sign >> xpath=ancestor::section[1]")
    pg.click("#btn-records"); pg.wait_for_timeout(600)
    shot(pg, "13_records")
    pg.click("#sh-rec [data-close]")
    pg.click("#btn-setup"); pg.wait_for_timeout(400)
    shot(pg, "14_setup")
    pg.click("#sh-gen [data-close]")

    # ---- compiler
    pg.evaluate("""() => {
        S.role = 'compiler'; save();
        team = []; addTeamRecord(dataRecord());
        const add = (n, st, ot) => { const d = dataRecord(); d.profile.name = n; d.profile.status = st; if (ot) d.md.rows[2].v[20] = ot; addTeamRecord(d); };
        add('Nurul Aina binti Hassan', 'Inspector of Works', '3'); add('Mohd Hafiz bin Kassim', 'Site Engineer');
        saveTeam(); render();
    }""")
    pg.wait_for_timeout(300)
    pg.click("#btn-hq"); pg.wait_for_timeout(400)
    shot(pg, "15_hq")
    pg.click("#hub-team"); pg.wait_for_timeout(500)
    shot(pg, "16_team")
    # photocopier scan of the signed stack
    save_blob(pg, """
        const blob = await makePDF(team.map(teamSheet), 'All'); await loadPdfJs(); await loadPdfLib();
        const pdf = await pdfjsLib.getDocument({data: new Uint8Array(await blob.arrayBuffer())}).promise;
        const out = await PDFLib.PDFDocument.create();
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i), vp = page.getViewport({scale: 200 / 72});
          const cv = document.createElement('canvas'); cv.width = vp.width; cv.height = vp.height;
          await page.render({canvasContext: cv.getContext('2d'), viewport: vp}).promise;
          const c = cv.getContext('2d'), id = c.getImageData(0, 0, cv.width, cv.height), d = id.data;
          for (let j = 0; j < d.length; j += 4) { const g = Math.min(255, Math.max(0, (d[j]*.3 + d[j+1]*.59 + d[j+2]*.11) * 0.94 + 6 + (Math.random() - .5) * 18)); d[j] = d[j+1] = d[j+2] = g; }
          c.putImageData(id, 0, 0);
          const jpg = await new Promise(res => cv.toBlob(res, 'image/jpeg', .7));
          const img = await out.embedJpg(await jpg.arrayBuffer());
          const pp = out.addPage([img.width * 72 / 200, img.height * 72 / 200]); pp.drawImage(img, {x: 0, y: 0, width: pp.getWidth(), height: pp.getHeight()});
        }
        return new Blob([await out.save()], {type: 'application/pdf'});
    """, TMP / "photocopier_scan.pdf")
    pg.click("#sh-team [data-close]")
    pg.click("#hub-bundle"); pg.wait_for_timeout(300)
    with pg.expect_file_chooser() as fc:
        pg.click("#b-files")
    fc.value.set_files(str(TMP / "photocopier_scan.pdf"))
    for _ in range(240):
        pg.wait_for_timeout(500)
        if pg.evaluate("async () => (await bundleItems()).length") == 1 and pg.evaluate("() => document.querySelector('#busy').hidden"):
            break
    pg.fill("#b-by", "Ts. Adam Lee Chee Wai"); pg.dispatch_event("#b-by", "change")
    pg.wait_for_timeout(3400)
    shot(pg, "17_bundle")
    pg.click("[data-pcheck]"); pg.wait_for_timeout(500)
    shot(pg, "18_check_pages")
    pg.click("#pc-save"); pg.wait_for_timeout(3400)
    pg.click("#b-preview"); pg.wait_for_timeout(2500)
    shot(pg, "19_hq_preview")
    pg.click("#sh-gen [data-close]")
    # the HQ cover page on its own, as printed (for the guide, the docs site and the brochure)
    pg.evaluate("() => { S.bundle.month = '2026-09'; save(); }")
    save_blob(pg, "await loadPdfLib(); return new Blob([(await buildBundlePDF()).bytes], {type: 'application/pdf'});", TMP / "hq.pdf")
    subprocess.run(["pdftoppm", "-r", "110", "-png", "-f", "1", "-l", "1", str(TMP / "hq.pdf"), str(TMP / "cover")], check=True)
    im = Image.open(next(TMP.glob("cover*.png"))).convert("RGB")
    im.thumbnail((720, 4000)); im.save(OUT / "20_hq_cover.png", optimize=True); print("guide/20_hq_cover.png", im.size)

    # ---- drag and drop on a computer
    desk = br.new_context(viewport={"width": 1100, "height": 700}, device_scale_factor=1)
    dp = desk.new_page()
    dp.goto(URL); dp.wait_for_selector("#w-name"); dp.evaluate(PLACEHOLDER)
    dp.fill("#w-name", "Ts. Adam Lee Chee Wai"); dp.click("#w-go")
    dp.evaluate("() => { S.ui.y = 2026; S.ui.m = 8; save(); fillMonth(false); render(); }"); dp.wait_for_timeout(3500)
    dp.evaluate("""() => { const dt = new DataTransfer(); dt.items.add(new File(['x'], 'signed.pdf', { type: 'application/pdf' }));
        document.dispatchEvent(new DragEvent('dragenter', { dataTransfer: dt, bubbles: true, cancelable: true })); }""")
    dp.wait_for_timeout(300)
    shot(dp, "21_drop")
    br.close()
print("done")
