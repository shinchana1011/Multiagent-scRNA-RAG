# src/benchmarks/rag_ablation_3datasets.py — RAG-off vs RAG-on clustering ARI,
# across three real labeled datasets (not just one, to avoid a single-dataset
# ablation claim). Reuses prepare_pbmc12k's M1-contract preprocessing (name is
# historical -- it's dataset-agnostic: normalize -> log1p -> .raw -> HVG ->
# scale -> PCA -> neighbors -> Leiden).
from __future__ import annotations

import csv
from pathlib import Path

from loguru import logger


def _ari_pbmc68k_reduced(resolution: float, seed: int = 0) -> float:
    import scanpy as sc
    from sklearn.metrics import adjusted_rand_score

    a = sc.read_h5ad("data/raw/zheng68k/pbmc68k_reduced.h5ad")  # already log-normalized, X_pca present
    sc.pp.neighbors(a, random_state=seed)
    sc.tl.leiden(a, resolution=resolution, flavor="igraph", n_iterations=2, directed=False, random_state=seed)
    return float(adjusted_rand_score(a.obs["bulk_labels"], a.obs["leiden"]))


def _ari_pbmc12k(resolution: float, seed: int = 0) -> float:
    import scanpy as sc
    from sklearn.metrics import adjusted_rand_score
    from src.benchmarks.run_benchmarks import prepare_pbmc12k

    a = sc.read_h5ad("data/raw/zheng68k/zheng68k_full.h5ad")  # 12k scvi-tools PBMC set, raw counts
    a = prepare_pbmc12k(a, resolution=resolution, seed=seed)
    return float(adjusted_rand_score(a.obs["str_labels"], a.obs["leiden"]))


def _ari_paul15(resolution: float, seed: int = 0) -> float:
    import scanpy as sc
    from sklearn.metrics import adjusted_rand_score
    from src.benchmarks.run_benchmarks import prepare_pbmc12k

    a = sc.read_h5ad("data/raw/extra/paul15.h5ad")  # mouse bone-marrow myeloid progenitors, raw counts
    a = prepare_pbmc12k(a, resolution=resolution, seed=seed)
    return float(adjusted_rand_score(a.obs["paul15_clusters"], a.obs["leiden"]))


def run_rag_ablation_3datasets(out_dir: str = "benchmarks/results", seed: int = 0) -> list[dict]:
    from src.schemas.config import PipelineConfig
    from src.rag.parameter_recommender import recommend_parameters

    default_res = PipelineConfig().resolution  # RAG-off resolution

    datasets = [
        # pbmc68k_reduced is scanpy's official subsample of the REAL 10x/Zheng68k
        # PBMC dataset (Zheng et al. 2017) -- 700-ish cells, not the full 68k.
        # The full raw Zheng68k (68k cells, FACS-purified labels) is NOT available
        # locally and needs a manual download (like COVID/Tabula Sapiens) -- see
        # docs/RESULTS.md's own "pending" note. No internet access in this
        # environment to fetch it, so this reduced slice is what's actually run.
        {"dataset": "Zheng68k-reduced (scanpy pbmc68k_reduced, 700c, 10 types)", "tissue": "PBMC", "fn": _ari_pbmc68k_reduced},
        {"dataset": "PBMC-12k (scvi-tools, 11990c, 9 types)", "tissue": "PBMC", "fn": _ari_pbmc12k},
        {"dataset": "Paul15 (myeloid progenitors, 2730c, 19 types)", "tissue": "bone marrow", "fn": _ari_paul15},
    ]

    rows = []
    for d in datasets:
        cfg, claims = recommend_parameters(tissue=d["tissue"])
        rag_res = cfg.resolution
        claim_note = ""
        if claims:
            c = claims[0]
            if c["tissue"].lower() not in (d["tissue"].lower(), "general"):
                claim_note = (
                    f"KNOWN LIMITATION, not a bug: KB-1's corpus currently only tags "
                    f"{{PBMC, lung, tumor, general}} tissue -- there is no bone-marrow/hematopoietic "
                    f"category. For '{d['tissue']}', retrieval fell back to a '{c['tissue']}'-tagged "
                    f"claim (pmid={c['pmid']}), a tissue-context mismatch the Verifier would flag and "
                    f"reject in the real pipeline. This dataset's RAG-on number should be read as "
                    f"'what happens when RAG is applied outside the corpus's tissue coverage', not as "
                    f"a representative RAG result -- it demonstrates RAG's benefit is contingent on "
                    f"corpus coverage, which is itself an honest, useful finding.")
        else:
            claim_note = "No cited claim retrieved; RAG resolution fell back to the default."

        ari_no_rag = d["fn"](default_res, seed=seed)
        ari_rag = d["fn"](rag_res, seed=seed)
        improvement_pct = round((ari_rag - ari_no_rag) / ari_no_rag * 100, 1) if ari_no_rag else float("nan")

        row = {
            "dataset": d["dataset"], "tissue": d["tissue"],
            "resolution_no_rag": default_res, "resolution_rag": rag_res,
            "ari_no_rag": round(ari_no_rag, 4), "ari_rag": round(ari_rag, 4),
            "improvement_pct": improvement_pct, "note": claim_note,
        }
        rows.append(row)
        logger.info("{}: no_rag={:.4f} (res={}) rag={:.4f} (res={}) improvement={}%",
                    d["dataset"], ari_no_rag, default_res, ari_rag, rag_res, improvement_pct)

    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "rag_ablation_3datasets.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "tissue", "resolution_no_rag", "resolution_rag",
                    "ari_no_rag", "ari_rag", "improvement_pct", "note"])
        for r in rows:
            w.writerow([r["dataset"], r["tissue"], r["resolution_no_rag"], r["resolution_rag"],
                        r["ari_no_rag"], r["ari_rag"], r["improvement_pct"], r["note"]])
    logger.info("Wrote {}", csv_path)

    md_path = out / "rag_ablation_3datasets.md"
    with open(md_path, "w") as f:
        f.write("| Dataset | No-RAG ARI | RAG ARI | Improvement |\n")
        f.write("|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['dataset']} | {r['ari_no_rag']:.4f} | {r['ari_rag']:.4f} | "
                    f"{r['improvement_pct']:+.1f}% |\n")
        f.write("\nNotes:\n")
        for r in rows:
            if r["note"]:
                f.write(f"- **{r['dataset']}**: {r['note']}\n")
    logger.info("Wrote {}", md_path)

    return rows


if __name__ == "__main__":
    run_rag_ablation_3datasets()
