# src/rag/parameter_recommender.py — prose -> PipelineConfig + citations (Member 2, Task 3)
from __future__ import annotations

import re
from loguru import logger

from src.schemas.config import PipelineConfig     # the frozen Member 1 <-> 2 contract
from src.rag.retriever import Retriever
from src.rag.llm_extractor import extract_parameters_llm

# --- regex heuristics: find the number tied to each parameter's keyword ---
_MITO = re.compile(r"mitochondrial[^.]*?(\d+(?:\.\d+)?)\s*(?:to\s*(\d+(?:\.\d+)?)\s*)?percent", re.I)
_PCS  = re.compile(r"(\d+)\s*(?:to\s*(\d+)\s*)?principal components", re.I)
_RES  = re.compile(r"resolution[^.]*?(\d\.\d+)", re.I)


def _first_match(pattern: re.Pattern, hits: list[dict], upper: bool = False):
    """Scan hits in order; return (value, source_hit) for the first match.
    upper=True picks the top of a 'X to Y' range (e.g. '10 to 30' -> 30)."""
    for h in hits:
        m = pattern.search(h["text"])
        if m:
            val = m.group(1)
            if upper:
                try:
                    if m.group(2):
                        val = m.group(2)
                except IndexError:
                    pass
            return float(val), h
    return None, None


def _claim(parameter: str, value, hit: dict) -> dict:
    """A citation-backed claim. Member 3's Verifier checks and re-scores these."""
    return {
        "parameter": parameter,
        "value": value,
        "pmid": hit["pmid"],
        "title": hit["title"],
        "tissue": hit.get("tissue", "general"),
        "snippet": hit["text"][:160],
        "confidence": "MED",     # default; Verifier upgrades to HIGH or downgrades
    }


def recommend_parameters(tissue: str = "general", disease: str = "") -> tuple[PipelineConfig, list[dict]]:
    """Retrieve tissue-matched literature and extract QC/PCA/resolution values.
    Returns a filled PipelineConfig (ready for Member 1's run_analysis) and the
    list of citation-backed claims behind it."""
    retr = Retriever()
    query = (f"quality control mitochondrial threshold, number of principal "
             f"components, and Leiden clustering resolution for {tissue} {disease} "
             f"single-cell RNA-seq")
    hits = retr.retrieve(query, tissue=tissue, k=6)

    cfg = PipelineConfig()          # start from defaults; override what we find
    claims: list[dict] = []

    mito, h = _first_match(_MITO, hits, upper=True)
    if mito is not None:
        cfg.mito_pct = mito
        claims.append(_claim("mito_pct", mito, h))

    pcs, h = _first_match(_PCS, hits, upper=True)
    if pcs is not None:
        cfg.n_pcs = int(pcs)
        claims.append(_claim("n_pcs", int(pcs), h))

    res, h = _first_match(_RES, hits)
    if res is not None:
        cfg.resolution = res
        claims.append(_claim("resolution", res, h))

    logger.info("RAG params for tissue='{}': mito_pct={}, n_pcs={}, resolution={} "
                "({} cited claims)", tissue, cfg.mito_pct, cfg.n_pcs, cfg.resolution, len(claims))
    return cfg, claims

def retrieve_alternative(parameter: str, tissue: str, exclude_pmids: set[str]) -> dict | None:
    """FR-08: fetch a DIFFERENT cited value for `parameter`, excluding sources
    already tried. Returns a claim dict or None if KB-1 has no alternative."""
    from src.rag.retriever import Retriever
    retr = Retriever()
    query = f"{parameter} value for {tissue} single-cell RNA-seq analysis"
    hits = retr.retrieve(query, tissue=tissue, k=10)
    # regex map reused from this module
    pat = {"mito_pct": _MITO, "n_pcs": _PCS, "resolution": _RES}.get(parameter)
    if pat is None:
        return None
    for h in hits:
        if h["pmid"] in exclude_pmids:
            continue                      # skip sources already tried
        m = pat.search(h["text"])
        if m:
            val = m.group(2) if (m.lastindex and m.lastindex >= 2 and m.group(2)) else m.group(1)
            caster = int if parameter == "n_pcs" else float
            return {"parameter": parameter, "value": caster(val),
                    "pmid": h["pmid"], "tissue": h.get("tissue", tissue)}
    return None