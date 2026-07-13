from src.schemas.state import PipelineState
from src.agents.data_agent import DataAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.annotation_agent import AnnotationAgent

state = PipelineState(input_path="data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")
state = DataAgent().run(state)
state = AnalysisAgent().run(state)
state = AnnotationAgent().run(state)

for a in state.annotations:
    state_str = f" | state: {a.cell_state}" if a.cell_state else ""
    print(f"cluster {a.cluster_id}: {a.cell_type:14} [{a.confidence}]{state_str}")