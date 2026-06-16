"""
app/api/v1/routes/crawler.py

HTTP route definitions for the crawler feature.

Rules enforced here:
  - No business logic. Routes only validate input, call a service
    function, and return a response.
  - No direct SDK imports. The service layer owns that.
  - All exceptions from the service layer are caught here and
    converted into meaningful HTTP responses.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.crawler import (
    CrawlRequest,
    CrawlResponse,
    ScrapeRequest,
    ScrapeResponse,
)
from app.services import crawler_service
from app.core.exceptions import (
    CrawlEmptyResultError,
    CrawlJobFailedError,
    FirecrawlClientError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawler", tags=["Crawler"])


# --------------------------------------------------------------------------- #
#  POST /crawl  — crawl a whole website
# --------------------------------------------------------------------------- #

@router.post(
    "/crawl",
    response_model=CrawlResponse,
    status_code=status.HTTP_200_OK,
    summary="Crawl an entire website",
    description=(
        "Kicks off a Firecrawl job that recursively visits all internal links "
        "starting from the given root URL. Returns clean, structured content "
        "for every page — ready to be chunked and turned into embeddings.\n\n"
        "**Tip:** Set `limit` to a small number (e.g. 10) while testing "
        "to avoid burning through your Firecrawl quota."
    ),
)
def crawl_website(body: CrawlRequest) -> CrawlResponse:
    """
    Accepts a root URL and crawl options, delegates to the crawler service,
    and returns structured page content.
    """
    url = str(body.url)

    try:
        return crawler_service.crawl_website(
            url=url,
            limit=body.limit,
            format=body.format,
        )

    except CrawlJobFailedError as exc:
        logger.warning("Crawl job failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Firecrawl job failed with status '{exc.status}' for URL: {exc.url}",
        )

    except CrawlEmptyResultError as exc:
        logger.warning("Crawl returned no pages: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No pages were retrieved from '{exc.url}'. "
                   "The site may be unreachable or blocking crawlers.",
        )

    except FirecrawlClientError as exc:
        logger.error("Firecrawl client error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )


# --------------------------------------------------------------------------- #
#  POST /scrape  — scrape a single page
# --------------------------------------------------------------------------- #

@router.post(
    "/scrape",
    response_model=ScrapeResponse,
    status_code=status.HTTP_200_OK,
    summary="Scrape a single page",
    description=(
        "Scrapes a single URL via Firecrawl and returns its clean content. "
        "Use this when you already know the exact page URL and don't need "
        "recursive link discovery."
    ),
)
def scrape_page(body: ScrapeRequest) -> ScrapeResponse:
    """
    Accepts a single URL and format, delegates to the crawler service,
    and returns the page content.
    """
    url = str(body.url)

    try:
        return crawler_service.scrape_single_page(url=url, format=body.format)

    except CrawlEmptyResultError as exc:
        logger.warning("Scrape returned no content: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No content was retrieved from '{exc.url}'. "
                   "The page may be unreachable or returning an empty response.",
        )

    except FirecrawlClientError as exc:
        logger.error("Firecrawl client error during scrape: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
