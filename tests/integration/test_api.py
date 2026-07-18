from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"

def test_upload_rejects_bad_ext():
    r = client.post("/api/upload", files={"file": ("x.txt", b"nope")})
    assert r.status_code == 400

def test_run_missing_file_404():
    r = client.post("/api/run", json={"file_id": "nonexistent.h5ad", "tissue": "PBMC"})
    assert r.status_code == 404

def test_status_unknown_job_404():
    assert client.get("/api/status/deadbeef").status_code == 404