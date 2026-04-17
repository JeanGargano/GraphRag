import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from config import settings
from Controller.Embedding_Controller import router
from Infra.Qdrant_Client import QdrantClientManager
from Infra.FastEmbed_Client import FastEmbedClient
from Repository.Embedding_Repository import EmbeddingRepository
from Service.Embedding_Service import EmbeddingService

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    qdrant_manager = QdrantClientManager(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
    )
    fastembed_client = FastEmbedClient(
        model_name=settings.embedding_model,
        max_tokens=settings.max_tokens_per_chunk,
    )
    app.state.embedding_service = EmbeddingService(
        embedding_repository=EmbeddingRepository(
            client=qdrant_manager.client,
            collection_name=settings.qdrant_collection,
            vector_size=fastembed_client.vector_size,
        ),
        fastembed_client=fastembed_client,
    )
    yield
    qdrant_manager.close()


app = FastAPI(lifespan=lifespan)
app.include_router(router)