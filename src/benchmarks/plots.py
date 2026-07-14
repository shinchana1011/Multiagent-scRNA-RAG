# src/benchmarks/plots.py — benchmark figures (Member 4, Task 4)
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def bar(labels, values, title, ylabel, out, hline=None):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(labels, values, color="#2E6E6A")
    if hline is not None:
        ax.axhline(hline, ls="--", color="crimson", label=f"target {hline}")
        ax.legend()
    ax.set_title(title); ax.set_ylabel(ylabel)
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)
    return out