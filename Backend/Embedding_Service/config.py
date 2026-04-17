from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "documents"
    embedding_model: str = "BAAI/bge-small-en"
    max_tokens_per_chunk: int = 512

    class Config:
        env_file = ".env"

settings = Settings()