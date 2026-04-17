from fastapi import FastAPI
from pydantic import BaseModel

from config import settings


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


app = FastAPI(title="Indexer Service")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )
