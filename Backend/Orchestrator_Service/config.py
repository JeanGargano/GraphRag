from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Servicios
    document_service_url: str

    # API Gateway
    app_env: str = "development"
    max_file_size_mb: int = 10
    allowed_extensions: str = "pdf,docx,txt"

    # Timeouts
    http_timeout: int = 30

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    class Config:
        env_file = ".env"


settings = Settings()