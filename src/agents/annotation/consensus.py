# src/agents/annotation/consensus.py — with harmonization (Member 3)
from __future__ import annotations
from collections import Counter
from src.agents.annotation.harmonize import canon


def score_consensus(votes: dict[str, str]) -> tuple[str, str]:
    """Given {method: cell_type} for one cluster, harmonize labels then score
    agreement. Returns (winning_cell_type, confidence)."""
    valid = [canon(v) for v in votes.values() if v and v != "Unknown"]
    if not valid:
        return "Unknown", "LOW"

    tally = Counter(valid)
    winner, top_count = tally.most_common(1)[0]
    n = len(valid)

    if top_count == n:
        confidence = "HIGH"
    elif top_count > n / 2:
        confidence = "MED"
    else:
        confidence = "LOW"
    return winner, confidence