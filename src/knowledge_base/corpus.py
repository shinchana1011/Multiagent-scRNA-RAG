# src/knowledge_base/corpus.py — load documents into a common format (Member 2, Task 1)
from __future__ import annotations

import json
from pathlib import Path


def load_seed_corpus(path: str = "data/kb/seed_corpus.jsonl") -> list[dict]:
    """Read a JSONL corpus. Each line -> a dict with text + metadata
    (pmid, title, year, tissue). Later swapped for a real PMC loader."""
    docs: list[dict] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            docs.append(json.loads(line))
    if not docs:
        raise ValueError(f"No documents loaded from {path}")
    return docs