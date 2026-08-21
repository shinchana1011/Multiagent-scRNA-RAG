# tests/orchestrator/test_audit.py — FR-26 audit trail (Member 3)
import json, os
from src.schemas.state import PipelineState, Claim, Annotation


def test_fr26_audit_exports_json(tmp_path):
    s = PipelineState(input_path="x", tissue="PBMC")
    s.claims.append(Claim("resolution", 0.5, pmid="123", verified=True))
    s.annotations.append(Annotation("0", "T cell", "HIGH", marker_genes=["CD3D"]))
    s.log_event("test", "action1")
    s.log_event("test", "action2")

    path = tmp_path / "audit.json"
    s.export_audit(str(path))
    assert os.path.exists(path)

    data = json.loads(path.read_text())
    assert data["input"] == "x"
    assert len(data["log"]) == 2
    assert data["claims"][0]["pmid"] == "123"
    assert data["annotations"][0]["confidence"] == "HIGH"