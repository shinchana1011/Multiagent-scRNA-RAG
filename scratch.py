from src.schemas.state import PipelineState, Claim
from src.agents.verifier_agent import VerifierAgent

state = PipelineState(input_path="x", tissue="PBMC")
state.claims.append(Claim("resolution", 0.8, pmid="13328136"))   # good: sane + cited
state.claims.append(Claim("resolution", 99.0, pmid="12345"))     # bad: out of range
state.claims.append(Claim("mito_pct", 10.0, pmid=""))            # bad: no citation

VerifierAgent().run(state)

for c in state.claims:
    print(f"{c.parameter}={c.value:<6} verified={c.verified}  confidence={c.confidence}")