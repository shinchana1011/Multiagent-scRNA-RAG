# src/pipeline/reduce.py — PCA, Harmony, neighbours (Member 1, Task 4)
from __future__ import annotations

import scanpy as sc
from anndata import AnnData
from loguru import logger


def run_pca(adata: AnnData, n_comps: int = 50, random_state: int = 0) -> AnnData:
    """PCA on the scaled HVG matrix. n_comps is clamped to a valid range."""
    n_comps = min(n_comps, adata.n_obs - 1, adata.n_vars - 1)
    sc.pp.pca(adata, n_comps=n_comps, random_state=random_state)
    logger.info("PCA: {} components", n_comps)
    return adata


def run_harmony(adata: AnnData, batch_key: str) -> AnnData:
    """Harmony batch correction. Writes adata.obsm['X_pca_harmony'].
    Call ONLY when the dataset is multi-batch (decided by the runner)."""
    sc.external.pp.harmony_integrate(adata, batch_key)
    logger.info("Harmony batch correction on '{}'", batch_key)
    return adata


def build_neighbors(adata: AnnData, n_pcs: int = 50,
                     use_rep: str = "X_pca", random_state: int = 0) -> AnnData:
    """kNN graph from the chosen embedding.
    use_rep = 'X_pca_harmony' if Harmony ran, else 'X_pca'."""
    n_pcs = min(n_pcs, adata.obsm[use_rep].shape[1])
    sc.pp.neighbors(adata, n_pcs=n_pcs, use_rep=use_rep, random_state=random_state)
    logger.info("Neighbour graph: n_pcs={}, use_rep={}", n_pcs, use_rep)
    return adata
