from src.agents.annotation.consensus import score_consensus

def test_unanimous_high():
    assert score_consensus({"a": "B cell", "b": "B cell", "c": "B cell"}) == ("B cell", "HIGH")

def test_majority_med():
    assert score_consensus({"a": "B cell", "b": "B cell", "c": "T cell"}) == ("B cell", "MED")

def test_tie_low():
    assert score_consensus({"a": "B cell", "b": "T cell"})[1] == "LOW"

def test_ignores_unknown():
    # only "a" is a valid vote (b=Unknown, c=empty are excluded) -- a single
    # method's opinion must not be reported as HIGH-confidence consensus.
    assert score_consensus({"a": "B cell", "b": "Unknown", "c": ""}) == ("B cell", "LOW")

def test_single_valid_vote_is_low_not_high():
    assert score_consensus({"a": "B cell"}) == ("B cell", "LOW")