"""
app/services/crawler_service.py

All Firecrawl business logic lives here.

The service layer is responsible for:
  - Initialising the Firecrawl client.
  - Calling the SDK and handling its responses.
  - Translating SDK output into our own schema types.
  - Raising domain-specific exceptions so routes don't
    need to know anything about Firecrawl internals.

Routes import functions from here; they never touch the SDK directly.

SDK facts (firecrawl v4.x / V1FirecrawlApp):
  - Client class  : V1FirecrawlApp
  - Crawl method  : crawl_url(url, limit=N, scrape_options=V1ScrapeOptions(...), max_concurrency=1)
  - Scrape method : scrape_url(url, formats=[...])
  - Crawl response: V1CrawlStatusResponse  →  .data = List[V1FirecrawlDocument]
  - Scrape response: V1ScrapeResponse       (content fields live directly on this object)
  - Document fields: .url, .markdown, .html, .rawHtml, .metadata, .title, .description
"""

import logging
from firecrawl import V1FirecrawlApp
from firecrawl.v1.client import V1ScrapeOptions

from app.core.config import get_settings
from app.core.exceptions import (
    CrawlEmptyResultError,
    CrawlJobFailedError,
    FirecrawlClientError,
)
from app.schemas.crawler import CrawlResponse, PageResult, ScrapeResponse

logger = logging.getLogger(__name__)

# ── Free-plan safe: only 1 browser at a time ─────────────────────────────── #
_MAX_CONCURRENCY = 1


# --------------------------------------------------------------------------- #
#  Client factory
# --------------------------------------------------------------------------- #

def _get_firecrawl_client() -> V1FirecrawlApp:
    """
    Creates a V1FirecrawlApp client using the API key from settings.

    Kept private so tests can patch it without touching business logic.
    """
    settings = get_settings()
    return V1FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)


# --------------------------------------------------------------------------- #
#  Internal helpers
# --------------------------------------------------------------------------- #

def _extract_content(document, fmt: str) -> str:
    """
    Reads the content field that matches the requested format from a
    V1FirecrawlDocument (or a V1ScrapeResponse, which has the same shape).

    V1FirecrawlDocument exposes content as typed attributes:
      "markdown"  → .markdown
      "html"      → .html
      "rawHtml"   → .rawHtml

    Returns an empty string if the attribute is absent or None.
    """
    return getattr(document, fmt, None) or ""


def _extract_metadata(document) -> dict:
    """
    Returns a plain dict of page metadata from a V1FirecrawlDocument.

    The .metadata field can be a dict, a Pydantic model, or None.
    We normalise it to a plain dict so our schemas stay simple.
    """
    meta = getattr(document, "metadata", None)
    if meta is None:
        return {}
    if isinstance(meta, dict):
        return meta
    # Pydantic model → dict
    if hasattr(meta, "model_dump"):
        return meta.model_dump()
    # Fallback
    return vars(meta) if hasattr(meta, "__dict__") else {}


def _document_to_page_result(document, fmt: str) -> PageResult:
    """
    Converts a single V1FirecrawlDocument into a PageResult schema object.
    """
    content = _extract_content(document, fmt)
    metadata = _extract_metadata(document)

    # .url lives directly on the document in the v4 SDK
    url = getattr(document, "url", None) or metadata.get("sourceURL", "")

    return PageResult(url=url, content=content, metadata=metadata)


def _filter_and_build_pages(raw_docs: list, fmt: str) -> list[PageResult]:
    """
    Converts all V1FirecrawlDocuments to PageResults, skipping empty pages.

    Empty pages (no content after stripping whitespace) are usually
    error pages, redirects, or pages that blocked the crawler.
    """
    results: list[PageResult] = []

    for doc in raw_docs:
        page = _document_to_page_result(doc, fmt)

        if not page.content.strip():
            logger.debug("Skipping page with no content: %s", page.url)
            continue

        results.append(page)

    return results


# --------------------------------------------------------------------------- #
#  Public service functions  (imported by routes)
# --------------------------------------------------------------------------- #

def crawl_website(url: str, limit: int, format: str) -> CrawlResponse:
    """
    Crawls an entire website starting from `url` and returns structured,
    chunking-ready page content for every page discovered.

    Firecrawl recursively follows internal links up to `limit` pages,
    rendering JavaScript if needed and stripping nav/footer noise.

    max_concurrency is locked to 1 to stay within the free plan's
    single-browser constraint.

    Args:
        url:    Root URL to start the crawl from.
        limit:  Maximum number of pages to visit.
        format: Content format ("markdown" | "html" | "rawHtml").

    Returns:
        CrawlResponse with one PageResult per successfully crawled page.

    Raises:
        CrawlJobFailedError:   Firecrawl reported a non-successful status.
        CrawlEmptyResultError: Crawl succeeded but returned zero pages.
        FirecrawlClientError:  Unexpected SDK / network error.
    """
    client = _get_firecrawl_client()
    logger.info(
        "Starting crawl | url=%s | limit=%d | format=%s | concurrency=%d",
        url, limit, format, _MAX_CONCURRENCY,
    )

    try:
        result = client.crawl_url(
            url,
            limit=limit,
            scrape_options=V1ScrapeOptions(formats=[format]),
            max_concurrency=_MAX_CONCURRENCY,
        )
    except Exception as exc:
        logger.exception("Firecrawl SDK raised an unexpected error during crawl")
        raise FirecrawlClientError(str(exc)) from exc

    # V1CrawlStatusResponse.status: 'scraping' | 'completed' | 'failed' | 'cancelled'
    status = getattr(result, "status", None)
    if status and status not in ("completed", "scraping"):
        raise CrawlJobFailedError(url=url, status=status)

    raw_docs: list = getattr(result, "data", None) or []
    if not raw_docs:
        raise CrawlEmptyResultError(url=url)

    pages = _filter_and_build_pages(raw_docs, format)
    logger.info("Crawl complete | pages_retrieved=%d", len(pages))

    return CrawlResponse(
        root_url=url,
        total_pages=len(pages),
        pages=pages,
    )


def scrape_single_page(url: str, format: str) -> ScrapeResponse:
    """
    Scrapes a single URL and returns its content.

    Use this when you already have the exact page URL and don't need
    Firecrawl to discover sub-pages via link crawling.

    Args:
        url:    The exact page to scrape.
        format: Content format ("markdown" | "html" | "rawHtml").

    Returns:
        ScrapeResponse containing a single PageResult.

    Raises:
        CrawlEmptyResultError: Firecrawl returned no content for the URL.
        FirecrawlClientError:  Unexpected SDK / network error.
    """
    client = _get_firecrawl_client()
    logger.info("Scraping single page | url=%s | format=%s", url, format)

    try:
        # scrape_url returns a V1ScrapeResponse which shares the same
        # content attributes as V1FirecrawlDocument
        result = client.scrape_url(url, formats=[format])
    except Exception as exc:
        logger.exception("Firecrawl SDK raised an unexpected error during scrape")
        raise FirecrawlClientError(str(exc)) from exc

    content = _extract_content(result, format)
    if not content.strip():
        raise CrawlEmptyResultError(url=url)

    metadata = _extract_metadata(result)
    page_result = PageResult(url=url, content=content, metadata=metadata)

    logger.info("Scrape complete | url=%s", url)
    return ScrapeResponse(page=page_result)
