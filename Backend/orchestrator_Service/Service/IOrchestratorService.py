from abc import ABC, abstractmethod

from document_Service.Model.Schemas import DocumentUploadResponse
from question_Service.Model.Schemas import QuestionRequest, QuestionResponse


class IOrchestratorService(ABC):

    @abstractmethod
    async def send_document(
        self, filename: str, content_type: str, file_content: bytes
    ) -> DocumentUploadResponse:
        """Orquesta la ingesta de un documento."""
        pass

    @abstractmethod
    async def ask_question(self, request: QuestionRequest) -> QuestionResponse:
        """Delega la pregunta al QuestionService para recuperación híbrida."""
        pass
