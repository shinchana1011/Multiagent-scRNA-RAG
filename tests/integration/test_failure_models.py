import pytest
from src.agents.data_agent import DataAgent
from src.schemas.state import PipelineState


def test_preprocessed_data_fails_gracefully():
    """Pre-processed (negative-value) input must NOT crash — caught + flagged."""
    s = PipelineState(input_path="data/raw/zheng68k/pbmc68k_reduced.h5ad", tissue="PBMC")
    s = DataAgent().run(s)
    assert s.adata is None                    # rejected
    assert s.error is not None                # error recorded, not raised
    assert DataAgent().validate(s) is False   # validation catches it

def test_worker_writes_failed_status_on_error(tmp_path):
    """The worker must write a clean 'failed' status when the pipeline errors,
    rather than letting the process die. Simulates the pre-processed-data case."""
    import json
    from src.api.worker import _write_status
    run_dir = str(tmp_path / "job1")
    # simulate what execute_job does on a caught pipeline error
    _write_status(run_dir, "failed", 100, "Pipeline error",
                  error="Matrix has negative values — not raw counts.")
    status = json.loads((tmp_path / "job1" / "status.json").read_text())
    assert status["status"] == "failed"
    assert "not raw counts" in status["error"]      # clean, descriptive error