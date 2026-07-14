# src/reporting/composition.py — cell-type composition profiling (Member 4, novelty)
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Reference healthy PBMC composition (approx. fractions from Zheng et al. 2017,
# 10x Genomics 68k PBMC; broad ranges, for DEVIATION FLAGGING only — not diagnosis).
HEALTHY_PBMC_REFERENCE: dict[str, tuple[float, float]] = {
    # cell_type: (low_fraction, high_fraction)
    "T cell":          (0.45, 0.70),
    "B cell":          (0.05, 0.15),
    "NK cell":         (0.05, 0.15),
    "Monocyte":        (0.10, 0.25),
    "Dendritic cell":  (0.01, 0.04),
    "Platelet":        (0.00, 0.03),
}


def compute_composition(adata, annotations: list[dict]) -> list[dict]:
    """Return per-cell-type composition of the sample with deviation vs the
    healthy reference. Aggregates clusters that share a (harmonised) cell type."""
    leiden = adata.obs["leiden"].astype(str)
    total = len(leiden)
    label_of = {a["cluster_id"]: a["cell_type"] for a in annotations}

    # cells per cell type (sum across clusters with the same label)
    counts: dict[str, int] = {}
    for cid in leiden:
        ct = label_of.get(cid, "Unknown")
        counts[ct] = counts.get(ct, 0) + 1

    rows = []
    for ct, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        frac = n / total if total else 0.0
        ref = HEALTHY_PBMC_REFERENCE.get(ct)
        if ref is None:
            status = "no reference"
        elif frac < ref[0]:
            status = "below healthy range"
        elif frac > ref[1]:
            status = "above healthy range"
        else:
            status = "within healthy range"
        rows.append({"cell_type": ct, "n_cells": n, "fraction": round(frac, 4),
                     "ref_low": ref[0] if ref else None, "ref_high": ref[1] if ref else None,
                     "status": status})
    return rows


def composition_summary(rows: list[dict]) -> str:
    """A one-paragraph, non-diagnostic interpretation."""
    atypical = [r for r in rows if r["status"] in ("below healthy range", "above healthy range")]
    if not atypical:
        return ("Cell-type composition falls within expected healthy PBMC reference ranges "
                "across all annotated populations.")
    parts = [f"{r['cell_type']} ({r['fraction']:.0%}, {r['status']})" for r in atypical]
    return ("Composition analysis identified populations deviating from the healthy PBMC "
            "reference: " + "; ".join(parts) + ". This flags the sample as compositionally "
            "atypical and is recommended for expert review. No disease classification is "
            "inferred; deviation flagging is descriptive only.")


def plot_composition(rows: list[dict], out_path: str) -> str:
    """Bar chart: sample fraction per cell type with healthy reference bands."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    types = [r["cell_type"] for r in rows]
    fracs = [r["fraction"] for r in rows]
    colors = {"within healthy range": "#2E6E6A", "above healthy range": "#C0504D",
              "below healthy range": "#E8A33D", "no reference": "#999999"}
    bar_colors = [colors[r["status"]] for r in rows]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(types, fracs, color=bar_colors)
    # draw reference bands
    for i, r in enumerate(rows):
        if r["ref_low"] is not None:
            ax.plot([i - 0.4, i + 0.4], [r["ref_high"], r["ref_high"]], color="black", lw=0.8)
            ax.plot([i - 0.4, i + 0.4], [r["ref_low"], r["ref_low"]], color="black", lw=0.8, ls=":")
    ax.set_ylabel("Fraction of cells")
    ax.set_title("Cell-type composition vs healthy PBMC reference\n"
                 "(green=within, red=above, amber=below; bars=ref range)")
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout(); fig.savefig(out_path, dpi=150); plt.close(fig)
    return out_path