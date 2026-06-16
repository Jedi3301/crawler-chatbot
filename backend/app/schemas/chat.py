"""
backend/app/schemas/chat.py

Pydantic models for the /chat endpoints.
"""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    """
    Request body for POST /chat/message.

    Attributes:
        question: The user's question.
        bot_id:   The specific website/bot to query (the crawl_job_id).
        history:  Previous messages in this conversation (for context).
                  Send an empty list for a fresh conversation.
    """
    question: str = Field(..., min_length=1, examples=["What does this website do?"])
    bot_id: str = Field(..., description="The ID of the crawl job to scope the search to.")
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Conversation history — previous user/assistant turns.",
    )


class SourceChunk(BaseModel):
    """
    A retrieved text chunk used as context for the LLM response.
    Returned alongside the answer so the frontend can show sources.
    """
    url: str
    text: str
    score: float = Field(description="Similarity score from Pinecone (0–1).")


class ChatResponse(BaseModel):
    """
    Returned after the LLM generates a response.

    Attributes:
        answer:  The LLM-generated answer.
        sources: The retrieved chunks that informed the answer.
    """
    answer: str
    sources: list[SourceChunk]
