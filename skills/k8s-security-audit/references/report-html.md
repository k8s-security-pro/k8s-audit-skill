# HTML version of the report

After the Markdown report is saved, write a single-file HTML version next to it
with the same name and an `.html` extension. Same content, same order; this
file is only the shareable view.

Rules:
- One file, inline CSS from the skeleton below, no JavaScript, no external
  fonts, images or links other than the ones in the report text. It must work
  offline and print to PDF from any browser.
- Escape `<`, `>` and `&` in all report text, including inside code blocks.
- Map Markdown to plain HTML: headings to `h1`-`h3`, lists to `ul`/`ol`,
  pipe tables to `table` with a `thead`, fenced code to `<pre><code>`,
  inline code to `<code>`, bold to `<strong>`, links to `<a href>`.
- Wrap each severity word in finding titles and tables in
  `<span class="sev-Critical">Critical</span>` (and `sev-High`, `sev-Medium`,
  `sev-Low`).
- Use the report's `#` heading as the `<title>`.

Skeleton:

```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kubernetes security audit: CONTEXT</title>
<style>
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
</style></head>
<body><main>
<!-- report content here -->
</main></body></html>
```
