# tests/agents/test_verifier_adversarial.py — NFR-06: 20-claim adversarial set (Member 3)
from src.schemas.state import PipelineState, Claim
from src.agents.verifier_agent import VerifierAgent


def _run(claims):
    s = PipelineState(input_path="x", tissue="PBMC")
    s.claims = claims
    return VerifierAgent().run(s)


# 20 deliberately-wrong claims across the three failure modes the Verifier checks:
# out-of-range values, missing citations, and tissue-context mismatches.
BAD_CLAIMS = [
    # --- out-of-range (7) ---
    Claim("resolution", 99.0, pmid="1", tissue="PBMC"),
    Claim("resolution", -1.0, pmid="2", tissue="PBMC"),
    Claim("mito_pct", 90.0, pmid="3", tissue="PBMC"),
    Claim("mito_pct", -5.0, pmid="4", tissue="PBMC"),
    Claim("n_pcs", 500, pmid="5", tissue="PBMC"),
    Claim("n_pcs", 0, pmid="6", tissue="PBMC"),
    Claim("resolution", 10.0, pmid="7", tissue="PBMC"),
    # --- missing citation (6) ---
    Claim("resolution", 0.5, pmid="", tissue="PBMC"),
    Claim("mito_pct", 10.0, pmid="", tissue="PBMC"),
    Claim("n_pcs", 30, pmid="", tissue="PBMC"),
    Claim("resolution", 0.8, pmid="", tissue="general"),
    Claim("mito_pct", 5.0, pmid="", tissue="PBMC"),
    Claim("n_pcs", 50, pmid="", tissue="general"),
    # --- tissue-context mismatch (7) ---
    Claim("resolution", 0.5, pmid="8", tissue="tumor"),
    Claim("mito_pct", 15.0, pmid="9", tissue="tumor"),
    Claim("n_pcs", 40, pmid="10", tissue="lung"),
    Claim("resolution", 0.6, pmid="11", tissue="brain"),
    Claim("mito_pct", 12.0, pmid="12", tissue="liver"),
    Claim("n_pcs", 35, pmid="13", tissue="kidney"),
    Claim("resolution", 0.7, pmid="14", tissue="heart"),
]


def test_adversarial_detection_rate():
    """NFR-06: verifier must catch >=90% of 20 deliberately-wrong claims
    for a PBMC dataset."""
    state = _run(list(BAD_CLAIMS))
    caught = sum(not c.verified for c in state.claims)
    rate = caught / len(state.claims)
    print(f"\nNFR-06 detection rate: {caught}/{len(state.claims)} = {rate:.0%}")
    assert rate >= 0.90


def test_valid_claims_not_flagged():
    """Sanity: genuinely-good claims must pass, so the verifier isn't just
    rejecting everything."""
    good = [
        Claim("resolution", 0.5, pmid="100", tissue="PBMC"),
        Claim("mito_pct", 5.0, pmid="101", tissue="PBMC"),
        Claim("n_pcs", 30, pmid="102", tissue="general"),
    ]
    state = _run(good)
    assert all(c.verified for c in state.claims)