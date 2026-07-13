# src/api/models.py — request/response schemas (Member 4, Task 2)
from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class UploadResponse(BaseModel):
    file_id: str
    filename: str


class RunRequest(BaseModel):
    file_id: str
    tissue: str = "general"
    disease: str = ""


class RunResponse(BaseModel):
    job_id: str


class StatusResponse(BaseModel):
    job_id: str
    status: str            # queued | running | done | failed
    progress: int          # 0-100
    message: str
    error: str | None = None


class AnnotationOut(BaseModel):
    cluster_id: str
    cell_type: str
    confidence: str
    cell_state: str | None = None
    marker_genes: list[str] = []
    method_votes: dict[str, str] = {}
    sources: dict[str, str] = {}


class ClaimOut(BaseModel):
    parameter: str
    value: Any
    pmid: str
    verified: bool
    confidence: str


class ResultsResponse(BaseModel):
    job_id: str
    n_clusters: int
    annotations: list[AnnotationOut]
    claims: list[ClaimOut]
    review_queue: list[str]


class ReviewDecision(BaseModel):
    cluster_id: str
    approved: bool
    override_label: str | None = None