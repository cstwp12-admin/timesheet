"""Optional colour fill on the printed form (Print / PDF → Colour fill → Colour by code).

    python3 -m http.server 8765 &
    python3 tests/test_color_fill.py

Off by default: no fill. On: the day's column (time codes 1-5) is tinted for RD, PH and leave,
normal working days stay white, the text stays black; the Excel file gets the same fills with
the form's borders kept.
"""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8765/index.html"
errors = []

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 390, "height": 844})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL)
    pg.wait_for_selector("#w-name")
    pg.fill("#w-name", "Ts. Adam Lee Chee Wai"); pg.click("#w-go")
    pg.evaluate("""() => { S.ui.y = 2026; S.ui.m = 8; save(); fillMonth(false); const v = month().rows[0].v;
        v[3] = 'AL'; v[9] = 'EL'; v[15] = 'MC'; v[23] = 'CT'; save(); render(); }""")
    off = pg.evaluate("() => sheetOps(sheetFor(2026, 8)).ops.filter(o => o.k === 'fill').length")
    pg.click("#dock-go"); pg.wait_for_timeout(300)
    pg.click('[data-fill="1"]'); pg.wait_for_timeout(300)
    r = pg.evaluate("""async () => {
        const sh = sheetFor(2026, 8), ops = sheetOps(sh).ops, fills = ops.filter(o => o.k === 'fill');
        const codeText = ops.filter(o => o.k === 'text' && o.runs.some(x => ['AL', 'EL', 'MC', 'CT', 'RD', 'PH'].includes(x.t))).map(o => o.runs[0].color || '000000');
        const svg = sheetSVG(sh), colors = [...new Set(fills.map(f => f.color))].sort();
        const zip = await JSZip.loadAsync(await makeXLSX([sh], ['Sept']));
        const styles = await zip.file('xl/styles.xml').async('string'), sheet = await zip.file('xl/worksheets/sheet1.xml').async('string');
        const sid = ref => Number((new RegExp(`<c r="${ref}"[^>]*s="(\\\\d+)"`).exec(sheet) || [])[1]);
        const xfs = [...new DOMParser().parseFromString(styles, 'application/xml').getElementsByTagName('cellXfs')[0].getElementsByTagName('xf')];
        const fillOf = ref => Number(xfs[sid(ref)].getAttribute('fillId')), borderOf = ref => xfs[sid(ref)].getAttribute('borderId');
        return { first: fills.findIndex(o => true) === 0 && ops[0].k === 'fill', n: fills.length, colors, codeText: [...new Set(codeText)],
                 svgFill: svg.includes('fill="#CFE2F7"'), pressed: document.querySelector('[data-fill="1"]').getAttribute('aria-pressed'),
                 xl: { G17: fillOf('G17') > 2, G21: fillOf('G21') > 2, E17: fillOf('E17'), border: borderOf('G19') === borderOf('F19') } };
    }""")
    print("off", off, r)
    assert off == 0
    assert r["first"] and r["pressed"] == "true"
    days = 4 + 4 + 1                                   # AL, EL, MC, CT, 4 Sundays (RD), 1 PH
    assert r["n"] == days * 5, r["n"]                  # 5 time-code rows per day
    assert r["colors"] == sorted({"CFE2F7", "FFE9A8", "F7CFD2", "E6D8C8", "D9DEE3", "E9D5F5"}), r["colors"]
    assert r["codeText"] == ["000000"], r["codeText"]  # text stays black
    assert r["svgFill"]
    assert r["xl"]["G17"] and r["xl"]["G21"] and r["xl"]["E17"] <= 2 and r["xl"]["border"], r["xl"]
    br.close()

print("errors:", errors)
assert not errors
print("OK")
