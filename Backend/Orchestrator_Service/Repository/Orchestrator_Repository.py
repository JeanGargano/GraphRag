import httpx
from fastapi import HTTPException, status

from Model.Schemas import DocumentUploadResponse


class OrchestratorRepository:
    def __init__(self, base_url: str):
        self._base_url = base_url

    async def send_document(
        self,
        filename: str,
        content_type: str,
        file_content: bytes,
    ) -> DocumentUploadResponse:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=f"{self._base_url}/documents/upload",
                    files={"file": (filename, file_content, content_type)},
                )
                response.raise_for_status()
                return DocumentUploadResponse(**response.json())
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="El Document Service no respondió a tiempo.",
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Document Service devolvió {exc.response.status_code}.",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible conectar con el Document Service.",
            ) from exc
