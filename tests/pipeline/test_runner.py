import numpy as np
from anndata import AnnData
from src.schemas.config import PipelineConfig
from src.pipeline.runner import run_analysis

def _synthetic(batches=None):
    rng = np.random.default_rng(0)
    X = rng.poisson(3.0, size=(200, 60)).astype("float32")
    a = AnnData(X)
    a.var_names = [f"MT-{i}" if i < 5 else f"GENE{i}" for i in range(60)]  # 5 mito genes
    a.obs_names = [f"cell{i}" for i in range(200)]
    if batches:
        a.obs["patient"] = np.resize(batches, 200)
    return a

def _small_cfg(**overrides):
    defaults = dict(min_genes=10, min_cells=1, mito_pct=50.0, n_hvg=30, n_pcs=10)
    defaults.update(overrides)
    return PipelineConfig(**defaults)

def test_run_analysis_end_to_end():
    adata = run_analysis(_synthetic(), _small_cfg())
    assert "leiden" in adata.obs
    assert "X_umap" in adata.obsm
    assert "rank_genes_groups" in adata.uns
    assert adata.raw is not None

def test_run_analysis_with_harmony_uses_corrected_rep():
    cfg = _small_cfg(use_harmony=True, batch_key="patient")
    adata = run_analysis(_synthetic(batches=["A", "B"]), cfg)
    assert adata.uns["neighbors"]["params"]["use_rep"] == "X_pca_harmony"

def test_run_analysis_skips_harmony_when_disabled():
    adata = run_analysis(_synthetic(batches=["A", "B"]), _small_cfg())
    assert adata.uns["neighbors"]["params"]["use_rep"] == "X_pca"
