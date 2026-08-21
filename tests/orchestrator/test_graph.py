# tests/orchestrator/test_graph.py — end-to-end graph test (Member 3)
import pytest
from src.orchestrator.run_pipeline import run_pipeline


@pytest.mark.slow
def test_full_pipeline_runs():
    """The whole LangGraph pipeline runs on PBMC3k and produces annotations."""
    final = run_pipeline("data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")
    assert len(final["annotations"]) >= 2
    assert all(a.confidence in ("HIGH", "MED", "LOW") for a in final["annotations"])
    # at least one claim should be verified
    assert any(c.verified for c in final["claims"])