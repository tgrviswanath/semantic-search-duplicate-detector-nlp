from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "NLP Semantic Search Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8001
    EMBED_MODEL: str = "all-MiniLM-L6-v2"
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    TOP_K: int = 10
    DUPLICATE_THRESHOLD: float = 0.85

    class Config:
        env_file = ".env"


settings = Settings()
