# src/agents/annotation/method_kb2.py — KB-2 annotation (Member 3, Task 4)
from __future__ import annotations
from src.pipeline.markers import top_markers_table
from src.knowledge_base.kb2_annotation import AnnotationKB


def annotate_kb2(adata, n_top: int = 10) -> dict[str, str]:
    """Return {cluster_id: cell_type} using Member 2's KB-2."""
    kb2 = AnnotationKB()
    table = top_markers_table(adata, n=n_top)
    result = {}
    for cluster in table["cluster"].unique():
        genes = list(table[table["cluster"] == cluster]["gene"])
        hits = kb2.annotate(genes, n=1)              # Member 2's function
        result[str(cluster)] = hits[0]["cell_type"] if hits else "Unknown"
    return result