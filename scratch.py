from src.schemas.state import PipelineState
from src.agents.data_agent import DataAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.annotation_agent import AnnotationAgent

state = PipelineState(input_path="data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")
state = DataAgent().run(state)
state = AnalysisAgent().run(state)
state = AnnotationAgent().run(state)

print(f"\n{'cluster':8}{'cell_type':14}{'conf':6}{'votes'}")
for a in state.annotations:
    print(f"{a.cluster_id:8}{a.cell_type:14}{a.confidence:6}{a.method_votes}")
print("\nreview queue:", [a.cluster_id for a in state.review_queue()])