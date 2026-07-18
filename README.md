# MultiAgent-scRNA-RAG

**A Multi-Agent Retrieval-Augmented Framework for Reliable scRNA-seq UMAP Analysis and Cell-Type Annotation**

An autonomous, multi-agent RAG pipeline that takes a raw single-cell RNA-seq file and produces a
clustered, annotated UMAP with a fully-cited, publication-ready report — grounding every analytical
parameter in published literature and scoring every cell-type annotation with a confidence level.

---

## Why this project

Standard scRNA-seq analysis is slow, irreproducible (parameters chosen by intuition), and unreliable
at annotation (methods disagree by up to 30 percentage points). This system automates the pipeline
while (1) retrieving evidence-based parameters from literature *with citations*, (2) verifying each
citation with a three-check protocol, and (3) cross-checking cell-type labels across three independent
methods to produce confidence-scored, reviewable output.

---

## Status: complete

| Stream | Component | Status |
|---|---|---|
| Member 1 | Bioinformatics pipeline (QC → norm → PCA/Harmony → Leiden → UMAP → markers) | ✅ Complete |
| Member 2 | RAG knowledge base (KB-1 FAISS / KB-2 ChromaDB) + parameter retrieval | ✅ Complete |
| Member 3 | Multi-agent system, verification, 3-method annotation, LangGraph orchestration | ✅ Complete |
| Member 4 | FastAPI backend, Streamlit UI, report generation, benchmarks, CI, containerization | ✅ Complete |

Runs end-to-end on PBMC3k, Paul15, and multi-batch COVID (GSE145926). 62 tests passing locally;
CI validates environment-independent components on every push.

---

## Architecture
Streamlit UI  ──►  FastAPI backend  ──►  LangGraph orchestrator
│
┌─────────────────────────────────────┼─────────────────────────────┐
Data Agent   Parameter Agent   Verifier Agent   Analysis Agent   Annotation Agent
│             │                │               │                  │
load/validate  RAG (KB-1)     3-check verify   Scanpy pipeline   3-method consensus
(SingleR + marker
overlap + KB-2)
│
Report generation
(UMAP · Methods · citations · scorecard · composition)

Single entry point: `run_pipeline(input_path, tissue, disease)` → dict with
`config, claims, annotations, log, adata, error`.

---

## Tech stack

- **Bioinformatics:** Scanpy, AnnData, harmonypy; SingleR + celldex (R, via rpy2)
- **RAG:** LangGraph, sentence-transformers, FAISS (KB-1), ChromaDB (KB-2)
- **LLM:** Ollama (llama3.1, local) — parameter extraction + Methods generation
- **Backend/Frontend:** FastAPI, Streamlit
- **Reporting:** reportlab (PDF), Jinja2, matplotlib
- **Utils:** Pydantic, Loguru, pytest; containerized via Podman/Docker

---

## Repository structure
Multiagent-scRNA-RAG/
├── .github/workflows/ci.yml    # CI (environment-independent tests)
├── .streamlit/config.toml      # UI config (upload size)
├── benchmarks/results/         # ARI / runtime / ablation outputs
├── data/
│   ├── kb/                     # KB-1 (FAISS) + KB-2 (ChromaDB) + corpus
│   ├── raw/                    # datasets (gitignored)
│   └── uploads/                # UI uploads (gitignored)
├── docker/                     # Dockerfile, Dockerfile.lite, docker-compose.yml
├── docs/                       # CONTRACT.md, MANUAL_TESTING.md, TESTING.md, agent_dag.png
├── requirements/               # base / app / agents / rag / pipeline / dev
├── src/
│   ├── io/                     # readers + validation           [Member 1]
│   ├── pipeline/               # QC, normalize, reduce, cluster, markers, runner  [Member 1]
│   ├── plots/                  # figures                          [Member 1]
│   ├── rag/                    # retriever, recommender, LLM extractor  [Member 2]
│   ├── knowledge_base/         # KB-1 / KB-2 stores               [Member 2]
│   ├── agents/                 # data, parameter, verifier, analysis, annotation  [Member 3]
│   ├── orchestrator/           # LangGraph graph + run_pipeline   [Member 3]
│   ├── schemas/                # PipelineConfig, PipelineState     [Member 1/3]
│   ├── api/                    # FastAPI backend + adapters        [Member 4]
│   ├── ui/                     # Streamlit dashboard               [Member 4]
│   ├── reporting/              # figures, methods, citations, scorecard, composition  [Member 4]
│   ├── config/                 # settings + logging                [Member 4]
│   └── benchmarks/             # ARI / runtime / ablation          [Member 4]
├── tests/                      # 62 tests (unit, integration, API, reporting, failure)
└── runs/                       # per-job outputs (gitignored)

---

## Setup

### Prerequisites
- Python 3.11+
- R 4.x + Bioconductor (SingleR, celldex) — for 3-method annotation
- [Ollama](https://ollama.com) running with `ollama pull llama3.1`

### Install
```bash
git clone https://github.com/shinchana1011/Multiagent-scRNA-RAG.git
cd Multiagent-scRNA-RAG
python -m venv venv
venv\Scripts\activate            # Windows  (source venv/bin/activate on macOS/Linux)

pip install -r requirements/base.txt -r requirements/app.txt \
            -r requirements/agents.txt -r requirements/rag.txt
# R deps (for SingleR):
R -e "install.packages('BiocManager'); BiocManager::install(c('SingleR','celldex'))"
```

**Windows R note:** if SingleR fails to load `stats.dll`, add R's binary folder to PATH
(`C:\Program Files\R\R-4.x.x\bin\x64`) and set `R_HOME`. The pipeline degrades gracefully to
2-method consensus if R is unavailable.

---

## Running the system

Three processes (three terminals):
```bash
ollama serve                                    # local LLM
python -m src.api.main                          # FastAPI backend  (localhost:8000)
python -m streamlit run src/ui/app.py           # UI               (localhost:8501)
```
Open http://localhost:8501, upload `data/raw/pbmc3k/pbmc3k_raw.h5ad`, select tissue = PBMC.
Watch progress → view annotated results, reliability scorecard, and composition → review
LOW-confidence clusters → download the PDF/HTML/JSON report.

**Programmatic use:**
```python
from src.orchestrator.run_pipeline import run_pipeline
final = run_pipeline("data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")
print(len(final["annotations"]), "clusters annotated")
```

**Input must be raw counts** (`.h5` / `.h5ad` / `.loom`). Pre-processed matrices are rejected by
design (FR-02) to prevent silent double-normalization.

---

## Reproduce benchmarks
```bash
python -m src.benchmarks.run_benchmarks
```
Outputs ARI / runtime / ablation plots + CSVs to `benchmarks/results/`.

---

## Testing
```bash
python -m pytest tests/ -v                 # full local suite (62 tests)
python -m pytest tests/ -v -m "not slow"   # fast subset (CI scope)
```
CI (GitHub Actions) runs environment-independent tests (integration, API, I/O, reporting) on every
push. Tests needing FAISS, LangGraph, R/SingleR, Ollama, or datasets run locally and via the manual
protocol in `docs/MANUAL_TESTING.md`.

---

## Containerization
```bash
podman build -f docker/Dockerfile.lite -t scrna-rag-lite .
podman run -p 8000:8000 scrna-rag-lite
# or full stack:  docker compose -f docker/docker-compose.yml up
```
Two images: `Dockerfile.lite` (Python-only, 2-method consensus, fast) and `Dockerfile`
(with R/SingleR for 3-method). Compose orchestrates API + UI + Ollama.

---

## Results

| Metric | Result | Notes |
|---|---|---|
| RAG ablation (ARI) | 0.43 → 0.50 (+16%) | RAG-off vs RAG-on, pbmc68k_reduced |
| Verifier detection | 100% (20/20) | adversarial citation set (NFR-06) |
| Retry recovery | 100% (4/4) | simulated agent failures (FR-25) |
| Batch mixing (iLISI) | 2.21 | COVID GSE145926 (> 1.5 target) |
| Retrieval accuracy | 83% top-1 | tissue-matched parameter retrieval |
| Annotation ARI | 0.43 | pbmc68k_reduced subset; below 0.75 target — see below |

**Honest limitations:** The FR-15 accuracy target (ARI ≥ 0.75 / accuracy ≥ 80%) was evaluated on the
700-cell `pbmc68k_reduced` benchmark subset and came in below target — Zheng68k is a known-difficult
benchmark (imbalanced, molecularly similar populations); full-scale raw Zheng68k validation is future
work. Expert biological validation (Cohen's κ) is documented as future work; the human-review queue
provides the operational review UI in its place.

---

## Team roles

| Member | Responsibility | Owns |
|---|---|---|
| 1 | Bioinformatics pipeline | `src/io`, `src/pipeline`, `src/plots` |
| 2 | RAG & knowledge base | `src/rag`, `src/knowledge_base`, `data/kb` |
| 3 | Multi-agent system & orchestration | `src/agents`, `src/orchestrator`, `src/schemas` |
| 4 | Backend, frontend, integration | `src/api`, `src/ui`, `src/reporting`, `src/benchmarks`, `docker`, `.github` |

---

## License
See `LICENSE`. Benchmark datasets are publicly available via NCBI GEO, 10x Genomics, and CELLxGENE.