import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "SourceLearn"
    API_V1_STR: str = "/api"
    # PostgreSQL port 5433 is our dedicated server; SQLite fallback available if needed
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres@localhost:5433/sourcelearn")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sourcelearn-super-secret-key-change-in-prod")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    EXTRACTED_MEDIA_DIR: str = os.path.join(UPLOAD_DIR, "extracted_media")
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://localhost:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.EXTRACTED_MEDIA_DIR, exist_ok=True)
