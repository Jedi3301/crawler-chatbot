"""
backend/app/services/chat_service.py

All Groq LLM interactions live here.

Flow for each chat request:
  1. Embed the user's question (embedding_service).
  2. Query Pinecone for the top-k most relevant chunks (vector_service).
  3. Build a system prompt that includes those chunks as context.
  4. Call the Groq API with the full conversation history.
  5. Return the answer + the sources used.

This service imports embedding_service and vector_service directly —
routes never need to know these steps exist.
"""

import logging
from groq import Groq

from app.core.config import get_settings
from app.core.exceptions import ChatError, EmbeddingError, VectorStoreError
from app.schemas.chat import ChatMessage, ChatResponse, SourceChunk
from app.services import embedding_service, vector_service

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
#  System prompt template
# --------------------------------------------------------------------------- #

_SYSTEM_PROMPT_TEMPLATE = """\
You are an official representative of the company whose website content is provided below.
Speak confidently in the first person ("we", "our", "us") as if you are part of the organization.

Rules:
- Answer strictly using the context below.
- Speak directly on behalf of the company. Do not say "Based on the provided context" or "According to the website". Just state the facts as the company.
- If a user asks a broad question or something that does not relate to the company's context, you MUST reply with: "Sorry, I can't answer that, but I can answer questions about our company."
- Be concise, helpful, and factual.

Context:
{context}
"""


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

def _build_context_string(chunks: list[dict]) -> str:
    """
    Formats retrieved Pinecone chunks into a readable context block
    that fits inside the system prompt.
    """
    if not chunks:
        return "No relevant content found."

    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[Source {i}] URL: {chunk['url']}\n{chunk['text']}")

    return "\n\n---\n\n".join(parts)


def _build_groq_messages(
    system_prompt: str,
    history: list[ChatMessage],
    question: str,
) -> list[dict]:
    """
    Assembles the full message list expected by the Groq chat API.

    Structure:
      [system message] + [conversation history] + [current user question]
    """
    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": question})
    return messages


# --------------------------------------------------------------------------- #
#  Public service function
# --------------------------------------------------------------------------- #

def answer_question(
    question: str,
    bot_id: str,
    history: list[ChatMessage],
) -> ChatResponse:
    """
    Runs the full RAG pipeline and returns an LLM-generated answer.

    Steps:
      1. Embed the question into a 384-dim vector.
      2. Retrieve the top-5 most similar chunks from Pinecone.
      3. Build a context-aware system prompt.
      4. Call Groq with the full conversation history.
      5. Return the answer and the source chunks.

    Args:
        question: The user's natural language question.
        bot_id:   The ID of the bot/website context to query against.
        history:  Previous conversation turns (user + assistant messages).

    Returns:
        ChatResponse with the LLM's answer and the sources used.

    Raises:
        EmbeddingError:   If embedding the question fails.
        VectorStoreError: If the Pinecone query fails.
        ChatError:        If the Groq API call fails.
    """
    settings = get_settings()
    logger.info("Processing chat question for bot_id %s: %.80s", bot_id, question)

    # Step 1: Embed the question
    try:
        query_vector = embedding_service.embed_single(question)
    except EmbeddingError:
        raise  # already a typed exception — let it propagate

    # Step 2: Retrieve relevant chunks
    try:
        raw_chunks = vector_service.query_similar_chunks(query_vector, top_k=5, namespace=bot_id)
    except VectorStoreError:
        raise

    # Step 3: Build system prompt with retrieved context
    context_str = _build_context_string(raw_chunks)
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(context=context_str)

    # Step 4: Call Groq
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        messages = _build_groq_messages(system_prompt, history, question)

        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.2,   # low temperature → factual, grounded answers
            max_tokens=1024,
        )
        answer = completion.choices[0].message.content or ""
        logger.info("Groq response received | tokens=%s", completion.usage)
    except Exception as exc:
        logger.exception("Groq API call failed")
        raise ChatError(str(exc)) from exc

    # Step 5: Build response with source attribution
    sources = [
        SourceChunk(url=c["url"], text=c["text"][:300], score=c["score"])
        for c in raw_chunks
        if c["text"]
    ]

    return ChatResponse(answer=answer, sources=sources)
