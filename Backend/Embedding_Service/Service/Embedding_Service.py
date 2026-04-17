import logging
from fastapi import HTTPException, status
from Model.Schemas import IndexRequest, IndexResponse
from Infra.FastEmbed_Client import FastEmbedClient
from Repository.Embedding_Repository import EmbeddingRepository
from Service.IEmbedding_Service import IEmbeddingService

logger = logging.getLogger(__name__)


class EmbeddingService(IEmbeddingService):

    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
        fastembed_client: FastEmbedClient,
    ):
        self._repo = embedding_repository
        self._fastembed = fastembed_client

    async def process_chunks(self, request: IndexRequest) -> IndexResponse:
        logger.info(
            "Procesando documento '%s' | %d chunks recibidos",
            request.document_id,
            len(request.chunks),
        )

        if not request.chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se recibieron chunks para indexar.",
            )

        # 1. Validar que los chunks no superen el límite de tokens del modelo
        valid_chunks = self._fastembed.validate_chunks(request.chunks)
        if not valid_chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Todos los chunks superan el límite de tokens del modelo.",
            )
        logger.info(
            "%d/%d chunks válidos tras validación de tokens",
            len(valid_chunks),
            len(request.chunks),
        )

        # 2. Generar embeddings (FastEmbed tokeniza internamente aquí)
        vectors = self._fastembed.embed(valid_chunks)
        logger.info("Embeddings generados: %d vectores de dimensión %d", len(vectors), len(vectors[0]))

        # 3. Persistir en Qdrant
        self._repo.upsert_points(
            document_id=request.document_id,
            filename=request.filename,
            chunks=valid_chunks,
            vectors=vectors,
        )

        return IndexResponse(
            message="Chunks indexados correctamente.",
            document_id=request.document_id,
            chunks_indexed=len(vectors),
            chunks_discarded=len(request.chunks) - len(valid_chunks),
        )