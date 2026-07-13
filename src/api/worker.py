# src/api/worker.py — pipeline execution in a separate process (Member 4, Task 2)
from __future__ import annotations
import json, traceback
from pathlib import Path


def _write_status(run_dir: str, status: str, progress: int, message: str, error: str | None = None):
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    (Path(run_dir) / "status.json").write_text(json.dumps(
        {"status": status, "progress": progress, "message": message, "error": error}))


def execute_job(job_id: str, file_path: str, tissue: str, disease: str, run_dir: str) -> None:
    """Top-level, picklable target for multiprocessing. Runs the full pipeline
    (clean process => rpy2/SingleR works) and writes all outputs to run_dir."""
    from src.config.logging_config import setup_logging
    setup_logging(f"{run_dir}/run.log")
    try:
        _write_status(run_dir, "running", 15, "Running multi-agent pipeline")
        from src.orchestrator.run_pipeline import run_pipeline
        final = run_pipeline(file_path, tissue=tissue, disease=disease)   # Member 3

        _write_status(run_dir, "running", 65, "Writing results")
        _dump_results(final, run_dir)

        _write_status(run_dir, "running", 80, "Generating reports")
        from src.reporting.report_builder import build_reports          # Member 4 Task 4
        build_reports(final, run_dir, tissue=tissue, disease=disease)

        _write_status(run_dir, "done", 100, "Complete")
    except Exception as e:                                              # noqa: BLE001
        _write_status(run_dir, "failed", 100, "Pipeline failed",
                      error=f"{e}\n{traceback.format_exc()}")


def _dump_results(final, run_dir: str) -> None:
    anns = [{"cluster_id": a.cluster_id, "cell_type": a.cell_type,
             "confidence": a.confidence, "cell_state": a.cell_state,
             "marker_genes": a.marker_genes, "method_votes": a.method_votes,
             "sources": a.sources} for a in final["annotations"]]
    claims = [{"parameter": c.parameter, "value": c.value, "pmid": c.pmid,
               "verified": c.verified, "confidence": c.confidence} for c in final["claims"]]
    (Path(run_dir) / "results.json").write_text(json.dumps({
        "n_clusters": len(anns), "annotations": anns, "claims": claims,
        "review_queue": [a["cluster_id"] for a in anns if a["confidence"] == "LOW"],
    }, default=str, indent=2))
    # persist Member 1's UMAP AnnData for figure regeneration
    try:
        final["adata"].write(str(Path(run_dir) / "adata.h5ad"))
    except Exception:
        pass