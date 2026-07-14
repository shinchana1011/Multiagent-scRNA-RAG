# src/reporting/methods_section.py — auto Methods section (Member 4, FR-21)
from __future__ import annotations
from loguru import logger
from src.config.settings import settings


def _template(cfg: dict, claims: list[dict]) -> str:
    cite = {c["parameter"]: f"PMID:{c['pmid']}" for c in claims if c.get("pmid")}
    return (
        "Single-cell RNA-seq data were processed with Scanpy. Cells with fewer than "
        f"{cfg.get('min_genes', 200)} genes or over {cfg.get('mito_pct', 5)}% mitochondrial "
        f"counts [{cite.get('mito_pct','')}] were removed. Counts were normalised to 1e4 and "
        f"log1p-transformed; {cfg.get('n_hvg',2000)} highly variable genes were selected. "
        f"PCA used {cfg.get('n_pcs',50)} components [{cite.get('n_pcs','')}]"
        + (", followed by Harmony batch correction. " if cfg.get('use_harmony') else ". ")
        + f"Leiden clustering was performed at resolution {cfg.get('resolution',0.5)} "
        f"[{cite.get('resolution','')}]. Clusters were annotated by a three-method consensus "
        "(SingleR, marker-enrichment, KB-2 retrieval) with HIGH/MED/LOW confidence; "
        "LOW-confidence clusters were routed to human review."
    )


def generate_methods(cfg: dict, claims: list[dict]) -> str:
    base = _template(cfg, claims)
    if not settings.llm_methods_section:
        return base
    try:                                   # polish with local Ollama (reuses Member 2/3 setup)
        from openai import OpenAI
        client = OpenAI(base_url=settings.ollama_base_url, api_key="ollama")
        r = client.chat.completions.create(
            model=settings.ollama_model, temperature=0.2,
            messages=[{"role": "user", "content":
                       "Rewrite as a formal scientific Methods paragraph, keep all numbers and "
                       f"PMIDs exactly, no new claims:\n\n{base}"}])
        return r.choices[0].message.content.strip()
    except Exception as e:                 # noqa: BLE001
        logger.warning("LLM methods polish failed ({}); using template", e)
        return base