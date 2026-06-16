"use client";

/**
 * components/crawl/CrawlHistory.tsx
 *
 * Displays the list of previously crawled websites fetched from Supabase.
 * Shown below the UrlIngester in the left panel.
 */

import { useEffect, useState } from "react";
import { getCrawlHistory } from "@/lib/api";
import type { CrawlJob } from "@/lib/types";

interface Props {
  refreshTrigger: number; // increment this to force a re-fetch
}

export default function CrawlHistory({ refreshTrigger }: Props) {
  const [jobs, setJobs] = useState<CrawlJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      setLoading(true);
      setError(null);
      try {
        const data = await getCrawlHistory();
        setJobs(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load history.");
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [refreshTrigger]);

  if (loading) {
    return <p className="history__loading">Loading history…</p>;
  }

  if (error) {
    return <p className="history__error">Could not load history: {error}</p>;
  }

  if (jobs.length === 0) {
    return (
      <div className="history__empty">
        <p>No sites ingested yet.</p>
        <p>Use the form above to crawl your first website.</p>
      </div>
    );
  }

  return (
    <div className="history" aria-label="Crawl history">
      <h2 className="history__title">Ingested Sites</h2>
      <ul className="history__list" role="list">
        {jobs.map((job) => (
          <li key={job.id} className="history__item">
            <div className="history__item-meta">
              <span className="history__item-status history__item-status--completed">
                ✓
              </span>
              <span className="history__item-pages">{job.total_pages} pages</span>
            </div>
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="history__item-url"
              title={job.url}
            >
              {job.url}
            </a>
            <time className="history__item-date" dateTime={job.created_at}>
              {new Date(job.created_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
            </time>
          </li>
        ))}
      </ul>
    </div>
  );
}
