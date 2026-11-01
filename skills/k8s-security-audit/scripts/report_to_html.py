#!/usr/bin/env python3
"""Turn a k8s-security-audit Markdown report into a single self-contained HTML file.

Usage: python3 report_to_html.py REPORT.md [OUT.html]

Standard library only. The output is static HTML with inline CSS: no JavaScript,
no external requests, works offline. Open it in a browser and use
Print > Save as PDF for a PDF.

Supports the Markdown the report template uses: headings, paragraphs, bullet
and numbered lists, pipe tables, fenced code blocks, inline code, bold, italics
and links.
"""
import html
import pathlib
import re
import sys

SEVERITIES = ("Critical", "High", "Medium", "Low")


def inline(text):
    """Escape text and apply inline Markdown (code, bold, italics, links)."""
    codes = []

    def stash(m):
        codes.append("<code>" + html.escape(m.group(1)) + "</code>")
        return "\x00%d\x00" % (len(codes) - 1)

    s = re.sub(r"`([^`]+)`", stash, text)
    s = html.escape(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"(?<![\"'>])(https?://[^\s<)\x00]+)", r'<a href="\1">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    for sev in SEVERITIES:
        s = re.sub(r"\b%s\b" % sev, '<span class="sev-%s">%s</span>' % (sev, sev), s, count=1)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)


def table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, body = cells[0], [r for r in cells[2:]]
    h = "".join("<th>%s</th>" % inline(c) for c in head)
    b = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r) for r in body)
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (h, b)


def render(md):
    lines = md.splitlines()
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            lang = stripped[3:].strip()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            cls = ' class="lang-%s"' % html.escape(lang) if lang else ""
            out.append("<pre><code%s>%s</code></pre>" % (cls, html.escape("\n".join(code))))
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush()
            n = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (n, inline(m.group(2)), n))
            i += 1
            continue
        if stripped in ("---", "***"):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(table(rows))
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            flush()
            ordered = m.group(2)[0].isdigit()
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines):
                m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                if m:
                    items.append(m.group(3))
                elif lines[i].strip() and lines[i].startswith((" ", "\t")) and items:
                    items[-1] += " " + lines[i].strip()
                else:
                    break
                i += 1
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(t) for t in items), tag))
            continue
        if not stripped:
            flush()
        else:
            para.append(stripped)
        i += 1
    flush()
    return "\n".join(out)


CSS = """
:root{--bg:#fff;--fg:#1f2328;--line:#d1d9e0;--code:#f6f8fa;--link:#0969da;--crit:#cf222e;--high:#bc4c00;--med:#9a6700;--low:#59636e}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--line:#30363d;--code:#161b22;--link:#4493f8;--crit:#ff7b72;--high:#ffa657;--med:#d29922;--low:#9198a1}}
body{background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;max-width:900px;margin:0 auto;padding:32px 16px}
h1{font-size:28px;border-bottom:1px solid var(--line);padding-bottom:8px}
h2{font-size:21px;border-bottom:1px solid var(--line);padding-bottom:6px;margin-top:36px}
h3{font-size:17px;margin-top:28px}
a{color:var(--link);overflow-wrap:anywhere}
code{background:var(--code);padding:1px 5px;border-radius:4px;font-size:13px;overflow-wrap:anywhere}
pre{background:var(--code);border:1px solid var(--line);border-radius:6px;padding:12px;overflow-x:auto}
pre code{padding:0;background:none;overflow-wrap:normal}
table{border-collapse:collapse;width:100%;font-size:13px;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
.sev-Critical{color:var(--crit);font-weight:700}.sev-High{color:var(--high);font-weight:700}
.sev-Medium{color:var(--med);font-weight:700}.sev-Low{color:var(--low);font-weight:700}
@media print{body{max-width:none;padding:0;font-size:11pt}pre,table,h3{break-inside:avoid}a{color:inherit}}
"""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".html")
    md = src.read_text(encoding="utf-8")
    title = next((l[2:].strip() for l in md.splitlines() if l.startswith("# ")), src.stem)
    page = (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title><style>%s</style></head>\n<body><main>\n%s\n</main></body></html>\n"
        % (html.escape(title), CSS, render(md))
    )
    out.write_text(page, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
