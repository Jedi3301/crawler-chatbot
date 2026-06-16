"use client";

/**
 * components/crawl/UrlIngester.tsx
 *
 * The URL input panel — left half of the split-screen.
 *
 * Responsibilities:
 *   - Accept a URL and optional page limit from the user.
 *   - Call api.ingestWebsite() and show progress / result.
 *   - On success, notify the parent so it can refresh the history list.
 */

import { useState } from "react";
import { API_BASE } from "@/lib/api";
import type { IngestResponse } from "@/lib/types";

interface Props {
  botId: string;
  onIngestComplete: () => void;
}

export default function UrlIngester({ botId, onIngestComplete }: Props) {
  const [url, setUrl] = useState("");
  const [limit, setLimit] = useState(20);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState("");
  const [progress, setProgress] = useState(0);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setStatusMsg("Starting...");
    setProgress(0);

    try {
      const res = await fetch(`${API_BASE}/api/v1/ingest/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), limit, bot_id: botId })
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder("utf-8");

      if (!reader) {
        throw new Error("Response body is not readable.");
      }

      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Process line by line
        const lines = buffer.split('\n');
        buffer = lines.pop() || ""; // Keep the last incomplete line in the buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.replace("data: ", "");
            try {
              const data = JSON.parse(dataStr);
              if (data.error) {
                throw new Error(data.status);
              }
              setStatusMsg(data.status);
              setProgress(data.progress);
              
              if (data.done) {
                setResult(data.result);
                onIngestComplete();
              }
            } catch (err) {
              if (err instanceof Error && err.message !== "Unexpected end of JSON input") {
                throw err;
              }
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred.");
    } finally {
      setLoading(false);
      setStatusMsg("");
      setProgress(0);
    }
  }

  return (
    <section className="ingester" id="ingest" aria-labelledby="ingester-title">
      {/* Header */}
      <div className="ingester__header">
        <p className="ingester__eyebrow">Step 1</p>
        <h1 className="ingester__title" id="ingester-title">
          Ingest a Website
        </h1>
        <p className="ingester__subtitle">
          Enter a URL. We'll crawl it, chunk the content, and store it as
          searchable embeddings in Pinecone.
        </p>
      </div>

      {/* Form */}
      <form className="ingester__form" onSubmit={handleSubmit} noValidate>
        <div className="ingester__field">
          <label className="ingester__label" htmlFor="url-input">
            Website URL
          </label>
          <input
            id="url-input"
            type="url"
            className="ingester__input"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            disabled={loading}
          />
        </div>

        <div className="ingester__field">
          <label className="ingester__label" htmlFor="limit-input">
            Max Pages&nbsp;
            <span className="ingester__label-hint">
              (keep low on free plan)
            </span>
          </label>
          <input
            id="limit-input"
            type="number"
            className="ingester__input ingester__input--narrow"
            min={1}
            max={200}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            disabled={loading}
          />
        </div>

        <button
          id="ingest-submit-btn"
          type="submit"
          className="btn-primary"
          disabled={loading || !url.trim()}
        >
          {loading ? "Crawling…" : "Start Ingest"}
        </button>
      </form>

      {/* Loading state with SSE progress */}
      {loading && (
        <div style={{ marginTop: '24px', backgroundColor: '#fff', border: '1px solid #e5e5e5', borderRadius: '8px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px', fontWeight: 500 }}>
            <span>{statusMsg || "Initializing..."}</span>
            <span>{progress}%</span>
          </div>
          <div style={{ width: '100%', backgroundColor: '#eee', borderRadius: '4px', overflow: 'hidden', height: '8px' }}>
            <div style={{ 
              width: `${progress}%`, 
              backgroundColor: '#3b82f6', 
              height: '100%', 
              transition: 'width 0.3s ease-out' 
            }} />
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="ingester__error" role="alert">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Success */}
      {result && !loading && (
        <div className="ingester__result" role="status">
          <div className="ingester__result-check" aria-hidden="true">✓</div>
          <div>
            <p className="ingester__result-title">Ingest complete</p>
            <p className="ingester__result-detail">
              {result.pages_crawled} pages · {result.chunks_stored} chunks stored
            </p>
            <p className="ingester__result-url">{result.url}</p>
          </div>
        </div>
      )}
    </section>
  );
}
