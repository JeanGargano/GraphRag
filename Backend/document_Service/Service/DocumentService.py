import logging
import uuid
import asyncio

from DomainExceptions import (
    EmptyDocumentError,
    MissingFileExtensionError,
    UnsupportedFileTypeError,
)
from document_Service.Model.Schemas import DocumentUploadResponse
from embedding_Service.Model.Schemas import IndexRequest
from indexer_Service.Model.Schemas import (
    ChunkPayload as IndexerChunkPayload,
    IndexerRequest,
)
from document_Service.Repository.DocumentRepository import DocumentRepository
from document_Service.Service.IDocumentService import IDocumentService
from embedding_Service.Service.IEmbeddingService import IEmbeddingService
from indexer_Service.Service.IIndexerService import IIndexerService
from document_Service.Service.Extraction_Strategies import (
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
        embedding_service: IEmbeddingService,
        indexer_service: IIndexerService,
    ):
        self._document_repo = document_repository
        self._embedding_service = embedding_service
        self._indexer_service = indexer_service

    async def process_document(
        self,
        filename: str,
        content_type: str | None,
        file_content: bytes,
    ) -> DocumentUploadResponse:
        extension = self._get_extension(filename)
        strategy = STRATEGIES.get(extension)
        if not strategy:
            raise UnsupportedFileTypeError(extension)

        document_id = str(uuid.uuid4())
        file_path = await self._save_file(
            filename=filename,
            file_content=file_content,
            document_id=document_id,
        )
        logger.info("Archivo guardado en: %s", file_path)

        content = await asyncio.to_thread(strategy.extract_content, file_path)
        if not content:
            raise EmptyDocumentError()
        logger.info("Texto extraído: %d caracteres", len(content))

        chunks = self._embedding_service.split_into_chunks(content)
        if not chunks:
            raise EmptyDocumentError()
        logger.info("Chunks generados: %d", len(chunks))

        await self._send_chunks(
            document_id=document_id,
            filename=filename,
            chunks=chunks,
        )
        logger.info("Chunks enviados a Embedding e Indexer")

        return DocumentUploadResponse(
            message="Documento procesado correctamente.",
            document_id=document_id,
        )

    async def _save_file(self, filename: str, file_content: bytes, document_id: str) -> str:
        return await self._document_repo.save_file(
            filename=filename,
            file_content=file_content,
            document_id=document_id,
        )

    async def _send_chunks(self, document_id: str, filename: str, chunks: list[str]) -> None:
        chunk_ids = [f"{document_id}-{index:04d}" for index in range(len(chunks))]

        embedding_task = self._embedding_service.save_embeddings(
            IndexRequest(
                document_id=document_id,
                filename=filename,
                chunks=chunks,
                chunk_ids=chunk_ids,
            )
        )

        indexer_chunks = [
            IndexerChunkPayload(
                chunk_id=cid,
                chunk_index=index,
                text=chunk,
            )
            for index, (cid, chunk) in enumerate(zip(chunk_ids, chunks))
        ]

        indexer_task = self._indexer_service.process_chunks(
            IndexerRequest(
                document_id=document_id,
                filename=filename,
                chunks=indexer_chunks,
            )
        )
        await asyncio.gather(embedding_task, indexer_task)

    @staticmethod
    def _get_extension(filename: str) -> str:
        parts = filename.rsplit(".", 1)
        if len(parts) < 2:
            raise MissingFileExtensionError()
        return parts[1].lower()
