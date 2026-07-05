# src/pipeline/markers.py — differential expression per cluster (Member 1, Task 6)
from __future__ import annotations

import pandas as pd
import scanpy as sc
from anndata import AnnData
from loguru import logger


def rank_markers(adata: AnnData, groupby: str = "leiden",
                  method: str = "wilcoxon") -> AnnData:
    """Rank marker genes per cluster. use_raw=True reads the FULL log-normalised
    gene set from adata.raw — this is why the Task 3 .raw contract matters."""
    sc.tl.rank_genes_groups(adata, groupby, method=method, use_raw=True)
    logger.info("Marker genes ranked per '{}' using {}", groupby, method)
    return adata


def top_markers_table(adata: AnnData, n: int = 10) -> pd.DataFrame:
    """Tidy DataFrame [cluster, rank, gene, score] — consumed by Members 3 & 4."""
    res = adata.uns["rank_genes_groups"]
    rows = []
    for cluster in res["names"].dtype.names:
        for i in range(min(n, len(res["names"][cluster]))):
            rows.append({
                "cluster": cluster,
                "rank": i + 1,
                "gene": res["names"][cluster][i],
                "score": float(res["scores"][cluster][i]),
            })
    return pd.DataFrame(rows)
