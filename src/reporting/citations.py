# src/reporting/citations.py — citation report (Member 4, FR-22)
from __future__ import annotations
import re

_PMID = re.compile(r"PMID:(\d+)")


def collect_citations(claims: list[dict], annotations: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for c in claims:
        if c.get("pmid"):
            seen.setdefault(c["pmid"], {"pmid": c["pmid"], "context": f"parameter:{c['parameter']}"})
    for a in annotations:
        for src in a.get("sources", {}).values():
            for pid in _PMID.findall(str(src)):
                seen.setdefault(pid, {"pmid": pid, "context": "annotation"})
    return sorted(seen.values(), key=lambda d: d["pmid"])


def format_citations(cits: list[dict]) -> str:
    lines = ["References"]
    for i, c in enumerate(cits, 1):
        lines.append(f"[{i}] PMID:{c['pmid']}  (https://pubmed.ncbi.nlm.nih.gov/{c['pmid']}/)  "
                     f"— used for {c['context']}")
    return "\n".join(lines)