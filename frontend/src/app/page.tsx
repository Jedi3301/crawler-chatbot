"use client";

/**
 * app/page.tsx
 *
 * The root page — a split-screen layout:
 *   Left panel  (light parchment tile) → URL ingestion + crawl history
 *   Right panel (near-black tile)      → Chat interface
 *
 * Design system: Apple-inspired (see globals.css for all tokens).
 */

import { useState } from "react";
import GlobalNav from "@/components/layout/GlobalNav";
import UrlIngester from "@/components/crawl/UrlIngester";
import CrawlHistory from "@/components/crawl/CrawlHistory";
import ChatInterface from "@/components/chat/ChatInterface";

export default function Home() {
  // Incrementing this number triggers a re-fetch in CrawlHistory
  const [historyTick, setHistoryTick] = useState(0);

  function onIngestComplete() {
    setHistoryTick((t) => t + 1);
  }

  return (
    <>
      <GlobalNav />

      <main className="split-screen">
        {/* ── Left: ingest + history ───────────────────────────────── */}
        <div className="split-screen__left">
          <UrlIngester onIngestComplete={onIngestComplete} />
          <div className="split-screen__divider" aria-hidden="true" />
          <CrawlHistory refreshTrigger={historyTick} />
        </div>

        {/* ── Right: chat ──────────────────────────────────────────── */}
        <div className="split-screen__right">
          <ChatInterface />
        </div>
      </main>
    </>
  );
}
