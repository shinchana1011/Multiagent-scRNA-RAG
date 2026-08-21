# src/agents/annotation/cell_state.py — FR-18 cell-state annotation (Member 3)
from __future__ import annotations
import scanpy as sc

# broad state markers per cell type (extend as needed)
_STATE_MARKERS = {
    "T cell": {"naive": ["CCR7", "SELL", "TCF7", "LEF1"],
               "memory": ["GZMK", "CD44", "IL7R", "S100A4"]},
    "Monocyte": {"classical": ["CD14", "S100A8", "S100A9"],
                 "non-classical": ["FCGR3A", "MS4A7", "CDKN1C"]},
    "B cell": {"naive": ["TCL1A", "IL4R", "FCER2"],
               "memory": ["CD27", "TNFRSF13B", "AIM2"]},
}


def annotate_cell_state(adata, cluster_id: str, cell_type: str) -> str | None:
    """FR-18: return a broad cell-state label for one HIGH-confidence cluster,
    or None if no state markers are defined for this cell type."""
    states = _STATE_MARKERS.get(cell_type)
    if states is None:
        return None
    mask = adata.obs["leiden"] == cluster_id
    best_state, best_score = None, float("-inf")
    for state_name, genes in states.items():
        present = [g for g in genes if g in adata.raw.var_names]
        if not present:
            continue
        sc.tl.score_genes(adata, present, score_name="_st", use_raw=True)
        score = float(adata.obs.loc[mask, "_st"].mean())
        if score > best_score:
            best_state, best_score = state_name, score
    return best_state