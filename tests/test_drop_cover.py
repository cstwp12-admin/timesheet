"""Drag and drop on a computer, checks on imported data, and the HQ cover page.

    python3 -m http.server 8765 &
    python3 tests/test_drop_cover.py

1. Main screen: dropping a photo saves it as the month's signed copy (overlay shows while dragging).
2. Signed copies for HQ open: dropping a PDF adds it to the HQ list.
3. Team timesheets open: dropping a data file adds the person; a file with a bad month is refused.
4. The HQ cover page: caption, month in large type, three figure boxes, details, contents and total.
5. Help > Share this app shows the QR code, the address and Copy link.
"""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8765/index.html?p=OTHER"
errors = []

DROP = """async ([name, type, text, b64]) => {
  const bytes = b64 ? Uint8Array.from(atob(b64), c => c.charCodeAt(0)) : new TextEncoder().encode(text);
  const dt = new DataTransfer(); dt.items.add(new File([bytes], name, { type }));
  document.dispatchEvent(new DragEvent('dragenter', { dataTransfer: dt, bubbles: true, cancelable: true }));
  const shown = !document.querySelector('#drop').hidden, head = document.querySelector('#drop-h').textContent;
  document.dispatchEvent(new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true }));
  await new Promise(r => setTimeout(r, 900));
  return { shown, head, hidden: document.querySelector('#drop').hidden };
}"""

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1100, "height": 900})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(URL)
    pg.wait_for_selector("#w-name")
    pg.fill("#w-name", "Ts. Adam Lee Chee Wai"); pg.click("#w-go")
    pg.evaluate("() => { S.ui.y = 2026; S.ui.m = 8; S.role = 'compiler'; save(); fillMonth(false); render(); }")
    # a small JPEG made in the page
    jpg = pg.evaluate("""() => { const c = document.createElement('canvas'); c.width = 400; c.height = 300; const x = c.getContext('2d');
        x.fillStyle = '#fff'; x.fillRect(0, 0, 400, 300); x.fillStyle = '#000'; x.fillRect(40, 40, 320, 20); return c.toDataURL('image/jpeg').split(',')[1]; }""")

    # 1. main screen -> signed copy
    r = pg.evaluate(DROP, ["signed.jpg", "image/jpeg", "", jpg])
    print("main", r)
    assert r["shown"] and r["head"] == "Drop to save" and r["hidden"]
    pg.wait_for_timeout(600)
    n = pg.evaluate("async () => (await DB.all()).filter(f => f.scope === 'signed' && f.month === '2026-09').length")
    assert n == 1, n

    # 2. HQ list
    pdf = pg.evaluate("async () => { const b = await makePDF([sheetFor(2026, 8)], 't'); const u = new Uint8Array(await b.arrayBuffer()); let s = ''; for (let i = 0; i < u.length; i += 8192) s += String.fromCharCode(...u.subarray(i, i + 8192)); return btoa(s); }")
    pg.evaluate("() => { renderHQ(); openSheet('#sh-bundle'); }")
    r = pg.evaluate(DROP, ["scan.pdf", "application/pdf", "", pdf])
    print("bundle", r)
    assert r["head"] == "Drop to add to the HQ list"
    pg.wait_for_function("async () => (await bundleItems()).length === 1", timeout=60000)

    # 3. team data file; bad month refused
    pg.evaluate("() => { closeSheet('#sh-bundle'); openSheet('#sh-team'); }")
    good = pg.evaluate("() => { const d = dataRecord(); d.profile.name = 'Nurul Aina binti Hassan'; return JSON.stringify(d); }")
    r = pg.evaluate(DROP, ["nurul.json", "application/json", good, None])
    assert r["head"] == "Drop to add timesheets"
    bad = pg.evaluate("() => { const d = dataRecord(); d.profile.name = 'Bad Month'; d.month = '2026-13'; return JSON.stringify(d); }")
    pg.evaluate(DROP, ["bad.json", "application/json", bad, None])
    names = pg.evaluate("() => team.map(t => t.profile.name)")
    print("team", names)
    assert "Nurul Aina binti Hassan" in names and "Bad Month" not in names
    # the QR route goes through the same check
    rej = pg.evaluate("() => { try { addTeamRecord({ kind: 'ts-data', month: 'x', profile: { name: 'A' }, md: { rows: [] } }); return 'accepted'; } catch (e) { return e.message; } }")
    assert rej != "accepted", rej

    # 4. cover page
    cv = pg.evaluate("""async () => { S.bundle.month = '2026-09'; S.bundle.by = 'Ts. Adam Lee Chee Wai'; save();
        const items = await bundleItems(), c = coverOps(items), txt = JSON.stringify(c.pages[0]);
        return { n: c.pages.length, caption: txt.includes('MONTHLY TIMESHEET SUBMISSION'), month: txt.includes('SEPTEMBER 2026'),
                 boxes: c.pages[0].filter(o => o.k === 'rect' && o.r).length, total: txt.includes('"Total"'),
                 details: txt.includes('Submission details') && txt.includes('PREPARED ON'), credit: txt.includes('developed by WPN') }; }""")
    print("cover", cv)
    assert cv["n"] == 1 and cv["caption"] and cv["month"] and cv["boxes"] == 4 and cv["total"] and cv["details"] and cv["credit"]
    # many timesheets -> continuation page
    many = pg.evaluate("() => { const it = { pages: 40, labels: Array.from({ length: 40 }, (_, k) => ({ who: 'Person ' + String.fromCharCode(65 + k % 26, 65 + Math.floor(k / 26)), ym: '2026-09' })) }; return coverOps([it]).pages.length; }")
    assert many == 2, many

    # 5. Help > Share this app: QR and link
    pg.evaluate("() => openHelp()")
    pg.click("#h-share")
    sh = pg.evaluate("() => ({ svg: !!document.querySelector('#sa-qr svg'), url: document.querySelector('#gen-body .mono').textContent, copy: !!document.querySelector('#sa-copy') })")
    print("share", sh)
    assert sh["svg"] and sh["copy"] and sh["url"] == "http://localhost:8765/", sh
    br.close()

print("errors:", errors)
assert not errors
print("OK")
