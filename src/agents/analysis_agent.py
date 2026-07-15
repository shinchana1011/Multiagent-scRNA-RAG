# src/agents/analysis_agent.py — wraps Member 1's pipeline (Member 3, Task 2)
from src.agents.base import BaseAgent
from src.schemas.state import PipelineState
from src.pipeline.runner import run_analysis


class AnalysisAgent(BaseAgent):
    agent_id = "analysis"

    def run(self, state: PipelineState) -> PipelineState:
        if state.adata is None:
            state.error = state.error or "No data to analyse"
            return state
        state.adata = run_analysis(state.adata, state.config)
        n = state.adata.obs["leiden"].nunique()
        state.log_event(self.agent_id, "analysed", {"clusters": n})
        return state

    def validate(self, state: PipelineState) -> bool:
        return (state.adata is not None
                and "leiden" in state.adata.obs and "X_umap" in state.adata.obsm)