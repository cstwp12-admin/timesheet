"""Automatic checks of the Timesheet app.

Run from the repository folder with a local server:
    python3 -m http.server 8765 &
    python3 tests/test_app.py [outdir]

Fills September 2026 for a sample person (AL on 8-9, PH 16, overtime), then checks the totals,
the status undo, the QR round trip, the document scanner steps, the PDF, Excel and HQ PDF.
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
    pg.wait_for_selector("#w-name")                       # first run: welcome
    pg.screenshot(path=str(OUT / "00_welcome.png"))
    pg.fill("#w-name", "Ts. Adam Lee Chee Wai")
    pg.fill("#w-status", "Resident Engineer")
    pg.click('#w-role [data-r="compiler"]')
    pg.click("#w-go")
    pg.click("#btn-collapse")
    pg.evaluate("() => { S.ui.y = 2026; S.ui.m = 8; save(); render(); }")
    pg.click('#seg-code [data-code="F"]')
    pg.click('#seg-stage [data-stage="F"]')
    pg.click("#btn-fill")
    pg.click("#btn-select")
    pg.click('[data-day="8"]'); pg.click('[data-day="9"]')
    pg.click('#bulk-codes [data-setsel="AL"]')
    pg.click("#bulk-done")
    pg.click('[data-day="20"]')
    pg.fill("#ot-2", "4"); pg.dispatch_event("#ot-2", "change")
    pg.click("#sh-day [data-close]")
    pg.click('[data-day="3"]')
    pg.fill("#ot-1", "2.5"); pg.dispatch_event("#ot-1", "change")
    pg.fill("#day-note", "Concrete pour")
    pg.click("#sh-day [data-close]")
    pg.wait_for_timeout(3500)
    pg.screenshot(path=str(OUT / "01_main.png"), full_page=True)

    tot = pg.evaluate("() => { const t = totals(month(), 2026, 8); return {n: t.rowSum[0], ot: t.ot, rd: t.RD, ph: t.PH, leave: t.leave, empty: t.empty.length, stage: month().rows[0].stage, code: cfg().codeNo}; }")
    print("totals", tot)
    assert tot["n"] == 184 and tot["ot"] == 6.5 and tot["rd"] == 4 and tot["ph"] == 1 and tot["leave"] == {"AL": 2}, tot
    assert tot["stage"] == "F" and tot["code"] == "F", tot

    # status: mark signed (also sets printed), then undo
    pg.click('#status [data-st="signed"]')
    st = pg.evaluate("() => month().status")
    assert st["printed"] and st["signed"] and not st["sent"], st
    pg.click('#status [data-st="signed"]')
    st = pg.evaluate("() => month().status")
    assert st["printed"] and not st["signed"], st

    # day editor screenshot
    pg.click('[data-day="16"]'); pg.wait_for_timeout(200)
    pg.screenshot(path=str(OUT / "02_day.png"))
    pg.click("#sh-day [data-close]")

    # print sheet
    pg.click("#dock-go"); pg.wait_for_timeout(400)
    pg.screenshot(path=str(OUT / "03_print.png"))
    save(pg, "return await makePDF([sheetFor(2026, 8)], 't');", "september.pdf")
    save(pg, "return await makeXLSX([sheetFor(2026, 8)], ['September 2026']);", "september.xlsx")

    # QR round trip: payload -> QR image -> decode -> same totals
    rt = pg.evaluate("""async () => {
        const d = dataRecord(), txt = qrPayload(d);
        const q = qrcode(0, 'M'); q.addData(txt, 'Byte'); q.make();
        const n = q.getModuleCount(), cs = 6, cv = document.createElement('canvas'); cv.width = cv.height = (n + 8) * cs;
        const c = cv.getContext('2d'); c.fillStyle = '#fff'; c.fillRect(0, 0, cv.width, cv.height); c.fillStyle = '#000';
        for (let r = 0; r < n; r++) for (let k = 0; k < n; k++) if (q.isDark(r, k)) c.fillRect((k + 4) * cs, (r + 4) * cs, cs, cs);
        const back = await decodeQRFromCanvas(cv); const d2 = parsePayload(back);
        const a = totals(d.md, 2026, 8), b = totals(d2.md, 2026, 8);
        return {len: txt.length, modules: n, same: JSON.stringify(a) === JSON.stringify(b), name: d2.profile.name, stage: d2.md.rows[0].stage};
    }""")
    print("qr", rt)
    assert rt["same"] and rt["name"] == "Ts. Adam Lee Chee Wai" and rt["stage"] == "F", rt
    pg.click("#btn-showqr"); pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "04_qr.png"))
    pg.click("#sh-gen [data-close]"); pg.click("#sh-out [data-close]")

    # document scanner steps on a synthetic photo: the timesheet page, tilted, on a dark desk
    sc = pg.evaluate("""async () => {
        const blob = await makePDF([sheetFor(2026, 8)], 't');
        const svg = new Blob([sheetSVG(sheetFor(2026, 8))], {type: 'image/svg+xml'});
        const img = await new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = URL.createObjectURL(svg); });
        const W = 1600, H = 1200, cv = document.createElement('canvas'); cv.width = W; cv.height = H; const c = cv.getContext('2d');
        const gr = c.createLinearGradient(0, 0, W, H); gr.addColorStop(0, '#3b3026'); gr.addColorStop(1, '#5a4a3a'); c.fillStyle = gr; c.fillRect(0, 0, W, H);
        c.save(); c.translate(W / 2, H / 2); c.rotate(-0.12); c.fillStyle = '#f3f1ea'; c.fillRect(-620, -440, 1240, 877); c.drawImage(img, -620, -440, 1240, 877); c.restore();
        // shade one side like a phone photo
        const sh = c.createLinearGradient(0, 0, W, 0); sh.addColorStop(0, 'rgba(0,0,0,0)'); sh.addColorStop(1, 'rgba(0,0,0,.25)'); c.fillStyle = sh; c.fillRect(0, 0, W, H);
        const q = detectQuad(cv, W, H);
        const flat = warpQuad(cv, q); const bw = cleanUp(flat, 'bw');
        const o = await new Promise(r => bw.toBlob(r, 'image/jpeg', .85));
        const raw = await new Promise(r => cv.toBlob(r, 'image/jpeg', .85));
        window.__scan = o; window.__raw = raw;
        return {q: q && q.map(p => p.map(v => +v.toFixed(3))), w: bw.width, h: bw.height};
    }""")
    print("scan", sc)
    assert sc["q"] and sc["w"] > sc["h"], sc
    save(pg, "return window.__raw;", "scan_input.jpg")
    save(pg, "return window.__scan;", "scan_output.jpg")

    # HQ: add the scan and the PDF, make the HQ PDF
    pg.click("#btn-hq"); pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "05a_hub.png"))
    pg.click("#hub-bundle"); pg.wait_for_timeout(300)
    pg.evaluate("async () => { await addBundle([{blob: window.__scan, type: 'image/jpeg', name: 'TIMESHEET_WP12_2026-09_ADAM-LEE-CHEE-WAI.jpg'}]); }")
    with pg.expect_file_chooser() as fc:
        pg.click("#b-files")
    fc.value.set_files(str(OUT / "september.pdf"))
    for _ in range(120):
        pg.wait_for_timeout(500)
        if pg.evaluate("async () => (await bundleItems()).length") == 2 and pg.evaluate("() => document.querySelector('#busy').hidden"):
            break
    assert pg.evaluate("async () => (await bundleItems()).length") == 2
    pg.evaluate("() => { addTeamRecord(dataRecord()); const d = dataRecord(); d.profile.name = 'Nurul Aina binti Hassan'; d.profile.status = 'Assistant Resident Engineer'; addTeamRecord(d); renderHQ(); }")
    pg.wait_for_timeout(500)
    pg.screenshot(path=str(OUT / "05_hq.png"), full_page=False)
    pg.fill('[data-bmeta$="|who"] >> nth=1', "Nurul Aina binti Hassan"); pg.dispatch_event('[data-bmeta$="|who"] >> nth=1', "change")
    pg.fill('[data-bmeta$="|month"] >> nth=1', "September 2026"); pg.dispatch_event('[data-bmeta$="|month"] >> nth=1', "change")
    pg.fill("#b-by", "Ts. Adam Lee Chee Wai")
    pg.click("#sh-bundle [data-close]"); pg.click("#hub-team"); pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "05b_team.png"))
    pg.click("#t-preview"); pg.wait_for_timeout(600)
    pg.screenshot(path=str(OUT / "07_team_preview.png"))
    pg.click("#sh-gen [data-close]")
    pg.click("#sh-team [data-close]"); pg.click("#hub-bundle"); pg.wait_for_timeout(300)
    pg.click("#b-preview"); pg.wait_for_timeout(1500)
    pg.screenshot(path=str(OUT / "08_hq_preview.png"))
    pg.click("#sh-gen [data-close]")
    save(pg, "await loadPdfLib(); let blob; const orig = window.shareFile; window.shareFile = async b => { blob = b; }; await makeBundle(); window.shareFile = orig; return blob;", "hq.pdf")
    save(pg, "const sh = team.map(teamSheet); return await makeXLSX(sh, ['Adam Sep 2026', 'Nurul Sep 2026']);", "team.xlsx")
    pg.click("#sh-bundle [data-close]"); pg.click("#sh-hq [data-close]")

    pg.click("#btn-records"); pg.wait_for_timeout(500)
    pg.screenshot(path=str(OUT / "06_records.png"))
    pg.click("#sh-rec [data-close]")

    pg.goto(URL + "?p=WP13"); pg.wait_for_timeout(800)
    assert pg.evaluate("() => S.pkg") == "WP13"
    br.close()

print("errors:", errors)
assert not errors, errors
print("OK")
