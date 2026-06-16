"""
backend/app/schemas/ingest.py

Pydantic models for the /ingest endpoints.

IngestRequest  → what the client sends
IngestResponse → what the server returns after crawl + embed + store
"""

from pydantic import BaseModel, HttpUrl, Field


class IngestRequest(BaseModel):
    """
    Request body for POST /ingest/ingest.

    Attributes:
        url:    Root URL to crawl recursively.
        bot_id: The ID of the bot this knowledge belongs to.
        limit:  Max pages Firecrawl will visit.
    """
    url: HttpUrl = Field(..., description="The root URL to crawl and ingest.")
    bot_id: str = Field(..., description="The ID of the bot this knowledge belongs to.")
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of pages to crawl.",
    )


class IngestResponse(BaseModel):
    """
    Returned after a successful ingest pipeline run.

    Attributes:
        crawl_job_id: UUID of the crawl job stored in Supabase.
        url:          The root URL that was crawled.
        pages_crawled: How many pages were fetched from the site.
        chunks_stored: How many text chunks were embedded + upserted to Pinecone.
        message:      Human-readable summary.
    """
    crawl_job_id: str
    url: str
    pages_crawled: int
    chunks_stored: int
    message: str
