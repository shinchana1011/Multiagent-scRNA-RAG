from src.schemas.state import PipelineState
from src.agents.data_agent import DataAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.annotation.method_overlap import annotate_overlap
from src.agents.annotation.method_kb2 import annotate_kb2

state = PipelineState(input_path="data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")
state = DataAgent().run(state)
state = AnalysisAgent().run(state)     # uses default config; gives ~8 clusters

overlap = annotate_overlap(state.adata)
kb2 = annotate_kb2(state.adata)

print(f"{'cluster':8}{'overlap':18}{'kb2':18}")
for cid in sorted(overlap, key=int):
    print(f"{cid:8}{overlap[cid]:18}{kb2.get(cid,'?'):18}")