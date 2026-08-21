from src.agents.annotation.consensus import score_consensus

def test_unanimous_high():
    assert score_consensus({"a": "B cell", "b": "B cell", "c": "B cell"}) == ("B cell", "HIGH")

def test_majority_med():
    assert score_consensus({"a": "B cell", "b": "B cell", "c": "T cell"}) == ("B cell", "MED")

def test_tie_low():
    assert score_consensus({"a": "B cell", "b": "T cell"})[1] == "LOW"

def test_ignores_unknown():
    assert score_consensus({"a": "B cell", "b": "Unknown", "c": ""}) == ("B cell", "HIGH")