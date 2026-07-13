# src/api/jobs.py — process-based job manager (Member 4, Task 2)
from __future__ import annotations
import json, uuid
from pathlib import Path
from multiprocessing import Process
from src.config.settings import settings
from src.api.worker import execute_job


class JobManager:
    def __init__(self) -> None:
        self._procs: dict[str, Process] = {}

    def submit(self, file_path: str, tissue: str, disease: str) -> str:
        job_id = uuid.uuid4().hex[:12]
        run_dir = str(Path(settings.runs_dir) / job_id)
        Path(run_dir).mkdir(parents=True, exist_ok=True)
        (Path(run_dir) / "status.json").write_text(json.dumps(
            {"status": "queued", "progress": 0, "message": "Queued", "error": None}))
        (Path(run_dir) / "meta.json").write_text(json.dumps(
            {"tissue": tissue, "disease": disease, "file": file_path}))
        p = Process(target=execute_job, args=(job_id, file_path, tissue, disease, run_dir),
                    daemon=True)
        p.start()
        self._procs[job_id] = p
        return job_id

    def status(self, job_id: str) -> dict:
        run_dir = Path(settings.runs_dir) / job_id
        sfile = run_dir / "status.json"
        if not sfile.exists():
            return {"status": "not_found", "progress": 0, "message": "Unknown job", "error": None}
        data = json.loads(sfile.read_text())
        # crash detection: process dead but status still 'running'
        p = self._procs.get(job_id)
        if data["status"] in ("queued", "running") and p is not None and not p.is_alive():
            data = {"status": "failed", "progress": 100,
                    "message": "Worker process exited unexpectedly", "error": "process died"}
            sfile.write_text(json.dumps(data))
        return data


job_manager = JobManager()