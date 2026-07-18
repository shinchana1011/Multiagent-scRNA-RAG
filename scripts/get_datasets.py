# scripts/get_datasets.py — download additional RAW datasets
import scanpy as sc
from pathlib import Path

out = Path("data/raw/extra"); out.mkdir(parents=True, exist_ok=True)

# Krumsiek11 — synthetic myeloid (small, raw-like) — good for a quick different test
try:
    ad = sc.datasets.krumsiek11()
    ad.write(out / "krumsiek11.h5ad")
    print("krumsiek11:", ad.shape)
except Exception as e:
    print("krumsiek11 failed:", e)

# Paul15 — myeloid progenitors (~2700 cells, raw counts)
try:
    ad = sc.datasets.paul15()
    ad.write(out / "paul15.h5ad")
    print("paul15:", ad.shape)
except Exception as e:
    print("paul15 failed:", e)

# moignard15 — early blood development
try:
    ad = sc.datasets.moignard15()
    ad.write(out / "moignard15.h5ad")
    print("moignard15:", ad.shape)
except Exception as e:
    print("moignard15 failed:", e)