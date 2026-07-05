# src/pipeline/runner.py — full analysis pipeline (Member 1, Task 7)
from __future__ import annotations

from anndata import AnnData
from loguru import logger

from src.schemas.config import PipelineConfig
from src.pipeline.qc import compute_qc_metrics, filter_cells_genes
from src.pipeline.normalize import normalize, select_hvg, scale
from src.pipeline.reduce import run_pca, run_harmony, build_neighbors
from src.pipeline.cluster import run_leiden, run_umap
from src.pipeline.markers import rank_markers


def run_analysis(adata: AnnData, cfg: PipelineConfig) -> AnnData:
    """QC -> normalise -> HVG -> scale -> PCA -> [Harmony] -> neighbours
    -> Leiden -> UMAP -> markers. Pure: no file I/O, no plotting."""
    adata = compute_qc_metrics(adata)
    adata = filter_cells_genes(adata, cfg.min_genes, cfg.min_cells, cfg.mito_pct)

    adata = normalize(adata, cfg.target_sum)
    adata = select_hvg(adata, cfg.n_hvg)
    adata = scale(adata)

    adata = run_pca(adata, cfg.n_pcs, cfg.random_state)
    use_rep = "X_pca"
    if cfg.use_harmony and cfg.batch_key:
        adata = run_harmony(adata, cfg.batch_key)
        use_rep = "X_pca_harmony"
    adata = build_neighbors(adata, cfg.n_pcs, use_rep, cfg.random_state)

    adata = run_leiden(adata, cfg.resolution, cfg.random_state)
    adata = run_umap(adata, cfg.random_state)
    adata = rank_markers(adata)

    logger.info("Analysis complete: {} cells, {} clusters",
                adata.n_obs, adata.obs["leiden"].nunique())
    return adata
