import logging
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from embedding_Service.Infra.ANNSearchHelper import ANNSearchHelper

logger = logging.getLogger(__name__)


class EmbeddingRepository:

    def __init__(self, client: QdrantClient, collection_name: str, vector_size: int):
        self._client = client
        self._collection_name = collection_name
        self._ensure_collection(vector_size)

    def _ensure_collection(self, vector_size: int) -> None:
        existing = [c.name for c in self._client.get_collections().collections]
        if self._collection_name not in existing:
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Colección '%s' creada", self._collection_name)
        else:
            logger.info("Colección '%s' ya existe", self._collection_name)

    def upsert_points(
        self,
        document_id: str,
        filename: str,
        chunks: list[str],
        chunk_ids: list[str],
        vectors: list[list[float]],
    ) -> None:
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id)),
                vector=vector,
                payload={
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "filename": filename,
                    "chunk_index": i,
                    "text": chunk,
                },
            )
            for i, (chunk, chunk_id, vector) in enumerate(zip(chunks, chunk_ids, vectors))
        ]
        self._client.upsert(
            collection_name=self._collection_name,
            points=points,
        )
        logger.info("Upsert de %d puntos", len(points))

    def search_vectors(self, query_vector: list[float], limit: int = 5) -> list[dict]:
        search_params = ANNSearchHelper.get_hnsw_search_params(ef_search=128)

        results = self._client.search(
            collection_name=self._collection_name,
            query_vector=query_vector,
            limit=limit,
            search_params=search_params,
        )

        return [{"score": hit.score, **hit.payload} for hit in results]
