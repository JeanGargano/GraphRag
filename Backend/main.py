import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from Config import settings
from DomainExceptions import GraphRAGError

from embedding_Service.Infra.Qdrant_Client import get_qdrant_client
from indexer_Service.Infra.Neo4j_Client import get_neo4j_driver

from document_Service.Repository.DocumentRepository import DocumentRepository
from document_Service.Service.DocumentService import DocumentService

from embedding_Service.Repository.EmbeddingRepository import EmbeddingRepository
from embedding_Service.Service.EmbeddingService import EmbeddingService
from embedding_Service.Infra.FastEmbedClient import FastEmbedClient

from indexer_Service.Repository.GraphRepository import GraphRepository
from indexer_Service.Service.Indexer_Service import IndexerService
from indexer_Service.Infra.Spacy_Client import SpacyNERProvider

from question_Service.Service.QuestionService import QuestionService
from question_Service.Infra.LLMClient import LLMClient

from orchestrator_Service.Controller.OrchestratorController import router as orchestrator_router
from orchestrator_Service.Service.OrchestratorService import OrchestratorService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando GraphRAG")

    qdrant = get_qdrant_client()
    neo4j = get_neo4j_driver()

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
        ner_provider=ner_provider,
    )

    document_repo = DocumentRepository()
    document_service = DocumentService(
        document_repository=document_repo,
        embedding_service=embedding_service,
        indexer_service=indexer_service,
    )

    llm_client = None
    if settings.groq_api_key:
        llm_client = LLMClient(api_key=settings.groq_api_key)
    else:
        logger.warning("No se proporcionó groq_api_key. /ask devolverá 503.")

    question_service = QuestionService(
        embedding_service=embedding_service,
        indexer_service=indexer_service,
        ner_provider=ner_provider,
        llm_client=llm_client,
    )

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # "http://localhost:5173"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(GraphRAGError)
async def graphrag_error_handler(_request: Request, exc: GraphRAGError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )


app.include_router(orchestrator_router)


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}

