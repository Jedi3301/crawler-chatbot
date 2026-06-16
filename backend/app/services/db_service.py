"""
backend/app/services/db_service.py

All Supabase (PostgreSQL) operations live here.

We use the supabase-py SDK which wraps the Supabase REST API.
No raw SQL is written here — the SDK's fluent query builder keeps
things readable and avoids SQL injection concerns.

Required Supabase tables (run this SQL in your Supabase dashboard):

    create table crawl_jobs (
      id          uuid primary key default gen_random_uuid(),
      url         text not null,
      status      text not null default 'completed',
      total_pages int  default 0,
      created_at  timestamptz default now()
    );

    create table pages (
      id           uuid primary key default gen_random_uuid(),
      crawl_job_id uuid references crawl_jobs(id) on delete cascade,
      url          text not null,
      content      text,
      created_at   timestamptz default now()
    );
"""

import logging
from functools import lru_cache

from supabase import create_client, Client

from app.core.config import get_settings
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
#  Client singleton
# --------------------------------------------------------------------------- #

@lru_cache(maxsize=1)
def _get_client() -> Client:
    """Returns a cached Supabase client — created once per process."""
    settings = get_settings()
    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        logger.info("Supabase client initialized")
        return client
    except Exception as exc:
        logger.exception("Failed to initialize Supabase client")
        raise DatabaseError(str(exc)) from exc


# --------------------------------------------------------------------------- #
#  Bot operations
# --------------------------------------------------------------------------- #

def create_bot(name: str, description: str | None = None) -> dict:
    """Creates a new bot and returns its record."""
    client = _get_client()
    data = {"name": name, "description": description}
    try:
        response = client.table("bots").insert(data).execute()
        return response.data[0]
    except Exception as exc:
        logger.exception("Failed to create bot")
        raise DatabaseError(str(exc)) from exc

def list_bots() -> list[dict]:
    """Returns all bots ordered by most recent first."""
    client = _get_client()
    try:
        response = (
            client.table("bots")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        logger.exception("Failed to list bots")
        raise DatabaseError(str(exc)) from exc

def get_bot(bot_id: str) -> dict:
    """Returns a specific bot by ID."""
    client = _get_client()
    try:
        response = (
            client.table("bots")
            .select("*")
            .eq("id", bot_id)
            .execute()
        )
        if not response.data:
            raise DatabaseError(f"Bot {bot_id} not found")
        return response.data[0]
    except Exception as exc:
        logger.exception("Failed to get bot")
        raise DatabaseError(str(exc)) from exc


# --------------------------------------------------------------------------- #
#  Crawl job (knowledge) operations
# --------------------------------------------------------------------------- #

def save_crawl_job(url: str, total_pages: int, job_id: str | None = None, bot_id: str | None = None) -> str:
    """
    Inserts a new crawl job record and returns its generated UUID.

    Args:
        url:         The root URL that was crawled.
        total_pages: Number of pages successfully retrieved.
        job_id:      Optional predefined UUID (useful for sync across services).
        bot_id:      The ID of the bot this knowledge belongs to.

    Returns:
        The UUID string of the created row (used to link pages).

    Raises:
        DatabaseError: If the insert fails.
    """
    client = _get_client()
    data = {"url": url, "total_pages": total_pages, "status": "completed"}
    if job_id:
        data["id"] = job_id
    if bot_id:
        data["bot_id"] = bot_id

    try:
        response = (
            client.table("crawl_jobs")
            .insert(data)
            .execute()
        )
        returned_id: str = response.data[0]["id"]
        logger.info("Saved crawl job | id=%s | url=%s", returned_id, url)
        return returned_id
    except Exception as exc:
        logger.exception("Failed to save crawl job")
        raise DatabaseError(str(exc)) from exc


def save_pages(crawl_job_id: str, pages: list[dict]) -> None:
    """
    Batch-inserts page records linked to a crawl job.

    Args:
        crawl_job_id: UUID from save_crawl_job().
        pages:        List of dicts with 'url' and 'content' keys.
                      Content is truncated to 2000 chars to keep
                      the DB row small — full text lives in Pinecone.

    Raises:
        DatabaseError: If the insert fails.
    """
    if not pages:
        return

    client = _get_client()
    rows = [
        {
            "crawl_job_id": crawl_job_id,
            "url": page["url"],
            # Store only a preview in the DB; full text is in Pinecone.
            "content": page["content"][:2000],
        }
        for page in pages
    ]

    try:
        client.table("pages").insert(rows).execute()
        logger.info("Saved %d pages for job %s", len(rows), crawl_job_id)
    except Exception as exc:
        logger.exception("Failed to save pages")
        raise DatabaseError(str(exc)) from exc


# --------------------------------------------------------------------------- #
#  Read operations  (used by the frontend to show history)
# --------------------------------------------------------------------------- #

def list_bot_knowledge(bot_id: str) -> list[dict]:
    """
    Returns all crawl jobs (knowledge sources) for a specific bot.

    Raises:
        DatabaseError: If the query fails.
    """
    client = _get_client()
    try:
        response = (
            client.table("crawl_jobs")
            .select("id, url, status, total_pages, created_at")
            .eq("bot_id", bot_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        logger.exception("Failed to list knowledge for bot")
        raise DatabaseError(str(exc)) from exc
