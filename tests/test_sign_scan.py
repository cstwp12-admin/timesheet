"""Checks for digital signatures and recognising scanned pages.

    python3 -m http.server 8765 &
    python3 tests/test_sign_scan.py [outdir]

1. Default signature layout is the original form.
2. A drawn signature signs "Prepared by"; it travels in the QR and comes back the same.
3. The RE signs the team timesheets under "Verified by PYKP"; PDF and Excel carry both signatures.
4. The team's timesheets are printed (no QR on the form), "photocopied" (rasterised, one page turned,
   grey, noisy) into one PDF, and the app reads the printed name on each page.
"""
import base64
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:8765/index.html"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "test-out")
OUT.mkdir(exist_ok=True)
errors = []
B64 = "const buf = new Uint8Array(await b.arrayBuffer()); let s=''; for (let i=0;i<buf.length;i+=8192) s += String.fromCharCode(...buf.subarray(i,i+8192)); return btoa(s);"


def save(pg, js, name):
    data = pg.evaluate("async () => { const b = await (async () => {" + js + "})(); " + B64 + " }")
    (OUT / name).write_bytes(base64.b64decode(data))


with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(URL)
    pg.wait_for_selector("#w-name")
    pg.fill("#w-name", "Nurul Aina binti Hassan"); pg.click("#w-go")
    assert pg.evaluate("() => cfg().signLayout") == "form"
    pg.evaluate("""() => {
        S.profile.name = 'Nurul Aina binti Hassan'; S.profile.status = 'Assistant Resident Engineer'; S.ui.y = 2026; S.ui.m = 8; save(); fillMonth(false);
        // a drawn signature: a few loops and a flourish
        const st = []; for (let k = 0; k < 3; k++) { const a = []; for (let t = 0; t <= 60; t++) { const u = t / 60 * Math.PI * 2; a.push(40 + k * 70 + t * 1.2 + 22 * Math.cos(u), 60 + 26 * Math.sin(u * (k + 1)) ); } st.push(a); }
        st.push([20, 95, 120, 88, 260, 92, 300, 80]);
        S.mySig = strokesToSig(st); S.sigPin = pinHash('1234'); S.digiSign = true; save(); render();
    }""")
    pg.click("#sig-sign"); pg.fill("#pin-in", "9999"); pg.click("#pin-ok"); pg.wait_for_timeout(200)
    assert not pg.evaluate("() => !!(month().sig && month().sig.prep)"), "wrong PIN must not sign"
    pg.fill("#pin-in", "1234"); pg.click("#pin-ok"); pg.wait_for_timeout(300)
    assert pg.evaluate("() => sigValid(month().sig.prep, month())")
    # change the hours after signing: signature no longer valid, not printed
    pg.evaluate("() => { const md = month(); md.rows[0].v[1] = '4'; touch(md); render(); }")
    assert pg.evaluate("() => !sigValid(month().sig.prep, month()) && sigPlacements(sheetFor(2026, 8)).length === 0")
    pg.evaluate("() => { const md = month(); md.rows[0].v[1] = '8'; touch(md); render(); }")
    assert pg.evaluate("() => sigValid(month().sig.prep, month())")
    pg.screenshot(path=str(OUT / "s1_signed_panel.png"), full_page=True)

    rt = pg.evaluate("""async () => {
        const d = dataRecord(), txt = qrPayload(d);
        const q = qrcode(0, txt.length > 650 ? 'L' : 'M'); q.addData(txt, 'Byte'); q.make();
        const n = q.getModuleCount(), cs = 4, cv = document.createElement('canvas'); cv.width = cv.height = (n + 8) * cs;
        const c = cv.getContext('2d'); c.fillStyle = '#fff'; c.fillRect(0, 0, cv.width, cv.height); c.fillStyle = '#000';
        for (let r = 0; r < n; r++) for (let k = 0; k < n; k++) if (q.isDark(r, k)) c.fillRect((k + 4) * cs, (r + 4) * cs, cs, cs);
        await loadJsQR(); const id = c.getImageData(0, 0, cv.width, cv.height); const r = jsQR(id.data, cv.width, cv.height);
        const d2 = parsePayload(r.data);
        window.__member = d2;
        return {len: txt.length, modules: n, sig: !!(d2.md.sig && d2.md.sig.prep), strokes: d2.md.sig.prep.sig.s.length, valid: sigValid(d2.md.sig.prep, d2.md)};
    }""")
    print("qr with signature", rt)
    assert rt["sig"] and rt["strokes"] == 4 and rt["valid"], rt

    # RE (another phone): receives the member's QR, signs as RE
    pg.evaluate("""() => {
        S.profile.name = 'Ir. Daniel Wong'; S.profile.status = 'Resident Engineer'; S.role = 'staff'; save();
        team = []; addTeamRecord(window.__member);
        const d2 = JSON.parse(JSON.stringify(window.__member)); d2.profile.name = 'Ts. Adam Lee Chee Wai'; d2.profile.status = 'Inspector of Works'; d2.md.sig = {}; addTeamRecord(d2);
    }""")
    # staff role cannot sign as RE
    pg.evaluate("async () => { await reSign(team); }")
    assert not pg.evaluate("() => team.some(d => d.md.sig && d.md.sig.v1)"), "staff must not sign as RE"
    pg.evaluate("() => { S.role = 're'; save(); render(); }")
    pg.evaluate("() => { reSign(team); }"); pg.fill("#pin-in", "1234"); pg.click("#pin-ok"); pg.wait_for_timeout(600)
    assert pg.evaluate("() => team.every(d => d.md.sig && sigValid(d.md.sig.v1, d.md))")
    # adjust the RE signature a little to the right and bigger
    pg.evaluate("() => { (S.over[S.pkg] = S.over[S.pkg] || {}).sigAdj = { form: { v1: { dx: 30, dy: -2, s: 1.2 } } }; save(); }")
    save(pg, "return await makePDF(team.map(teamSheet), 'All');", "s2_team_signed.pdf")
    save(pg, "const sh = team.map(teamSheet); return await makeXLSX(sh, ['Adam', 'Nurul']);", "s2_team_signed.xlsx")
    # side-by-side layout too
    pg.evaluate("() => { (S.over[S.pkg] = S.over[S.pkg] || {}).signLayout = 'side'; save(); }")
    save(pg, "return await makePDF([teamSheet(team[1])], 'side');", "s3_side_signed.pdf")
    pg.evaluate("() => { S.over[S.pkg].signLayout = 'form'; save(); }")

    # photocopier: print all, rasterise each page (grey, noise), turn page 2 by 90 degrees, join into one PDF
    save(pg, """
        const blob = await makePDF(team.map(teamSheet), 'All'); await loadPdfJs(); await loadPdfLib();
        const pdf = await pdfjsLib.getDocument({data: new Uint8Array(await blob.arrayBuffer())}).promise;
        const out = await PDFLib.PDFDocument.create();
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i), vp = page.getViewport({scale: 200 / 72});
          let cv = document.createElement('canvas'); cv.width = vp.width; cv.height = vp.height;
          await page.render({canvasContext: cv.getContext('2d'), viewport: vp}).promise;
          const c = cv.getContext('2d'), id = c.getImageData(0, 0, cv.width, cv.height), d = id.data;
          for (let j = 0; j < d.length; j += 4) { const g = Math.min(255, Math.max(0, (d[j]*.3 + d[j+1]*.59 + d[j+2]*.11) * 0.93 + 8 + (Math.random() - .5) * 26)); d[j] = d[j+1] = d[j+2] = g; }
          c.putImageData(id, 0, 0);
          if (i === 2) { const r = document.createElement('canvas'); r.width = cv.height; r.height = cv.width; const x = r.getContext('2d'); x.translate(r.width / 2, r.height / 2); x.rotate(Math.PI / 2); x.drawImage(cv, -cv.width / 2, -cv.height / 2); cv = r; }
          const jpg = await new Promise(res => cv.toBlob(res, 'image/jpeg', .7));
          const img = await out.embedJpg(await jpg.arrayBuffer());
          const pp = out.addPage([img.width * 72 / 200, img.height * 72 / 200]); pp.drawImage(img, {x: 0, y: 0, width: pp.getWidth(), height: pp.getHeight()});
        }
        return new Blob([await out.save()], {type: 'application/pdf'});
    """, "s4_photocopier_scan.pdf")
    pg.click("#btn-hq"); pg.wait_for_timeout(300); pg.click("#hub-bundle"); pg.wait_for_timeout(300)
    with pg.expect_file_chooser() as fc:
        pg.click("#b-files")
    fc.value.set_files(str(OUT / "s4_photocopier_scan.pdf"))
    for _ in range(240):
        pg.wait_for_timeout(500)
        if pg.evaluate("async () => (await bundleItems()).length") == 1 and pg.evaluate("() => document.querySelector('#busy').hidden"):
            break
    labels = pg.evaluate("async () => (await bundleItems())[0].labels")
    print("labels", labels)
    assert labels and all(labels) and sorted(l["who"] for l in labels) == ["Nurul Aina binti Hassan", "Ts. Adam Lee Chee Wai"], labels
    assert all(l["via"] == "name" for l in labels), labels       # read from the printed name, not guessed by order
    pg.screenshot(path=str(OUT / "s5_hq.png"))
    pg.click("[data-pcheck]"); pg.wait_for_timeout(400)
    pg.screenshot(path=str(OUT / "s5b_check_pages.png"))
    pg.click("#pc-save"); pg.wait_for_timeout(300)
    save(pg, "let blob; const orig = window.shareFile; window.shareFile = async b => { blob = b; }; await makeBundle(); window.shareFile = orig; return blob;", "s6_hq.pdf")
    br.close()

print("errors:", errors)
assert not errors, errors
print("OK")
