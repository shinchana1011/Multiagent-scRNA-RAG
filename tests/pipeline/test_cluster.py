import numpy as np
from anndata import AnnData
from src.pipeline.normalize import normalize, select_hvg, scale
from src.pipeline.reduce import run_pca, build_neighbors
from src.pipeline.cluster import run_leiden, run_umap

def _clustering_ready():
    rng = np.random.default_rng(0)
    X = rng.poisson(3.0, size=(200, 100)).astype("float32")
    a = AnnData(X)
    a.var_names = [f"GENE{i}" for i in range(100)]
    a.obs_names = [f"cell{i}" for i in range(200)]
    a = scale(select_hvg(normalize(a), n_top_genes=30))
    a = run_pca(a, n_comps=10)
    return build_neighbors(a, n_pcs=10)

def test_leiden_assigns_cluster_labels():
    a = run_leiden(_clustering_ready())
    assert "leiden" in a.obs
    assert a.obs["leiden"].nunique() >= 1
    assert len(a.obs["leiden"]) == a.n_obs

def test_leiden_is_deterministic_given_random_state():
    a1 = run_leiden(_clustering_ready(), random_state=0)
    a2 = run_leiden(_clustering_ready(), random_state=0)
    assert list(a1.obs["leiden"]) == list(a2.obs["leiden"])

def test_umap_writes_2d_embedding():
    a = run_leiden(_clustering_ready())
    a = run_umap(a)
    assert a.obsm["X_umap"].shape == (a.n_obs, 2)
