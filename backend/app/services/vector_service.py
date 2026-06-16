"""
backend/app/services/vector_service.py

All Pinecone operations live here.

Responsibilities:
  - Initialize the Pinecone client and connect to the index.
  - Upsert (insert/update) embedded chunks with their metadata.
  - Query the index with an embedding vector to find similar chunks.

The index is expected to already exist in Pinecone with:
  dimensions = 384  (to match all-MiniLM-L6-v2)
  metric     = cosine

We use Pinecone's serverless index (free tier) — no pod costs.
"""

import logging
import uuid
from functools import lru_cache

from pinecone import Pinecone, Index

from app.core.config import get_settings
from app.core.exceptions import VectorStoreError

logger = logging.getLogger(__name__)

# How many vectors to send in one upsert batch.
# Pinecone recommends 100 at a time to stay within request size limits.
_UPSERT_BATCH_SIZE = 100

# How many nearest-neighbour chunks to retrieve per query.
_DEFAULT_TOP_K = 5


# --------------------------------------------------------------------------- #
#  Client & index singleton
# --------------------------------------------------------------------------- #

@lru_cache(maxsize=1)
def _get_index() -> Index:
    """
    Connects to the Pinecone index once and reuses the connection.

    Raises VectorStoreError if the index cannot be reached.
    """
    settings = get_settings()
    try:
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index = pc.Index(settings.PINECONE_INDEX_NAME)
        logger.info("Connected to Pinecone index: %s", settings.PINECONE_INDEX_NAME)
        return index
    except Exception as exc:
        logger.exception("Failed to connect to Pinecone")
        raise VectorStoreError(str(exc)) from exc


# --------------------------------------------------------------------------- #
#  Upsert
# --------------------------------------------------------------------------- #

def upsert_chunks(
    chunks_with_vectors: list[tuple[str, list[float]]],
    page_url: str,
    crawl_job_id: str,
) -> int:
    """
    Stores embedded text chunks into Pinecone.

    Each chunk becomes one vector in the index. The chunk text and its
    source URL are stored as Pinecone metadata so we can surface them
    as sources in the chat response.

    Args:
        chunks_with_vectors: List of (chunk_text, embedding_vector) tuples
                             from embedding_service.chunk_and_embed().
        page_url:            The URL the chunk was extracted from.
        crawl_job_id:        Links this chunk back to its Supabase crawl job.

    Returns:
        Number of vectors upserted.

    Raises:
        VectorStoreError: On any Pinecone failure.
    """
    if not chunks_with_vectors:
        return 0

    index = _get_index()

    # Build Pinecone vector dicts
    vectors = [
        {
            "id": str(uuid.uuid4()),   # unique ID per chunk
            "values": vector,
            "metadata": {
                "text": chunk_text,       # the raw text (returned in query results)
                "url": page_url,          # source page URL
                "crawl_job_id": crawl_job_id,
            },
        }
        for chunk_text, vector in chunks_with_vectors
    ]

    # Upsert in batches to stay within Pinecone's request size limits
    total_upserted = 0
    try:
        for i in range(0, len(vectors), _UPSERT_BATCH_SIZE):
            batch = vectors[i : i + _UPSERT_BATCH_SIZE]
            index.upsert(vectors=batch)
            total_upserted += len(batch)
            logger.debug("Upserted batch of %d vectors", len(batch))
    except Exception as exc:
        logger.exception("Pinecone upsert failed")
        raise VectorStoreError(str(exc)) from exc

    logger.info(
        "Upserted %d vectors for page: %s", total_upserted, page_url
    )
    return total_upserted


# --------------------------------------------------------------------------- #
#  Query
# --------------------------------------------------------------------------- #

def query_similar_chunks(
    query_vector: list[float],
    top_k: int = _DEFAULT_TOP_K,
) -> list[dict]:
    """
    Finds the most semantically similar chunks to the query vector.

    Used during chat: the user's question is embedded and the top-k
    closest chunks are retrieved to form the LLM's context window.

    Args:
        query_vector: Embedding of the user's question (384 floats).
        top_k:        Number of chunks to return.

    Returns:
        List of dicts, each with keys: 'text', 'url', 'score'.

    Raises:
        VectorStoreError: On any Pinecone failure.
    """
    index = _get_index()

    try:
        response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
        )
    except Exception as exc:
        logger.exception("Pinecone query failed")
        raise VectorStoreError(str(exc)) from exc

    results = []
    for match in response.matches:
        meta = match.metadata or {}
        results.append({
            "text": meta.get("text", ""),
            "url": meta.get("url", ""),
            "score": match.score,
        })

    logger.info("Retrieved %d similar chunks from Pinecone", len(results))
    return results
