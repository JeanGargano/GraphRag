import asyncio
import logging

from Config import settings
from DomainExceptions import NoValidChunksError
from embedding_Service.Infra.FastEmbedClient import FastEmbedClient
from embedding_Service.Model.Schemas import IndexRequest, IndexResponse, SearchHit
from embedding_Service.Repository.EmbeddingRepository import EmbeddingRepository
from embedding_Service.Service.IEmbeddingService import IEmbeddingService

logger = logging.getLogger(__name__)


class EmbeddingService(IEmbeddingService):

    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
        fastembed_client: FastEmbedClient,
    ):
        self._repo = embedding_repository
        self._fastembed = fastembed_client

    def split_into_chunks(self, content: str) -> list[str]:
        return self._fastembed.split_into_chunks(
            content,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )

    async def save_embeddings(self, request: IndexRequest) -> IndexResponse:
        logger.info(
            "Procesando documento '%s' | %d chunks recibidos",
            request.document_id,
            len(request.chunks),
        )

        if not request.chunks:
            raise NoValidChunksError("No se recibieron chunks para indexar.")

        valid_indices = [
            i for i, chunk in enumerate(request.chunks)
            if self._fastembed.count_tokens(chunk) <= self._fastembed._max_tokens
        ]

        if not valid_indices:
            raise NoValidChunksError(
                "Todos los chunks superan el límite de tokens del modelo."
            )

        valid_chunks = [request.chunks[i] for i in valid_indices]
        valid_ids = [request.chunk_ids[i] for i in valid_indices]
        discarded = len(request.chunks) - len(valid_chunks)

        if discarded:
            logger.warning(
                "%d chunks descartados por límite de tokens; no deberían llegar aquí",
                discarded,
            )

        logger.info(
            "%d/%d chunks válidos tras validación de tokens",
            len(valid_chunks),
            len(request.chunks),
        )

        vectors = await asyncio.to_thread(self._fastembed.embed, valid_chunks)
        logger.info(
            "Embeddings generados: %d vectores de dimensión %d",
            len(vectors),
            len(vectors[0]),
        )

        await asyncio.to_thread(
            self._repo.upsert_points,
            request.document_id,
            request.filename,
            valid_chunks,
            valid_ids,
            vectors,
        )

        return IndexResponse(
            message="Chunks indexados correctamente.",
            document_id=request.document_id,
            chunks_indexed=len(vectors),
            chunks_discarded=discarded,
        )

    async def search(self, query: str, limit: int = 5) -> list[SearchHit]:
        query_vector = (await asyncio.to_thread(self._fastembed.embed, [query]))[0]
        results = await asyncio.to_thread(self._repo.search_vectors, query_vector, limit)
        return [
            SearchHit(
                chunk_id=res.get("chunk_id", "unknown"),
                text=res.get("text", ""),
                score=res.get("score"),
                document_id=res.get("document_id"),
            )
            for res in results
        ]
