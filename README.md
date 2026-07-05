# MultiAgent-scRNA-RAG

**A Multi-Agent Retrieval-Augmented Framework for Reliable scRNA-seq UMAP Analysis and Cell-Type Annotation**

An autonomous, multi-agent, Retrieval-Augmented Generation (RAG) pipeline that takes a raw
single-cell RNA-seq file and produces a clustered, annotated UMAP with a publication-ready,
fully-cited report — grounding every analytical parameter in published literature and scoring
every cell-type annotation with a confidence level.

---

## Why this project

Standard scRNA-seq analysis is slow (6–8 weeks of expert effort per dataset), irreproducible
(parameters are chosen by intuition, not evidence), and unreliable at the annotation step
(different methods disagree by up to 30 percentage points). This system automates the full
pipeline while (1) retrieving evidence-based parameters from literature with citations, and
(2) cross-checking cell-type labels across three methods to produce confidence-scored,
verifiable output.

---

## Project status

| Stream | Component | Status |
|---|---|---|
| **Member 1** | Bioinformatics pipeline (ingestion → QC → norm → PCA/Harmony → Leiden → UMAP → markers) | ✅ **Working end-to-end** |
| Member 2 | RAG knowledge base (KB-1 / KB-2) + parameter retrieval | 🚧 In progress |
| Member 3 | Multi-agent system, verification, annotation, orchestration | 🚧 In progress |
| Member 4 | FastAPI backend, Streamlit UI, report generation, Docker/CI | 🚧 In progress |

The analysis pipeline runs today on PBMC3k and the multi-batch COVID (GSE145926) dataset.
The RAG, agent-orchestration, and UI layers are under active development.

---

## Architecture

```
User Interface (Streamlit)        [Member 4]
        │
FastAPI backend                   [Member 4]
        │
LangGraph orchestrator            [Member 3]
        │
Agents  ── RAG Parameter Agent    [Member 2/3]
        ── Verifier Agent         [Member 3]
        ── Analysis Agent ────────► Bioinformatics pipeline  [Member 1] ✅
        ── Annotation Agent       [Member 3]
        ── Report Agent           [Member 4]
        │
RAG layer ── KB-1 (Methods, FAISS) / KB-2 (Annotation, ChromaDB)  [Member 2]
        │
Storage (AnnData, logs, reports)
```

---

## Tech stack

- **Language:** Python 3.12+
- **Bioinformatics:** Scanpy 1.12, AnnData, harmonypy; SingleR + ScType (R, via rpy2)
- **AI / RAG:** LangGraph, LangChain, sentence-transformers, FAISS, ChromaDB
- **ML utils:** scikit-learn, scipy
- **Backend / Frontend:** FastAPI, Streamlit
- **Utilities:** Pydantic, python-dotenv, Loguru, pytest, Docker

---

## Repository structure

```
MultiAgent-scRNA-RAG/
├── data/
│   ├── raw/                # downloaded datasets (gitignored)
│   └── processed/          # pipeline outputs + figures (gitignored)
├── requirements/
│   ├── base.txt            # shared core
│   ├── pipeline.txt        # Member 1
│   ├── rag.txt             # Member 2
│   ├── agents.txt          # Member 3
│   ├── app.txt             # Member 4
│   └── dev.txt             # testing / linting
├── scripts/
│   ├── download_data.py    # fetch / assemble datasets
│   └── install_r_deps.R    # SingleR + celldex (Member 3)
├── src/
│   ├── io/readers.py       # load .h5/.h5ad/.loom + validation  [Task 1] ✅
│   ├── pipeline/
│   │   ├── qc.py           # QC metrics + filtering             [Task 2] ✅
│   │   ├── normalize.py    # normalise / HVG / scale            [Task 3] ✅
│   │   ├── reduce.py       # PCA / Harmony / neighbours         [Task 4] ✅
│   │   ├── cluster.py      # Leiden + UMAP                      [Task 5] ✅
│   │   ├── markers.py      # marker gene extraction             [Task 6] ✅
│   │   └── runner.py       # run_analysis(adata, cfg)           [Task 7] ✅
│   ├── plots/figures.py    # QC / UMAP / dotplot figures        [Task 8] ✅
│   └── schemas/config.py   # PipelineConfig (frozen contract)
├── tests/                  # pytest unit tests
├── requirements.txt        # installs all layers (for Docker)
├── Dockerfile
└── README.md
```

---

## Setup

### 1. Prerequisites
- Python 3.12 or newer
- Git
- (Member 3 only, later) R 4.3+ for SingleR/ScType

### 2. Clone and create a virtual environment
```bash
git clone https://github.com/shinchana1011/Multiagent-scRNA-RAG.git
cd Multiagent-scRNA-RAG
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
```

### 3. Install dependencies
Install only the layer you need. To run the analysis pipeline (Member 1):
```bash
pip install -r requirements/pipeline.txt
pip install -r requirements/dev.txt      # for running tests
```
For the full system (all members / Docker):
```bash
pip install -r requirements.txt
```

---

## Getting the data

Datasets are **not** committed to the repo. Fetch them with:
```bash
python scripts/download_data.py
```
- **PBMC3k** — downloads automatically via Scanpy.
- **COVID GSE145926** (multi-batch) — download `GSE145926_RAW.tar` from
  [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE145926), extract the twelve
  `.h5` files into `data/raw/covid_gse145926/source/`, then re-run the script.
- **Tabula Sapiens** (scale test) — download a tissue `.h5ad` from CELLxGENE into
  `data/raw/tabula_sapiens/source/`, then re-run.

The script prints the exact folder to place manual downloads in.

---

## Running the analysis pipeline

The entire Member 1 pipeline runs through one call. Minimal example:
```python
from src.io.readers import load_dataset
from src.schemas.config import PipelineConfig
from src.pipeline.runner import run_analysis
from src.plots.figures import plot_umap, plot_marker_dotplot

adata = load_dataset("data/raw/pbmc3k/pbmc3k_raw.h5ad")
cfg = PipelineConfig()                 # defaults = the RAG-off baseline
adata = run_analysis(adata, cfg)

print("clusters:", adata.obs["leiden"].nunique())
plot_umap(adata, "data/processed/figures")
plot_marker_dotplot(adata, "data/processed/figures")
```
Expected on PBMC3k: ~2,643 cells after QC, ~8–12 Leiden clusters, and a UMAP figure written
to `data/processed/figures/umap_leiden.png`.

`run_analysis(adata, cfg)` is the integration point: every parameter comes from `cfg`, so
Member 2's RAG-retrieved `PipelineConfig` plugs in with no code changes, and the default `cfg`
serves as the ablation baseline (NFR-05).

---

## Running tests

```bash
python -m pytest -v
```
Run a single module:
```bash
python -m pytest tests/pipeline/test_qc.py -v
```

---

## Team roles

| Member | Responsibility | Owns |
|---|---|---|
| 1 | Bioinformatics & data pipeline | `src/io/`, `src/pipeline/`, `src/plots/`, `scripts/` |
| 2 | RAG & knowledge base | `src/rag/`, `src/knowledge_base/`, `data/kb/` |
| 3 | Multi-agent system & AI logic | `src/agents/`, `src/orchestrator/`, `src/schemas/` |
| 4 | Backend, frontend & integration | `src/api/`, `src/ui/`, `src/reporting/`, `docker/`, `.github/` |

---

## Git workflow

- `main` — protected, always working.
- `dev` — integration branch.
- Feature branches per member: `feat/m1-pipeline`, `feat/m2-rag`, `feat/m3-agents`, `feat/m4-app`.
- PRs go into `dev`; `dev` is merged to `main` at weekly integration checkpoints.

**Contract rule:** `src/schemas/config.py` (`PipelineConfig`) is a shared contract. Do not rename
its fields without team sign-off — three streams depend on it.

---

## Benchmarks (targets)

| Metric | Target | Dataset |
|---|---|---|
| Clustering quality (ARI) | ≥ 0.75 | Zheng68k |
| Annotation accuracy | ≥ 80% | Zheng68k |
| Verifier sensitivity | ≥ 90% | adversarial citation set |
| Expert agreement (Cohen's κ) | ≥ 0.70 | 100 blind annotations |
| Batch mixing (iLISI) | > 1.5 | COVID GSE145926 |
| End-to-end runtime | < 10 min | PBMC3k |

---

## License

Released under an open-source license (see `LICENSE`). Benchmark datasets are publicly available
via NCBI GEO, 10x Genomics, and CELLxGENE.
