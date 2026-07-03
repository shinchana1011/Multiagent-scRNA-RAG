# src/pipeline/qc.py — quality control (Member 1, Task 2)
from __future__ import annotations

import scanpy as sc
from anndata import AnnData
from loguru import logger


def compute_qc_metrics(adata: AnnData, mito_prefix: str = "MT-") -> AnnData:
    """Flag mitochondrial genes and compute per-cell QC metrics.

    Adds to adata.obs: n_genes_by_counts, total_counts, pct_counts_mt.
    """
    adata.var["mt"] = adata.var_names.str.upper().str.startswith(mito_prefix)
    n_mito = int(adata.var["mt"].sum())
    if n_mito == 0:
        logger.warning("No mitochondrial genes found with prefix '{}' — "
                       "check gene naming (Ensembl vs symbol).", mito_prefix)
    sc.pp.calculate_qc_metrics(
        adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True
    )
    logger.info("QC metrics computed ({} mito genes flagged)", n_mito)
    return adata


def filter_cells_genes(
    adata: AnnData,
    min_genes: int = 200,
    min_cells: int = 3,
    max_mito_pct: float = 5.0,
) -> AnnData:
    """Drop low-quality cells and rarely-detected genes.

    - cells with < min_genes detected genes  (empty / low-quality droplets)
    - genes seen in < min_cells cells         (noise)
    - cells with >= max_mito_pct mito percent (dying / ruptured cells)
    Returns a filtered copy; the input is not mutated.
    """
    n_start = adata.n_obs
    adata = adata.copy()

    sc.pp.filter_cells(adata, min_genes=min_genes)
    sc.pp.filter_genes(adata, min_cells=min_cells)
    adata = adata[adata.obs["pct_counts_mt"] < max_mito_pct].copy()

    logger.info(
        "QC filter: {} -> {} cells (min_genes={}, max_mito_pct={})",
        n_start, adata.n_obs, min_genes, max_mito_pct,
    )
    if adata.n_obs == 0:
        raise ValueError("All cells filtered out — thresholds are too strict.")
    return adata