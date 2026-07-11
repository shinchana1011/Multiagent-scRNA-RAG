# src/agents/analysis_agent.py — wraps Member 1's pipeline (Member 3, Task 2)
from src.agents.base import BaseAgent
from src.schemas.state import PipelineState
from src.pipeline.runner import run_analysis


class AnalysisAgent(BaseAgent):
    agent_id = "analysis"

    def run(self, state: PipelineState) -> PipelineState:
        state.adata = run_analysis(state.adata, state.config)   # Member 1's code
        n = state.adata.obs["leiden"].nunique()
        state.log_event(self.agent_id, "analysed", {"clusters": n})
        return state

    def validate(self, state: PipelineState) -> bool:
        return "leiden" in state.adata.obs and "X_umap" in state.adata.obsm