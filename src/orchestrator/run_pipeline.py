# Orchestrates the complete workflow
# src/orchestrator/run_pipeline.py — one-call entry point (Member 3, Task 6)
from __future__ import annotations
from src.schemas.state import PipelineState
from src.orchestrator.graph import build_graph


def run_pipeline(input_path: str, tissue: str = "general", disease: str = "") -> PipelineState:
    """Run the entire multi-agent pipeline autonomously with one call."""
    graph = build_graph()
    initial = PipelineState(input_path=input_path, tissue=tissue, disease=disease)
    final = graph.invoke(initial)
    # LangGraph returns a dict-like; rebuild a PipelineState for clean access
    return final