# src/reporting/exporters.py — PDF / HTML / JSON export (Member 4, FR-23 + novelty)
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


def _conf_color(c: str) -> str:
    return {"HIGH": "#2E6E6A", "MED": "#E8A33D", "LOW": "#C0504D"}.get(c, "#666")


def export_html(payload: dict, out: str) -> str:
    sc = payload.get("scorecard", {})
    # --- scorecard block ---
    score_block = ""
    if sc:
        score_block = f"""<div class="score">
<div class="score-num">{sc.get('reliability_score','?')}<span>/100</span></div>
<div class="score-grade">Grade {sc.get('grade','')}</div>
<div class="score-detail">{payload.get('scorecard_summary','')}</div></div>"""

    # --- annotation rows with colour + evidence (markers) ---
    ann_rows = "".join(
        f"<tr><td>{a['cluster_id']}</td><td>{a['cell_type']}</td>"
        f"<td style='color:{_conf_color(a['confidence'])};font-weight:600'>{a['confidence']}</td>"
        f"<td>{a.get('cell_state') or ''}</td>"
        f"<td class='markers'>{', '.join(a['marker_genes'][:6])}</td></tr>"
        for a in payload["annotations"])

    # --- marker-gene evidence panel (HIGH clusters only, FR-19 deepened) ---
    evidence = ""
    for a in payload["annotations"]:
        if a["confidence"] == "HIGH":
            src = "; ".join(f"{k}: {v}" for k, v in a.get("sources", {}).items())
            evidence += (f"<div class='ev'><b>Cluster {a['cluster_id']} — {a['cell_type']}</b>"
                         f"<br><span class='ev-markers'>{', '.join(a['marker_genes'][:8])}</span>"
                         f"<br><span class='ev-src'>Evidence: {src}</span></div>")

    # --- composition block ---
    comp_rows = "".join(
        f"<tr><td>{c['cell_type']}</td><td>{c['fraction']:.1%}</td>"
        f"<td>{c['status']}</td></tr>" for c in payload.get("composition", []))
    comp_block = ""
    if comp_rows:
        comp_block = f"""<h2>Cell-type composition</h2>
<p>{payload.get('composition_summary','')}</p>
<img src="composition.png" style="max-width:640px">
<table><tr><th>Cell type</th><th>Fraction</th><th>vs healthy reference</th></tr>
{comp_rows}</table>"""

    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>{payload['title']}</title><style>
body{{font-family:Arial,Helvetica,sans-serif;margin:40px;color:#222;line-height:1.5}}
h1{{color:#1F3A5F}} h2{{color:#2E6E6A;border-bottom:2px solid #eef3f7;padding-bottom:4px}}
table{{border-collapse:collapse;width:100%;margin:8px 0}}
th,td{{border:1px solid #ccc;padding:6px;font-size:13px;text-align:left}}
th{{background:#f0f3f7}} .markers{{color:#555;font-size:12px}}
.score{{background:linear-gradient(90deg,#2E6E6A,#1F3A5F);color:#fff;padding:20px;
  border-radius:12px;margin:16px 0}}
.score-num{{font-size:44px;font-weight:700}} .score-num span{{font-size:20px;opacity:.7}}
.score-grade{{font-size:16px;opacity:.9;margin-bottom:6px}} .score-detail{{font-size:13px;opacity:.9}}
.ev{{background:#f7faf9;border-left:3px solid #2E6E6A;padding:8px 12px;margin:6px 0;font-size:13px}}
.ev-markers{{color:#2E6E6A;font-family:monospace}} .ev-src{{color:#777;font-size:12px}}
</style></head><body>
<h1>{payload['title']}</h1>
{score_block}
<h2>Annotated UMAP</h2>
<img src="umap_confidence.png" style="max-width:660px">
<h2>Methods</h2><p>{payload['methods']}</p>
<h2>Annotations</h2>
<table><tr><th>Cluster</th><th>Cell type</th><th>Confidence</th><th>State</th><th>Top markers</th></tr>
{ann_rows}</table>
<h2>Marker-gene evidence (HIGH-confidence clusters)</h2>{evidence or '<p>None.</p>'}
{comp_block}
<h2>Citations</h2><pre>{payload['citations']}</pre>
</body></html>"""
    Path(out).write_text(html, encoding="utf-8")
    return out


def export_pdf(payload: dict, umap_png: str, out: str) -> str:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(out, pagesize=A4)
    flow = [Paragraph(payload["title"], styles["Title"]), Spacer(1, 10)]

    # --- scorecard ---
    sc = payload.get("scorecard", {})
    if sc:
        flow += [Paragraph("Run Reliability Scorecard", styles["Heading2"])]
        score_data = [["Reliability score", f"{sc.get('reliability_score','?')}/100 (grade {sc.get('grade','')})"],
                      ["HIGH-confidence clusters", f"{sc.get('pct_high_confidence','?')}% ({sc.get('n_high',0)})"],
                      ["Parameters verified", f"{sc.get('pct_claims_verified','?')}% ({sc.get('verified_claims',0)}/{sc.get('total_claims',0)})"],
                      ["Flagged for review", f"{sc.get('n_low',0)} cluster(s)"]]
        if sc.get("ilisi") is not None:
            score_data.append(["Batch iLISI", f"{sc['ilisi']} (target > 1.5)"])
        st = Table(score_data, hAlign="LEFT", colWidths=[6 * cm, 8 * cm])
        st.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3f7")),
                                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                                ("FONTSIZE", (0, 0), (-1, -1), 9)]))
        flow += [st, Spacer(1, 12)]

    if Path(umap_png).exists():
        flow += [Paragraph("Annotated UMAP", styles["Heading2"]),
                 Image(umap_png, width=15 * cm, height=11 * cm), Spacer(1, 12)]

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
    flow += [t, Spacer(1, 12)]

    # --- marker evidence panel (HIGH only) ---
    high = [a for a in payload["annotations"] if a["confidence"] == "HIGH"]
    if high:
        flow += [Paragraph("Marker-gene evidence (HIGH-confidence clusters)", styles["Heading2"])]
        for a in high:
            src = "; ".join(f"{k}: {v}" for k, v in a.get("sources", {}).items())
            flow += [Paragraph(f"<b>Cluster {a['cluster_id']} — {a['cell_type']}</b>: "
                               f"{', '.join(a['marker_genes'][:8])}<br/>"
                               f"<font size=8 color='#777'>Evidence: {src}</font>",
                               styles["BodyText"]), Spacer(1, 4)]
        flow += [Spacer(1, 8)]

    # --- composition ---
    if payload.get("composition_summary"):
        flow += [Paragraph("Cell-type composition", styles["Heading2"]),
                 Paragraph(payload["composition_summary"], styles["BodyText"]), Spacer(1, 8)]
        comp_png = str(Path(out).parent / "composition.png")
        if Path(comp_png).exists():
            flow += [Image(comp_png, width=14 * cm, height=8 * cm), Spacer(1, 12)]

    flow += [Paragraph("Citations", styles["Heading2"]),
             Paragraph(payload["citations"].replace("\n", "<br/>"), styles["BodyText"])]
    doc.build(flow)
    return out