from src.orchestrator.run_pipeline import run_pipeline
final = run_pipeline("data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")
print("annotations:", len(final["annotations"]), "| retries:", final["retry_count"])