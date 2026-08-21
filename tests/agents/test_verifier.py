from src.schemas.state import PipelineState, Claim
from src.agents.verifier_agent import VerifierAgent

def _run(claims):
    s = PipelineState(input_path="x", tissue="PBMC")
    s.claims = claims
    return VerifierAgent().run(s)

def test_good_claim_verified():
    s = _run([Claim("resolution", 0.5, pmid="123")])
    assert s.claims[0].verified and s.claims[0].confidence == "HIGH"

def test_out_of_range_caught():
    s = _run([Claim("resolution", 50.0, pmid="123")])
    assert not s.claims[0].verified

def test_missing_citation_caught():
    s = _run([Claim("mito_pct", 10.0, pmid="")])
    assert not s.claims[0].verified

def test_detection_rate():
    # 5 deliberately-bad claims; verifier should catch all
    bad = [Claim("resolution", 99, "1"), Claim("n_pcs", 500, "2"),
           Claim("mito_pct", 90, "3"), Claim("resolution", 0.5, ""),  # no cite
           Claim("mito_pct", -5, "5")]
    s = _run(bad)
    caught = sum(not c.verified for c in s.claims)
    assert caught / len(bad) >= 0.90      # NFR-06 target

def test_context_mismatch_caught():
    from src.schemas.state import PipelineState, Claim
    from src.agents.verifier_agent import VerifierAgent
    s = PipelineState(input_path="x", tissue="PBMC")
    s.claims = [Claim("resolution", 0.5, pmid="1", tissue="tumor")]
    VerifierAgent().run(s)
    assert not s.claims[0].verified          # wrong tissue -> not verified

def test_context_general_passes():
    from src.schemas.state import PipelineState, Claim
    from src.agents.verifier_agent import VerifierAgent
    s = PipelineState(input_path="x", tissue="PBMC")
    s.claims = [Claim("resolution", 0.5, pmid="1", tissue="general")]
    VerifierAgent().run(s)
    assert s.claims[0].verified              # general applies anywhere

def test_fr08_attempts_alternative_on_failure():
    from src.schemas.state import PipelineState, Claim
    from src.agents.verifier_agent import VerifierAgent
    s = PipelineState(input_path="x", tissue="PBMC")
    s.claims = [Claim("resolution", 99.0, pmid="bad", tissue="PBMC")]
    VerifierAgent().run(s)
    # proof the retry/alternative path executed
    assert any(e["action"] == "claim_failed_retrying" for e in s.log)