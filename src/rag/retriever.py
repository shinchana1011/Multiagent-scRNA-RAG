# src/rag/retriever.py — tissue-aware retrieval over KB-1 (Member 2, Task 2)
from __future__ import annotations

from src.knowledge_base.vector_store import VectorStore


class Retriever:
    """Searches KB-1 and re-ranks so tissue-matched chunks come first."""

    def __init__(self, index_dir: str = "data/kb/kb1_index") -> None:
        self.store = VectorStore().load(index_dir)

    def retrieve(self, query: str, tissue: str = "general",
                 k: int = 5, overfetch: int = 4) -> list[dict]:
        """Fetch k*overfetch by similarity, then prefer this tissue, then
        'general', then everything else. Returns the top k."""
        hits = self.store.search(query, k=k * overfetch)

        def rank(h: dict) -> int:
            t = h.get("tissue", "general")
            if t == tissue:
                return 0        # exact tissue match first
            if t == "general":
                return 1        # generic guidance second
            return 2            # other tissues last

        hits.sort(key=lambda h: (rank(h), -h["score"]))
        return hits[:k]