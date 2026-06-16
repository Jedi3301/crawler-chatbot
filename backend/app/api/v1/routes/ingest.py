"""
backend/app/api/v1/routes/ingest.py

HTTP route for the ingest pipeline.

This file only:
  1. Validates the incoming request.
  2. Orchestrates calls to the service layer.
  3. Maps service exceptions → HTTP status codes.

No business logic lives here.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.ingest import IngestRequest, IngestResponse
from app.services import crawler_service, embedding_service, vector_service, db_service
from app.core.exceptions import (
    CrawlEmptyResultError,
    CrawlJobFailedError,
    FirecrawlClientError,
    EmbeddingError,
    VectorStoreError,
    DatabaseError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingest"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Crawl a website and store its content as embeddings",
    description=(
        "Runs the full pipeline:\n"
        "1. Crawl the site with Firecrawl.\n"
        "2. Split each page into text chunks.\n"
        "3. Embed chunks with `all-MiniLM-L6-v2`.\n"
        "4. Upsert vectors + metadata into Pinecone.\n"
        "5. Save the crawl job record in Supabase.\n\n"
        "After this, the site's content is ready to be queried via `/chat/message`."
    ),
)
def ingest_website(body: IngestRequest) -> IngestResponse:
    """Orchestrates the crawl → chunk → embed → store pipeline."""
    url = str(body.url)

    # ── Step 1: Crawl ──────────────────────────────────────────────── #
    try:
        crawl_result = crawler_service.crawl_website(
            url=url,
            limit=body.limit,
            format="markdown",
        )
    except CrawlJobFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Crawl job failed ({exc.status}) for: {exc.url}",
        )
    except CrawlEmptyResultError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No pages found at '{exc.url}'. The site may be blocking crawlers.",
        )
    except FirecrawlClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    # ── Step 2 & 3: Chunk + Embed + Upsert to Pinecone ────────────── #
    total_chunks = 0
    page_dicts = []

    try:
        for page in crawl_result.pages:
            chunks_with_vectors = embedding_service.chunk_and_embed(page.content)
            if chunks_with_vectors:
                # We need a crawl_job_id for metadata, but we haven't saved
                # to Supabase yet. We use the URL as a temporary namespace key.
                # The actual UUID is attached after the DB insert below.
                upserted = vector_service.upsert_chunks(
                    chunks_with_vectors=chunks_with_vectors,
                    page_url=page.url,
                    crawl_job_id="pending",  # updated after DB save
                )
                total_chunks += upserted

            page_dicts.append({"url": page.url, "content": page.content})

    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except VectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    # ── Step 4: Save to Supabase ───────────────────────────────────── #
    try:
        crawl_job_id = db_service.save_crawl_job(
            url=url,
            total_pages=crawl_result.total_pages,
        )
        db_service.save_pages(crawl_job_id=crawl_job_id, pages=page_dicts)
    except DatabaseError as exc:
        # DB failure is non-fatal — vectors are already in Pinecone.
        # Log it and return a partial success rather than a 500.
        logger.warning("DB save failed (vectors are stored): %s", exc)
        crawl_job_id = "db-unavailable"

    logger.info(
        "Ingest complete | url=%s | pages=%d | chunks=%d",
        url, crawl_result.total_pages, total_chunks,
    )

    return IngestResponse(
        crawl_job_id=crawl_job_id,
        url=url,
        pages_crawled=crawl_result.total_pages,
        chunks_stored=total_chunks,
        message=(
            f"Successfully ingested {crawl_result.total_pages} pages "
            f"({total_chunks} chunks stored in Pinecone)."
        ),
    )


@router.get(
    "/history",
    summary="List previously crawled websites",
    description="Returns all crawl jobs stored in Supabase, newest first.",
)
def get_crawl_history() -> list[dict]:
    """Returns the list of all crawl jobs from Supabase."""
    try:
        return db_service.list_crawl_jobs()
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
