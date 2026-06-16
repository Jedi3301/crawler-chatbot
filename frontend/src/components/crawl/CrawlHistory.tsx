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
  activeBotId?: string;
  onSelectBot?: (bot: CrawlJob) => void;
}

export default function CrawlHistory({ refreshTrigger, activeBotId, onSelectBot }: Props) {
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
        {jobs.map((job) => {
          const isActive = job.id === activeBotId;
          return (
            <li key={job.id} className={`history__item ${isActive ? 'history__item--active' : ''}`} style={isActive ? { borderLeft: "3px solid #000", paddingLeft: "13px" } : {}}>
              <div className="history__item-meta" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <span className="history__item-status history__item-status--completed">
                    ✓
                  </span>
                  <span className="history__item-pages">{job.total_pages} pages</span>
                </div>
                {onSelectBot && (
                  <button 
                    onClick={() => onSelectBot(job)}
                    style={{
                      padding: "4px 8px",
                      fontSize: "12px",
                      borderRadius: "12px",
                      backgroundColor: isActive ? "#000" : "#e5e5e5",
                      color: isActive ? "#fff" : "#000",
                      border: "none",
                      cursor: "pointer"
                    }}
                  >
                    {isActive ? "Chatting..." : "Chat"}
                  </button>
                )}
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
          );
        })}
      </ul>
    </div>
  );
}
