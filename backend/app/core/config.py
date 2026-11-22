from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "LifeSync AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-64chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://lifesync:lifesync_secret@localhost:5432/lifesync_db"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://lifesync:lifesync_secret@localhost:5432/lifesync_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Provider Settings
    DEFAULT_AI_PROVIDER: str = "openai_compatible"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_CHAT_MODEL: str = "gpt-4o-mini"
    DEFAULT_REASONING_MODEL: str = "gpt-4o"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    # Local Model Settings (Ollama / vLLM / Custom)
    LOCAL_LLM_BASE_URL: str = "http://localhost:11434/v1"
    LOCAL_CHAT_MODEL: str = "llama3.1:8b"
    LOCAL_EMBEDDING_MODEL: str = "nomic-embed-text"

    # External Integrations (Google OAuth & Gmail)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:5173/integrations/callback"

    # External Integrations (Microsoft Outlook & Graph)
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_REDIRECT_URI: str = "http://localhost:5173/integrations/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()