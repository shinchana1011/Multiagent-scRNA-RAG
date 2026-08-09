# src/knowledge_base/vector_store.py — embeddings + FAISS index (Member 2, Task 1)
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from loguru import logger


class VectorStore:
    """Embeds text chunks and searches them by cosine similarity via FAISS.
    FAISS stores only vectors, so a parallel self.metadata list holds the
    chunk text + citation info, aligned by position."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model = SentenceTransformer(model_name)   # downloads ~80MB on first run
        self.index: faiss.Index | None = None
        self.metadata: list[dict] = []

    def build(self, chunks: list[dict]) -> None:
        """chunks: list of dicts, each with a 'text' key + metadata."""
        texts = [c["text"] for c in chunks]
        emb = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        emb = np.asarray(emb, dtype="float32")
        self.index = faiss.IndexFlatIP(emb.shape[1])   # inner product on normalised = cosine
        self.index.add(emb)
        self.metadata = chunks
        logger.info("Built KB-1 index: {} vectors, dim {}", self.index.ntotal, emb.shape[1])

    def save(self, dir_path: str = "data/kb/kb1_index") -> None:
        p = Path(dir_path); p.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(p / "kb1.faiss"))
        (p / "kb1_meta.json").write_text(json.dumps(self.metadata))
        logger.info("Saved KB-1 to {}", p)

    def load(self, dir_path: str = "data/kb/kb1_index") -> "VectorStore":
        p = Path(dir_path)
        self.index = faiss.read_index(str(p / "kb1.faiss"))
        self.metadata = json.loads((p / "kb1_meta.json").read_text())
        logger.info("Loaded KB-1: {} vectors", self.index.ntotal)
        return self

    def search(self, query: str, k: int = 5) -> list[dict]:
        q = np.asarray(self.model.encode([query], normalize_embeddings=True), dtype="float32")
        scores, idx = self.index.search(q, k)
        results = []
        for score, i in zip(scores[0], idx[0]):
            if i == -1:
                continue
            hit = dict(self.metadata[i])
            hit["score"] = float(score)
            results.append(hit)
        return results