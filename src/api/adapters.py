# src/api/adapters.py — convert Members 1-3 objects to Member 4 dicts (single choke point)
from __future__ import annotations
from typing import Any


def annotation_to_dict(a: Any) -> dict:
    return {"cluster_id": str(a.cluster_id), "cell_type": a.cell_type,
            "confidence": a.confidence, "cell_state": getattr(a, "cell_state", None),
            "marker_genes": list(getattr(a, "marker_genes", [])),
            "method_votes": dict(getattr(a, "method_votes", {})),
            "sources": dict(getattr(a, "sources", {}))}


def claim_to_dict(c: Any) -> dict:
    return {"parameter": c.parameter, "value": c.value, "pmid": c.pmid,
            "verified": bool(c.verified), "confidence": c.confidence}


def config_to_dict(cfg: Any) -> dict:
    return cfg.model_dump() if hasattr(cfg, "model_dump") else vars(cfg)


def state_to_results(final: dict) -> dict:
    """The canonical results.json shape consumed by API + UI + reporting."""
    anns = [annotation_to_dict(a) for a in final.get("annotations", [])]
    return {"n_clusters": len(anns),
            "annotations": anns,
            "claims": [claim_to_dict(c) for c in final.get("claims", [])],
            "config": config_to_dict(final["config"]) if final.get("config") else {},
            "review_queue": [a["cluster_id"] for a in anns if a["confidence"] == "LOW"],
            "error": final.get("error")}