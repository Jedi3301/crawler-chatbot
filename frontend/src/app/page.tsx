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
import BotList from "@/components/bots/BotList";
import CreateBotModal from "@/components/bots/CreateBotModal";

export default function Home() {
  const [historyTick, setHistoryTick] = useState(0);
  const [isCreatingBot, setIsCreatingBot] = useState(false);

  function triggerBotRefresh() {
    setHistoryTick((t) => t + 1);
  }

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#fafafa" }}>
      <GlobalNav />

      <main style={{ paddingTop: "60px" }}>
        <BotList 
          refreshTrigger={historyTick} 
          onCreateClick={() => setIsCreatingBot(true)}
        />
      </main>

      {isCreatingBot && (
        <CreateBotModal 
          onClose={() => setIsCreatingBot(false)}
          onSuccess={() => {
            setIsCreatingBot(false);
            triggerBotRefresh();
          }}
        />
      )}
    </div>
  );
}
