"use client";

/**
 * components/chat/MessageBubble.tsx
 *
 * Renders a single chat message — user or assistant.
 * Assistant messages also show their source chunks.
 */

import type { ChatMessage, SourceChunk } from "@/lib/types";

interface Props {
  message: ChatMessage;
  sources?: SourceChunk[]; // only populated for assistant messages
}

export default function MessageBubble({ message, sources }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`bubble ${isUser ? "bubble--user" : "bubble--assistant"}`}>
      {/* Role label */}
      <span className="bubble__role" aria-label={isUser ? "You" : "Assistant"}>
        {isUser ? "You" : "AI"}
      </span>

      {/* Message text */}
      <div className="bubble__content">
        <p className="bubble__text">{message.content}</p>

        {/* Source attribution — only for assistant messages */}
        {!isUser && sources && sources.length > 0 && (
          <details className="bubble__sources">
            <summary className="bubble__sources-toggle">
              {sources.length} source{sources.length > 1 ? "s" : ""} used
            </summary>
            <ul className="bubble__sources-list" role="list">
              {sources.map((src, i) => (
                <li key={i} className="bubble__source-item">
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bubble__source-url"
                    title={src.url}
                  >
                    {src.url}
                  </a>
                  <span className="bubble__source-score">
                    {(src.score * 100).toFixed(0)}% match
                  </span>
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}
