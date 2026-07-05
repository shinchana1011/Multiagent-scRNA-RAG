# src/plots/figures.py — visualisation outputs (Member 1, Task 8)
from __future__ import annotations

from pathlib import Path
import matplotlib
matplotlib.use("Agg")               # no GUI; save straight to file
import matplotlib.pyplot as plt
import scanpy as sc
from anndata import AnnData


def _save(path: Path) -> Path:
    plt.savefig(path, bbox_inches="tight", dpi=150)
    plt.close()
    return path


def plot_qc(adata: AnnData, out_dir: str) -> Path:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    sc.pl.violin(adata, ["n_genes_by_counts", "total_counts", "pct_counts_mt"],
                 jitter=0.4, multi_panel=True, show=False)
    return _save(out / "qc_violin.png")


def plot_umap(adata: AnnData, out_dir: str, color: str = "leiden") -> Path:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    sc.pl.umap(adata, color=color, show=False)
    return _save(out / f"umap_{color}.png")


def plot_marker_dotplot(adata: AnnData, out_dir: str, n: int = 5) -> Path:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    sc.pl.rank_genes_groups_dotplot(adata, n_genes=n, show=False)
    return _save(out / "marker_dotplot.png")
