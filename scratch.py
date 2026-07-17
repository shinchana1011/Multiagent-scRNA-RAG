# scratch.py
from src.orchestrator.run_pipeline import run_pipeline
from src.api.adapters import state_to_results
final = run_pipeline("data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")
r = state_to_results(final)
print("keys:", list(r.keys()))
print("n_clusters:", r["n_clusters"], "| review_queue:", r["review_queue"])
print("first annotation:", r["annotations"][0])