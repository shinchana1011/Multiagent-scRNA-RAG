# src/agents/annotation/method_overlap.py — marker-overlap annotation (Member 3, Task 4)
from __future__ import annotations
from src.pipeline.markers import top_markers_table

# canonical PBMC markers (same set Member 2's KB-2 uses)
PBMC_MARKERS = {
    "CD4 T cell":       ["IL7R", "CD3D", "CD3E", "CCR7"],
    "CD8 T cell":       ["CD8A", "CD8B", "CD3D", "GZMK"],
    "B cell":           ["MS4A1", "CD79A", "CD79B", "CD19"],
    "NK cell":          ["GNLY", "NKG7", "KLRD1", "NCAM1"],
    "CD14 Monocyte":    ["CD14", "LYZ", "S100A8", "S100A9"],
    "FCGR3A Monocyte":  ["FCGR3A", "MS4A7", "CDKN1C"],
    "Dendritic cell":   ["FCER1A", "CST3", "CLEC10A"],
    "Platelet":         ["PPBP", "PF4", "ITGA2B"],
}


def annotate_overlap(adata, n_top: int = 15) -> dict[str, str]:
    """Return {cluster_id: cell_type} by best marker-gene overlap."""
    table = top_markers_table(adata, n=n_top)      # Member 1's function
    result = {}
    for cluster in table["cluster"].unique():
        genes = set(table[table["cluster"] == cluster]["gene"])
        best_type, best_hits = "Unknown", 0
        for cell_type, markers in PBMC_MARKERS.items():
            hits = len(genes & set(markers))
            if hits > best_hits:
                best_type, best_hits = cell_type, hits
        result[str(cluster)] = best_type
    return result