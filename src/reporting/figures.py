# src/reporting/figures.py — annotated UMAP with confidence encoding (Member 4, FR-20)
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# HIGH = solid filled marker; MED = hollow (edge only); LOW = small grey
_CMAP = plt.get_cmap("tab20")


def plot_umap_confidence(adata, annotations: list[dict], out_path: str) -> str:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    conf = {a["cluster_id"]: a["confidence"] for a in annotations}
    label = {a["cluster_id"]: a["cell_type"] for a in annotations}
    xy = adata.obsm["X_umap"]
    clusters = list(adata.obs["leiden"].astype(str))

    fig, ax = plt.subplots(figsize=(9, 7))
    for i, cid in enumerate(sorted(set(clusters), key=lambda c: int(c))):
        mask = [c == cid for c in clusters]
        pts = xy[mask]
        color = _CMAP(i % 20)
        c = conf.get(cid, "LOW")
        name = f"{label.get(cid, '?')} [{c}]"
        if c == "HIGH":
            ax.scatter(pts[:, 0], pts[:, 1], s=8, color=color, label=name)
        elif c == "MED":
            ax.scatter(pts[:, 0], pts[:, 1], s=10, facecolors="none",
                       edgecolors=color, linewidths=0.6, label=name)
        else:
            ax.scatter(pts[:, 0], pts[:, 1], s=5, color="lightgrey", label=name)
    ax.set_xlabel("UMAP_1"); ax.set_ylabel("UMAP_2")
    ax.set_title("Annotated UMAP (solid=HIGH, hollow=MED, grey=LOW)")
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=7, markerscale=2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path