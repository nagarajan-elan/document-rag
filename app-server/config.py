from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str
    MINIO_SECURE: bool = False

    DATABASE_URL: str

    LLM_API_KEY: str
    LLM_BASE_URL: str
    CHAT_MODEL: str


    class Config:
        env_file = ".env"


settings = Settings()
