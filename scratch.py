from src.io.readers import load_dataset
from src.schemas.config import PipelineConfig
from src.pipeline.runner import run_analysis
from src.plots.figures import plot_umap, plot_marker_dotplot

from src.rag.parameter_recommender import recommend_parameters
from src.io.readers import load_dataset
from src.pipeline.runner import run_analysis


adata = load_dataset("data/raw/pbmc3k/pbmc3k_raw.h5ad")
cfg = PipelineConfig()                       # all defaults (the RAG-off baseline)
adata = run_analysis(adata, cfg)

print(adata)
print("clusters:", adata.obs["leiden"].nunique())
plot_umap(adata, "data/processed/figures")
plot_marker_dotplot(adata, "data/processed/figures")


from src.rag.retriever import Retriever

r = Retriever()
for h in r.retrieve("mito cutoff and clustering resolution", tissue="lung", k=3):
    print(f"[{h['score']:.2f}] {h['tissue']:8} PMID:{h['pmid']}  {h['text'][:70]}...")

from src.rag.parameter_recommender import recommend_parameters

cfg, claims = recommend_parameters(tissue="lung", disease="COVID")
print("CONFIG:", cfg.mito_pct, cfg.n_pcs, cfg.resolution)
for c in claims:
    print(f"  {c['parameter']} = {c['value']}  <- PMID:{c['pmid']} ({c['tissue']})")


# 1. Member 2's job: look up parameters from literature for lung/COVID
cfg, claims = recommend_parameters(tissue="lung", disease="COVID")

print("Parameters chosen from literature:")
print(f"  mito_pct   = {cfg.mito_pct}")
print(f"  n_pcs      = {cfg.n_pcs}")
print(f"  resolution = {cfg.resolution}")
print("Backed by these papers:")
for c in claims:
    print(f"  {c['parameter']} = {c['value']}  (PMID:{c['pmid']})")

# 2. Member 1's pipeline runs with THOSE parameters, not defaults
adata = load_dataset("data/raw/pbmc3k/pbmc3k_raw.h5ad")
adata = run_analysis(adata, cfg)      # <-- this is "feeding the config in"

print(f"\nDone: {adata.obs['leiden'].nunique()} clusters using literature-based parameters")

from src.knowledge_base.kb2_annotation import AnnotationKB

kb2 = AnnotationKB()
# pretend a cluster's top markers came out of Member 1's pipeline:
for hit in kb2.annotate(["CD3D", "IL7R", "CCR7", "CD3E"], n=3):
    print(f"  {hit['cell_type']:16} (dist {hit['distance']:.2f}, PMID:{hit['pmid']})")