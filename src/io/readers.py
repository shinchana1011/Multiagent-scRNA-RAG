# src/io/readers.py — dataset loading + validation (Member 1, Task 1)
from __future__ import annotations

from pathlib import Path
import numpy as np
from scipy.sparse import issparse
from anndata import AnnData
import scanpy as sc
from loguru import logger

# columns that commonly hold gene symbols when var_names are Ensembl IDs
_SYMBOL_COLUMNS = ("feature_name", "gene_symbols", "gene_symbol", "Symbol", "symbol", "gene_name")


def load_dataset(path: str | Path) -> AnnData:
    """Load an scRNA-seq file (.h5 / .h5ad / .loom) into a validated AnnData.

    Guards applied every time:
      1. unique variable names   (prevents the concat / reindex crash)
      2. gene-symbol var index   (remaps Ensembl IDs so MT- and markers work)
      3. raw-counts sanity check (rejects already-normalised matrices)

    Raises FileNotFoundError, or ValueError on unsupported format / normalised data.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No such file: {path}")

    adata = _read_by_extension(path)
    adata.var_names_make_unique()      # guard 1
    _ensure_gene_symbols(adata)        # guard 2
    _validate_counts(adata)            # guard 3
    logger.info("Loaded {} -> {} cells x {} genes", path.name, adata.n_obs, adata.n_vars)
    return adata


def _read_by_extension(path: Path) -> AnnData:
    suffix = path.suffix.lower()
    if suffix == ".h5ad":
        return sc.read_h5ad(path)
    if suffix == ".h5":
        return sc.read_10x_h5(path)
    if suffix == ".loom":
        return sc.read_loom(path)
    raise ValueError(f"Unsupported format '{suffix}'. Use .h5, .h5ad, or .loom.")


def _ensure_gene_symbols(adata: AnnData) -> None:
    if not adata.var_names.astype(str).str.startswith("ENSG").any():
        return  # already gene symbols, nothing to do
    for col in _SYMBOL_COLUMNS:
        if col in adata.var.columns:
            adata.var["ensembl_id"] = adata.var_names
            adata.var_names = adata.var[col].astype(str)
            adata.var_names_make_unique()
            logger.info("Remapped Ensembl IDs to symbols via var['{}']", col)
            return
    logger.warning(
        "var_names look like Ensembl IDs but no symbol column found ({}). "
        "Mito filtering and marker genes may not work.", ", ".join(_SYMBOL_COLUMNS)
    )


def _validate_counts(adata: AnnData) -> None:
    sample = adata.X[:100]
    values = sample.data if issparse(sample) else np.asarray(sample).ravel()
    if values.size == 0:
        return
    if (values < 0).any():
        raise ValueError("Matrix has negative values — not raw counts.")
    if not np.allclose(values, np.round(values)):
        raise ValueError(
            "Matrix has non-integer values — looks normalised, not raw counts. "
            "The pipeline must start from raw counts (check for a 'counts' layer)."
        )