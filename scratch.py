from src.schemas.state import PipelineState
from src.agents.data_agent import DataAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.annotation_agent import AnnotationAgent

state = PipelineState(input_path="data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")
state = DataAgent().run(state)
state = AnalysisAgent().run(state)
state = AnnotationAgent().run(state)

print(f"{'cluster':8}{'cell_type':16}{'confidence':12}{'votes'}")
for a in state.annotations:
    print(f"{a.cluster_id:8}{a.cell_type:16}{a.confidence:12}{a.method_votes}")

print("\nReview queue (LOW):", [a.cluster_id for a in state.review_queue()])