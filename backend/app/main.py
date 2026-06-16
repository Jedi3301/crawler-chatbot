"""
app/main.py

FastAPI application factory and entry point.

Responsibilities:
  - Create and configure the FastAPI app instance.
  - Mount all versioned API routers.
  - Register global exception handlers.
  - Expose a health-check endpoint.

Everything else (business logic, DB, settings) lives in its own module.
"""

import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import CrawlerBaseError

# --------------------------------------------------------------------------- #
#  Logging setup
# --------------------------------------------------------------------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
#  Lifespan (startup / shutdown hooks)
# --------------------------------------------------------------------------- #

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Code before `yield` runs on startup; code after runs on shutdown.
    Add DB pool init, cache warm-up, etc. here when needed.
    """
    settings = get_settings()
    logger.info("🚀 %s v%s starting up", settings.APP_TITLE, settings.APP_VERSION)
    yield
    logger.info("🛑 %s shutting down", settings.APP_TITLE)


# --------------------------------------------------------------------------- #
#  App factory
# --------------------------------------------------------------------------- #

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ---- CORS ---- #
    # Permissive for local dev. Lock this down in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Global exception handler ---- #
    # Catches any unhandled CrawlerBaseError that slips past the route layer.
    @app.exception_handler(CrawlerBaseError)
    async def crawler_error_handler(request, exc: CrawlerBaseError):
        logger.error("Unhandled crawler error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )

    # ---- Routers ---- #
    app.include_router(api_router)

    return app


# --------------------------------------------------------------------------- #
#  Health check  (mounted at root so load balancers can reach it easily)
# --------------------------------------------------------------------------- #

app = create_app()


@app.get("/health", tags=["Health"], summary="Service health check")
def health_check():
    """Returns 200 OK when the service is running."""
    return {"status": "ok", "service": get_settings().APP_TITLE}
