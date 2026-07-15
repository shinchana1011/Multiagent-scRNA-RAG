# src/agents/data_agent.py — wraps Member 1's loader (Member 3, Task 2)
from src.agents.base import BaseAgent
from src.schemas.state import PipelineState
from src.io.readers import load_dataset
from loguru import logger


class DataAgent(BaseAgent):
    agent_id = "data"

    def run(self, state: PipelineState) -> PipelineState:
        try:
            state.adata = load_dataset(state.input_path)
            state.log_event(self.agent_id, "loaded",
                            {"cells": state.adata.n_obs, "genes": state.adata.n_vars})
        except Exception as e:                       # noqa: BLE001
            state.error = f"Data loading failed: {e}"
            state.adata = None
            logger.error("DataAgent failed: {}", e)
        return state

    def validate(self, state: PipelineState) -> bool:
        return state.adata is not None and getattr(state.adata, "n_obs", 0) > 0