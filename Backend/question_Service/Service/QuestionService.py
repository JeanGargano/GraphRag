import logging

from DomainExceptions import LLMNotConfiguredError
from embedding_Service.Service.IEmbeddingService import IEmbeddingService
from indexer_Service.Infra.Spacy_Client import INERProvider
from indexer_Service.Service.IIndexerService import IIndexerService
from question_Service.Infra.LLMClient import LLMClient
from question_Service.Model.Schemas import QuestionRequest, QuestionResponse, RetrievedChunk
from question_Service.Service.IQuestionService import IQuestionService

logger = logging.getLogger(__name__)


def _entity_search_terms(extraction: dict) -> list[str]:
    terms: list[str] = []
    for ent in extraction.get("entities", []):
        properties = ent.get("properties") or {}
        if not isinstance(properties, dict):
            continue
        for value in properties.values():
            if value is None:
                continue
            text = str(value).strip()
            if text and text.lower() != "null":
                terms.append(text)
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        key = term.lower()
        if key not in seen:
            seen.add(key)
            unique.append(term)
    return unique


class QuestionService(IQuestionService):

    def __init__(
        self,
        embedding_service: IEmbeddingService,
        indexer_service: IIndexerService,
        ner_provider: INERProvider,
        llm_client: LLMClient | None,
    ):
        self._embedding_service = embedding_service
        self._indexer_service = indexer_service
        self._ner = ner_provider
        self._llm = llm_client

    async def ask_question(self, request: QuestionRequest) -> QuestionResponse:
        logger.info("Procesando pregunta: '%s'", request.query)

        if self._llm is None:
            raise LLMNotConfiguredError()

        all_chunks: dict[str, RetrievedChunk] = {}

        try:
            logger.info("Buscando en Qdrant (HNSW)...")
            vector_results = await self._embedding_service.search(
                request.query,
                limit=request.limit,
            )
            for res in vector_results:
                text = res.text or ""
                if text not in all_chunks:
                    all_chunks[text] = RetrievedChunk(
                        chunk_id=res.chunk_id,
                        text=text,
                        source="vector",
                        score=res.score,
                        metadata={"document_id": res.document_id},
                    )
        except Exception as e:
            logger.error("Error en búsqueda vectorial: %s", e)

        try:
            logger.info("Extrayendo entidades de la pregunta...")
            extraction = await self._ner.extract(request.query)
            entities_list = _entity_search_terms(extraction)
            logger.info("Entidades detectadas: %s", entities_list)

            if entities_list:
                logger.info("Buscando en Neo4j...")
                graph_results = await self._indexer_service.search_by_entities(
                    entities_list,
                    limit=request.limit,
                )
                for res in graph_results:
                    text = res.text or ""
                    if text not in all_chunks:
                        all_chunks[text] = RetrievedChunk(
                            chunk_id=res.chunk_id,
                            text=text,
                            source="graph",
                            metadata={
                                "document_id": res.document_id,
                                "matched_entity": res.matched_entity,
                            },
                        )
                    else:
                        all_chunks[text].source = "hybrid"
                        all_chunks[text].metadata["matched_entity"] = res.matched_entity
            else:
                logger.info("No se detectaron entidades, saltando búsqueda en grafo.")
        except Exception as e:
            logger.error("Error en búsqueda de grafo: %s", e)

        combined_chunks = list(all_chunks.values())
        logger.info("Total de chunks únicos recuperados: %d", len(combined_chunks))

        if not combined_chunks:
            answer = (
                "No encontré información relevante en mis documentos "
                "para responder a esta pregunta."
            )
        else:
            context_text = "\n\n---\n\n".join([c.text for c in combined_chunks])
            answer = await self._llm.generate_answer(
                query=request.query,
                context=context_text,
            )

        return QuestionResponse(
            query=request.query,
            answer=answer,
            chunks=combined_chunks,
        )
