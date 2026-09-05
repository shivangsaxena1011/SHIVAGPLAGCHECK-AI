"""Core Configuration for SHIVANG PLAGCHECK AI.

Loads settings from environment variables and provides sensible defaults
for local, desktop, and production environments.
"""

from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "SHIVANG PLAGCHECK AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SUBTITLE: str = "Academic Similarity, AI-Writing & Citation Integrity Platform"

    # Server & Security
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "shivang-plagcheck-ai-super-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    # Default to local SQLite for instant zero-config startup; supports PostgreSQL + pgvector
    DATABASE_URL: str = "sqlite+aiosqlite:///./shivang_plagcheck.db"

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    REPORT_DIR: Path = STORAGE_DIR / "reports"
    CORPUS_DIR: Path = STORAGE_DIR / "corpus"
    MODEL_CACHE_DIR: Path = STORAGE_DIR / "models"

    # Limits
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt"}

    # Detection Algorithms Configuration
    WINNOWING_K: int = 5
    WINNOWING_W: int = 8
    MIN_SEED_LEN: int = 12
    MIN_PASSAGE_LEN: int = 15
    EXTEND_TOLERANCE: float = 0.75
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.82
    SEMANTIC_MODEL_NAME: str = "all-MiniLM-L6-v2"
    DEVICE: str = "cpu"

    # External APIs
    CROSSREF_API_EMAIL: str = "researcher@example.edu"
    OPENALEX_EMAIL: str = "researcher@example.edu"
    SEMANTIC_SCHOLAR_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    def ensure_directories(self) -> None:
        """Ensure that all necessary storage directories exist."""
        for path in [
            self.STORAGE_DIR,
            self.UPLOAD_DIR,
            self.REPORT_DIR,
            self.CORPUS_DIR,
            self.MODEL_CACHE_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
