"""
backend/app/services/embedding_service.py

Handles text chunking and vector embedding.

Model: all-MiniLM-L6-v2  (sentence-transformers)
  - Runs locally — no API key or network call needed.
  - Produces 384-dimensional float32 vectors.
  - Your Pinecone index MUST be created with dimensions=384.

Why sentence-transformers?
  - Free, open-source, runs in the same Python process.
  - all-MiniLM-L6-v2 is fast (< 100ms per batch), small (80 MB), and
    performs well on semantic search benchmarks.
  - Compatible with Groq's llama-3.x context window — both are trained
    on similar English corpora, so the semantic space aligns well.
"""

import logging
from functools import lru_cache
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
#  Model loading (singleton — loaded once, reused across requests)
# --------------------------------------------------------------------------- #

@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """
    Loads the embedding model once and caches it for the process lifetime.

    The first call downloads the model (~80 MB) if not already cached
    locally. Subsequent calls are instant.
    """
    model_name = get_settings().EMBEDDING_MODEL
    logger.info("Loading embedding model: %s", model_name)
    return SentenceTransformer(model_name)


# --------------------------------------------------------------------------- #
#  Chunking
# --------------------------------------------------------------------------- #

def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Splits a long text into overlapping fixed-size character chunks.

    Why overlap?
      A sentence that spans a chunk boundary would be cut in half if there
      were no overlap. The overlap duplicates a small tail from the previous
      chunk into the next one, preserving cross-boundary context.

    Args:
        text:       The full page content (markdown or plain text).
        chunk_size: Maximum characters per chunk.
        overlap:    How many characters from the end of one chunk are
                    repeated at the start of the next.

    Returns:
        A list of non-empty text chunks.
    """
    if not text.strip():
        return []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        # Move forward by (chunk_size - overlap) so the next chunk
        # begins "overlap" characters before the end of this one.
        start += chunk_size - overlap

    return chunks


# --------------------------------------------------------------------------- #
#  Embedding
# --------------------------------------------------------------------------- #

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Converts a list of text strings into embedding vectors.

    Args:
        texts: Non-empty list of strings to embed.

    Returns:
        A list of 384-dimensional float vectors, one per input text.

    Raises:
        EmbeddingError: If the model fails to encode the texts.
    """
    if not texts:
        return []

    try:
        model = _get_model()
        # encode() returns a numpy array → convert to plain Python lists
        # so they're JSON-serializable and Pinecone-compatible.
        vectors = model.encode(texts, show_progress_bar=False)
        return [v.tolist() for v in vectors]

    except Exception as exc:
        logger.exception("Embedding model failed")
        raise EmbeddingError(str(exc)) from exc


def embed_single(text: str) -> list[float]:
    """
    Convenience wrapper — embeds a single string.
    Used when embedding a user's chat question before a Pinecone query.
    """
    results = embed_texts([text])
    return results[0]


# --------------------------------------------------------------------------- #
#  Combined helper used by the ingest pipeline
# --------------------------------------------------------------------------- #

def chunk_and_embed(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[tuple[str, list[float]]]:
    """
    Splits text into chunks and embeds them in one call.

    Returns:
        A list of (chunk_text, embedding_vector) tuples.
        Empty if the input text is blank.
    """
    settings = get_settings()
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    chunks = chunk_text(text, chunk_size, overlap)
    if not chunks:
        return []

    vectors = embed_texts(chunks)
    return list(zip(chunks, vectors))
