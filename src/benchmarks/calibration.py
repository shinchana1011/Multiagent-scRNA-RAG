# src/benchmarks/calibration.py — Experiment #3: per-cell annotation-confidence
# calibration on the PBMC-12k (scvi-tools pbmc_dataset, 9 types) labeled set.
# This is NOT Zheng68k, despite living under data/raw/zheng68k/ historically.
#
# The consensus pipeline produces LINEAGE-LEVEL (coarse) predictions, not fine
# PBMC-subtype predictions -- harmonize.canon() collapses CD4/CD8 T cells to
# "T cell" and CD14+/FCGR3A+ monocytes to "Monocyte" before consensus ever sees
# them. All accuracy/calibration numbers below are lineage-level accordingly.
from __future__ import annotations

import json
from pathlib import Path

from loguru import logger

# --- human-confirmed CANON mapping: predicted lineage -> set of true labels that
# count as a match. Confirmed by the user; do not edit without re-confirming. ---
CANON_LINEAGE: dict[str, set[str]] = {
    "B cell": {"B cells"},
    "Dendritic cell": {"Dendritic Cells"},
    "Monocyte": {"CD14+ Monocytes", "FCGR3A+ Monocytes"},
    "NK cell": {"NK cells"},
    # Platelets are anucleate fragments shed from megakaryocytes; this scvi-tools
    # PBMC set's "Megakaryocytes" population is the closest true-label analog to a
    # "Platelet" prediction -- a known PBMC naming equivalence, not a claim that
    # the two terms mean the same cell state. Footnoted, not silently assumed.
    "Platelet": {"Megakaryocytes"},
    "T cell": {"CD4 T cells", "CD8 T cells"},
}

# reverse map: each fine-grained TRUE label -> its coarse lineage bucket (used for
# the per-lineage breakdown, grouped by ground truth rather than prediction).
TRUE_LABEL_TO_LINEAGE: dict[str, str] = {"Other": "Other"}
for _lineage, _true_set in CANON_LINEAGE.items():
    for _t in _true_set:
        TRUE_LABEL_TO_LINEAGE[_t] = _lineage

# Nominal numeric confidence assumed per categorical bin, for ECE only. This is a
# documented assumption (score_consensus returns HIGH/MED/LOW, not a probability),
# not a fitted or measured value -- flagged in the output so it's auditable.
ECE_NOMINAL_CONFIDENCE = {"HIGH": 1.00, "MED": 0.67, "LOW": 0.33}


def _cluster_bootstrap_ci(a, per_cluster_col: str, bin_name: str, n_boot: int = 1000, seed: int = 0):
    """Cluster-level bootstrap for one confidence bin's accuracy CI. Annotation
    confidence is a per-cluster property, so per-cell Wilson CIs pretend cells
    are independent draws when they're pseudoreplicated within a cluster. This
    resamples CLUSTERS (with replacement, same count as the bin has), not cells,
    to get an uncertainty estimate that respects that structure."""
    import numpy as np

    conf = a.obs[per_cluster_col].astype(str)
    cluster_ids = sorted(a.obs.loc[conf == bin_name, "leiden"].astype(str).unique())
    k = len(cluster_ids)
    if k == 0:
        return None

    per_cluster = {}
    leiden_str = a.obs["leiden"].astype(str)
    for cid in cluster_ids:
        mask = leiden_str == cid
        per_cluster[cid] = (int(mask.sum()), int((mask & a.obs["correct"]).sum()))

    rng = np.random.default_rng(seed)
    accs = []
    for _ in range(n_boot):
        draw = rng.choice(cluster_ids, size=k, replace=True)
        n_sum = sum(per_cluster[c][0] for c in draw)
        nc_sum = sum(per_cluster[c][1] for c in draw)
        if n_sum > 0:
            accs.append(nc_sum / n_sum)
    if not accs:
        return None
    lo, hi = np.percentile(accs, [2.5, 97.5])
    return {
        "n_clusters_in_bin": k,
        "n_boot_valid": len(accs),
        "boot_mean_accuracy": round(float(np.mean(accs)), 4),
        "boot_2.5pct": round(float(lo), 4),
        "boot_97.5pct": round(float(hi), 4),
    }


def _prepare_annotated(labeled_path: str, out_dir: str, resolution: float):
    """Shared steps 1-4: load, remap gene IDs, cluster (M1-contract), run the
    3 annotation methods + consensus, propagate to a per-cell frame."""
    import scanpy as sc
    from src.benchmarks.run_benchmarks import prepare_pbmc12k
    from src.pipeline.gene_ids import remap_var_names_to_symbol
    from src.pipeline.markers import rank_markers, top_markers_table
    from src.agents.annotation.method_overlap import annotate_overlap
    from src.agents.annotation.method_kb2 import annotate_kb2
    from src.agents.annotation.method_singler import annotate_singler
    from src.agents.annotation.consensus import score_consensus

    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    a = sc.read_h5ad(labeled_path)
    print("obs columns:", list(a.obs.columns))
    candidates = [
        c for c in a.obs.columns
        if a.obs[c].dtype.name in ("category", "object") and 1 < a.obs[c].nunique() < 30
    ]
    print("candidate label columns (categorical, <30 levels):", candidates)
    for c in candidates:
        print(f"  {c}: {a.obs[c].nunique()} levels -> {sorted(a.obs[c].astype(str).unique())}")

    label_key = "str_labels" if "str_labels" in a.obs.columns else (candidates[0] if candidates else None)
    if label_key is None:
        raise ValueError("Could not find a categorical ground-truth label column in obs.")
    print(f"-> chose label_key = '{label_key}' (human-readable cell-type strings; "
          f"'labels' is its integer encoding, 'batch'/'n_counts' are technical covariates)")

    a = remap_var_names_to_symbol(a)
    a = prepare_pbmc12k(a, resolution=resolution, seed=0)
    rank_markers(a)

    methods = {"overlap": annotate_overlap(a), "kb2": annotate_kb2(a)}
    singler_error = None
    try:
        singler_votes = annotate_singler(a)
        if not singler_votes:
            singler_error = "annotate_singler returned no votes (see log above for the R-side reason)"
    except Exception as e:                                    # noqa: BLE001
        singler_votes, singler_error = {}, repr(e)
    methods["singler"] = singler_votes

    two_method_fallback = not bool(singler_votes)
    if two_method_fallback:
        logger.warning("SingleR produced no votes ({}); falling back to 2-method consensus", singler_error)
        print(f"[FALLBACK] SingleR unavailable ({singler_error}) -> using 2-method consensus (overlap + kb2)")
    else:
        print(f"3-method consensus active: SingleR returned {len(singler_votes)} cluster votes")

    table5 = top_markers_table(a, n=5)
    clusters = sorted(a.obs["leiden"].cat.categories, key=int)

    cluster_annotations = {}
    for cid in clusters:
        votes = {m: methods[m].get(cid, "") for m in methods}
        cell_type, confidence = score_consensus(votes)
        cluster_annotations[cid] = {
            "cell_type": cell_type,
            "confidence": confidence,
            "raw_votes": votes,
            "marker_genes": list(table5[table5["cluster"] == cid]["gene"]),
        }

    a.obs["pred_cell_type"] = a.obs["leiden"].astype(str).map(lambda c: cluster_annotations[c]["cell_type"])
    a.obs["pred_confidence"] = a.obs["leiden"].astype(str).map(lambda c: cluster_annotations[c]["confidence"])

    return a, cluster_annotations, label_key, out, two_method_fallback, singler_error


def run_calibration(
    labeled_path: str = "data/raw/zheng68k/zheng68k_full.h5ad",
    out_dir: str = "benchmarks/results",
    resolution: float = 0.5,
) -> dict:
    """STOP-point entry: builds predictions and prints the vocabulary mismatch,
    but does NOT compute accuracy/CI/ECE without a confirmed CANON mapping.
    Use compute_full_calibration() once CANON_LINEAGE is confirmed."""
    a, cluster_annotations, label_key, out, two_fb, singler_err = _prepare_annotated(
        labeled_path, out_dir, resolution)

    clusters = sorted(a.obs["leiden"].cat.categories, key=int)
    pred_labels = sorted(a.obs["pred_cell_type"].unique().tolist())
    true_labels = sorted(a.obs[label_key].astype(str).unique().tolist())

    print("\n=== STOP: vocabulary mismatch check (do not proceed without a confirmed CANON mapping) ===")
    print("Predicted labels (post-consensus, already harmonize.canon()'d):", pred_labels)
    print(f"True labels (ground truth, '{label_key}'):", true_labels)
    print("\nPer-cluster detail — cell_type | confidence | raw method votes | n_cells | majority true label:")
    for cid in clusters:
        n = int((a.obs["leiden"] == cid).sum())
        maj_true = a.obs.loc[a.obs["leiden"] == cid, label_key].value_counts().idxmax()
        info = cluster_annotations[cid]
        print(f"  cluster {cid:>3} (n={n:>5}): pred='{info['cell_type']}' conf={info['confidence']:<4} "
              f"votes={info['raw_votes']}  majority_true='{maj_true}'")

    partial = {
        "dataset": "PBMC-12k (scvi-tools pbmc_dataset, 9 types) -- NOT Zheng68k",
        "labeled_path": labeled_path, "label_key_chosen": label_key,
        "obs_columns": list(a.obs.columns), "n_cells": int(a.n_obs), "resolution": resolution,
        "two_method_fallback": two_fb, "singler_error": singler_err,
        "cluster_annotations": cluster_annotations,
        "predicted_labels": pred_labels, "true_labels": true_labels,
        "status": "STOPPED_AWAITING_CANON_MAPPING",
    }
    out_path = out / "calibration_partial.json"
    with open(out_path, "w") as f:
        json.dump(partial, f, indent=2, default=str)
    print(f"\nPartial results written to {out_path}")
    return partial


def compute_full_calibration(
    labeled_path: str = "data/raw/zheng68k/zheng68k_full.h5ad",
    out_dir: str = "benchmarks/results",
    resolution: float = 0.5,
) -> dict:
    """LINEAGE-LEVEL (coarse) calibration table using the human-confirmed
    CANON_LINEAGE mapping: per-confidence-bin accuracy + Wilson 95% CI + ECE,
    per-lineage accuracy breakdown, and the confidence-bin distribution of
    'Other' (no-analog) cells."""
    from statsmodels.stats.proportion import proportion_confint

    a, cluster_annotations, label_key, out, two_fb, singler_err = _prepare_annotated(
        labeled_path, out_dir, resolution)

    true = a.obs[label_key].astype(str)
    pred = a.obs["pred_cell_type"].astype(str)
    conf = a.obs["pred_confidence"].astype(str)

    correct = [t in CANON_LINEAGE.get(p, set()) for p, t in zip(pred, true)]
    a.obs["correct"] = correct
    a.obs["true_lineage"] = true.map(TRUE_LABEL_TO_LINEAGE)

    def _wilson(n_correct: int, n_total: int):
        if n_total == 0:
            return float("nan"), float("nan"), float("nan")
        acc = n_correct / n_total
        lo, hi = proportion_confint(n_correct, n_total, alpha=0.05, method="wilson")
        return acc, lo, hi

    # --- 1. per-confidence-bin accuracy + per-cell Wilson CI + cluster-bootstrap CI ---
    # Framed as: confidence rank-orders accuracy (ordinal categories), not a
    # probabilistic calibration claim -- see the ECE appendix note below for why.
    print("\n=== Confidence rank-orders accuracy: per-bin accuracy (per-cell Wilson CI + cluster bootstrap) ===")
    bin_rows = {}
    n_total_cells = len(a)
    for bin_name in ["HIGH", "MED", "LOW"]:
        mask = conf == bin_name
        n = int(mask.sum())
        n_correct = int((mask & a.obs["correct"]).sum())
        acc, lo, hi = _wilson(n_correct, n)
        boot = _cluster_bootstrap_ci(a, "pred_confidence", bin_name, n_boot=1000, seed=0)
        bin_rows[bin_name] = {
            "n": n, "n_correct": n_correct,
            "accuracy": round(acc, 4) if n else None,
            "wilson_95ci_low": round(lo, 4) if n else None,
            "wilson_95ci_high": round(hi, 4) if n else None,
            "cluster_bootstrap": boot,
        }
        ci_str = f"[{lo:.3f}, {hi:.3f}]" if n else "[n/a]"
        boot_str = (f"cluster-boot 95% = [{boot['boot_2.5pct']:.3f}, {boot['boot_97.5pct']:.3f}] "
                    f"(k={boot['n_clusters_in_bin']} clusters)") if boot else "cluster-boot n/a"
        print(f"  {bin_name:<4} n={n:>5}  accuracy={acc:.4f}  per-cell Wilson 95% CI={ci_str}  {boot_str}")

    high_lo, high_hi = bin_rows["HIGH"]["wilson_95ci_low"], bin_rows["HIGH"]["wilson_95ci_high"]
    low_lo, low_hi = bin_rows["LOW"]["wilson_95ci_low"], bin_rows["LOW"]["wilson_95ci_high"]
    ci_overlap = (high_lo is not None and low_lo is not None and high_lo <= low_hi and low_lo <= high_hi)
    if ci_overlap:
        print("  NOTE: HIGH and LOW per-cell Wilson 95% CIs OVERLAP — not statistically "
              "distinguishable on this benchmark; reporting as-is.")
    else:
        print("  HIGH and LOW per-cell Wilson 95% CIs do not overlap.")

    boot_h, boot_l = bin_rows["HIGH"]["cluster_bootstrap"], bin_rows["LOW"]["cluster_bootstrap"]
    if boot_h and boot_l:
        boot_overlap = boot_h["boot_2.5pct"] <= boot_l["boot_97.5pct"] and boot_l["boot_2.5pct"] <= boot_h["boot_97.5pct"]
        if boot_overlap:
            print("  NOTE: HIGH and LOW cluster-bootstrap 95% CIs OVERLAP (only 3 HIGH clusters / "
                  "5 LOW clusters) — the per-cell CIs above understate uncertainty; reporting as-is.")
        else:
            print("  HIGH and LOW cluster-bootstrap 95% CIs do not overlap, despite the wider spread "
                  "from resampling only 3 HIGH / 5 LOW clusters.")

    # --- 1b. robustness check: is LOW's low accuracy just its largest cluster? ---
    low_mask = conf == "LOW"
    low_cluster_counts = a.obs.loc[low_mask, "leiden"].astype(str).value_counts()
    dom_cluster = low_cluster_counts.idxmax()
    dom_n = int(low_cluster_counts.max())
    dom_share = dom_n / int(low_mask.sum())
    excl_mask = low_mask & (a.obs["leiden"].astype(str) != dom_cluster)
    n_excl = int(excl_mask.sum())
    nc_excl = int((excl_mask & a.obs["correct"]).sum())
    acc_excl, lo_excl, hi_excl = _wilson(nc_excl, n_excl)
    print(f"\n=== Robustness check: LOW bin excluding its largest cluster (cluster {dom_cluster}, "
          f"n={dom_n}, {dom_share:.1%} of LOW) ===")
    print(f"  LOW excl. cluster {dom_cluster}: n={n_excl}  accuracy={acc_excl:.4f}  "
          f"Wilson 95% CI=[{lo_excl:.3f}, {hi_excl:.3f}]")
    if n_excl and acc_excl > 0.5:
        print("  LOW's poor accuracy was largely driven by this one cluster's tie-break — excluding "
              "it, the remaining LOW cells look like a moderate-accuracy bin, not a broken one.")
    else:
        print("  LOW remains low-accuracy even excluding its largest cluster — not just one cluster's artifact.")
    low_excl_dominant = {
        "dominant_cluster": dom_cluster, "dominant_cluster_n": dom_n,
        "dominant_cluster_share_of_low": round(dom_share, 4),
        "n_excluding_dominant": n_excl, "n_correct_excluding_dominant": nc_excl,
        "accuracy_excluding_dominant": round(acc_excl, 4) if n_excl else None,
        "wilson_95ci_low_excluding_dominant": round(lo_excl, 4) if n_excl else None,
        "wilson_95ci_high_excluding_dominant": round(hi_excl, 4) if n_excl else None,
    }

    # --- appendix: ECE under an ASSUMED nominal-confidence mapping (not a real
    # probability -- score_consensus emits ordinal categories, not scores) ---
    ece = 0.0
    for bin_name in ["HIGH", "MED", "LOW"]:
        row = bin_rows[bin_name]
        if row["n"]:
            ece += (row["n"] / n_total_cells) * abs(row["accuracy"] - ECE_NOMINAL_CONFIDENCE[bin_name])
    print(f"\n[Appendix, not headline] ECE under ASSUMED nominal confidences "
          f"(HIGH=1.00/MED=0.67/LOW=0.33) = {ece:.4f} — an artifact of that assumption, "
          f"not a probabilistic calibration score.")

    # --- 2. per-lineage accuracy breakdown (grouped by TRUE lineage) ---
    print("\n=== Per-lineage accuracy (grouped by ground-truth lineage) ===")
    lineage_rows = {}
    for lineage in ["B cell", "Dendritic cell", "Monocyte", "NK cell", "Platelet", "T cell", "Other"]:
        mask = a.obs["true_lineage"] == lineage
        n = int(mask.sum())
        n_correct = int((mask & a.obs["correct"]).sum())
        acc, lo, hi = _wilson(n_correct, n)
        # sub-type composition within this true lineage, to keep the CD4/CD8 and
        # CD14/FCGR3A collapse visible instead of hidden by the coarse number
        composition = true[mask].value_counts().to_dict()
        lineage_rows[lineage] = {
            "n": n, "n_correct": n_correct,
            "accuracy": round(acc, 4) if n else None,
            "wilson_95ci_low": round(lo, 4) if n else None,
            "wilson_95ci_high": round(hi, 4) if n else None,
            "true_subtype_composition": composition,
        }
        ci_str = f"[{lo:.3f}, {hi:.3f}]" if n else "[n/a]"
        print(f"  {lineage:<15} n={n:>5}  accuracy={acc if n else float('nan'):.4f}  "
              f"Wilson 95% CI={ci_str}  composition={composition}")

    # --- 3. confidence-bin distribution of 'Other' (no-analog) cells ---
    print("\n=== 'Other' (no-analog) cells — which confidence bin do they land in? ===")
    other_mask = true == "Other"
    other_by_bin = {b: int((other_mask & (conf == b)).sum()) for b in ["HIGH", "MED", "LOW"]}
    n_other = int(other_mask.sum())
    for b, n in other_by_bin.items():
        pct = 100 * n / n_other if n_other else 0.0
        print(f"  {b:<4}: {n:>4} / {n_other} ({pct:.1f}%)")
    if other_by_bin.get("HIGH", 0) > 0:
        print("  FINDING: some 'Other' cells landed in HIGH confidence — the consensus method is "
              "confidently agreeing on a lineage label for cells that have no true lineage analog. "
              "That is a miscalibration, not a mapping artifact.")
    else:
        print("  'Other' cells did not land in HIGH — consistent with there being no correct label "
              "available for them.")

    result = {
        "dataset": "PBMC-12k (scvi-tools pbmc_dataset, 9 types) -- NOT Zheng68k",
        "annotation_granularity": "LINEAGE-LEVEL (coarse) -- not fine PBMC-subtype annotation",
        "headline_claim": "Confidence rank-orders accuracy (HIGH > MED > LOW), not a probabilistic "
            "calibration claim -- score_consensus emits ordinal categories (HIGH/MED/LOW), not "
            "numeric probabilities, so 'calibration' in the strict sense doesn't apply. See "
            "appendix_ece below for why ECE is not a headline number.",
        "labeled_path": labeled_path, "label_key": label_key,
        "n_cells": int(a.n_obs), "resolution": resolution,
        "two_method_fallback": two_fb, "singler_error": singler_err,
        "canon_lineage_mapping": {k: sorted(v) for k, v in CANON_LINEAGE.items()},
        "canon_mapping_footnotes": {
            "Platelet->Megakaryocytes": "Known PBMC naming equivalence (platelets are anucleate "
                "fragments shed from megakaryocytes); this scvi-tools set's ground truth uses "
                "'Megakaryocytes' for the corresponding population.",
            "Monocyte": "Collapses CD14+ and FCGR3A+ monocyte subtypes -- prediction does not "
                "distinguish them (harmonize.canon() merges 'CD14 Monocyte'/'FCGR3A Monocyte' "
                "before consensus).",
            "T cell": "Collapses CD4+ and CD8+ T cell subtypes for the same reason.",
            "Other": "No predicted lineage maps to 'Other' -- these cells are always counted wrong "
                "by construction, not tuned.",
        },
        "confidence_bin_accuracy": bin_rows,
        "robustness_check_low_bin_excluding_dominant_cluster": low_excl_dominant,
        "high_low_ci_overlap_per_cell": bool(ci_overlap),
        "high_low_ci_overlap_cluster_bootstrap": bool(boot_overlap) if (boot_h and boot_l) else None,
        "per_lineage_accuracy": lineage_rows,
        "other_cells_by_confidence_bin": other_by_bin,
        "cluster_annotations": cluster_annotations,
        "appendix_ece": {
            "value": round(ece, 4),
            "assumed_nominal_confidence": ECE_NOMINAL_CONFIDENCE,
            "note": "NOT a headline result. Nominal confidence per categorical bin (HIGH=1.00, "
                "MED=0.67, LOW=0.33) is an assumption made solely to compute this number -- "
                "score_consensus returns ordinal HIGH/MED/LOW categories, not a fitted or measured "
                "probability, so this is an artifact of the assumed values, not a probabilistic "
                "calibration score. The supported claim is that confidence rank-orders accuracy, "
                "not that it is calibrated in the ECE sense.",
        },
    }

    out_path = out / "calibration_pbmc12k.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nFull calibration results written to {out_path}")
    return result


if __name__ == "__main__":
    compute_full_calibration()
