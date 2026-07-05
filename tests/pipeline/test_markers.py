import numpy as np
from anndata import AnnData
from src.pipeline.normalize import normalize, select_hvg, scale
from src.pipeline.reduce import run_pca, build_neighbors
from src.pipeline.cluster import run_leiden
from src.pipeline.markers import rank_markers, top_markers_table

def _clustered():
    rng = np.random.default_rng(0)
    X = rng.poisson(3.0, size=(200, 100)).astype("float32")
    a = AnnData(X)
    a.var_names = [f"GENE{i}" for i in range(100)]
    a.obs_names = [f"cell{i}" for i in range(200)]
    a = scale(select_hvg(normalize(a), n_top_genes=30))
    a = run_pca(a, n_comps=10)
    a = build_neighbors(a, n_pcs=10)
    return run_leiden(a)

def test_rank_markers_uses_raw_full_gene_set():
    a = rank_markers(_clustered())
    n_clusters = a.obs["leiden"].nunique()
    assert len(a.uns["rank_genes_groups"]["names"].dtype.names) == n_clusters
    # markers must be drawn from the full raw gene set (100), not the 30 HVGs
    all_genes = set(a.raw.var_names)
    first_cluster = a.uns["rank_genes_groups"]["names"].dtype.names[0]
    assert set(a.uns["rank_genes_groups"]["names"][first_cluster]) <= all_genes

def test_top_markers_table_shape():
    a = rank_markers(_clustered())
    df = top_markers_table(a, n=5)
    assert list(df.columns) == ["cluster", "rank", "gene", "score"]
    n_clusters = a.obs["leiden"].nunique()
    assert len(df) == n_clusters * 5
