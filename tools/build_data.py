#!/usr/bin/env python3
"""Pack the project files into app-data.js so the app also works when index.html is opened
straight from a folder (file://), where the browser does not allow it to read the JSON files.

Run after changing anything in packages/, holidays/ or templates/:
    python3 tools/build_data.py

When the app is served (GitHub Pages or a local server) it reads the JSON files first and uses
app-data.js only as a fallback, so an updated project file on GitHub still takes effect.
"""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = {"json": {}, "bin": {}}
for folder in ("packages", "holidays", "templates"):
    for f in sorted((ROOT / folder).glob("*")):
        rel = f"{folder}/{f.name}"
        if f.suffix == ".json":
            data["json"][rel] = json.loads(f.read_text(encoding="utf-8"))
        elif f.suffix in (".xlsx", ".jpeg", ".jpg", ".png"):
            data["bin"][rel] = base64.b64encode(f.read_bytes()).decode()
js = "/* Made by tools/build_data.py - do not edit by hand. */\nwindow.TS_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
(ROOT / "app-data.js").write_text(js, encoding="utf-8")
print("app-data.js", len(js) // 1024, "KB,", len(data["json"]), "json,", len(data["bin"]), "binary")
