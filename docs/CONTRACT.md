# Pipeline Integration Contract (FROZEN — do not change field names without team signoff)

Entry point: run_pipeline(input_path: str, tissue: str, disease: str) -> dict

Returned dict keys (consumed by Member 4's API, UI, reporting):
  config      : PipelineConfig   — .model_dump() gives parameter dict
  claims      : list[Claim]      — .parameter .value .pmid .verified .confidence
  annotations : list[Annotation] — .cluster_id .cell_type .confidence .cell_state
                                    .marker_genes .method_votes .sources
  log         : list[dict]       — audit events
  adata       : AnnData          — .obs["leiden"], .obsm["X_umap"], .raw
  error       : str | None       — set if pipeline failed gracefully

Any rename to these field names breaks Member 4's integration layer (src/api/adapters.py).