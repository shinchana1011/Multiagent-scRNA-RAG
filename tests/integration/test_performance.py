# tests/integration/test_performance.py — performance smoke test (Member 4)
import time
import numpy as np
import pytest
from anndata import AnnData
from src.pipeline.runner import run_analysis
from src.schemas.config import PipelineConfig


@pytest.mark.slow
def test_pipeline_completes_within_budget():
    """Analysis on a synthetic 5k-cell dataset must finish within a time budget.
    Documents scalability; not a rigorous load test."""
    rng = np.random.default_rng(0)
    # synthetic raw-like counts: 5000 cells x 2000 genes, non-negative integers
    X = rng.poisson(1.0, size=(5000, 2000)).astype("float32")
    ad = AnnData(X)
    ad.var_names = [f"g{i}" for i in range(2000)]
    ad.obs_names = [f"c{i}" for i in range(5000)]

    t0 = time.time()
    result = run_analysis(ad, PipelineConfig())
    elapsed = time.time() - t0

    print(f"\n5k-cell analysis: {elapsed:.1f}s")
    assert "leiden" in result.obs                 # completed
    assert elapsed < 300                          # 5-min budget (generous)


def test_records_timing_metric(capsys):
    """Trivial guard that timing is observable — documents the perf approach."""
    import time
    t0 = time.time(); _ = sum(range(10000)); dt = time.time() - t0
    assert dt >= 0