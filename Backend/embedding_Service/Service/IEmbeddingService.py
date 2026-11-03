from abc import ABC, abstractmethod
from embedding_Service.Model.Schemas import IndexRequest, IndexResponse, SearchHit


class IEmbeddingService(ABC):

    @abstractmethod
    async def save_embeddings(self, request: IndexRequest) -> IndexResponse:
        """Genera embeddings e indexa los chunks en Qdrant."""
        pass

    @abstractmethod
    def split_into_chunks(self, content: str) -> list[str]:
        """Divide texto en ventanas de tokens compatibles con el modelo."""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> list[SearchHit]:
        """Búsqueda vectorial a partir del texto de la pregunta."""
        pass
