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
import type { ChatMessage, SourceChunk, Bot } from "@/lib/types";
import MessageBubble from "./MessageBubble";

interface LocalMessage extends ChatMessage {
  sources?: SourceChunk[];
}

interface Props {
  activeBot?: Bot | null;
}

export default function ChatInterface({ activeBot }: Props) {
  // Store chat history separately for each bot using its ID as the key
  const [histories, setHistories] = useState<Record<string, LocalMessage[]>>({});
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const currentMessages = activeBot ? (histories[activeBot.id] || []) : [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentMessages, loading]);

  // Focus input when bot changes
  useEffect(() => {
    if (activeBot && !loading) {
      inputRef.current?.focus();
    }
    setError(null);
  }, [activeBot]);

  async function handleSend() {
    const question = input.trim();
    if (!question || loading || !activeBot) return;

    const userMessage: LocalMessage = { role: "user", content: question };
    const updatedMessages = [...currentMessages, userMessage];
    
    setHistories(prev => ({
      ...prev,
      [activeBot.id]: updatedMessages
    }));
    
    setInput("");
    setError(null);
    setLoading(true);

    try {
      const history: ChatMessage[] = updatedMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await sendChatMessage({ 
        question, 
        bot_id: activeBot.id,
        history 
      });

      const assistantMessage: LocalMessage = {
        role: "assistant",
        content: response.answer,
        sources: response.sources,
      };
      
      setHistories(prev => ({
        ...prev,
        [activeBot.id]: [...(prev[activeBot.id] || []), assistantMessage]
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleClear() {
    if (!activeBot) return;
    setHistories(prev => ({ ...prev, [activeBot.id]: [] }));
    setError(null);
    inputRef.current?.focus();
  }

  if (!activeBot) {
    return (
      <section className="chat chat--unselected">
        <div className="chat__empty" style={{ margin: "auto", textAlign: "center" }}>
          <p className="chat__empty-icon" aria-hidden="true" style={{ fontSize: "3rem" }}>🤖</p>
          <p className="chat__empty-title" style={{ fontSize: "1.5rem", marginTop: "1rem" }}>Select a Bot</p>
          <p className="chat__empty-hint" style={{ color: "#a1a1aa", marginTop: "0.5rem" }}>
            Click "Chat" on any ingested website in the left panel to start a conversation.
          </p>
        </div>
      </section>
    );
  }

  const isEmpty = currentMessages.length === 0;

  return (
    <section
      className="chat"
      id="chat"
      aria-label={`Chat with ${activeBot.name}`}
    >
      <div className="chat__messages" role="log" aria-live="polite">
        <div className="chat__header">
          <div>
            <p className="chat__eyebrow">Chatting with bot:</p>
            <h2 className="chat__title" style={{ fontSize: "1.2rem", wordBreak: "break-all" }}>{activeBot.name}</h2>
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
            <p className="chat__empty-title">Say hello!</p>
            <p className="chat__empty-hint">
              Ask any question about the content {activeBot.name} knows.
            </p>
          </div>
        )}

        {currentMessages.map((msg, i) => (
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

        <div ref={bottomRef} aria-hidden="true" />
      </div>

      <div className="chat__input-area">
        <textarea
          ref={inputRef}
          id="chat-input"
          className="chat__textarea"
          placeholder={`Ask about ${activeBot.name}…`}
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
