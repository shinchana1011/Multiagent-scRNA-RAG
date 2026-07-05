# src/pipeline/normalize.py — normalization, HVG, scaling (Member 1, Task 3)
from __future__ import annotations

import scanpy as sc
from anndata import AnnData
from loguru import logger


def normalize(adata: AnnData, target_sum: float = 1e4) -> AnnData:
    """Library-size normalise, log1p, then freeze the log-normalised matrix in .raw.

    CONTRACT: .raw is set here — AFTER log1p, BEFORE HVG/scaling — so it holds the
    FULL gene set at log-normalised values. Member 3's annotation reads adata.raw.
    Do not reorder these steps.
    """
    sc.pp.normalize_total(adata, target_sum=target_sum)
    sc.pp.log1p(adata)
    adata.raw = adata                       # <-- the cross-team contract
    logger.info("Normalised to {:.0f} counts/cell + log1p; .raw frozen ({} genes)",
                target_sum, adata.raw.n_vars)
    return adata


def select_hvg(adata: AnnData, n_top_genes: int = 2000, flavor: str = "seurat") -> AnnData:
    """Select highly variable genes on log-normalised data and subset to them.

    Must run AFTER normalize() so .raw already holds all genes.
    """
    n_top_genes = min(n_top_genes, adata.n_vars)
    sc.pp.highly_variable_genes(adata, n_top_genes=n_top_genes, flavor=flavor)
    adata = adata[:, adata.var["highly_variable"]].copy()
    logger.info("Selected {} highly variable genes", adata.n_vars)
    return adata


def scale(adata: AnnData, max_value: float = 10.0) -> AnnData:
    """Z-score each gene (zero-centre, unit variance), clipped at max_value.

    Prepares the HVG matrix for PCA. Operates on adata.X only; adata.raw is untouched.
    """
    sc.pp.scale(adata, max_value=max_value)
    logger.info("Scaled HVG matrix (clip={})", max_value)
    return adata