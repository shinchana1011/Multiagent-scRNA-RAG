# src/pipeline/cluster.py — Leiden + UMAP (Member 1, Task 5)
from __future__ import annotations

import scanpy as sc
from anndata import AnnData
from loguru import logger


def run_leiden(adata: AnnData, resolution: float = 0.5, random_state: int = 0) -> AnnData:
    """Leiden community detection. Adds adata.obs['leiden'].
    resolution controls granularity; RAG will supply this value later."""
    sc.tl.leiden(adata, resolution=resolution, flavor="igraph",
                 n_iterations=2, directed=False, random_state=random_state)
    n = adata.obs["leiden"].nunique()
    logger.info("Leiden: {} clusters at resolution {}", n, resolution)
    return adata


def run_umap(adata: AnnData, random_state: int = 0) -> AnnData:
    """2D UMAP embedding from the neighbour graph. Adds adata.obsm['X_umap']."""
    sc.tl.umap(adata, random_state=random_state)
    logger.info("UMAP embedding computed")
    return adata
