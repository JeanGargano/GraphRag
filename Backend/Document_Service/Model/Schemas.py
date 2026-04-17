from typing import List
from pydantic import BaseModel


# ── Request al Embedding Service ───────────────────────────────────────────────

class ChunkPayload(BaseModel):
    document_id: str
    filename: str
    chunks: List[str]


# ── Response al Orchestrator ───────────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str


# ── Health ─────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str