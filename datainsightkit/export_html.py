from html import escape
from .export_json import render_json

def row(cells):
    return "<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in cells) + "</tr>"

def render_html(report):
    profiles = "".join(row((name, col["kind"], col["missing"], col["distinct"]))
                       for name, col in report["columns"].items())
    pairs = "".join(row((pair["left"], pair["right"], f'{pair["pearson_r"]:.3f}', pair["pairs"]))
                    for pair in report["associations"][:20])
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>DataInsightKit report</title>
<style>body{{font:16px system-ui;max-width:66rem;margin:3rem auto;padding:0 1rem;color:#163442}}
table{{border-collapse:collapse;width:100%}}th,td{{padding:.55rem;text-align:left;border-bottom:1px solid #dbe4ea}}
pre{{overflow:auto;background:#f5f8fa;padding:1rem}}</style>
<h1>CSV profile</h1><p>{report['rows']} rows · {report['column_count']} columns · {report['quality']['duplicate_rows']} duplicate rows</p>
<h2>Column quality</h2><table><tr><th>Column</th><th>Type</th><th>Missing</th><th>Distinct</th></tr>{profiles}</table>
<h2>Numeric associations</h2><table><tr><th>Column</th><th>Column</th><th>Pearson r</th><th>Pairs</th></tr>{pairs}</table>
<details><summary>Full report</summary><pre>{escape(render_json(report))}</pre></details>
</html>"""
