import logging

from Model.Schemas import DocumentUploadResponse
from Repository.Orchestrator_Repository import OrchestratorRepository
from Service.IOrchestrator_Service import IOrchestratorService

logger = logging.getLogger(__name__)


class OrchestratorService(IOrchestratorService):

    def __init__(self, repository: OrchestratorRepository):
        self._repository = repository

    async def handle_document_upload(
        self,
        filename: str,
        content_type: str,
        file_content: bytes,
    ) -> DocumentUploadResponse:
        logger.info("Iniciando Envio de documento: %s", filename)
        result = await self._repository.send_document(
            filename=filename,
            content_type=content_type,
            file_content=file_content,
        )
        logger.info("Documento ingresado correctamente. ID: %s", result.document_id)
        return result
