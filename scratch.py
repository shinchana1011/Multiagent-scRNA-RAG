# scratch.py
from src.io.readers import load_dataset
from src.pipeline.qc import compute_qc_metrics, filter_cells_genes
from src.pipeline.normalize import normalize, select_hvg, scale
from src.pipeline.reduce import run_pca, integrate_harmony, compute_neighbors
from src.pipeline.cluster import run_leiden

a = load_dataset("data/raw/pbmc3k/pbmc3k_raw.h5ad")
a = compute_qc_metrics(a)
a = filter_cells_genes(a)

a = normalize(a)
print("raw genes (full set, ~13714):", a.raw.n_vars)

a = select_hvg(a)
print("HVG genes (should be 2000):", a.n_vars)

a = scale(a)
print("X min (should be negative after z-scoring):", float(a.X.min()))
print(a)

a = run_pca(a)
print("PCA shape (should be n_cells x 50):", a.obsm["X_pca"].shape)

# pbmc3k has no "patient" column (single batch) — integrate_harmony would just
# warn and skip. Only call it on multi-batch data (e.g. the COVID cohort).
if "patient" in a.obs.columns:
    a = integrate_harmony(a, batch_key="patient")

a = compute_neighbors(a)
print("Neighbors graph present:", "distances" in a.obsp and "connectivities" in a.obsp)

a = run_leiden(a)
print("Leiden clusters found:", a.obs["leiden"].nunique())
print(a)