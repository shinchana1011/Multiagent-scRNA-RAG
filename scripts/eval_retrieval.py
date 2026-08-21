# scripts/eval_retrieval.py — measure retrieval relevance (Member 2, Task 6)
from src.rag.retriever import Retriever

# (query, expected tissue) pairs — the "ground truth" for retrieval
TESTS = [
    ("mitochondrial cutoff for blood immune cells", "PBMC"),
    ("clustering resolution for peripheral blood", "PBMC"),
    ("bronchoalveolar lavage COVID quality control", "lung"),
    ("airway inflamed tissue mito threshold", "lung"),
    ("tumor microenvironment malignant cell resolution", "tumor"),
    ("solid tumour mitochondrial threshold", "tumor"),
]


def evaluate(k: int = 3) -> None:
    r = Retriever()
    hits_at_1, total = 0, 0
    for query, expected in TESTS:
        results = r.retrieve(query, tissue=expected, k=k)
        top_tissue = results[0]["tissue"] if results else "none"
        correct = top_tissue == expected
        hits_at_1 += int(correct)
        total += 1
        mark = "OK " if correct else "MISS"
        print(f"[{mark}] '{query[:45]}' -> top={top_tissue} (want {expected})")
    print(f"\nRetrieval accuracy @top-1: {hits_at_1}/{total} = {hits_at_1/total:.0%}")


if __name__ == "__main__":
    evaluate()