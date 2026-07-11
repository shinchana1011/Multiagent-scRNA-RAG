# src/agents/annotation/method_singler.py — SingleR annotation (Member 3, Task 4, STUB)
from __future__ import annotations
from loguru import logger


def annotate_singler(adata) -> dict[str, str]:
    """SingleR via rpy2 — STUB until R toolchain is installed.
    Returns {} so consensus treats it as 'no vote' for now."""
    logger.warning("SingleR not yet wired (R toolchain pending); returning no votes")
    return {}