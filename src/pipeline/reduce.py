# src/pipeline/reduce.py — PCA, Harmony batch correction, neighbors (Member 1, Task 4)
from __future__ import annotations

import scanpy as sc
from anndata import AnnData
from loguru import logger


def run_pca(adata: AnnData, n_comps: int = 50, random_state: int = 0) -> AnnData:
    """Run PCA on the scaled HVG matrix (adata.X).

    Must run AFTER normalize() -> select_hvg() -> scale(). Writes adata.obsm["X_pca"].
    """
    n_comps = min(n_comps, adata.n_vars - 1, adata.n_obs - 1)
    sc.tl.pca(adata, n_comps=n_comps, random_state=random_state)
    logger.info("PCA computed ({} components)", n_comps)
    return adata


def integrate_harmony(adata: AnnData, batch_key: str, random_state: int = 0) -> AnnData:
    """Correct adata.obsm["X_pca"] for batch effects across `batch_key` (e.g. "patient").

    Only does anything for multi-batch datasets (e.g. the COVID cohort). Writes
    adata.obsm["X_pca_harmony"]; adata.obsm["X_pca"] is left untouched so the
    uncorrected embedding stays available for comparison.
    """
    if batch_key not in adata.obs.columns:
        raise KeyError(f"batch_key '{batch_key}' not found in adata.obs")
    n_batches = adata.obs[batch_key].nunique()
    if n_batches < 2:
        logger.warning("Only {} batch(es) in '{}' — Harmony has nothing to correct for; skipping.",
                        n_batches, batch_key)
        return adata
    sc.external.pp.harmony_integrate(adata, key=batch_key, random_state=random_state)
    logger.info("Harmony-integrated across {} batches (key='{}')", n_batches, batch_key)
    return adata


def compute_neighbors(adata: AnnData, n_neighbors: int = 15, random_state: int = 0) -> AnnData:
    """Build the kNN graph used later for clustering/UMAP.

    Uses the Harmony-corrected embedding when present (adata.obsm["X_pca_harmony"]),
    otherwise falls back to the plain PCA embedding (adata.obsm["X_pca"]).
    """
    use_rep = "X_pca_harmony" if "X_pca_harmony" in adata.obsm else "X_pca"
    sc.pp.neighbors(adata, use_rep=use_rep, n_neighbors=n_neighbors, random_state=random_state)
    logger.info("Neighbors graph computed (use_rep='{}', n_neighbors={})", use_rep, n_neighbors)
    return adata
