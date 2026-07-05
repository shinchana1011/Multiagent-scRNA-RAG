import numpy as np
from anndata import AnnData
from src.pipeline.normalize import normalize, select_hvg, scale

def _counts():
    rng = np.random.default_rng(0)
    X = rng.poisson(3.0, size=(200, 100)).astype("float32")
    a = AnnData(X)
    a.var_names = [f"GENE{i}" for i in range(100)]
    a.obs_names = [f"cell{i}" for i in range(200)]
    return a

def test_normalize_freezes_full_raw():
    a = normalize(_counts())
    assert a.raw is not None
    assert a.raw.n_vars == 100          # full gene set frozen before HVG

def test_hvg_subsets_but_raw_keeps_all():
    a = select_hvg(normalize(_counts()), n_top_genes=30)
    assert a.n_vars == 30               # working matrix shrunk
    assert a.raw.n_vars == 100          # .raw still has everything

def test_scale_zero_centers():
    a = scale(select_hvg(normalize(_counts()), n_top_genes=30))
    assert np.allclose(a.X.mean(axis=0), 0, atol=1e-4)
