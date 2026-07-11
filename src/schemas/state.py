# src/schemas/state.py — the shared object passed between all agents (Member 3, Task 1)
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import time

from src.schemas.config import PipelineConfig   # the frozen Member 1 contract


@dataclass
class Claim:
    """A literature-backed parameter recommendation (produced by Member 2's RAG,
    verified by your Verifier in Task 3)."""
    parameter: str
    value: Any
    pmid: str = ""
    verified: bool = False
    confidence: str = "MED"          # HIGH / MED / LOW

    def downgrade(self) -> None:
        order = ["HIGH", "MED", "LOW"]
        i = min(order.index(self.confidence) + 1, len(order) - 1)
        self.confidence = order[i]


@dataclass
class Annotation:
    """A cell-type label for one cluster (produced by your Annotation +
    Consensus tasks)."""
    cluster_id: str
    cell_type: str
    confidence: str                  # HIGH / MED / LOW
    marker_genes: list[str] = field(default_factory=list)
    method_votes: dict[str, str] = field(default_factory=dict)

    def needs_review(self) -> bool:
        return self.confidence == "LOW"


@dataclass
class PipelineState:
    """The single object every agent reads from and writes to. It flows
    Data -> Parameter -> Verifier -> Analysis -> Annotation -> Report,
    accumulating results at each step."""
    input_path: str
    config: PipelineConfig = field(default_factory=PipelineConfig)
    adata: Any = None                        # the AnnData (filled by DataAgent)
    tissue: str = "general"
    disease: str = ""
    claims: list[Claim] = field(default_factory=list)
    annotations: list[Annotation] = field(default_factory=list)
    log: list[dict] = field(default_factory=list)
    error: Optional[str] = None

    retry_count: dict[str, int] = field(default_factory=dict)   # per-agent retry tally
    max_retries: int = 2

    def log_event(self, agent: str, action: str, detail: Any = None) -> None:
        self.log.append({"t": round(time.time(), 3), "agent": agent,
                         "action": action, "detail": detail})

    def review_queue(self) -> list[Annotation]:
        return [a for a in self.annotations if a.needs_review()]