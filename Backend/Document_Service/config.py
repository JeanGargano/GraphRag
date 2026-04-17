from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Almacenamiento
    upload_dir: str = "Uploads"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Servicios downstream
    embedding_service_url: str

    # App
    app_env: str = "development"
    http_timeout: int = 30

    class Config:
        env_file = ".env"


settings = Settings()