# src/orchestrator/graph.py — LangGraph orchestration with retry loop (Member 3, Task 6 + FR-25)
from __future__ import annotations
from langgraph.graph import StateGraph, END
from loguru import logger

from src.schemas.state import PipelineState
from src.agents.data_agent import DataAgent
from src.agents.parameter_agent import ParameterAgent
from src.agents.verifier_agent import VerifierAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.annotation_agent import AnnotationAgent

_AGENTS = {
    "data": DataAgent(), "parameter": ParameterAgent(), "verifier": VerifierAgent(),
    "analysis": AnalysisAgent(), "annotation": AnnotationAgent(),
}
# the happy-path order
_NEXT = {"data": "parameter", "parameter": "verifier", "verifier": "analysis",
         "analysis": "annotation", "annotation": END}


def _node(name: str):
    agent = _AGENTS[name]
    def fn(state: PipelineState) -> PipelineState:
        state = agent.run(state)
        return state
    return fn


def _route(name: str):
    """Conditional edge: if validate() passed -> next node; if failed and retries
    remain -> loop back to this same node; if retries exhausted -> continue anyway."""
    agent = _AGENTS[name]
    def decide(state: PipelineState) -> str:
        if agent.validate(state):
            return _NEXT[name]                          # passed -> move on
        tries = state.retry_count.get(name, 0)
        if tries < state.max_retries:
            state.retry_count[name] = tries + 1
            logger.warning("{} failed validation; retry {}/{}", name, tries + 1, state.max_retries)
            return name                                 # loop back to retry
        logger.error("{} exhausted retries", name)
        if name == "data":                             # no data => cannot continue
            state.error = state.error or "Data loading failed after retries"
            return END                                 # stop the pipeline cleanly
        return _NEXT[name]                              # other agents: continue degraded
    return decide


def build_graph():
    g = StateGraph(PipelineState)
    for name in _AGENTS:
        g.add_node(name, _node(name))
    g.set_entry_point("data")
    for name in _AGENTS:
        # each node routes through its conditional edge
        targets = {_NEXT[name]: _NEXT[name], name: name}
        if _NEXT[name] is END:
            targets = {END: END, name: name}
        g.add_conditional_edges(name, _route(name), targets)
    return g.compile()