import numpy as np
import pytest
from anndata import AnnData
from src.io.readers import load_dataset

def _tiny(counts=True):
    rng = np.random.default_rng(0)
    X = rng.poisson(1.0, size=(50, 20)).astype("float32")
    if not counts:
        X = X + 0.3                       # fractional -> looks normalised
    a = AnnData(X)
    a.var_names = [f"GENE{i}" for i in range(20)]
    a.obs_names = [f"cell{i}" for i in range(50)]
    return a

def test_loads_h5ad(tmp_path):
    p = tmp_path / "tiny.h5ad"; _tiny().write(p)
    a = load_dataset(p)
    assert a.n_obs == 50 and a.n_vars == 20

def test_rejects_unknown_format(tmp_path):
    p = tmp_path / "data.txt"; p.write_text("nope")
    with pytest.raises(ValueError):
        load_dataset(p)

def test_rejects_normalised(tmp_path):
    p = tmp_path / "norm.h5ad"; _tiny(counts=False).write(p)
    with pytest.raises(ValueError):
        load_dataset(p)