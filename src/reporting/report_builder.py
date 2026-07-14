# src/reporting/report_builder.py — build all report artifacts into a run folder (Member 4)
from __future__ import annotations
import csv, json
from pathlib import Path
from src.reporting.figures import plot_umap_confidence
from src.reporting.methods_section import generate_methods
from src.reporting.citations import collect_citations, format_citations
from src.reporting.exporters import export_json, export_html, export_pdf
from src.reporting.composition import compute_composition, composition_summary, plot_composition
from src.reporting.scorecard import compute_scorecard, scorecard_summary

def build_reports(final, run_dir: str, tissue: str, disease: str) -> dict:
    run = Path(run_dir); run.mkdir(parents=True, exist_ok=True)
    cfg = final["config"].model_dump() if hasattr(final["config"], "model_dump") else vars(final["config"])
    anns = [{"cluster_id": a.cluster_id, "cell_type": a.cell_type, "confidence": a.confidence,
             "cell_state": a.cell_state, "marker_genes": a.marker_genes,
             "method_votes": a.method_votes, "sources": a.sources} for a in final["annotations"]]
    claims = [{"parameter": c.parameter, "value": c.value, "pmid": c.pmid,
               "verified": c.verified, "confidence": c.confidence} for c in final["claims"]]

    umap = plot_umap_confidence(final["adata"], anns, str(run / "umap_confidence.png"))  # FR-20
    methods = generate_methods(cfg, claims)                                              # FR-21
    cits = collect_citations(claims, anns)
    citation_text = format_citations(cits)                                               # FR-22
    (run / "methods.txt").write_text(methods, encoding="utf-8")
    (run / "citations.txt").write_text(citation_text, encoding="utf-8")

    # --- novelty: cell-type composition profiling (deviation flagging, non-diagnostic) ---
    composition = compute_composition(final["adata"], anns)
    comp_summary = composition_summary(composition)
    comp_png = plot_composition(composition, str(run / "composition.png"))
    (run / "composition.txt").write_text(comp_summary, encoding="utf-8")

    # --- novelty: run reliability scorecard ---
    ilisi = None  # optional: pass a real iLISI if you compute it for batch-corrected runs
    scorecard = compute_scorecard(anns, claims, ilisi=ilisi)
    score_summary = scorecard_summary(scorecard)
    (run / "scorecard.txt").write_text(score_summary, encoding="utf-8")

    payload = {"title": f"scRNA-seq Report — {tissue} {disease}".strip(),
               "tissue": tissue, "disease": disease, "config": cfg,
               "methods": methods, "citations": citation_text,
               "annotations": anns, "claims": claims,
               "composition": composition,            # <-- add
               "composition_summary": comp_summary, "scorecard": scorecard,                 # <-- add
               "scorecard_summary": score_summary,     }  # <-- add
    
    export_json(payload, str(run / "report.json"))                                       # FR-23
    export_html(payload, str(run / "report.html"))
    export_pdf(payload, umap, str(run / "report.pdf"))

    _write_metrics_csv(run, anns, claims)          # CSV metrics
    try:
        final.get("log") and (run / "audit_trail.json").write_text(
            json.dumps(final["log"], indent=2, default=str))
    except Exception:
        pass
    return payload


def _write_metrics_csv(run: Path, anns: list[dict], claims: list[dict]) -> None:
    conf = {"HIGH": 0, "MED": 0, "LOW": 0}
    for a in anns:
        conf[a["confidence"]] = conf.get(a["confidence"], 0) + 1
    with open(run / "metrics.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerow(["n_clusters", len(anns)])
        w.writerow(["high", conf["HIGH"]]); w.writerow(["med", conf["MED"]]); w.writerow(["low", conf["LOW"]])
        w.writerow(["review_queue", conf["LOW"]])
        w.writerow(["verified_claims", sum(c["verified"] for c in claims)])
        w.writerow(["total_claims", len(claims)])