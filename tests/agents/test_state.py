from src.schemas.state import PipelineState, Claim, Annotation

def test_claim_downgrade():
    c = Claim("resolution", 0.5, "1", confidence="HIGH")
    c.downgrade(); assert c.confidence == "MED"
    c.downgrade(); assert c.confidence == "LOW"

def test_review_queue_flags_low():
    s = PipelineState(input_path="x")
    s.annotations.append(Annotation("0", "CD4 T", "HIGH"))
    s.annotations.append(Annotation("1", "Unknown", "LOW"))
    assert [a.cluster_id for a in s.review_queue()] == ["1"]

def test_default_config_present():
    s = PipelineState(input_path="x")
    assert s.config.resolution == 0.5     # inherits Member 1's PipelineConfig