from src.schemas.state import PipelineState
from src.agents.data_agent import DataAgent
from src.agents.parameter_agent import ParameterAgent
from src.agents.analysis_agent import AnalysisAgent

state = PipelineState(input_path="data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")

for agent in [DataAgent(), ParameterAgent(), AnalysisAgent()]:
    state = agent.run(state)
    ok = agent.validate(state)
    print(f"{agent.agent_id:10} -> valid={ok}")

print("\nclusters:", state.adata.obs["leiden"].nunique())
print("claims:", [(c.parameter, c.value, c.pmid) for c in state.claims])