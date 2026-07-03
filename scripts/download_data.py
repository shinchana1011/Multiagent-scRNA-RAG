# scripts/download_data.py
import scanpy as sc, anndata as ad
from pathlib import Path

def fetch_pbmc3k(out="data/raw/pbmc3k/pbmc3k_raw.h5ad"):
    adata = sc.datasets.pbmc3k()
    adata.write(out)
def fetch_covid_gse145926(patient_files: dict, out="data/raw/covid_gse145926/covid_merged.h5ad"):
    parts = []
    for patient_id, path in patient_files.items():
        a = sc.read_10x_h5(path)
        a.var_names_make_unique()          # <-- add this line: fixes the duplicate gene names
        a.obs["patient"] = patient_id
        parts.append(a)
    ad.concat(parts, join="outer", index_unique="-").write(out)

def fetch_tabula_sapiens(adata, out="data/raw/tabula_sapiens/ts_100k.h5ad"):
    sc.pp.subsample(adata, n_obs=100_000, random_state=0)
    adata.write(out)

if __name__ == "__main__":
    Path("data/raw/pbmc3k").mkdir(parents=True, exist_ok=True)
    fetch_pbmc3k()
    print("PBMC3k ready.")

    # --- COVID GSE145926 (manual download) ---
    covid_source = Path("data/raw/covid_gse145926/source")
    covid_source.mkdir(parents=True, exist_ok=True)          # make the folder so it's obvious
    covid_files = sorted(covid_source.glob("*.h5"))
    if covid_files:
        # filename GSM4339769_C141_..._matrix.h5  ->  patient id "C141"
        patient_map = {f.stem.split("_")[1]: str(f) for f in covid_files}
        fetch_covid_gse145926(patient_map)
        print(f"COVID ready: {len(patient_map)} patients.")
    else:
        print(f"COVID skipped. Download GSE145926_RAW.tar from GEO, "
              f"extract the .h5 files, and put them in: {covid_source.resolve()}")

    # --- Tabula Sapiens (manual download) ---
    ts_source = Path("data/raw/tabula_sapiens/source")
    ts_source.mkdir(parents=True, exist_ok=True)
    ts_files = sorted(ts_source.glob("*.h5ad"))
    if ts_files:
        fetch_tabula_sapiens(sc.read_h5ad(ts_files[0]))
        print("Tabula Sapiens ready.")
    else:
        print(f"Tabula skipped. Download a tissue .h5ad from CELLxGENE "
              f"and put it in: {ts_source.resolve()}")