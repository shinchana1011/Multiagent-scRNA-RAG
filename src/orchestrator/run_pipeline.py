# Orchestrates the complete workflow
# src/orchestrator/run_pipeline.py — one-call entry point (Member 3, Task 6)
from __future__ import annotations
from src.schemas.state import PipelineState
from src.orchestrator.graph import build_graph


def run_pipeline(input_path: str, tissue: str = "general", disease: str = "") -> PipelineState:
    graph = build_graph()
    initial = PipelineState(input_path=input_path, tissue=tissue, disease=disease)
    final = graph.invoke(initial)

    # FR-26: persist audit trail to disk
    try:
        audit = PipelineState(input_path=input_path, tissue=tissue)
        audit.config = final["config"]
        audit.claims = final["claims"]
        audit.annotations = final["annotations"]
        audit.log = final["log"]
        audit.export_audit()
    except Exception as e:
        from loguru import logger
        logger.warning("audit export failed: {}", e)

    return final