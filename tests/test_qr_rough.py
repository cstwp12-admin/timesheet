"""QR covering on rough office-copier scans, and version numbers in step.

    python3 -m http.server 8765 &
    python3 tests/test_qr_rough.py [outdir]

A timesheet with the summary QR is printed, then "copied" at 200 dpi in black and white with
blur, specks, a small skew and the page turned, so badly that the QR may not decode. The app
must still find the QR by its look and blank it in the HQ PDF. A page printed with no QR but
with a stamp-like ring must be left alone. Also: APP_BUILD = version.json build = sw.js cache.
"""
import base64, json, random, re, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "http://localhost:8765/index.html"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/ts-test-out"); OUT.mkdir(exist_ok=True, parents=True)
errors = []

# version numbers in step
html = (ROOT / "index.html").read_text(); build = re.search(r'APP_BUILD = "([\d.]+)"', html).group(1)
assert json.loads((ROOT / "version.json").read_text())["build"] == build, "version.json build"
assert f'const C = "ts-v{build}"' in (ROOT / "sw.js").read_text(), "sw.js cache name"

B64 = "const b = new Uint8Array(await x.arrayBuffer()); let s=''; for (let i=0;i<b.length;i+=8192) s += String.fromCharCode(...b.subarray(i,i+8192)); return btoa(s);"
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e))); pg.on("dialog", lambda d: d.accept())
    pg.goto(URL); pg.wait_for_selector("#w-name")
    pg.fill("#w-name", "Ts. Adam Lee Chee Wai"); pg.click("#w-go")
    d = pg.evaluate("async () => { S.ui.y=2026; S.ui.m=8; save(); fillMonth(false); S.profile.status='Resident Engineer'; S.role='compiler'; (S.over[S.pkg]=S.over[S.pkg]||{}).pageId='sum'; save(); const x = await makePDF([sheetFor(2026,8)], 't'); " + B64 + " }")
    (OUT / "print_sum.pdf").write_bytes(base64.b64decode(d))
    subprocess.run(["pdftoppm", "-r", "200", "-gray", "-singlefile", str(OUT / "print_sum.pdf"), str(OUT / "r")], check=True)
    random.seed(3); pages = []
    for kind in ["qr", "none"]:
        im = Image.open(OUT / "r.pgm").convert("L")
        if kind == "none":
            w, h = im.size; dr = ImageDraw.Draw(im); dr.rectangle((int(w * .85), int(h * .86), w, h), fill=255)
            dr.ellipse((int(w * .70), int(h * .66), int(w * .80), int(h * .80)), outline=60, width=6)
        im = im.rotate(-90, expand=True).rotate(-0.8, fillcolor=255).filter(ImageFilter.GaussianBlur(1.6))
        px = im.load(); w, h = im.size
        for _ in range(int(w * h * 0.004)): px[random.randrange(w), random.randrange(h)] = random.choice([0, 255])
        pages.append(im.point(lambda v: 0 if v < 120 else 255).convert("1"))
    pages[0].save(OUT / "rough.pdf", "PDF", resolution=200, save_all=True, append_images=pages[1:])
    b64 = base64.b64encode((OUT / "rough.pdf").read_bytes()).decode()
    r = pg.evaluate("""async (b64) => { team = []; addTeamRecord(dataRecord());
        const bin = atob(b64), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
        await addBundle([new File([u], 'rough.pdf', {type: 'application/pdf'})]);
        const it = (await bundleItems())[0]; $('#b-month').value = '2026-09'; $('#b-cover').checked = false; $('#b-footer').checked = false;
        const res = await buildBundlePDF(), b = new Uint8Array(res.bytes); let s=''; for (let i=0;i<b.length;i+=8192) s += String.fromCharCode(...b.subarray(i,i+8192));
        return { qrb: it.qrb.map(x => !!x), prot: it.prot, pdf: btoa(s) }; }""", b64)
    (OUT / "rough_hq.pdf").write_bytes(base64.b64decode(r.pop("pdf")))
    print(r)
    assert r["qrb"] == [True, False], r["qrb"]       # QR page found; the stamp is not taken for a QR
    assert r["prot"][0] == 270, r["prot"]
    br.close()

subprocess.run(["pdftoppm", "-r", "60", "-png", "-f", "1", "-l", "1", "-singlefile", str(OUT / "rough_hq.pdf"), str(OUT / "q")], check=True)
im = Image.open(OUT / "q.png").convert("L"); w, h = im.size
assert w > h, "turned to landscape"
corner = im.crop((int(w * .84), int(h * .83), int(w * .985), int(h * .975)))
dark = sum(1 for v in corner.getdata() if v < 100) / (corner.width * corner.height)
print("dark in QR corner", round(dark, 3))
assert dark < 0.03, dark
print("errors:", errors); assert not errors
print("OK")
