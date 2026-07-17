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
        if final.get("error"):
            _write_status(run_dir, "failed", 100, "Pipeline error", error=final["error"])
            return
        _write_status(run_dir, "running", 65, "Writing results")
        _dump_results(final, run_dir)

        _write_status(run_dir, "running", 80, "Generating reports")
        try:
            from src.reporting.report_builder import build_reports      # Member 4 Task 4
            build_reports(final, run_dir, tissue=tissue, disease=disease)
        except Exception as re:                                          # noqa: BLE001
            import traceback
            (Path(run_dir) / "report_error.log").write_text(
                f"{re}\n{traceback.format_exc()}")
            # analysis succeeded; reporting is best-effort
        _write_status(run_dir, "done", 100, "Complete (see report_error.log if reports missing)")
    except Exception as e:                                              # noqa: BLE001
        _write_status(run_dir, "failed", 100, "Pipeline failed",
                      error=f"{e}\n{traceback.format_exc()}")


def _dump_results(final, run_dir: str) -> None:
    from src.api.adapters import state_to_results
    import json
    from pathlib import Path
    (Path(run_dir) / "results.json").write_text(
        json.dumps(state_to_results(final), default=str, indent=2))
    try:
        final["adata"].write(str(Path(run_dir) / "adata.h5ad"))
    except Exception:
        pass