import logging
import uuid
from typing import List

from fastapi import HTTPException, UploadFile, status

from config import settings
from Model.Schemas import DocumentUploadResponse
from Repository.Document_Repository import DocumentRepository
from Repository.Embedding_Client import EmbeddingServiceClient
from Service.IDocument_Service import IDocumentService
from Service.Extraction_Strategies import (
    PDFExtractionStrategy,
    DocxExtractionStrategy,
    TxtExtractionStrategy,
)

logger = logging.getLogger(__name__)

STRATEGIES = {
    "pdf": PDFExtractionStrategy(),
    "docx": DocxExtractionStrategy(),
    "txt": TxtExtractionStrategy(),
}


class DocumentService(IDocumentService):

    def __init__(
        self,
        document_repository: DocumentRepository,
        embedding_client: EmbeddingServiceClient,
    ):
        self._document_repo = document_repository
        self._embedding_client = embedding_client

    async def process_document(self, file: UploadFile) -> DocumentUploadResponse:
        # 1. Obtener extensión y validar
        extension = self._get_extension(file.filename)
        strategy = STRATEGIES.get(extension)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Tipo de archivo '{extension}' no soportado.",
            )

        # 2. Guardar archivo y generar ID
        document_id = str(uuid.uuid4())
        file_path = await self.save_file(file=file, document_id=document_id)
        logger.info("Archivo guardado en: %s", file_path)

        # 3. Extraer texto
        content = strategy.extract_content(file_path)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se pudo extraer texto del documento.",
            )
        logger.info("Texto extraído: %d caracteres", len(content))

        # 4. Dividir en chunks
        chunks = self._chunk_content(content)
        logger.info("Chunks generados: %d", len(chunks))

        # 5. Enviar al Embedding Service
        await self.send_chunks(
            document_id=document_id,
            filename=file.filename,
            chunks=chunks,
        )
        logger.info("Chunks enviados al Embedding Service")

        return DocumentUploadResponse(
            message="Documento procesado correctamente.",
            document_id=document_id,
        )

    async def save_file(self, file: UploadFile, document_id: str) -> str:
        file_path = await self._document_repo.save_file(
            file=file,
            document_id=document_id,
        )
        return file_path

    async def send_chunks(self, document_id: str, filename: str, chunks: list[str]) -> None:
        await self._embedding_client.send_chunks(
            document_id=document_id,
            filename=filename,
            chunks=chunks,
        )

    def _chunk_content(self, content: str) -> List[str]:
        size = settings.chunk_size
        overlap = settings.chunk_overlap
        chunks = []
        start = 0
        while start < len(content):
            end = start + size
            chunks.append(content[start:end])
            start += size - overlap
        return chunks

    @staticmethod
    def _get_extension(filename: str) -> str:
        parts = filename.rsplit(".", 1)
        if len(parts) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no tiene extensión.",
            )
        return parts[1].lower()