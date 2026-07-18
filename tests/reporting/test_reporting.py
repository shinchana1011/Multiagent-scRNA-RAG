# tests/reporting/test_reporting.py — Member 4 report generation tests
import numpy as np
from anndata import AnnData
from src.reporting.scorecard import compute_scorecard, scorecard_summary
from src.reporting.composition import compute_composition, composition_summary
from src.reporting.citations import collect_citations


def test_scorecard_computes():
    anns = [{"confidence": "HIGH"}, {"confidence": "HIGH"}, {"confidence": "LOW"}]
    claims = [{"verified": True}, {"verified": False}]
    sc = compute_scorecard(anns, claims)
    assert 0 <= sc["reliability_score"] <= 100
    assert sc["n_high"] == 2 and sc["n_low"] == 1
    assert sc["grade"] in ("A", "B", "C", "D")
    assert scorecard_summary(sc)                      # produces non-empty text


def test_citations_dedup():
    claims = [{"pmid": "111", "parameter": "resolution"},
              {"pmid": "111", "parameter": "n_pcs"}]
    anns = [{"sources": {"kb2": "KB-2 (PMID:222)"}}]
    cits = collect_citations(claims, anns)
    pmids = {c["pmid"] for c in cits}
    assert pmids == {"111", "222"}                    # deduped, both captured


def test_composition_flags_status():
    ad = AnnData(np.ones((10, 3), dtype="float32"))
    ad.obs["leiden"] = ["0"] * 10
    anns = [{"cluster_id": "0", "cell_type": "T cell"}]
    rows = compute_composition(ad, anns)
    assert rows[0]["cell_type"] == "T cell"
    assert rows[0]["fraction"] == 1.0
    assert rows[0]["status"] in ("within healthy range", "above healthy range",
                                 "below healthy range", "no reference")
    assert composition_summary(rows)                  # produces text