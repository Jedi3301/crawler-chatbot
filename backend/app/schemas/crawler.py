"""
app/schemas/crawler.py

Pydantic models that define the shape of every request and response
for the crawler endpoints.

Keeping schemas in a dedicated file means:
  - Routes are thin (just wiring).
  - Services deal with plain data, not HTTP concerns.
  - Auto-generated OpenAPI docs are rich and accurate.
"""

from typing import Literal
from pydantic import BaseModel, HttpUrl, Field


# --------------------------------------------------------------------------- #
#  Request models
# --------------------------------------------------------------------------- #

class CrawlRequest(BaseModel):
    """
    Body sent by the client when requesting a full site crawl.

    Attributes:
        url:    The root URL to start crawling from. Firecrawl will
                recursively follow internal links from this page.
        limit:  Maximum number of pages to visit. Protects against
                very large sites blowing through your Firecrawl quota.
        format: The content format to return.
                  - "markdown"  → clean, LLM-ready text  (default)
                  - "html"      → sanitised HTML
                  - "rawHtml"   → raw HTML as served by the server
    """

    url: HttpUrl = Field(..., examples=["https://example.com"])
    limit: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Max pages to crawl (1–500).",
    )
    format: Literal["markdown", "html", "rawHtml"] = Field(
        default="markdown",
        description="Content format for each crawled page.",
    )


class ScrapeRequest(BaseModel):
    """
    Body sent by the client when scraping a single URL.

    Attributes:
        url:    The exact page to scrape.
        format: Content format to return (same options as CrawlRequest).
    """

    url: HttpUrl = Field(..., examples=["https://example.com/about"])
    format: Literal["markdown", "html", "rawHtml"] = Field(
        default="markdown",
        description="Content format for the scraped page.",
    )


# --------------------------------------------------------------------------- #
#  Sub-models used inside response bodies
# --------------------------------------------------------------------------- #

class PageResult(BaseModel):
    """
    Represents a single page returned from Firecrawl.

    Attributes:
        url:      The canonical URL of the page.
        content:  The page content in the requested format.
        metadata: Any extra metadata Firecrawl attaches
                  (title, description, status code, etc.).
    """

    url: str
    content: str
    metadata: dict = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
#  Response models
# --------------------------------------------------------------------------- #

class CrawlResponse(BaseModel):
    """
    Returned after a full site crawl completes.

    Attributes:
        root_url:    The URL that was crawled.
        total_pages: How many pages were successfully retrieved.
        pages:       One PageResult per crawled page, ready for chunking
                     and downstream embedding pipelines.
    """

    root_url: str
    total_pages: int
    pages: list[PageResult]


class ScrapeResponse(BaseModel):
    """
    Returned after scraping a single page.

    Attributes:
        page: The single scraped PageResult.
    """

    page: PageResult
