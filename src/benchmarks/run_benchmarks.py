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

def benchmark_full(labeled_path: str, label_key: str = "bulk_labels",
                   out_dir: str = "benchmarks/results", tissue: str = "PBMC",
                   n_seeds: int = 5) -> dict:
    """Complete benchmark: RAG ablation across multiple seeds with a Wilcoxon
    signed-rank test (NFR-05), plus runtime. Writes a consolidated summary."""
    import scanpy as sc
    from scipy.stats import wilcoxon
    from sklearn.metrics import adjusted_rand_score
    from src.schemas.config import PipelineConfig
    from src.rag.parameter_recommender import recommend_parameters
    from src.benchmarks.plots import bar

    out = Path(out_dir).resolve(); out.mkdir(parents=True, exist_ok=True)
    cfg_on, _ = recommend_parameters(tissue=tissue)
    res_off, res_on = PipelineConfig().resolution, cfg_on.resolution

    def _ari_seeded(resolution: float, seed: int) -> tuple[float, float]:
        a = sc.read_h5ad(labeled_path)
        if "X_pca" not in a.obsm:
            sc.pp.pca(a, n_comps=min(50, a.n_vars - 1), random_state=seed)
        sc.pp.neighbors(a, random_state=seed)
        t = time.time()
        sc.tl.leiden(a, resolution=resolution, flavor="igraph",
                     n_iterations=2, directed=False, random_state=seed)
        rt = time.time() - t
        return adjusted_rand_score(a.obs[label_key], a.obs["leiden"]), rt

    off_aris, on_aris, off_rts, on_rts = [], [], [], []
    for seed in range(n_seeds):
        oa, ort = _ari_seeded(res_off, seed); off_aris.append(oa); off_rts.append(ort)
        na, nrt = _ari_seeded(res_on, seed);  on_aris.append(na);  on_rts.append(nrt)
        logger.info("seed {}: off={:.3f} on={:.3f}", seed, oa, na)

    mean = lambda xs: sum(xs) / len(xs)
    # NFR-05: paired Wilcoxon signed-rank on ARI (on vs off)
    try:
        stat, pval = wilcoxon(on_aris, off_aris)
    except ValueError:
        pval = float("nan")   # identical values -> test undefined

    # CSV: per-seed + summary
    with open(out / "benchmark_full.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "ari_off", "ari_on", "rt_off_s", "rt_on_s"])
        for i in range(n_seeds):
            w.writerow([i, round(off_aris[i], 4), round(on_aris[i], 4),
                        round(off_rts[i], 2), round(on_rts[i], 2)])
        w.writerow([]); w.writerow(["mean_ari_off", round(mean(off_aris), 4)])
        w.writerow(["mean_ari_on", round(mean(on_aris), 4)])
        w.writerow(["improvement_pct", round((mean(on_aris) - mean(off_aris)) / mean(off_aris) * 100, 1)])
        w.writerow(["wilcoxon_p", round(pval, 5) if pval == pval else "n/a"])
        w.writerow(["mean_runtime_s", round(mean(off_rts + on_rts), 2)])

    bar(["RAG-off", "RAG-on"], [mean(off_aris), mean(on_aris)],
        f"ARI (mean of {n_seeds} seeds, p={pval:.3f})", "ARI",
        str(out / "ari_summary.png"), hline=0.75)
    bar(["RAG-off", "RAG-on"], [mean(off_rts), mean(on_rts)],
        "Mean clustering runtime", "seconds", str(out / "runtime_summary.png"))

    summary = {"mean_ari_off": round(mean(off_aris), 4),
               "mean_ari_on": round(mean(on_aris), 4),
               "improvement_pct": round((mean(on_aris) - mean(off_aris)) / mean(off_aris) * 100, 1),
               "wilcoxon_p": pval, "n_seeds": n_seeds, "output_dir": str(out)}
    logger.info("FULL BENCHMARK: {}", summary)
    return summary


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/zheng68k/pbmc68k_reduced.h5ad"
    key = sys.argv[2] if len(sys.argv) > 2 else "bulk_labels"
    benchmark_full(path, key)