from src.api.adapters import state_to_results


def test_results_shape(fake_final):
    r = state_to_results(fake_final)
    assert r["n_clusters"] == 1
    assert r["annotations"][0]["cell_type"] == "T cell"
    assert r["claims"][0]["verified"] is True
    assert r["review_queue"] == []          # no LOW clusters

def test_review_queue_flags_low(fake_final):
    fake_final["annotations"][0].confidence = "LOW"
    r = state_to_results(fake_final)
    assert r["review_queue"] == ["0"]