from src.orchestrator.run_pipeline import run_pipeline

final = run_pipeline("data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")

print("\n=== AUTONOMOUS PIPELINE COMPLETE ===")
print("claims:", [(c.parameter, c.value, c.confidence) for c in final["claims"]])
print("\nannotations:")
for a in final["annotations"]:
    print(f"  cluster {a.cluster_id}: {a.cell_type:16} [{a.confidence}]")
print("\nreview queue:", [a.cluster_id for a in final["annotations"] if a.confidence == "LOW"])