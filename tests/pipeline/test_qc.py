import numpy as np
import pytest
from anndata import AnnData
from src.pipeline.qc import compute_qc_metrics, filter_cells_genes

def _synthetic():
    rng = np.random.default_rng(0)
    X = rng.poisson(3.0, size=(200, 60)).astype("float32")
    a = AnnData(X)
    a.var_names = [f"MT-{i}" if i < 5 else f"GENE{i}" for i in range(60)]  # 5 mito genes
    a.obs_names = [f"cell{i}" for i in range(200)]
    return a

def test_metrics_added():
    a = compute_qc_metrics(_synthetic())
    for col in ("n_genes_by_counts", "total_counts", "pct_counts_mt"):
        assert col in a.obs

def test_filter_reduces_cells():
    a = compute_qc_metrics(_synthetic())
    out = filter_cells_genes(a, min_genes=30, max_mito_pct=50)
    assert out.n_obs <= a.n_obs
    assert (out.obs["pct_counts_mt"] < 50).all()

def test_too_strict_raises():
    a = compute_qc_metrics(_synthetic())
    with pytest.raises(ValueError):
        filter_cells_genes(a, max_mito_pct=0.0)   # deletes everything