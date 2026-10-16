"""HQ PDF from a photocopier scan: pages turned upright, QR codes covered, footer optional.

    python3 -m http.server 8765 &
    python3 tests/test_hq_pages.py [outdir]

Three timesheets are printed (two with the summary QR, one with the full data QR) and
"photocopied" at 200 dpi onto portrait pages: page 1 turned clockwise, page 2 anticlockwise,
page 3 upright landscape. The HQ PDF must keep the cover portrait, show every timesheet
landscape and upright, have the QR areas blank, and put the footer only when asked.
"""
import base64, subprocess, sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

URL = "http://localhost:8765/index.html"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "test-out"); OUT.mkdir(exist_ok=True)
errors = []
B64 = "const b = new Uint8Array(bytes); let s=''; for (let i=0;i<b.length;i+=8192) s += String.fromCharCode(...b.subarray(i,i+8192)); return btoa(s);"

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 390, "height": 844})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(URL); pg.wait_for_selector("#w-name")
    pg.fill("#w-name", "Ts. Adam Lee Chee Wai"); pg.click("#w-go")
    r = pg.evaluate("""async () => {
        S.ui.y = 2026; S.ui.m = 8; save(); fillMonth(false); S.profile.status = 'Resident Engineer'; S.role = 'compiler'; save();
        const o = S.over[S.pkg] = S.over[S.pkg] || {};
        team = []; addTeamRecord(dataRecord());
        const d2 = dataRecord(); d2.profile.name = 'Nurul Aina binti Hassan'; d2.profile.status = 'Inspector of Works'; addTeamRecord(d2);
        const d3 = dataRecord(); d3.profile.name = 'Mohd Hafiz bin Kassim'; d3.profile.status = 'Site Engineer'; addTeamRecord(d3);
        o.pageId = 'sum'; save(); const a = await makePDF([teamSheet(team[0]), teamSheet(team[1])], 'a');
        o.pageId = 'data'; save(); const b = await makePDF([teamSheet(team[2])], 'b');
        o.pageId = 'off'; save();
        await loadPdfJs(); await loadPdfLib();
        const out = await PDFLib.PDFDocument.create(), turns = [90, -90, 0];
        let idx = 0;
        for (const blob of [a, b]) {
          const pdf = await pdfjsLib.getDocument({data: new Uint8Array(await blob.arrayBuffer())}).promise;
          for (let i = 1; i <= pdf.numPages; i++, idx++) {
            const page = await pdf.getPage(i), vp = page.getViewport({scale: 200 / 72});
            let cv = document.createElement('canvas'); cv.width = vp.width; cv.height = vp.height;
            await page.render({canvasContext: cv.getContext('2d'), viewport: vp}).promise;
            const t = turns[idx];
            if (t) { const r = document.createElement('canvas'); r.width = cv.height; r.height = cv.width; const x = r.getContext('2d'); x.translate(r.width / 2, r.height / 2); x.rotate(t * Math.PI / 180); x.drawImage(cv, -cv.width / 2, -cv.height / 2); cv = r; }
            const jpg = await new Promise(res => cv.toBlob(res, 'image/jpeg', .8)), img = await out.embedJpg(await jpg.arrayBuffer());
            const pp = out.addPage([img.width * 72 / 200, img.height * 72 / 200]); pp.drawImage(img, {x: 0, y: 0, width: pp.getWidth(), height: pp.getHeight()});
          }
        }
        const scan = new File([await out.save()], 'photocopier.pdf', {type: 'application/pdf'});
        await addBundle([scan]);
        const it = (await bundleItems())[0];
        $('#b-month').value = '2026-09';
        const pdfOf = async () => { const res = await buildBundlePDF(); const bytes = res.bytes; """ + B64 + """ };
        const withFooter = await pdfOf();
        $('#b-footer').checked = false; const noFooter = await pdfOf();
        return { prot: it.prot, qrb: it.qrb.map(b => !!b), who: it.labels.map(l => l && l.who), withFooter, noFooter };
    }""")
    (OUT / "hq_footer.pdf").write_bytes(base64.b64decode(r.pop("withFooter")))
    (OUT / "hq_nofooter.pdf").write_bytes(base64.b64decode(r.pop("noFooter")))
    print(r)
    assert r["prot"] == [270, 90, 0], r["prot"]          # turns that put each page upright
    assert r["qrb"] == [True, True, True], r["qrb"]
    br.close()

info = subprocess.run(["pdfinfo", "-f", "1", "-l", "4", str(OUT / "hq_footer.pdf")], capture_output=True, text=True).stdout
sizes = [l for l in info.splitlines() if "size" in l and "Page" in l]
print("\n".join(sizes))
rot = [l for l in info.splitlines() if "rot" in l]
subprocess.run(["pdftoppm", "-r", "50", "-png", str(OUT / "hq_footer.pdf"), str(OUT / "hq")], check=True)
pages = sorted(OUT.glob("hq-*.png"))
dims = [Image.open(x).size for x in pages]
print(dims)
assert dims[0][1] > dims[0][0], "cover portrait"
assert all(w > h for w, h in dims[1:]), "timesheets landscape"
# QR areas blank: bottom-right corner region of each timesheet page has no dark QR modules
for x in pages[1:]:
    im = Image.open(x).convert("L"); w, h = im.size
    corner = im.crop((int(w * 0.80), int(h * 0.78), w, int(h * 0.97)))
    dark = sum(1 for v in corner.getdata() if v < 100) / (corner.width * corner.height)
    print(x.name, "dark in QR corner", round(dark, 3))
    assert dark < 0.02, (x.name, dark)
# footer text present only when asked
t1 = subprocess.run(["pdftotext", str(OUT / "hq_footer.pdf"), "-"], capture_output=True, text=True).stdout
t2 = subprocess.run(["pdftotext", str(OUT / "hq_nofooter.pdf"), "-"], capture_output=True, text=True).stdout
assert "Page 4 of 4" in t1 and "Page 1 of 4" not in t2, "footer option"
print("errors:", errors)
assert not errors
print("OK")
