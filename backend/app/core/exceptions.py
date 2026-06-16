"""
backend/app/core/exceptions.py

All custom exception types for the application.

Using a typed hierarchy means:
  - Service functions raise meaningful domain errors.
  - Route handlers catch the right type and return the right HTTP code.
  - Generic errors never leak SDK internals to the client.
"""


# ── Base ──────────────────────────────────────────────────────────────── #

class AppBaseError(Exception):
    """Root exception for all application-specific errors."""


# ── Crawler ───────────────────────────────────────────────────────────── #

class CrawlerBaseError(AppBaseError):
    """Root exception for crawler errors."""


class CrawlJobFailedError(CrawlerBaseError):
    """Firecrawl job ended with a failure status."""
    def __init__(self, url: str, status: str) -> None:
        self.url = url
        self.status = status
        super().__init__(f"Crawl job for '{url}' ended with status: '{status}'")


class CrawlEmptyResultError(CrawlerBaseError):
    """Firecrawl returned no pages for the given URL."""
    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__(f"No pages retrieved from '{url}'")


class FirecrawlClientError(CrawlerBaseError):
    """Wraps unexpected errors from the Firecrawl SDK."""
    def __init__(self, message: str) -> None:
        super().__init__(f"Firecrawl client error: {message}")


# ── Embedding ─────────────────────────────────────────────────────────── #

class EmbeddingError(AppBaseError):
    """Raised when the sentence-transformers model fails to encode text."""
    def __init__(self, message: str) -> None:
        super().__init__(f"Embedding error: {message}")


# ── Vector store (Pinecone) ───────────────────────────────────────────── #

class VectorStoreError(AppBaseError):
    """Raised when a Pinecone operation (upsert or query) fails."""
    def __init__(self, message: str) -> None:
        super().__init__(f"Vector store error: {message}")


# ── Database (Supabase) ───────────────────────────────────────────────── #

class DatabaseError(AppBaseError):
    """Raised when a Supabase insert or select operation fails."""
    def __init__(self, message: str) -> None:
        super().__init__(f"Database error: {message}")


# ── Chat / LLM (Groq) ────────────────────────────────────────────────── #

class ChatError(AppBaseError):
    """Raised when the Groq LLM call fails or returns an unexpected response."""
    def __init__(self, message: str) -> None:
        super().__init__(f"Chat error: {message}")
