import logging
from typing import List
from question_Service.Model.Schemas import QuestionRequest, QuestionResponse, RetrievedChunk
from embedding_Service.Repository.EmbeddingRepository import EmbeddingRepository
from embedding_Service.Infra.FastEmbedClient import FastEmbedClient
from indexer_Service.Repository.GraphRepository import GraphRepository
from indexer_Service.Infra.Spacy_Client import SpacyNERProvider
from question_Service.Infra.LLMClient import LLMClient

logger = logging.getLogger(__name__)

class QuestionService:
    def __init__(
        self,
        embedding_repo: EmbeddingRepository,
        fastembed_client: FastEmbedClient,
        graph_repo: GraphRepository,
        spacy_client: SpacyNERProvider,
        llm_client: LLMClient,
    ):
        self._embedding_repo = embedding_repo
        self._fastembed = fastembed_client
        self._graph_repo = graph_repo
        self._spacy = spacy_client
        self._llm = llm_client

    async def ask_question(self, request: QuestionRequest) -> QuestionResponse:
        logger.info(f"Procesando pregunta: '{request.query}'")
        
        all_chunks = {} # Dictionary to deduplicate by chunk text or id
        
        # 1. Búsqueda Vectorial (Qdrant)
        try:
            logger.info("Generando embedding de la pregunta...")
            query_vector = self._fastembed.embed([request.query])[0]
            
            logger.info("Buscando en Qdrant (HNSW)...")
            vector_results = self._embedding_repo.search_vectors(query_vector, limit=request.limit)
            for res in vector_results:
                text = res.get("text", "")
                if text not in all_chunks:
                    all_chunks[text] = RetrievedChunk(
                        chunk_id=res.get("chunk_id", "unknown"),
                        text=text,
                        source="vector",
                        score=res.get("score"),
                        metadata={"document_id": res.get("document_id")}
                    )
        except Exception as e:
            logger.error(f"Error en búsqueda vectorial: {e}")

        # 2. Búsqueda en Grafo (Neo4j)
        try:
            logger.info("Extrayendo entidades de la pregunta con spaCy...")
            entities_tuples = await self._spacy.extract(request.query)
            entities_list = [e[0] for e in entities_tuples]
            logger.info(f"Entidades detectadas: {entities_list}")
            
            if entities_list:
                logger.info("Buscando en Neo4j...")
                graph_results = self._graph_repo.search_chunks_by_entities(entities_list, limit=request.limit)
                for res in graph_results:
                    text = res.get("text", "")
                    if text not in all_chunks:
                        all_chunks[text] = RetrievedChunk(
                            chunk_id=res.get("chunk_id", "unknown"),
                            text=text,
                            source="graph",
                            metadata={"document_id": res.get("document_id"), "matched_entity": res.get("matched_entity")}
                        )
                    else:
                        # Si ya estaba de vector, le añadimos info
                        all_chunks[text].source = "hybrid"
                        all_chunks[text].metadata["matched_entity"] = res.get("matched_entity")
            else:
                logger.info("No se detectaron entidades, saltando búsqueda en grafo.")
        except Exception as e:
            logger.error(f"Error en búsqueda de grafo: {e}")

        # Retornar combinados
        combined_chunks = list(all_chunks.values())
        logger.info(f"Total de chunks únicos recuperados: {len(combined_chunks)}")
        
        # 3. Generar respuesta con LLM
        context_text = "\n\n---\n\n".join([c.text for c in combined_chunks])
        
        if not combined_chunks:
            answer = "No encontré información relevante en mis documentos para responder a esta pregunta."
        else:
            answer = await self._llm.generate_answer(query=request.query, context=context_text)
        
        return QuestionResponse(
            query=request.query,
            answer=answer,
            chunks=combined_chunks
        )
