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
    """Runs RAG-off (defaults) vs RAG-on, records ARI + runtime, writes CSV + plots."""
    from src.io.readers import load_dataset
    from src.schemas.config import PipelineConfig
    from src.pipeline.runner import run_analysis
    from src.rag.parameter_recommender import recommend_parameters
    from src.benchmarks.plots import bar

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    rows, results = [], {}

    # RAG-OFF baseline
    t0 = time.time()
    a_off = run_analysis(load_dataset(labeled_path), PipelineConfig())
    off_ari, off_rt = _ari(a_off, label_key), time.time() - t0
    rows.append(["rag_off", off_ari, round(off_rt, 1)])

    # RAG-ON
    cfg, _ = recommend_parameters(tissue=tissue)
    t1 = time.time()
    a_on = run_analysis(load_dataset(labeled_path), cfg)
    on_ari, on_rt = _ari(a_on, label_key), time.time() - t1
    rows.append(["rag_on", on_ari, round(on_rt, 1)])

    with open(out / "benchmark_metrics.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["condition", "ARI", "runtime_s"]); w.writerows(rows)

    bar(["RAG-off", "RAG-on"], [off_ari, on_ari], "Clustering quality (ARI)",
        "ARI", str(out / "ari.png"), hline=0.75)                       # NFR-04 target
    bar(["RAG-off", "RAG-on"], [off_rt, on_rt], "Runtime", "seconds", str(out / "runtime.png"))

    results = {"rag_off_ari": off_ari, "rag_on_ari": on_ari,
               "rag_off_runtime": off_rt, "rag_on_runtime": on_rt}
    logger.info("Benchmarks: {}", results)
    return results


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/zheng68k/pbmc68k_reduced.h5ad"
    key = sys.argv[2] if len(sys.argv) > 2 else "bulk_labels"
    benchmark_all(path, key)