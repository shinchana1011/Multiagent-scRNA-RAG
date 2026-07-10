from src.schemas.state import PipelineState, Claim, Annotation
from src.agents.base import BaseAgent

# build a state and add a claim + annotation
s = PipelineState(input_path="data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")
s.claims.append(Claim(parameter="resolution", value=0.5, pmid="12345"))
s.annotations.append(Annotation(cluster_id="0", cell_type="CD4 T cell", confidence="LOW"))
s.log_event("test", "created")

print("state OK:", s.tissue, "| claims:", len(s.claims))
print("review queue:", [a.cluster_id for a in s.review_queue()])   # LOW ones

# confirm BaseAgent can't be instantiated directly (it's abstract)
try:
    BaseAgent()
    print("ERROR: BaseAgent should be abstract")
except TypeError:
    print("BaseAgent correctly abstract")