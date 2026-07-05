# src/schemas/config.py — the shared parameter contract (Member 3 owns, everyone uses)
from __future__ import annotations

from pydantic import BaseModel


class PipelineConfig(BaseModel):
    # QC
    min_genes: int = 200
    min_cells: int = 3
    mito_pct: float = 5.0
    # normalisation / features
    target_sum: float = 1e4
    n_hvg: int = 2000
    # dimensionality reduction
    n_pcs: int = 50
    # clustering
    resolution: float = 0.5
    # markers
    n_top_markers: int = 10
    # batch correction (set by the Data Router)
    use_harmony: bool = False
    batch_key: str | None = None
    # reproducibility
    random_state: int = 0
