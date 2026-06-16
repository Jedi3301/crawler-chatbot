"""
backend/app/core/config.py

Single source of truth for every environment variable used in the app.
All services read settings from here — no scattered os.getenv() calls.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py → core/ → app/ → backend/ → project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):

    # ------------------------------------------------------------------ #
    #  Firecrawl
    # ------------------------------------------------------------------ #
    FIRECRAWL_API_KEY: str

    # ------------------------------------------------------------------ #
    #  Pinecone (vector store)
    # ------------------------------------------------------------------ #
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str

    # ------------------------------------------------------------------ #
    #  Supabase (relational store — crawl job metadata)
    # ------------------------------------------------------------------ #
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str

    # ------------------------------------------------------------------ #
    #  Groq (LLM for chat)
    # ------------------------------------------------------------------ #
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ------------------------------------------------------------------ #
    #  Embedding model
    #  all-MiniLM-L6-v2 → 384-dim vectors, runs locally, no API cost.
    #  Your Pinecone index MUST be created with dimensions=384.
    # ------------------------------------------------------------------ #
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMS: int = 384

    # ------------------------------------------------------------------ #
    #  Chunking
    # ------------------------------------------------------------------ #
    CHUNK_SIZE: int = 1000      # characters per chunk
    CHUNK_OVERLAP: int = 200    # overlap between consecutive chunks

    # ------------------------------------------------------------------ #
    #  Crawl defaults
    # ------------------------------------------------------------------ #
    DEFAULT_CRAWL_LIMIT: int = 100
    DEFAULT_CRAWL_FORMAT: str = "markdown"

    # ------------------------------------------------------------------ #
    #  FastAPI
    # ------------------------------------------------------------------ #
    APP_TITLE: str = "Chatbot Crawler API"
    APP_DESCRIPTION: str = (
        "Crawls websites, stores embeddings in Pinecone, "
        "and answers questions using Groq + RAG."
    )
    APP_VERSION: str = "2.0.0"

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — .env is read once per process."""
    return Settings()
