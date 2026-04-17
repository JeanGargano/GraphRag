from fastapi import Request
from Service.IEmbedding_Service import IEmbeddingService


def get_embedding_service(request: Request) -> IEmbeddingService:
    return request.app.state.embedding_service