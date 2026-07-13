# src/api/main.py — FastAPI application (Member 4, Task 2)
from __future__ import annotations
import json, uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from src.config.settings import settings
from src.config.logging_config import setup_logging
from src.api.models import (UploadResponse, RunRequest, RunResponse, StatusResponse,
                            ResultsResponse, AnnotationOut, ClaimOut, ReviewDecision)
from src.api.jobs import job_manager

setup_logging()
app = FastAPI(title=settings.app_name, version="1.0",
              description="Multi-agent RAG scRNA-seq pipeline API")

_ALLOWED = {".h5", ".h5ad", ".loom"}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@app.post("/api/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    ext = Path(file.filename).suffix.lower()
    if ext not in _ALLOWED:
        raise HTTPException(400, f"Unsupported format {ext}; use .h5/.h5ad/.loom")
    file_id = uuid.uuid4().hex[:12] + ext
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    dest = Path(settings.upload_dir) / file_id
    dest.write_bytes(await file.read())
    return UploadResponse(file_id=file_id, filename=file.filename)


@app.post("/api/run", response_model=RunResponse)
async def run(req: RunRequest) -> RunResponse:
    fpath = Path(settings.upload_dir) / req.file_id
    if not fpath.exists():
        raise HTTPException(404, "file_id not found; upload first")
    job_id = job_manager.submit(str(fpath), req.tissue, req.disease)
    return RunResponse(job_id=job_id)


@app.get("/api/status/{job_id}", response_model=StatusResponse)
async def status(job_id: str) -> StatusResponse:
    s = job_manager.status(job_id)
    if s["status"] == "not_found":
        raise HTTPException(404, "job not found")
    return StatusResponse(job_id=job_id, **s)


def _load_results(job_id: str) -> dict:
    f = Path(settings.runs_dir) / job_id / "results.json"
    if not f.exists():
        raise HTTPException(404, "results not ready")
    return json.loads(f.read_text())


@app.get("/api/results/{job_id}", response_model=ResultsResponse)
async def results(job_id: str) -> ResultsResponse:
    d = _load_results(job_id)
    return ResultsResponse(job_id=job_id, n_clusters=d["n_clusters"],
                           annotations=[AnnotationOut(**a) for a in d["annotations"]],
                           claims=[ClaimOut(**c) for c in d["claims"]],
                           review_queue=d["review_queue"])


@app.get("/api/review/{job_id}", response_model=list[AnnotationOut])
async def review_queue(job_id: str) -> list[AnnotationOut]:
    d = _load_results(job_id)
    return [AnnotationOut(**a) for a in d["annotations"] if a["confidence"] == "LOW"]


@app.post("/api/review/{job_id}")
async def review_decision(job_id: str, decision: ReviewDecision) -> dict:
    run_dir = Path(settings.runs_dir) / job_id
    rf = run_dir / "review_decisions.json"
    decisions = json.loads(rf.read_text()) if rf.exists() else []
    decisions.append(decision.model_dump())
    rf.write_text(json.dumps(decisions, indent=2))
    return {"ok": True, "recorded": decision.model_dump()}


@app.get("/api/report/{job_id}")
async def report(job_id: str, fmt: str = "pdf") -> FileResponse:
    ext = {"pdf": "report.pdf", "html": "report.html", "json": "report.json"}.get(fmt)
    if ext is None:
        raise HTTPException(400, "fmt must be pdf|html|json")
    path = Path(settings.runs_dir) / job_id / ext
    if not path.exists():
        raise HTTPException(404, "report not generated")
    return FileResponse(str(path), filename=ext)


if __name__ == "__main__":                     # required for Windows multiprocessing
    import uvicorn
    uvicorn.run("src.api.main:app", host=settings.api_host, port=settings.api_port, reload=False)