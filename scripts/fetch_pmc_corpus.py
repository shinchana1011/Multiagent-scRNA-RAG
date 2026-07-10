# scripts/fetch_pmc_corpus.py — download real open-access papers into a KB-1 corpus (Member 2, Task 5)
from __future__ import annotations

import json
import time
from pathlib import Path
from Bio import Entrez
from loguru import logger

Entrez.email = "scrnacapstone@gmail.com"     # <-- PUT YOUR REAL EMAIL (NCBI requires it)

# search terms -> tissue label, so retrieved papers keep tissue metadata
QUERIES = {
    "PBMC":    "single-cell RNA-seq PBMC quality control clustering",
    "lung":    "single-cell RNA-seq lung bronchoalveolar methods",
    "tumor":   "single-cell RNA-seq tumor microenvironment clustering resolution",
    "general": "single-cell RNA-seq analysis best practices parameters",
}


def _search(term: str, n: int) -> list[str]:
    """Return PMC IDs for open-access papers matching a term."""
    handle = Entrez.esearch(db="pmc", term=f"{term} AND open access[filter]", retmax=n)
    ids = Entrez.read(handle)["IdList"]
    handle.close()
    return ids


def _fetch_abstract(pmc_id: str) -> tuple[str, str] | None:
    """Fetch (title, text) for one PMC paper. Returns None on failure."""
    try:
        handle = Entrez.efetch(db="pmc", id=pmc_id, rettype="abstract", retmode="text")
        text = handle.read()
        handle.close()
        if len(text) < 200:                 # skip near-empty records
            return None
        title = text.strip().split("\n")[0][:200]
        return title, text
    except Exception as e:
        logger.warning("PMC {} failed: {}", pmc_id, e)
        return None


def build_corpus(per_query: int = 60, out: str = "data/kb/corpus.jsonl") -> None:
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(out, "w", encoding="utf-8") as f:
        for tissue, term in QUERIES.items():
            ids = _search(term, per_query)
            logger.info("{}: {} papers found", tissue, len(ids))
            for pmc_id in ids:
                res = _fetch_abstract(pmc_id)
                if res is None:
                    continue
                title, text = res
                f.write(json.dumps({
                    "pmid": pmc_id, "title": title,
                    "year": None, "tissue": tissue,
                    "text": text.replace("\n", " ").strip(),
                }) + "\n")
                written += 1
                time.sleep(0.4)             # be polite to NCBI (max ~3 req/sec)
    logger.info("Wrote {} documents to {}", written, out)


if __name__ == "__main__":
    build_corpus()