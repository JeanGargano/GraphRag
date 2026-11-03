import logging

from DomainExceptions import QuestionServiceUnavailableError
from document_Service.Model.Schemas import DocumentUploadResponse
from document_Service.Service.IDocumentService import IDocumentService
from orchestrator_Service.Service.IOrchestratorService import IOrchestratorService
from question_Service.Model.Schemas import QuestionRequest, QuestionResponse
from question_Service.Service.IQuestionService import IQuestionService

logger = logging.getLogger(__name__)


class OrchestratorService(IOrchestratorService):

    def __init__(
        self,
        document_service: IDocumentService,
        question_service: IQuestionService | None = None,
    ):
        self._document_service = document_service
        self._question_service = question_service

    async def send_document(
        self,
        filename: str,
        content_type: str,
        file_content: bytes,
    ) -> DocumentUploadResponse:
        logger.info("Iniciando Envio de documento: %s", filename)
        result = await self._document_service.process_document(
            filename=filename,
            content_type=content_type,
            file_content=file_content,
        )
        logger.info("Documento ingresado correctamente. ID: %s", result.document_id)
        return result

    async def ask_question(self, request: QuestionRequest) -> QuestionResponse:
        logger.info("Orquestando pregunta...")
        if not self._question_service:
            raise QuestionServiceUnavailableError()
        return await self._question_service.ask_question(request)
