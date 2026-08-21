# src/agents/annotation/harmonize.py — map all methods to a shared vocabulary (Member 3)
from __future__ import annotations

# every label variant -> one canonical name
_CANON = {
    # T cells (subtypes collapse to "T cell" for consensus)
    "CD4 T cell": "T cell", "CD8 T cell": "T cell", "T_cells": "T cell",
    "T cell": "T cell", "T cells": "T cell",
    # B cells
    "B cell": "B cell", "B_cell": "B cell", "B_cells": "B cell",
    # NK
    "NK cell": "NK cell", "NK_cell": "NK cell", "NK cells": "NK cell",
    # Monocytes (SingleR doesn't split CD14/FCGR3A, so collapse those too)
    "CD14 Monocyte": "Monocyte", "FCGR3A Monocyte": "Monocyte",
    "Monocyte": "Monocyte", "Monocytes": "Monocyte",
    # Dendritic
    "Dendritic cell": "Dendritic cell", "DC": "Dendritic cell",
    # Platelet
    "Platelet": "Platelet", "Platelets": "Platelet",
}


def canon(label: str) -> str:
    """Map a raw method label to the shared vocabulary. Unknown labels pass
    through unchanged (so they still count, just under their own name)."""
    return _CANON.get(label, label)