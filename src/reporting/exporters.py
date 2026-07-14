# src/reporting/exporters.py — PDF / HTML / JSON export (Member 4, FR-23)
from __future__ import annotations
import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle)
from reportlab.lib import colors


def export_json(payload: dict, out: str) -> str:
    Path(out).write_text(json.dumps(payload, indent=2, default=str))
    return out


def export_html(payload: dict, out: str) -> str:
    rows = "".join(
        f"<tr><td>{a['cluster_id']}</td><td>{a['cell_type']}</td>"
        f"<td>{a['confidence']}</td><td>{a.get('cell_state') or ''}</td>"
        f"<td>{', '.join(a['marker_genes'][:5])}</td></tr>" for a in payload["annotations"])
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>{payload['title']}</title><style>
body{{font-family:Arial;margin:40px;color:#222}} table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:6px;font-size:13px}} th{{background:#f0f3f7}}
</style></head><body>
<h1>{payload['title']}</h1>
<img src="umap_confidence.png" style="max-width:640px"><h2>Methods</h2><p>{payload['methods']}</p>
<h2>Annotations</h2><table><tr><th>Cluster</th><th>Cell type</th><th>Confidence</th>
<th>State</th><th>Top markers</th></tr>{rows}</table>
<h2>Citations</h2><pre>{payload['citations']}</pre></body></html>"""
    Path(out).write_text(html, encoding="utf-8")
    return out


def export_pdf(payload: dict, umap_png: str, out: str) -> str:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(out, pagesize=A4)
    flow = [Paragraph(payload["title"], styles["Title"]), Spacer(1, 12)]
    if Path(umap_png).exists():
        flow += [Image(umap_png, width=15 * cm, height=11 * cm), Spacer(1, 12)]
    flow += [Paragraph("Methods", styles["Heading2"]),
             Paragraph(payload["methods"], styles["BodyText"]), Spacer(1, 12),
             Paragraph("Annotations", styles["Heading2"])]
    data = [["Cluster", "Cell type", "Conf", "State"]]
    for a in payload["annotations"]:
        data.append([a["cluster_id"], a["cell_type"], a["confidence"], a.get("cell_state") or "-"])
    t = Table(data, hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E6E6A")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                           ("FONTSIZE", (0, 0), (-1, -1), 8)]))
    flow += [t, Spacer(1, 12), Paragraph("Citations", styles["Heading2"]),
             Paragraph(payload["citations"].replace("\n", "<br/>"), styles["BodyText"])]
    doc.build(flow)
    return out