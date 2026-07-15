# src/agents/annotation/method_singler.py — real SingleR via rpy2 (Member 3, modern API)
from __future__ import annotations
import numpy as np
from loguru import logger


def annotate_singler(adata) -> dict[str, str]:
    try:
        import rpy2.robjects as ro
        from rpy2.robjects import numpy2ri
        from rpy2.robjects.packages import importr
        from rpy2.robjects.conversion import localconverter
        importr("SingleR"); importr("celldex")

        raw = adata.raw.to_adata() if adata.raw is not None else adata
        expr = raw.X
        expr = expr.toarray() if hasattr(expr, "toarray") else np.asarray(expr)
        expr = np.asarray(expr, dtype="float64").T
        # GUARD: SingleR needs enough genes/cells; bail cleanly if too small
        if expr.shape[0] < 100 or expr.shape[1] < 50:
            logger.warning("SingleR skipped: matrix too small {}", expr.shape)
            return {}
        genes = list(raw.var_names)
        clusters = list(adata.obs["leiden"].astype(str))
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv["expr"] = expr
        ro.globalenv["genes"] = ro.StrVector(genes)
        ro.globalenv["clusters"] = ro.StrVector(clusters)
        ro.r('rownames(expr) <- genes')
        ro.r('ref <- celldex::HumanPrimaryCellAtlasData()')
        ro.r('pred <- SingleR::SingleR(test=expr, ref=ref, labels=ref$label.main, clusters=clusters)')
        labels = list(ro.r('as.character(pred$labels)'))
        cluster_ids = list(ro.r('rownames(pred)'))
        result = {str(cid): str(lab) for cid, lab in zip(cluster_ids, labels)}
        logger.info("SingleR annotated {} clusters", len(result))
        return result
    except Exception as e:                       # noqa: BLE001
        logger.warning("SingleR failed ({}); returning no votes", e)
        return {}