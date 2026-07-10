# src/agents/base.py — the interface every agent implements (Member 3, Task 1)
from __future__ import annotations

from abc import ABC, abstractmethod
from loguru import logger

from src.schemas.state import PipelineState


class BaseAgent(ABC):
    """Every agent inherits this. Two required methods:
      run(state)      -> do the agent's work, return the updated state
      validate(state) -> True if the output is acceptable; False triggers retry
    This uniform shape is what lets the orchestrator run all agents the same way.
    """
    agent_id: str = "base"

    def __init__(self) -> None:
        self.logger = logger.bind(agent=self.agent_id)

    @abstractmethod
    def run(self, state: PipelineState) -> PipelineState:
        ...

    @abstractmethod
    def validate(self, state: PipelineState) -> bool:
        ...