# src/agents/verifier_agent.py — three-check claim verification (Member 3, Task 3)
from src.agents.base import BaseAgent
from src.schemas.state import PipelineState

# physically sensible ranges per parameter
_RANGES = {
    "mito_pct":   (0.0, 50.0),
    "n_pcs":      (2, 100),
    "resolution": (0.0, 3.0),
}


class VerifierAgent(BaseAgent):
    agent_id = "verifier"

    def _check_range(self, claim) -> bool:
        lo, hi = _RANGES.get(claim.parameter, (float("-inf"), float("inf")))
        try:
            return lo <= float(claim.value) <= hi
        except (TypeError, ValueError):
            return False

    def _check_citation(self, claim) -> bool:
        return bool(claim.pmid)          # must carry a source

    def _check_context(self, claim, state) -> bool:
        # placeholder: real version compares the cited paper's tissue to state.tissue.
        # for now, accept (context data isn't stored on the claim yet).
        return True

    def run(self, state: PipelineState) -> PipelineState:
        for claim in state.claims:
            passed = (self._check_range(claim)
                      and self._check_citation(claim)
                      and self._check_context(claim, state))
            if passed:
                claim.verified = True
                claim.confidence = "HIGH"
            else:
                claim.verified = False
                claim.downgrade()
                state.log_event(self.agent_id, "claim_failed",
                                {"param": claim.parameter, "value": claim.value})
        n_verified = sum(c.verified for c in state.claims)
        state.log_event(self.agent_id, "verified",
                        {"passed": n_verified, "total": len(state.claims)})
        return state

    def validate(self, state: PipelineState) -> bool:
        # verification never hard-stops the pipeline; it only re-scores confidence
        return True