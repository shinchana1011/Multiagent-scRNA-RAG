# src/knowledge_base/chunking.py — split documents into retrievable chunks (Member 2, Task 1)
from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    """Split text into overlapping word windows. Overlap keeps sentences that
    straddle a boundary retrievable. Short texts return unchanged."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]
    step = chunk_size - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + chunk_size]))
        if start + chunk_size >= len(words):
            break
    return chunks