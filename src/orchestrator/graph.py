# src/orchestrator/graph.py — LangGraph orchestration of all agents (Member 3, Task 6)
from __future__ import annotations

from langgraph.graph import StateGraph, END
from loguru import logger

from src.schemas.state import PipelineState
from src.agents.data_agent import DataAgent
from src.agents.parameter_agent import ParameterAgent
from src.agents.verifier_agent import VerifierAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.annotation_agent import AnnotationAgent

# instantiate once
_data = DataAgent()
_param = ParameterAgent()
_verify = VerifierAgent()
_analysis = AnalysisAgent()
_annotate = AnnotationAgent()


def _node(agent):
    """Wrap an agent's run() as a LangGraph node with validate-based logging."""

    def fn(state: PipelineState) -> PipelineState:
        state = agent.run(state)
        if not agent.validate(state):
            logger.warning("{} failed validation", agent.agent_id)
        return state

    return fn


def build_graph():
    g = StateGraph(PipelineState)

    g.add_node("data", _node(_data))
    g.add_node("parameter", _node(_param))
    g.add_node("verifier", _node(_verify))
    g.add_node("analysis", _node(_analysis))
    g.add_node("annotation", _node(_annotate))

    g.set_entry_point("data")

    g.add_edge("data", "parameter")
    g.add_edge("parameter", "verifier")
    g.add_edge("verifier", "analysis")
    g.add_edge("analysis", "annotation")
    g.add_edge("annotation", END)

    return g.compile()