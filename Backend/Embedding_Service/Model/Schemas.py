from pydantic import BaseModel

class IndexRequest(BaseModel):
    document_id: str
    filename: str
    chunks: list[str]

class IndexResponse(BaseModel):
    message: str
    document_id: str
    chunks_indexed: int
    chunks_discarded: int = 0


Request = IndexRequest
Response = IndexResponse
