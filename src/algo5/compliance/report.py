from __future__ import annotations
from pathlib import Path
import pandas as pd, html
def build_html_report(run_id: str, metrics: dict, trades: pd.DataFrame, outdir: str | Path = ".reports") -> Path:
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{run_id}.html"
    rows = "\n".join(f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>" for k,v in metrics.items())
    trows = ""
    if not trades.empty:
        cols = list(trades.columns)[:6]
        trows = "<table border='1'><tr>" + "".join(f"<th>{html.escape(str(c))}</th>" for c in cols) + "</tr>"
        for _,r in trades.iloc[:200].iterrows():
            trows += "<tr>" + "".join(f"<td>{html.escape(str(r[c]))}</td>" for c in cols) + "</tr>"
        trows += "</table>"
    html_doc = f"""<html><head><meta charset='utf-8'><title>ALGO5 Report {html.escape(run_id)}</title></head>
    <body><h1>Run {html.escape(run_id)}</h1><h2>Metrics</h2><table border='1'>{rows}</table>
    <h2>Trades (first 200)</h2>{trows}</body></html>"""
    path.write_text(html_doc, encoding="utf-8"); return path
