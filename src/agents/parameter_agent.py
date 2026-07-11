# src/agents/parameter_agent.py — wraps Member 2's RAG recommender (Member 3, Task 2)
from src.agents.base import BaseAgent
from src.schemas.state import PipelineState, Claim
from src.rag.parameter_recommender import recommend_parameters


class ParameterAgent(BaseAgent):
    agent_id = "parameter"

    def run(self, state: PipelineState) -> PipelineState:
        cfg, claims = recommend_parameters(state.tissue, state.disease)   # Member 2's code
        state.config = cfg
        for c in claims:
            state.claims.append(Claim(parameter=c["parameter"], value=c["value"],
                                      pmid=c["pmid"], confidence=c.get("confidence", "MED")))
        state.log_event(self.agent_id, "recommended",
                        {"n_claims": len(claims), "resolution": cfg.resolution})
        return state

    def validate(self, state: PipelineState) -> bool:
        return state.config is not None      # always returns a config (defaults if RAG finds nothing)