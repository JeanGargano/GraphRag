import logging
from fastapi import APIRouter, Depends
from Model.Schemas import IndexRequest, IndexResponse
from Service.IEmbedding_Service import IEmbeddingService
from Service.Dependencies import get_embedding_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Embedding Service"])


@router.post(
    "/embeddings/process",
    response_model=IndexResponse,
    status_code=201,
    summary="Procesar chunks e indexar embeddings",
    description="Recibe chunks de un documento, genera embeddings y los persiste en Qdrant.",
)
async def index_document(
    payload: IndexRequest,
    service: IEmbeddingService = Depends(get_embedding_service),
):
    logger.info("Request de indexación: %s | chunks: %d", payload.document_id, len(payload.chunks))
    return await service.process_chunks(payload)
