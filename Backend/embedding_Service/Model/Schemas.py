from pydantic import BaseModel


class IndexRequest(BaseModel):
    document_id: str
    filename: str
    chunks: list[str]
    chunk_ids: list[str]


class IndexResponse(BaseModel):
    message: str
    document_id: str
    chunks_indexed: int
    chunks_discarded: int = 0


class SearchHit(BaseModel):
    chunk_id: str
    text: str
    score: float | None = None
    document_id: str | None = None


Request = IndexRequest
Response = IndexResponse
