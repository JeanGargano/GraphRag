import logging

from fastapi import APIRouter, Depends, File, Request, UploadFile

from document_Service.Model.Schemas import DocumentUploadResponse
from question_Service.Model.Schemas import QuestionRequest, QuestionResponse
from orchestrator_Service.Security.File_Validator import validate_file
from orchestrator_Service.Service.IOrchestratorService import IOrchestratorService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Orchestrator"])


def get_orchestrator_service(request: Request) -> IOrchestratorService:
    return request.app.state.orchestrator_service


@router.post(
    "/orchestrator/upload",
    response_model=DocumentUploadResponse,
    status_code=201,
    summary="Ingesta de documento",
    description="Recibe un documento, lo valida y lo delega al Document Service.",
)
async def upload_document(
    file: UploadFile = File(..., description="Archivo a ingestar (pdf, docx, txt)"),
    service: IOrchestratorService = Depends(get_orchestrator_service),
):
    file_content = await validate_file(file)

    return await service.send_document(
        filename=file.filename,
        content_type=file.content_type,
        file_content=file_content,
    )


@router.post(
    "/orchestrator/ask",
    response_model=QuestionResponse,
    status_code=200,
    summary="Preguntar al sistema",
    description="Realiza una recuperación híbrida (Vector + Grafo) basada en la pregunta del usuario.",
)
async def ask_question(
    request: QuestionRequest,
    service: IOrchestratorService = Depends(get_orchestrator_service),
):
    return await service.ask_question(request)
