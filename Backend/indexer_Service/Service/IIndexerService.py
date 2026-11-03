from abc import ABC, abstractmethod
from indexer_Service.Model.Schemas import (
    GraphSearchHit,
    IndexerRequest,
    IndexerResponse,
)


class IIndexerService(ABC):

    @abstractmethod
    async def process_chunks(self, request: IndexerRequest) -> IndexerResponse:
        """Recibe chunks, aplica NER e indexa el grafo en Neo4j."""
        pass

    @abstractmethod
    async def search_by_entities(
        self,
        entities: list[str],
        limit: int = 15,
    ) -> list[GraphSearchHit]:
        """Recupera chunks del grafo a partir de términos de entidad."""
        pass
