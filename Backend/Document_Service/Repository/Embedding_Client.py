import logging
from typing import List

import httpx
from fastapi import HTTPException, status

from config import settings
from Model.Schemas import ChunkPayload

logger = logging.getLogger(__name__)


class EmbeddingServiceClient:

    def __init__(self, base_url: str):
        self._base_url = base_url

    async def send_chunks(
        self,
        document_id: str,
        filename: str,
        chunks: List[str],
    ) -> None:
        payload = ChunkPayload(
            document_id=document_id,
            filename=filename,
            chunks=chunks,
        )

        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
                response = await client.post(
                    url=f"{self._base_url}/embeddings/process",
                    json=payload.model_dump(),
                )
                response.raise_for_status()

        except httpx.TimeoutException:
            logger.error("Timeout al conectar con Embedding Service")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="El Embedding Service no respondió a tiempo.",
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                "Error del Embedding Service: %s - %s",
                e.response.status_code,
                e.response.text,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error en Embedding Service: {e.response.status_code}",
            )
        except httpx.RequestError as e:
            logger.error("Error de red hacia Embedding Service: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Embedding Service no disponible.",
            )