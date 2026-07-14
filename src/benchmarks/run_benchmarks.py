# src/benchmarks/run_benchmarks.py — ARI / runtime / RAG ablation automation (Member 4, Task 4)
from __future__ import annotations
import csv, time
from pathlib import Path
from loguru import logger


def _ari(adata, label_key: str) -> float:
    from sklearn.metrics import adjusted_rand_score
    return float(adjusted_rand_score(adata.obs[label_key], adata.obs["leiden"]))


def benchmark_all(labeled_path: str, label_key: str = "bulk_labels",
                  out_dir: str = "benchmarks/results", tissue: str = "PBMC") -> dict:
    """Benchmark on a labeled (possibly pre-processed) dataset. Measures ARI of
    Leiden clustering vs ground-truth labels, RAG-off vs RAG-on resolution."""
    import scanpy as sc
    from src.schemas.config import PipelineConfig
    from src.rag.parameter_recommender import recommend_parameters
    from src.benchmarks.plots import bar

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    rows, results = [], {}

    def _cluster_ari(resolution: float) -> tuple[float, float]:
        a = sc.read_h5ad(labeled_path)               # bypass raw-counts guard (pre-processed data)
        if label_key not in a.obs:
            raise ValueError(f"'{label_key}' not in obs: {list(a.obs.columns)}")
        t = time.time()
        if "X_pca" not in a.obsm:                    # compute PCA if absent
            sc.pp.pca(a, n_comps=min(50, a.n_vars - 1), random_state=0)
        sc.pp.neighbors(a, random_state=0)
        sc.tl.leiden(a, resolution=resolution, flavor="igraph",
                     n_iterations=2, directed=False, random_state=0)
        return _ari(a, label_key), time.time() - t

    off_ari, off_rt = _cluster_ari(PipelineConfig().resolution)     # RAG-off (default 0.5)
    rows.append(["rag_off", round(off_ari, 4), round(off_rt, 1)])

    cfg, _ = recommend_parameters(tissue=tissue)                    # RAG-on (retrieved resolution)
    on_ari, on_rt = _cluster_ari(cfg.resolution)
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    logger.info("Writing benchmark outputs to: {}", out)

    csv_path = out / "benchmark_metrics.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["condition", "resolution", "ARI", "runtime_s"])
        w.writerow(["rag_off", PipelineConfig().resolution, round(off_ari, 4), round(off_rt, 1)])
        w.writerow(["rag_on", cfg.resolution, round(on_ari, 4), round(on_rt, 1)])
    logger.info("Wrote {}", csv_path)

    ari_png = bar(["RAG-off", "RAG-on"], [off_ari, on_ari],
                  "Clustering quality (ARI)", "ARI", str(out / "ari.png"), hline=0.75)
    rt_png = bar(["RAG-off", "RAG-on"], [off_rt, on_rt],
                 "Runtime", "seconds", str(out / "runtime.png"))
    logger.info("Wrote {} and {}", ari_png, rt_png)

    results = {"rag_off_ari": round(off_ari, 4), "rag_on_ari": round(on_ari, 4),
               "rag_off_resolution": PipelineConfig().resolution,
               "rag_on_resolution": cfg.resolution,
               "output_dir": str(out)}
    logger.info("Benchmarks: {}", results)
    return results

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/zheng68k/pbmc68k_reduced.h5ad"
    key = sys.argv[2] if len(sys.argv) > 2 else "bulk_labels"
    benchmark_all(path, key)