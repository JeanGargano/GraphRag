from abc import ABC, abstractmethod
from Model.Schemas import IndexRequest, IndexResponse


class IEmbeddingService(ABC):

    @abstractmethod
    async def process_chunks(self, request: IndexRequest) -> IndexResponse:
        """
        Recibe los chunks de un documento, genera sus embeddings
        y los indexa en Qdrant.
        """
        pass