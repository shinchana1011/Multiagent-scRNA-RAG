# src/agents/annotation_agent.py — runs all methods + consensus (Member 3, Task 5)
from src.agents.base import BaseAgent
from src.schemas.state import PipelineState, Annotation
from src.pipeline.markers import top_markers_table
from src.agents.annotation.method_overlap import annotate_overlap
from src.agents.annotation.method_kb2 import annotate_kb2
from src.agents.annotation.method_singler import annotate_singler
from src.agents.annotation.consensus import score_consensus
from src.agents.annotation.cell_state import annotate_cell_state
from src.knowledge_base.kb2_annotation import AnnotationKB

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

        kb2_for_src = AnnotationKB()
        kb2_src_table = top_markers_table(adata, n=10)

        for cid in clusters:
            votes = {m: methods[m].get(cid, "") for m in methods}
            cell_type, confidence = score_consensus(votes)
            markers = list(table[table["cluster"] == cid]["gene"])
            # FR-19: record the source/citation behind each method's vote
            sources = {
                "overlap": "PanglaoDB / CellMarker2.0 (marker overlap)",
                "singler": "SingleR: HumanPrimaryCellAtlas (PMID:24048455)",
            }
            src_genes = list(kb2_src_table[kb2_src_table["cluster"] == cid]["gene"])
            kb2_hit = kb2_for_src.annotate(src_genes, n=1)
            if kb2_hit:
                sources["kb2"] = f"KB-2 (PMID:{kb2_hit[0]['pmid']})"

            ann = Annotation(
                cluster_id=cid, cell_type=cell_type, confidence=confidence,
                marker_genes=markers, method_votes=votes, sources=sources,
            )

            if confidence == "HIGH":
                from src.agents.annotation.cell_state import annotate_cell_state
                ann.cell_state = annotate_cell_state(adata, cid, cell_type)

            state.annotations.append(ann)

        n_high = sum(a.confidence == "HIGH" for a in state.annotations)
        n_review = len(state.review_queue())
        state.log_event(self.agent_id, "annotated",
                        {"clusters": len(clusters), "high": n_high, "review": n_review})
        return state

    def validate(self, state: PipelineState) -> bool:
        return len(state.annotations) == state.adata.obs["leiden"].nunique()