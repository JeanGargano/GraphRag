from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "question_service"

    class Config:
        env_file = ".env"


settings = Settings()
