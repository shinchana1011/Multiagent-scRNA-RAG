# scratch.py
from src.orchestrator.run_pipeline import run_pipeline
final = run_pipeline("data/raw/covid_gse145926/covid_merged.h5ad",
                     tissue="PBMC", disease="COVID-19")
print("clusters:", len(final["annotations"]))