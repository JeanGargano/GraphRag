import logging
from indexer_Service.Model.Schemas import IndexerRequest, IndexerResponse
from indexer_Service.Infra.Spacy_Client import SpacyNERProvider
from indexer_Service.Repository.GraphRepository import GraphRepository
from indexer_Service.Service.IIndexerService import IIndexerService

logger = logging.getLogger(__name__)


class IndexerService(IIndexerService):

    def __init__(
        self,
        graph_repository: GraphRepository,
        spacy_client: SpacyNERProvider,
    ):
        self._repo = graph_repository
        self._spacy = spacy_client

    async def process_chunks(self, request: IndexerRequest) -> IndexerResponse:
        logger.info(
            "Indexando grafo '%s' | %d chunks",
            request.document_id,
            len(request.chunks),
        )

        total_entities = 0

        # 1. Crear nodo Document
        self._repo.upsert_document(
            document_id=request.document_id,
            filename=request.filename,
        )

        total_entities = 0
        total_relations = 0

        # 2. Procesar cada chunk
        for chunk in request.chunks:
            # Crear nodo Chunk + relación HAS_CHUNK
            self._repo.upsert_chunk(
                document_id=request.document_id,
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
            )

            # Extraer entidades y relaciones desde el LLM
            extraction_result = await self._spacy.extract(chunk.text)
            extracted_entities = extraction_result.get("entities", [])
            extracted_relations = extraction_result.get("relations", [])

            # Indexar entidades
            for ent in extracted_entities:
                ent_type = ent.get("type")
                properties = ent.get("properties", {})
                self._repo.upsert_custom_entity_and_link(
                    chunk_id=chunk.chunk_id,
                    entity_type=ent_type,
                    properties=properties,
                )
            
            # Indexar relaciones directas entre entidades
            for rel in extracted_relations:
                source = rel.get("source")
                target = rel.get("target")
                rel_type = rel.get("type")
                properties = rel.get("properties", {})
                self._repo.upsert_custom_relation(
                    source=source,
                    target=target,
                    rel_type=rel_type,
                    properties=properties,
                )

            total_entities += len(extracted_entities)
            total_relations += len(extracted_relations)
            logger.debug("Chunk %d: %d entidades, %d relaciones", chunk.chunk_index, len(extracted_entities), len(extracted_relations))

        # 3. Crear relaciones NEXT_CHUNK entre chunks consecutivos
        sorted_chunks = sorted(request.chunks, key=lambda c: c.chunk_index)
        for i in range(len(sorted_chunks) - 1):
            self._repo.link_consecutive_chunks(
                chunk_id_current=sorted_chunks[i].chunk_id,
                chunk_id_next=sorted_chunks[i + 1].chunk_id,
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
