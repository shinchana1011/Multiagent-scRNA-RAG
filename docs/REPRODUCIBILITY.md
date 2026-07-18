# Reproducibility

- Random seeds: random_state=0 throughout (PCA, neighbors, Leiden, UMAP).
- Datasets: PBMC3k (Scanpy), GSE145926 (GEO), pbmc68k_reduced (Scanpy) — accession IDs in README.
- KB-1: 11,251 vectors from open-access PubMed Central literature (scripts/fetch_pmc_corpus.py).
- Environment: pinned in requirements/*.txt; R 4.x + Bioconductor (SingleR, celldex); Ollama llama3.1.
- Tests: `pytest tests/` (62 tests). CI: .github/workflows/ci.yml.
- Audit trail: every run writes a JSON audit log (FR-26).