from abc import ABC, abstractmethod

from Model.Schemas import DocumentUploadResponse


class IOrchestratorService(ABC):

    @abstractmethod
    async def handle_document_upload(
        self, filename: str, content_type: str, file_content: bytes) -> DocumentUploadResponse:
        """
        Orquesta la ingesta de un documento.
        Recibe los bytes ya validados por el API Gateway.
        """
        pass