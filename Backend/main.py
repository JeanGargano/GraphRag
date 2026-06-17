import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI

from Config import settings

# ── Clientes de infraestructura ──────────────────────────────────────────────────────
from embedding_Service.Infra.Qdrant_Client import get_qdrant_client
from indexer_Service.Infra.Neo4j_Client import get_neo4j_driver

# ── Document ───────────────────────────────────────────────────────────────────
from document_Service.Repository.DocumentRepository import DocumentRepository
from document_Service.Service.DocumentService import DocumentService

# ── Embedding ─────────────────────────────────────────────────────────────────
from embedding_Service.Repository.EmbeddingRepository import EmbeddingRepository
from embedding_Service.Service.EmbeddingService import EmbeddingService
from embedding_Service.Infra.FastEmbedClient import FastEmbedClient

# ── Indexer ───────────────────────────────────────────────────────────────────
from indexer_Service.Repository.GraphRepository import GraphRepository
from indexer_Service.Service.Indexer_Service import IndexerService
from indexer_Service.Infra.Spacy_Client import SpacyNERProvider

# ── Question ──────────────────────────────────────────────────────────────────
from question_Service.Service.QuestionService import QuestionService
from question_Service.Infra.LLMClient import LLMClient

# ── Orchestrator ───────────────────────────────────────────────────────────────
from orchestrator_Service.Controller.OrchestratorController import router as orchestrator_router
from orchestrator_Service.Service.OrchestratorService import OrchestratorService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando GraphRAG")

    # Clientes de infraestructura
    qdrant = get_qdrant_client()
    neo4j = get_neo4j_driver()

    # Módulo Embedding
    embedding_provider = FastEmbedClient(
        model_name=settings.fastembed_model_name,
        max_tokens=settings.fastembed_max_tokens,
    )
    embedding_repo = EmbeddingRepository(
        client=qdrant,
        collection_name=settings.qdrant_collection,
        vector_size=embedding_provider.vector_size,
    )
    embedding_service = EmbeddingService(
        embedding_repository=embedding_repo,
        fastembed_client=embedding_provider,
    )

    # Módulo Indexer (NER Provider)
    if settings.groq_api_key:
        from indexer_Service.Infra.LLM_NER_Client import LLMNERProvider
        ner_provider = LLMNERProvider(api_key=settings.groq_api_key)
        logger.info("Usando LLMNERProvider (Groq) para extracción de entidades")
    else:
        logger.warning("No se proporcionó groq_api_key. Usando SpacyNERProvider como fallback.")
        ner_provider = SpacyNERProvider(model_name=settings.spacy_model)

    indexer_repo = GraphRepository(driver=neo4j)
    indexer_service = IndexerService(
        graph_repository=indexer_repo,
        spacy_client=ner_provider,
    )

    # Módulo Document
    document_repo = DocumentRepository()
    document_service = DocumentService(
        document_repository=document_repo,
        embedding_service=embedding_service,
        indexer_service=indexer_service,
    )

    # Módulo Question
    llm_client = None
    if settings.groq_api_key:
        llm_client = LLMClient(api_key=settings.groq_api_key)
    else:
        logger.warning("No se proporcionó groq_api_key. El generador de respuestas fallará.")
        
    question_service = QuestionService(
        embedding_repo=embedding_repo,
        fastembed_client=embedding_provider,
        graph_repo=indexer_repo,
        spacy_client=ner_provider,
        llm_client=llm_client,
    )

    # Orchestrator (recibe los servicios por inyección)
    orchestrator_service = OrchestratorService(
        document_service=document_service,
        question_service=question_service,
    )

    app.state.orchestrator_service = orchestrator_service

    logger.info("Todos los servicios listos.")
    yield

    logger.info("Apagando GraphRAG…")
    neo4j.close()


app = FastAPI(
    title="GraphRAG API",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(orchestrator_router)


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}
