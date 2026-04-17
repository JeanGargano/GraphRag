from typing import Optional
from pydantic import BaseModel, Field


# ── Documento ──────────────────────────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str


# ── Query ──────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)


class QueryResponse(BaseModel):
    answer: str


# ── Respuestas estándar de API Gateway ─────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str