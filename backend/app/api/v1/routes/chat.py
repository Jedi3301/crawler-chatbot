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
    summary="Ask a question about crawled websites",
    description=(
        "Answers a question using RAG (Retrieval-Augmented Generation):\n"
        "1. Embeds the question.\n"
        "2. Retrieves the most relevant chunks from Pinecone.\n"
        "3. Passes them as context to Groq's `llama-3.3-70b-versatile`.\n"
        "4. Returns the answer + source URLs.\n\n"
        "Make sure to run `/ingest/ingest` on a website first."
    ),
)
def send_message(body: ChatRequest) -> ChatResponse:
    """Runs the RAG pipeline and returns an LLM-generated answer."""
    try:
        return chat_service.answer_question(
            question=body.question,
            history=body.history,
        )
    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
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
