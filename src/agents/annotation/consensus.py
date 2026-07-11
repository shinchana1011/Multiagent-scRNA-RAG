# src/agents/annotation/consensus.py — combine method votes into confidence (Member 3, Task 5)
from __future__ import annotations
from collections import Counter


def score_consensus(votes: dict[str, str]) -> tuple[str, str]:
    """Given {method_name: cell_type} for ONE cluster, return
    (winning_cell_type, confidence). Ignores empty/'Unknown' votes."""
    valid = [v for v in votes.values() if v and v != "Unknown"]
    if not valid:
        return "Unknown", "LOW"

    tally = Counter(valid)
    winner, top_count = tally.most_common(1)[0]
    n = len(valid)

    if top_count == n:                 # everyone who voted agrees
        confidence = "HIGH"
    elif top_count > n / 2:            # majority
        confidence = "MED"
    else:                              # tie / no majority
        confidence = "LOW"
    return winner, confidence