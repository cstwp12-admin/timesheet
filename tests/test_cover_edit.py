"""Compiler enters designation and hours in Check pages when the scan has none.

    python3 -m http.server 8765 &
    python3 tests/test_cover_edit.py

Page 1: a name not in the team list and no QR, so no hours: the compiler types them.
Page 2: a team member whose hours differ from the signed copy: the compiler corrects OT.
Both show on the cover page marked *; clearing a box goes back to the automatic value.
"""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8765/index.html"
errors = []

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 390, "height": 844})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(URL)
    pg.wait_for_selector("#w-name")
    pg.fill("#w-name", "Ts. Adam Lee Chee Wai"); pg.click("#w-go")
    item = pg.evaluate("""async () => {
        S.ui.y = 2026; S.ui.m = 8; save(); fillMonth(false); S.profile.status = 'Resident Engineer'; S.role = 'compiler'; save();
        team = []; addTeamRecord(dataRecord()); saveTeam();
        const blob = await makePDF([sheetFor(2026, 8), sheetFor(2026, 8)], 't');
        const id = uid();
        await DB.put({ id, scope: 'bundle', name: 'scan.pdf', type: 'application/pdf', blob, order: 1, pages: 2,
          labels: [{ who: '', via: 'unsure', raw: '???' }, { who: 'Ts. Adam Lee Chee Wai', ym: '2026-09', via: 'name' }],
          thumbs: [], crops: [], who: '', month: '', ym: '', rotate: 0, added: new Date().toISOString() });
        render(); return id;
    }""")
    pg.evaluate(f"() => openPageCheck('{item}')")
    pg.wait_for_selector('#gen-body input[data-pk="0"]')
    # page 2 is prefilled from the team list
    assert pg.input_value('#gen-body [data-pcf="1"] [data-f="hrs"]') != "", "page 2 hours prefilled"
    assert pg.input_value('#gen-body [data-pcf="1"] [data-f="desig"]') == "Resident Engineer"
    # page 1: type a name not in the team list, then the boxes are empty and flagged
    pg.fill('#gen-body input[data-pk="0"]', "Lim Mei Ling"); pg.dispatch_event('#gen-body input[data-pk="0"]', "change"); pg.click('#gen-body [data-pcf="0"] [data-f="desig"]')
    assert pg.input_value('#gen-body [data-pcf="0"] [data-f="hrs"]') == ""
    assert "No hours found" in pg.inner_text('#gen-body [data-pcf="0"]')
    pg.fill('#gen-body [data-pcf="0"] [data-f="desig"]', "Inspector of Works")
    pg.fill('#gen-body [data-pcf="0"] [data-f="hrs"]', "176")
    pg.fill('#gen-body [data-pcf="0"] [data-f="ot"]', "6,5")
    pg.fill('#gen-body [data-pcf="1"] [data-f="ot"]', "3")
    pg.click("#pc-save"); pg.wait_for_timeout(300)
    r = pg.evaluate("""async () => {
        const items = await bundleItems(), rows = bundleRows(items, 1);
        const ops = coverOps(items), txt = JSON.stringify(ops);
        return { rows: rows.map(r => [r.who, r.desig, r.hrs, r.ot, !!r.edited]), labels: items[0].labels.map(l => l && l.edit),
                 star: txt.includes('176.0*') && txt.includes('6.5*') && txt.includes('3.0*'), note: txt.includes('entered by the compiler'),
                 tag: document.querySelector('#b-list').innerText };
    }""")
    print(r)
    assert r["rows"][0] == ["Lim Mei Ling", "Inspector of Works", "176.0", "6.5", True], r["rows"][0]
    assert r["rows"][1][3] == "3.0" and r["rows"][1][4], r["rows"][1]
    assert r["labels"][1] == {"ot": 3}, r["labels"]           # only what differs is kept
    assert r["star"] and r["note"]
    assert "without hours" not in r["tag"]
    # clearing the OT box on page 2 returns to the automatic value
    pg.evaluate(f"() => openPageCheck('{item}')")
    pg.wait_for_selector('#gen-body [data-pcf="1"]')
    assert "Entered by you" in pg.inner_text('#gen-body [data-pcf="1"]')
    pg.fill('#gen-body [data-pcf="1"] [data-f="ot"]', "")
    pg.click("#pc-save"); pg.wait_for_timeout(300)
    r2 = pg.evaluate("async () => { const it = (await bundleItems())[0]; return [bundleRows([it], 1)[1].ot, it.labels[1].edit || null]; }")
    print(r2)
    assert r2 == ["0.0", None], r2
    br.close()

print("errors:", errors)
assert not errors
print("OK")
