"""
backend/app/api/v1/router.py

Aggregates all v1 route modules into a single APIRouter.

To add a new feature:
  1. Create a module under app/api/v1/routes/
  2. Import its router here and call include_router().
"""

from fastapi import APIRouter

from app.api.v1.routes import crawler, ingest, chat

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(crawler.router)
api_router.include_router(ingest.router)
api_router.include_router(chat.router)
