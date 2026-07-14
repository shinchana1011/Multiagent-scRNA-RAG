# src/reporting/scorecard.py — run-level reliability scorecard (Member 4, novelty)
from __future__ import annotations


def compute_scorecard(annotations: list[dict], claims: list[dict],
                      ilisi: float | None = None) -> dict:
    """A single headline 'annotation reliability' score + its components.
    Surfaces the project's verification work as one number (on-thesis)."""
    n = len(annotations) or 1
    high = sum(a["confidence"] == "HIGH" for a in annotations)
    med = sum(a["confidence"] == "MED" for a in annotations)
    low = sum(a["confidence"] == "LOW" for a in annotations)
    pct_high = high / n
    pct_reviewed = low / n

    n_claims = len(claims) or 1
    verified = sum(c["verified"] for c in claims)
    pct_verified = verified / n_claims

    # composite reliability: weighted blend of annotation confidence + claim verification
    reliability = round(100 * (0.6 * pct_high + 0.4 * pct_verified), 1)

    grade = ("A" if reliability >= 80 else "B" if reliability >= 65 else
             "C" if reliability >= 50 else "D")

    return {
        "reliability_score": reliability,        # 0-100 headline
        "grade": grade,
        "pct_high_confidence": round(pct_high * 100, 1),
        "n_high": high, "n_med": med, "n_low": low,
        "pct_claims_verified": round(pct_verified * 100, 1),
        "verified_claims": verified, "total_claims": len(claims),
        "pct_flagged_for_review": round(pct_reviewed * 100, 1),
        "ilisi": round(ilisi, 2) if ilisi is not None else None,
    }


def scorecard_summary(sc: dict) -> str:
    parts = [f"Overall annotation reliability: {sc['reliability_score']}/100 (grade {sc['grade']}).",
             f"{sc['pct_high_confidence']}% of clusters achieved HIGH-confidence consensus "
             f"({sc['n_high']}/{sc['n_high']+sc['n_med']+sc['n_low']}).",
             f"{sc['pct_claims_verified']}% of literature-retrieved parameters passed verification."]
    if sc["ilisi"] is not None:
        parts.append(f"Batch integration iLISI = {sc['ilisi']} (target > 1.5).")
    if sc["n_low"]:
        parts.append(f"{sc['n_low']} cluster(s) flagged for human review.")
    return " ".join(parts)