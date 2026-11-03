from abc import ABC, abstractmethod
from document_Service.Model.Schemas import DocumentUploadResponse


class IDocumentService(ABC):

    @abstractmethod
    async def process_document(
        self,
        filename: str,
        content_type: str | None,
        file_content: bytes,
    ) -> DocumentUploadResponse:
        """
        Ingesta un documento: guarda, extrae, divide en chunks
        e indexa el mismo conjunto en embeddings y grafo.
        """
        pass
