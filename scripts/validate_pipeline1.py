# scripts/validate_pipeline.py — prove the pipeline is correct on real data
from __future__ import annotations

from pathlib import Path
import numpy as np
import scanpy as sc
from sklearn.metrics import adjusted_rand_score

from src.io.readers import load_dataset
from src.schemas.config import PipelineConfig
from src.pipeline.runner import run_analysis
from src.plots.figures import plot_umap

# label columns commonly used in Zheng68k / PBMC benchmark files
_LABEL_CANDIDATES = ["celltype", "cell_type", "CellType", "bulk_labels",
                     "labels", "label", "cell_types"]


def validate_harmony(covid_path: str, batch_key: str = "patient") -> None:
    """Run the pipeline WITH Harmony on the real multi-batch COVID file and
    measure integration LISI (NFR-07 target: iLISI > 1.5)."""
    print(f"\n=== HARMONY VALIDATION ({covid_path}) ===")
    adata = load_dataset(covid_path)
    if batch_key not in adata.obs:
        print(f"  '{batch_key}' not in obs — has: {list(adata.obs.columns)}")
        return

    cfg = PipelineConfig(use_harmony=True, batch_key=batch_key)
    adata = run_analysis(adata, cfg)

    # visual check: colour the UMAP by patient — good mixing = colours intermingled
    plot_umap(adata, "data/processed/figures", color=batch_key)

    # quantitative check: iLISI on the Harmony embedding
    try:
        from harmonypy import compute_lisi
    except ImportError:
        from harmonypy.lisi import compute_lisi
    emb = adata.obsm["X_pca_harmony"]
    lisi = compute_lisi(emb, adata.obs[[batch_key]], [batch_key])
    ilisi = float(np.mean(lisi[:, 0]))
    n_batches = adata.obs[batch_key].nunique()

    print(f"  patients: {n_batches}")
    print(f"  iLISI = {ilisi:.2f}   (target > 1.5; max possible ~{n_batches})")
    print(f"  {'PASS' if ilisi > 1.5 else 'BELOW TARGET'} — "
          f"higher means patients are well mixed within clusters")
    print(f"  eyeball: data/processed/figures/umap_{batch_key}.png "
          f"(colours should be intermingled, not separate blobs)")


def benchmark_ari(zheng_path: str, label_key: str | None = None) -> None:
    """Run the pipeline on labelled Zheng68k and compare clusters to ground
    truth via ARI (NFR-04 target: ARI >= 0.75)."""
    print(f"\n=== ARI BENCHMARK ({zheng_path}) ===")
    adata = load_dataset(zheng_path)

    if label_key is None:
        label_key = next((c for c in _LABEL_CANDIDATES if c in adata.obs), None)
    if label_key is None:
        print(f"  No label column found. obs has: {list(adata.obs.columns)}")
        print("  Re-run with the correct column, e.g. --label-key bulk_labels")
        return

    cfg = PipelineConfig()                      # defaults = the RAG-off baseline
    adata = run_analysis(adata, cfg)

    ari = adjusted_rand_score(adata.obs[label_key], adata.obs["leiden"])
    print(f"  ground-truth labels: {adata.obs[label_key].nunique()} types "
          f"(column '{label_key}')")
    print(f"  Leiden clusters:     {adata.obs['leiden'].nunique()}")
    print(f"  ARI = {ari:.3f}   (target >= 0.75)")
    print(f"  {'PASS' if ari >= 0.75 else 'BASELINE (below 0.75)'} — "
          f"this is the RAG-OFF baseline; RAG-tuned params aim to beat it")


if __name__ == "__main__":
    covid = "data/raw/covid_gse145926/covid_merged.h5ad"
    if Path(covid).exists():
        validate_harmony(covid)
    else:
        print(f"Skipping Harmony: {covid} not found.")

    zheng = "data/raw/zheng68k/zheng68k.h5ad"
    if Path(zheng).exists():
        benchmark_ari(zheng)
    else:
        print(f"Skipping ARI: {zheng} not found (download labelled Zheng68k first).")