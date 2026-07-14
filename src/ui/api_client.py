# src/ui/api_client.py — thin HTTP client to the FastAPI backend (Member 4, Task 3)
from __future__ import annotations
import requests
from src.config.settings import settings

_B = settings.api_base_url


def upload(file_bytes: bytes, filename: str) -> dict:
    return requests.post(f"{_B}/api/upload",
                         files={"file": (filename, file_bytes)}, timeout=120).json()


def run(file_id: str, tissue: str, disease: str) -> dict:
    return requests.post(f"{_B}/api/run",
                         json={"file_id": file_id, "tissue": tissue, "disease": disease},
                         timeout=30).json()


def status(job_id: str) -> dict:
    return requests.get(f"{_B}/api/status/{job_id}", timeout=30).json()


def results(job_id: str) -> dict:
    return requests.get(f"{_B}/api/results/{job_id}", timeout=30).json()


def review_queue(job_id: str) -> list[dict]:
    return requests.get(f"{_B}/api/review/{job_id}", timeout=30).json()


def submit_review(job_id: str, cluster_id: str, approved: bool, override: str | None) -> dict:
    return requests.post(f"{_B}/api/review/{job_id}",
                         json={"cluster_id": cluster_id, "approved": approved,
                               "override_label": override}, timeout=30).json()


def report_url(job_id: str, fmt: str) -> str:
    return f"{_B}/api/report/{job_id}?fmt={fmt}"