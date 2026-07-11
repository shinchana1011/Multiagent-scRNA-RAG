# src/agents/annotation_agent.py — runs all methods + consensus (Member 3, Task 5)
from src.agents.base import BaseAgent
from src.schemas.state import PipelineState, Annotation
from src.pipeline.markers import top_markers_table
from src.agents.annotation.method_overlap import annotate_overlap
from src.agents.annotation.method_kb2 import annotate_kb2
from src.agents.annotation.method_singler import annotate_singler
from src.agents.annotation.consensus import score_consensus


class AnnotationAgent(BaseAgent):
    agent_id = "annotation"

    def run(self, state: PipelineState) -> PipelineState:
        adata = state.adata
        methods = {
            "overlap": annotate_overlap(adata),
            "kb2":     annotate_kb2(adata),
            "singler": annotate_singler(adata),   # stub -> {} for now
        }
        table = top_markers_table(adata, n=5)
        clusters = sorted(adata.obs["leiden"].cat.categories, key=int)

        for cid in clusters:
            votes = {m: methods[m].get(cid, "") for m in methods}
            cell_type, confidence = score_consensus(votes)
            markers = list(table[table["cluster"] == cid]["gene"])
            state.annotations.append(Annotation(
                cluster_id=cid, cell_type=cell_type, confidence=confidence,
                marker_genes=markers, method_votes=votes,
            ))

        n_high = sum(a.confidence == "HIGH" for a in state.annotations)
        n_review = len(state.review_queue())
        state.log_event(self.agent_id, "annotated",
                        {"clusters": len(clusters), "high": n_high, "review": n_review})
        return state

    def validate(self, state: PipelineState) -> bool:
        return len(state.annotations) == state.adata.obs["leiden"].nunique()