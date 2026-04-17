import logging

from fastapi import APIRouter, Depends, UploadFile, File

from Model.Schemas import DocumentUploadResponse
from Service.IDocument_Service import IDocumentService
from Service.Dependencies import get_document_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Document Service"])


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=201,
    summary="Procesar documento",
    description="Recibe un documento, extrae su texto, lo divide en chunks y los envía al Embedding Service.",
)
async def upload_document(
    file: UploadFile = File(...),
    service: IDocumentService = Depends(get_document_service),
):
    logger.info("Documento recibido: %s | tipo: %s", file.filename, file.content_type)
    return await service.process_document(file)
