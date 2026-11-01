#!/usr/bin/env python3
"""Turn a k8s-security-audit Markdown report into a single self-contained HTML file.

Usage: python3 report_to_html.py REPORT.md [OUT.html]

No dependencies beyond Python 3. The Markdown renderer (marked, MIT) is inlined,
so the HTML works offline and loads nothing from the network. Open it in a
browser and use Print > Save as PDF for a PDF.
"""
import html
import json
import pathlib
import sys

if len(sys.argv) < 2:
    sys.exit(__doc__)
src = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".html")
md = src.read_text(encoding="utf-8")
marked = (pathlib.Path(__file__).parent / "vendor" / "marked.min.js").read_text(encoding="utf-8")
title = next((l[2:].strip() for l in md.splitlines() if l.startswith("# ")), src.stem)

CSS = """
:root{--bg:#fff;--fg:#1f2328;--muted:#59636e;--line:#d1d9e0;--code:#f6f8fa;--crit:#cf222e;--high:#bc4c00;--med:#9a6700;--low:#59636e}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--line:#30363d;--code:#161b22;--crit:#ff7b72;--high:#ffa657;--med:#d29922;--low:#9198a1}}
body{background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;max-width:900px;margin:0 auto;padding:32px 16px}
h1{font-size:28px;border-bottom:1px solid var(--line);padding-bottom:8px}
h2{font-size:21px;border-bottom:1px solid var(--line);padding-bottom:6px;margin-top:36px}
h3{font-size:17px;margin-top:28px}
a{color:#0969da}
code{background:var(--code);padding:1px 5px;border-radius:4px;font-size:13px}
pre{background:var(--code);border:1px solid var(--line);border-radius:6px;padding:12px;overflow-x:auto}
pre code{padding:0;background:none}
table{border-collapse:collapse;width:100%;font-size:13px;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
.sev-Critical{color:var(--crit);font-weight:700}.sev-High{color:var(--high);font-weight:700}
.sev-Medium{color:var(--med);font-weight:700}.sev-Low{color:var(--low);font-weight:700}
@media print{body{max-width:none;padding:0;font-size:11pt}pre,table,h3{break-inside:avoid}a{color:inherit}}
"""

JS = """
const md = JSON.parse(document.getElementById('md').textContent);
document.getElementById('report').innerHTML = marked.parse(md);
document.querySelectorAll('h3, td').forEach(el => {
  el.innerHTML = el.innerHTML.replace(/\\b(Critical|High|Medium|Low)\\b/, '<span class="sev-$1">$1</span>');
});
"""

md_json = json.dumps(md).replace("</", "<\\/")
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head>
<body><main id="report"><pre>{html.escape(md)}</pre></main>
<script id="md" type="application/json">{md_json}</script>
<script>{marked}</script><script>{JS}</script>
</body></html>
"""
out.write_text(page, encoding="utf-8")
print(out)
