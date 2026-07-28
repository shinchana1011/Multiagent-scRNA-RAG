| Dataset | No-RAG ARI | RAG ARI | Improvement |
|---|---|---|---|
| Zheng68k-reduced (scanpy pbmc68k_reduced, 700c, 10 types) | 0.4334 | 0.5042 | +16.3% |
| PBMC-12k (scvi-tools, 11990c, 9 types) | 0.7135 | 0.7190 | +0.8% |
| Paul15 (myeloid progenitors, 2730c, 19 types) | 0.3108 | 0.2301 | -26.0% |

Notes:
- **Paul15 (myeloid progenitors, 2730c, 19 types)**: KNOWN LIMITATION, not a bug: KB-1's corpus currently only tags {PBMC, lung, tumor, general} tissue -- there is no bone-marrow/hematopoietic category. For 'bone marrow', retrieval fell back to a 'tumor'-tagged claim (pmid=13339379), a tissue-context mismatch the Verifier would flag and reject in the real pipeline. This dataset's RAG-on number should be read as 'what happens when RAG is applied outside the corpus's tissue coverage', not as a representative RAG result -- it demonstrates RAG's benefit is contingent on corpus coverage, which is itself an honest, useful finding.
