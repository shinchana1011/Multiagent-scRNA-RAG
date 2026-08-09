# src/knowledge_base/kb2_annotation.py — cell-type marker KB via ChromaDB (Member 2, Task 4)
from __future__ import annotations

import json
from pathlib import Path
import chromadb
from loguru import logger


class AnnotationKB:
    """KB-2: stores cell types indexed by their marker-gene signatures.
    Given a cluster's top genes, returns the best-matching cell types."""

    def __init__(self, persist_dir: str = "data/kb/kb2") -> None:
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection("cell_types")

    def build(self, seed_path: str = "data/kb/markers_seed.jsonl") -> None:
        lines = [l for l in Path(seed_path).read_text(encoding="utf-8").splitlines() if l.strip()]
        docs, metas, ids = [], [], []
        for i, line in enumerate(lines):
            d = json.loads(line)
            docs.append(" ".join(d["markers"]))          # embed the marker list as text
            metas.append({
                "cell_type": d["cell_type"],
                "tissue": d["tissue"],
                "markers": ",".join(d["markers"]),
                "source": d["source"],
                "pmid": d["pmid"],
            })
            ids.append(f"ct_{i}")
        # rebuild cleanly each time
        if self.collection.count() > 0:
            self.client.delete_collection("cell_types")
            self.collection = self.client.get_or_create_collection("cell_types")
        self.collection.add(documents=docs, metadatas=metas, ids=ids)
        logger.info("Built KB-2: {} cell types", len(ids))

    def annotate(self, marker_genes: list[str], n: int = 3) -> list[dict]:
        """Given a cluster's top marker genes, return best-matching cell types."""
        res = self.collection.query(query_texts=[" ".join(marker_genes)], n_results=n)
        out = []
        for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
            out.append({
                "cell_type": meta["cell_type"],
                "markers": meta["markers"],
                "pmid": meta["pmid"],
                "source": meta["source"],
                "distance": float(dist),      # lower = closer match
            })
        return out