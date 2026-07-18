# scripts/get_zheng68k.py
import scanpy as sc
from pathlib import Path
out = Path("data/raw/zheng68k"); out.mkdir(parents=True, exist_ok=True)

# scvi-tools packages Zheng68k with labels
# pip install scvi-tools first
import scvi
adata = scvi.data.pbmc_dataset()  # or the purified 68k loader
adata.write(out / "zheng68k_full.h5ad")
print(adata.shape, adata.obs.columns.tolist())