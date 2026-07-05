import numpy as np
from anndata import AnnData
from src.pipeline.normalize import normalize, select_hvg, scale
from src.pipeline.reduce import run_pca, integrate_harmony, compute_neighbors

def _prepped(batches=None):
    rng = np.random.default_rng(0)
    X = rng.poisson(3.0, size=(200, 100)).astype("float32")
    a = AnnData(X)
    a.var_names = [f"GENE{i}" for i in range(100)]
    a.obs_names = [f"cell{i}" for i in range(200)]
    if batches:
        a.obs["patient"] = np.resize(batches, 200)
    return scale(select_hvg(normalize(a), n_top_genes=30))

def test_pca_writes_embedding():
    a = run_pca(_prepped(), n_comps=10)
    assert a.obsm["X_pca"].shape == (200, 10)

def test_harmony_corrects_multi_batch():
    a = run_pca(_prepped(batches=["A", "B"]), n_comps=10)
    a = integrate_harmony(a, batch_key="patient")
    assert "X_pca_harmony" in a.obsm
    assert "X_pca" in a.obsm            # uncorrected embedding preserved

def test_harmony_skips_single_batch():
    a = run_pca(_prepped(batches=["A"]), n_comps=10)
    a = integrate_harmony(a, batch_key="patient")
    assert "X_pca_harmony" not in a.obsm   # nothing to correct, no-op

def test_neighbors_uses_harmony_when_present():
    a = run_pca(_prepped(batches=["A", "B"]), n_comps=10)
    a = integrate_harmony(a, batch_key="patient")
    a = compute_neighbors(a)
    assert "distances" in a.obsp
    assert a.uns["neighbors"]["params"]["use_rep"] == "X_pca_harmony"
