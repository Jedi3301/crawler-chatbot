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


import json
from fastapi.responses import StreamingResponse

@router.post(
    "/ingest",
    summary="Crawl a website and store its content as embeddings (SSE Stream)",
    description=(
        "Runs the full pipeline, returning real-time progress via Server-Sent Events.\n"
        "Yields JSON objects in the `data: {...}` format with keys: status, progress, error, done, result."
    ),
)
def ingest_website(body: IngestRequest):
    """Orchestrates the crawl → chunk → embed → store pipeline, streaming progress."""
    
    def event_stream():
        url = str(body.url)
        
        def emit(status_msg: str, progress_val: int, is_error: bool = False, is_done: bool = False, result: dict = None):
            data = {
                "status": status_msg,
                "progress": progress_val,
                "error": is_error,
                "done": is_done,
                "result": result
            }
            return f"data: {json.dumps(data)}\n\n"

        yield emit("Starting crawler via Firecrawl...", 5)
        
        # ── Step 1: Crawl ──────────────────────────────────────────────── #
        try:
            crawl_result = crawler_service.crawl_website(
                url=url,
                limit=body.limit,
                format="markdown",
            )
        except CrawlJobFailedError as exc:
            yield emit(f"Crawl job failed ({exc.status}) for: {exc.url}", 100, is_error=True)
            return
        except CrawlEmptyResultError as exc:
            yield emit(f"No pages found at '{exc.url}'. The site may be blocking crawlers.", 100, is_error=True)
            return
        except FirecrawlClientError as exc:
            yield emit(f"Firecrawl Error: {str(exc)}", 100, is_error=True)
            return
        except Exception as exc:
            yield emit(f"Unexpected error during crawl: {str(exc)}", 100, is_error=True)
            return

        total_pages = crawl_result.total_pages
        yield emit(f"Crawl complete. Found {total_pages} pages. Processing...", 30)

        # ── Step 2 & 3: Chunk + Embed + Upsert to Pinecone ────────────── #
        total_chunks = 0
        page_dicts = []
        
        import uuid
        job_id = str(uuid.uuid4())

        try:
            for idx, page in enumerate(crawl_result.pages):
                progress = 30 + int(60 * (idx / max(total_pages, 1)))
                yield emit(f"Processing page {idx + 1} of {total_pages}...", progress)
                
                chunks_with_vectors = embedding_service.chunk_and_embed(page.content)
                if chunks_with_vectors:
                    upserted = vector_service.upsert_chunks(
                        chunks_with_vectors=chunks_with_vectors,
                        page_url=page.url,
                        crawl_job_id=job_id,
                        namespace=body.bot_id,
                    )
                    total_chunks += upserted

                page_dicts.append({"url": page.url, "content": page.content})

        except EmbeddingError as exc:
            yield emit(f"Embedding Error: {str(exc)}", 100, is_error=True)
            return
        except VectorStoreError as exc:
            yield emit(f"Vector Store Error: {str(exc)}", 100, is_error=True)
            return
        except Exception as exc:
            yield emit(f"Unexpected error during processing: {str(exc)}", 100, is_error=True)
            return

        # ── Step 4: Save to Supabase ───────────────────────────────────── #
        yield emit("Saving results to database...", 95)
        try:
            crawl_job_id = db_service.save_crawl_job(
                url=url,
                total_pages=total_pages,
                job_id=job_id,
                bot_id=body.bot_id,
            )
            db_service.save_pages(crawl_job_id=crawl_job_id, pages=page_dicts)
        except DatabaseError as exc:
            logger.warning("DB save failed (vectors are stored): %s", exc)
            crawl_job_id = "db-unavailable"

        yield emit("Complete!", 100, is_done=True, result={
            "crawl_job_id": crawl_job_id,
            "url": url,
            "pages_crawled": total_pages,
            "chunks_stored": total_chunks,
            "message": f"Successfully ingested {total_pages} pages ({total_chunks} chunks)."
        })

    return StreamingResponse(event_stream(), media_type="text/event-stream")
