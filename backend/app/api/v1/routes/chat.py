"""
backend/app/api/v1/routes/chat.py

HTTP route for the RAG chatbot.

This file only:
  1. Validates the incoming request.
  2. Calls chat_service.answer_question().
  3. Maps service exceptions → HTTP status codes.

All RAG logic (embed → retrieve → LLM) lives in chat_service.py.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service
from app.core.exceptions import ChatError, EmbeddingError, VectorStoreError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question about the crawled websites",
)
def send_message(body: ChatRequest) -> ChatResponse:
    """Runs the RAG pipeline and returns an LLM-generated answer."""
    try:
        return chat_service.answer_question(
            question=body.question,
            bot_id=body.bot_id,
            history=body.history,
        )
    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to embed question: {exc}",
        )
    except VectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except ChatError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
