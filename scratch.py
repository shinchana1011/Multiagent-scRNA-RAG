# scratch.py
from src.orchestrator.run_pipeline import run_pipeline
final = run_pipeline("data/raw/zheng68k/pbmc68k_reduced.h5ad", tissue="PBMC")  # pre-processed
print("error:", final.get("error"))
print("annotations:", len(final.get("annotations", [])))