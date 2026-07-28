# src/pipeline/gene_ids.py — Ensembl gene ID -> HGNC symbol remapping.
#
# Some labeled benchmark sets (e.g. scvi-tools' pbmc_dataset) ship with
# var_names as Ensembl IDs (ENSG...) instead of gene symbols. The annotation
# methods (marker-overlap panel, KB-2 seed corpus, SingleR/celldex reference)
# all key on gene symbols, so those genes are silently unmatchable without
# this remap. The mapping table is vendored from the standard 10x Genomics
# CellRanger GRCh38 reference (data/pbmc4k/filtered_gene_bc_matrices.tar.gz,
# filtered_gene_bc_matrices/GRCh38/genes.tsv) -- not fetched at runtime, so
# this works fully offline and isn't a guess.
from __future__ import annotations

from pathlib import Path

from anndata import AnnData
from loguru import logger

_DEFAULT_MAP_PATH = "data/kb/ensembl_to_symbol_grch38.tsv"


def load_ensembl_to_symbol(path: str = _DEFAULT_MAP_PATH) -> dict[str, str]:
    """Read the vendored two-column (Ensembl ID, symbol) TSV into a dict."""
    mapping: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            mapping[parts[0]] = parts[1]
    return mapping


def remap_var_names_to_symbol(adata: AnnData, map_path: str = _DEFAULT_MAP_PATH) -> AnnData:
    """Return a copy of adata with var_names swapped from Ensembl ID to gene
    symbol wherever the mapping has an entry. Genes with no mapping entry keep
    their original ID (not dropped) so no data is silently discarded; genes
    that collide on the same symbol are de-duplicated via var_names_make_unique.
    """
    mapping = load_ensembl_to_symbol(map_path)
    n_total = adata.n_vars
    symbols = [mapping.get(g, g) for g in adata.var_names]
    n_mapped = sum(1 for g in adata.var_names if g in mapping)

    adata = adata.copy()
    adata.var["ensembl_id"] = adata.var_names.values
    adata.var_names = symbols
    adata.var_names_make_unique()

    logger.info("Gene-ID remap: {}/{} var_names converted Ensembl ID -> symbol ({:.1f}%)",
                n_mapped, n_total, 100 * n_mapped / n_total)
    return adata
