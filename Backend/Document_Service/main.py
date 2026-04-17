from contextlib import asynccontextmanager
from fastapi import FastAPI
from config import settings
from Repository.Document_Repository import DocumentRepository
from Repository.Embedding_Client import EmbeddingServiceClient
from Service.Document_Service import DocumentService
from Controller import Document_Controller as document_controller
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.document_service = DocumentService(
        document_repository=DocumentRepository(),
        embedding_client=EmbeddingServiceClient(
            base_url=settings.embedding_service_url
        ),
    )
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document_controller.router)
