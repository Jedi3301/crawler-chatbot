"use client";

/**
 * components/chat/ChatInterface.tsx
 *
 * The full chat panel — right half of the split-screen.
 *
 * Manages:
 *   - Conversation history (array of messages + sources).
 *   - Sending new messages via api.sendChatMessage().
 *   - Auto-scrolling to the latest message.
 *   - Loading and error states.
 */

import { useRef, useState, useEffect } from "react";
import { sendChatMessage } from "@/lib/api";
import type { ChatMessage, SourceChunk } from "@/lib/types";
import MessageBubble from "./MessageBubble";

// A message as stored in local state — extends the backend type
// with an optional sources array for assistant messages.
interface LocalMessage extends ChatMessage {
  sources?: SourceChunk[];
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to the bottom whenever messages update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend() {
    const question = input.trim();
    if (!question || loading) return;

    // Immediately show the user's message
    const userMessage: LocalMessage = { role: "user", content: question };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setError(null);
    setLoading(true);

    try {
      // Build history for the API — only user/assistant turns, no sources
      const history: ChatMessage[] = updatedMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await sendChatMessage({ question, history });

      const assistantMessage: LocalMessage = {
        role: "assistant",
        content: response.answer,
        sources: response.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Send on Enter (without Shift — Shift+Enter adds a newline)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleClear() {
    setMessages([]);
    setError(null);
    inputRef.current?.focus();
  }

  const isEmpty = messages.length === 0;

  return (
    <section
      className="chat"
      id="chat"
      aria-label="Chat with your crawled content"
    >
      {/* Message list */}
      <div className="chat__messages" role="log" aria-live="polite">
        {/* Header (scrolls with messages) */}
        <div className="chat__header">
          <div>
            <p className="chat__eyebrow">Step 2</p>
            <h2 className="chat__title">Ask a Question</h2>
            <p className="chat__subtitle">
              Powered by Groq · llama-3.3-70b-versatile
            </p>
          </div>
          {!isEmpty && (
            <button
              className="chat__clear-btn"
              onClick={handleClear}
              aria-label="Clear conversation"
            >
              Clear
            </button>
          )}
        </div>

        {isEmpty && !loading && (
          <div className="chat__empty">
            <p className="chat__empty-icon" aria-hidden="true">💬</p>
            <p className="chat__empty-title">Start a conversation</p>
            <p className="chat__empty-hint">
              Ingest a website first, then ask anything about its content.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            sources={msg.role === "assistant" ? msg.sources : undefined}
          />
        ))}

        {loading && (
          <div className="chat__thinking" aria-label="AI is thinking">
            <span className="chat__thinking-dot" />
            <span className="chat__thinking-dot" />
            <span className="chat__thinking-dot" />
          </div>
        )}

        {error && (
          <div className="chat__error" role="alert">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={bottomRef} aria-hidden="true" />
      </div>

      {/* Input area */}
      <div className="chat__input-area">
        <textarea
          ref={inputRef}
          id="chat-input"
          className="chat__textarea"
          placeholder="Ask anything about the ingested websites…"
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          aria-label="Chat input"
        />
        <button
          id="chat-send-btn"
          className="btn-primary chat__send-btn"
          onClick={handleSend}
          disabled={loading || !input.trim()}
          aria-label="Send message"
        >
          {loading ? "…" : "Send"}
        </button>
      </div>
    </section>
  );
}
