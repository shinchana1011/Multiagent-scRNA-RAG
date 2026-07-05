from src.io.readers import load_dataset
from src.schemas.config import PipelineConfig
from src.pipeline.runner import run_analysis
from src.plots.figures import plot_umap, plot_marker_dotplot

adata = load_dataset("data/raw/pbmc3k/pbmc3k_raw.h5ad")
cfg = PipelineConfig()                       # all defaults (the RAG-off baseline)
adata = run_analysis(adata, cfg)

print(adata)
print("clusters:", adata.obs["leiden"].nunique())
plot_umap(adata, "data/processed/figures")
plot_marker_dotplot(adata, "data/processed/figures")
