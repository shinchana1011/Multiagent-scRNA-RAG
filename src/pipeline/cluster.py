# src/pipeline/cluster.py — Leiden clustering (Member 1, Task 5)
from __future__ import annotations

import scanpy as sc
from anndata import AnnData
from loguru import logger


def run_leiden(adata: AnnData, resolution: float = 1.0, random_state: int = 0) -> AnnData:
    """Cluster cells with the Leiden algorithm on the neighbors graph.

    Must run AFTER compute_neighbors(). Uses the igraph backend — scanpy 1.12's
    recommended flavor — since the old default (flavor="leidenalg") is deprecated
    and throws a FutureWarning.
    """
    sc.tl.leiden(
        adata,
        resolution=resolution,
        flavor="igraph",
        n_iterations=2,
        directed=False,
        random_state=random_state,
    )
    n_clusters = adata.obs["leiden"].nunique()
    logger.info("Leiden clustering: {} clusters (resolution={})", n_clusters, resolution)
    return adata
