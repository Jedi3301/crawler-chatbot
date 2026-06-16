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
import { ingestWebsite } from "@/lib/api";
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

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await ingestWebsite({ url: url.trim(), limit, bot_id: botId });
      setResult(res);
      onIngestComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred.");
    } finally {
      setLoading(false);
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

      {/* Loading state */}
      {loading && (
        <div className="ingester__status" role="status" aria-live="polite">
          <span className="ingester__spinner" aria-hidden="true" />
          Crawling and embedding — this may take a minute…
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
