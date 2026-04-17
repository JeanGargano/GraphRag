import logging

from fastapi import APIRouter, Depends, UploadFile, File

from Model.Schemas import DocumentUploadResponse
from Security.File_Validator import validate_file
from Service.IOrchestrator_Service import IOrchestratorService
from Service.Dependencies import get_orchestrator_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Orchestrator"])



# ── Ingesta de documentos ──────────────────────────────────

@router.post(
    "/orchestrator/upload",
    response_model=DocumentUploadResponse,
    status_code=201,
    summary="Ingesta de documento",
    description="Recibe un documento, lo valida y lo delega al Document Service.",
)
async def upload_document(
    file: UploadFile = File(..., description="Archivo a ingestar (pdf, docx, txt)"),
    service: IOrchestratorService = Depends(get_orchestrator_service)
):

    file_content = await validate_file(file)

    return await service.handle_document_upload(
        filename=file.filename,
        content_type=file.content_type,
        file_content=file_content,
    )
