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
        """Context check: the cited paper's tissue must match the dataset's
        tissue, OR be 'general' guidance (which applies to any tissue)."""
        claim_tissue = getattr(claim, "tissue", "general").lower()
        data_tissue = state.tissue.lower()
        return claim_tissue in (data_tissue, "general")

    def run(self, state: PipelineState) -> PipelineState:
        from src.rag.parameter_recommender import retrieve_alternative
        from src.schemas.state import Claim

        for claim in state.claims:
            tried_pmids = {claim.pmid}
            attempts = 0
            while attempts < 3:                       # cap re-retrieval attempts
                passed = (self._check_range(claim)
                          and self._check_citation(claim)
                          and self._check_context(claim, state))
                if passed:
                    claim.verified = True
                    claim.confidence = "HIGH"
                    break
                # FR-08: failed -> downgrade, then fetch an alternative source
                claim.downgrade()
                state.log_event(self.agent_id, "claim_failed_retrying",
                                {"param": claim.parameter, "pmid": claim.pmid})
                alt = retrieve_alternative(claim.parameter, state.tissue, tried_pmids)
                if alt is None:
                    break                             # no alternative in KB-1; stop
                tried_pmids.add(alt["pmid"])
                claim.value = alt["value"]            # swap in the alternative
                claim.pmid = alt["pmid"]
                claim.tissue = alt["tissue"]
                attempts += 1

        n_verified = sum(c.verified for c in state.claims)
        state.log_event(self.agent_id, "verified",
                        {"passed": n_verified, "total": len(state.claims)})
        return state

    def validate(self, state: PipelineState) -> bool:
        # verification never hard-stops the pipeline; it only re-scores confidence
        return True