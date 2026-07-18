import numpy as np, pytest
from anndata import AnnData


@pytest.fixture
def fake_final():
    """A minimal run_pipeline() output for fast tests (no real pipeline)."""
    class C: parameter="resolution"; value=0.8; pmid="123"; verified=True; confidence="HIGH"
    class A:
        cluster_id="0"; cell_type="T cell"; confidence="HIGH"; cell_state="memory"
        marker_genes=["CD3D","IL7R"]; method_votes={"singler":"T_cells"}; sources={"kb2":"PMID:1"}
    ad = AnnData(np.ones((10, 3), dtype="float32"))
    ad.obs["leiden"] = ["0"]*10
    ad.obsm["X_umap"] = np.zeros((10, 2))

    class Cfg:
        def model_dump(self): return {"resolution": 0.8, "n_pcs": 50}
    return {"config": Cfg(), "claims": [C()], "annotations": [A()],
            "log": [{"agent": "data", "action": "loaded"}], "adata": ad, "error": None}