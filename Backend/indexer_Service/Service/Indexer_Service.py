import asyncio
import logging

from indexer_Service.Infra.Spacy_Client import INERProvider
from indexer_Service.Model.Schemas import (
    GraphSearchHit,
    IndexerRequest,
    IndexerResponse,
)
from indexer_Service.Repository.GraphRepository import GraphRepository
from indexer_Service.Service.IIndexerService import IIndexerService

logger = logging.getLogger(__name__)


class IndexerService(IIndexerService):

    def __init__(
        self,
        graph_repository: GraphRepository,
        ner_provider: INERProvider,
    ):
        self._repo = graph_repository
        self._ner = ner_provider

    async def process_chunks(self, request: IndexerRequest) -> IndexerResponse:
        logger.info(
            "Indexando grafo '%s' | %d chunks",
            request.document_id,
            len(request.chunks),
        )

        await asyncio.to_thread(
            self._repo.upsert_document,
            request.document_id,
            request.filename,
        )

        total_entities = 0
        total_relations = 0

        for chunk in request.chunks:
            await asyncio.to_thread(
                self._repo.upsert_chunk,
                request.document_id,
                chunk.chunk_id,
                chunk.chunk_index,
                chunk.text,
            )

            extraction_result = await self._ner.extract(chunk.text)
            extracted_entities = extraction_result.get("entities", [])
            extracted_relations = extraction_result.get("relations", [])

            for ent in extracted_entities:
                await asyncio.to_thread(
                    self._repo.upsert_custom_entity_and_link,
                    chunk.chunk_id,
                    ent.get("type"),
                    ent.get("properties", {}),
                )

            for rel in extracted_relations:
                await asyncio.to_thread(
                    self._repo.upsert_custom_relation,
                    rel.get("source"),
                    rel.get("target"),
                    rel.get("type"),
                    rel.get("properties") or {},
                )

            total_entities += len(extracted_entities)
            total_relations += len(extracted_relations)
            logger.debug(
                "Chunk %d: %d entidades, %d relaciones",
                chunk.chunk_index,
                len(extracted_entities),
                len(extracted_relations),
            )

        sorted_chunks = sorted(request.chunks, key=lambda c: c.chunk_index)
        for i in range(len(sorted_chunks) - 1):
            await asyncio.to_thread(
                self._repo.link_consecutive_chunks,
                sorted_chunks[i].chunk_id,
                sorted_chunks[i + 1].chunk_id,
            )

        logger.info(
            "Grafo indexado: %d chunks, %d entidades, %d relaciones de ontología creadas",
            len(request.chunks),
            total_entities,
            total_relations,
        )

        return IndexerResponse(
            message="Grafo indexado correctamente.",
            document_id=request.document_id,
            chunks_processed=len(request.chunks),
            entities_found=total_entities,
        )

    async def search_by_entities(
        self,
        entities: list[str],
        limit: int = 15,
    ) -> list[GraphSearchHit]:
        rows = await asyncio.to_thread(
            self._repo.search_chunks_by_entities,
            entities,
            limit,
        )
        return [
            GraphSearchHit(
                chunk_id=row.get("chunk_id", "unknown"),
                text=row.get("text", ""),
                document_id=row.get("document_id"),
                matched_entity=row.get("matched_entity"),
            )
            for row in rows
        ]
