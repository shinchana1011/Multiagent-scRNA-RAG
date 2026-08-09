# scripts/build_kb1.py — build and save the KB-1 methods index (Member 2, Task 1)
from src.knowledge_base.corpus import load_seed_corpus
from src.knowledge_base.chunking import chunk_text
from src.knowledge_base.vector_store import VectorStore


def build() -> None:
    docs = load_seed_corpus()
    chunks: list[dict] = []
    for d in docs:
        for piece in chunk_text(d["text"]):
            chunks.append({
                "text": piece,
                "pmid": d["pmid"],
                "title": d["title"],
                "year": d.get("year"),
                "tissue": d.get("tissue", "general"),
            })
    vs = VectorStore()
    vs.build(chunks)
    vs.save()


if __name__ == "__main__":
    build()