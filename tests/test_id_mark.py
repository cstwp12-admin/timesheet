"""Summary QR: project, month, name, designation, normal and OT hours in a small QR under the form.

    python3 -m http.server 8765 &
    python3 tests/test_id_mark.py [outdir]

Prints two timesheets with the summary QR, "photocopies" them at 200 dpi (grey, noisy, one page
turned), and checks every page and its hours are read from the QR itself.
"""
import base64
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:8765/index.html"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "test-out")
OUT.mkdir(exist_ok=True)
errors = []

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 390, "height": 844})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL)
    pg.wait_for_selector("#w-name")
    pg.fill("#w-name", "Ts. Adam Lee Chee Wai"); pg.click("#w-go")
    r = pg.evaluate("""async () => {
        S.ui.y = 2026; S.ui.m = 8; save(); fillMonth(false);
        S.profile.status = 'Resident Engineer'; save(); (S.over[S.pkg] = S.over[S.pkg] || {}).pageId = 'sum'; save();
        team = []; addTeamRecord(dataRecord());
        const d2 = dataRecord(); d2.profile.name = 'Nurul Aina binti Hassan'; d2.profile.status = 'Assistant Resident Engineer'; d2.md.rows[2].v[6] = '4'; addTeamRecord(d2);
        const sheets = team.map(teamSheet), ids = sheets.map(pageIdSummary);
        const modules = ids.map(t => qrMatrix(t, 'L', 'Alphanumeric').getModuleCount());
        const blob = await makePDF(sheets, 'All'); await loadPdfJs(); await loadPdfLib();
        const pdf = await pdfjsLib.getDocument({data: new Uint8Array(await blob.arrayBuffer())}).promise;
        const out = await PDFLib.PDFDocument.create();
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i), vp = page.getViewport({scale: 200 / 72});
          let cv = document.createElement('canvas'); cv.width = vp.width; cv.height = vp.height;
          await page.render({canvasContext: cv.getContext('2d'), viewport: vp}).promise;
          const c = cv.getContext('2d'), id = c.getImageData(0, 0, cv.width, cv.height), d = id.data;
          for (let j = 0; j < d.length; j += 4) { const g = Math.min(255, Math.max(0, (d[j]*.3 + d[j+1]*.59 + d[j+2]*.11) * 0.93 + 8 + (Math.random() - .5) * 26)); d[j] = d[j+1] = d[j+2] = g; }
          c.putImageData(id, 0, 0);
          if (i === 2) { const r = document.createElement('canvas'); r.width = cv.height; r.height = cv.width; const x = r.getContext('2d'); x.translate(r.width / 2, r.height / 2); x.rotate(-Math.PI / 2); x.drawImage(cv, -cv.width / 2, -cv.height / 2); cv = r; }
          const jpg = await new Promise(res => cv.toBlob(res, 'image/jpeg', .7));
          const img = await out.embedJpg(await jpg.arrayBuffer());
          const pp = out.addPage([img.width * 72 / 200, img.height * 72 / 200]); pp.drawImage(img, {x: 0, y: 0, width: pp.getWidth(), height: pp.getHeight()});
        }
        const scan = new Blob([await out.save()], {type: 'application/pdf'});
        team = [];   // the compiler has no team list: everything must come from the QR
        const res = [];
        await pageCanvases(scan, 'application/pdf', async (cv) => { res.push(await readPageId(cv, cv.width, cv.height)); });
        const b = new Uint8Array(await blob.arrayBuffer()); let s = ''; for (let i = 0; i < b.length; i += 8192) s += String.fromCharCode(...b.subarray(i, i + 8192));
        return {ids, modules, res, pdf: btoa(s)};
    }""")
    (OUT / "id_mark.pdf").write_bytes(base64.b64decode(r.pop("pdf")))
    print(r)
    assert all(m <= 33 for m in r["modules"]), r["modules"]          # version 4 or smaller: about 15 mm at most
    got = [(x["who"], x["desig"], x["hrs"], x["ot"]) for x in r["res"]]
    assert got == [("Nurul Aina Binti Hassan", "Assistant Resident Engineer", 200, 4), ("Adam Lee Chee Wai", "Resident Engineer", 200, 0)], got
    br.close()

print("errors:", errors)
assert not errors, errors
print("OK")
