"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getBot } from "@/lib/api";
import type { Bot } from "@/lib/types";
import GlobalNav from "@/components/layout/GlobalNav";
import UrlIngester from "@/components/crawl/UrlIngester";
import ChatInterface from "@/components/chat/ChatInterface";
import EditBotModal from "@/components/bots/EditBotModal";
import { getBotKnowledge } from "@/lib/api";
import type { CrawlJob } from "@/lib/types";

export default function BotPage() {
  const params = useParams();
  const router = useRouter();
  const botId = params.id as string;

  const [bot, setBot] = useState<Bot | null>(null);
  const [knowledge, setKnowledge] = useState<CrawlJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [botData, knowledgeData] = await Promise.all([
          getBot(botId),
          getBotKnowledge(botId)
        ]);
        setBot(botData);
        setKnowledge(knowledgeData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load bot.");
      } finally {
        setLoading(false);
      }
    }
    if (botId) {
      loadData();
    }
  }, [botId, refreshTick]);

  function handleIngestComplete() {
    setRefreshTick((t) => t + 1);
  }

  function handleEditSuccess() {
    setIsEditing(false);
    setRefreshTick((t) => t + 1);
  }

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", backgroundColor: "#fafafa" }}>
        <GlobalNav />
        <div style={{ padding: "80px 20px", textAlign: "center" }}>Loading bot...</div>
      </div>
    );
  }

  if (error || !bot) {
    return (
      <div style={{ minHeight: "100vh", backgroundColor: "#fafafa" }}>
        <GlobalNav />
        <div style={{ padding: "80px 20px", textAlign: "center", color: "red" }}>
          {error || "Bot not found"}
          <br />
          <Link href="/" style={{ display: 'inline-block', marginTop: '20px', textDecoration: 'underline' }}>Back to Bots</Link>
        </div>
      </div>
    );
  }

  return (
    <>
      <GlobalNav />
      
      <div style={{ position: 'absolute', top: '15px', left: '150px', zIndex: 100 }}>
        <Link href="/" style={{ color: '#fff', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', opacity: 0.8 }}>
          ← Back to Dashboard
        </Link>
      </div>

      <main className="split-screen">
        {/* ── Left: Bot Studio / Knowledge ───────────────────────────────── */}
        <div className="split-screen__left" style={{ overflowY: 'auto' }}>
          <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h1 style={{ margin: '0 0 8px 0', fontSize: '2rem' }}>{bot.name}</h1>
              <p style={{ margin: '0', color: '#666' }}>{bot.description || "Manage what this bot knows."}</p>
            </div>
            <button 
              onClick={() => setIsEditing(true)}
              style={{ padding: '6px 12px', fontSize: '13px', borderRadius: '6px', border: '1px solid #ccc', backgroundColor: '#fff', cursor: 'pointer' }}
            >
              Edit
            </button>
          </div>

          <UrlIngester botId={bot.id} onIngestComplete={handleIngestComplete} />

          <div style={{ marginTop: '32px' }}>
            <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: '#666', letterSpacing: '0.05em', marginBottom: '16px' }}>Knowledge Sources</h3>
            
            {knowledge.length === 0 && (
              <p style={{ fontSize: '14px', color: '#666' }}>No knowledge added yet. Ingest a URL above.</p>
            )}

            {knowledge.length > 0 && (
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {knowledge.map((job) => (
                  <li key={job.id} style={{ 
                    backgroundColor: '#f9f9f9', 
                    border: '1px solid #e5e5e5', 
                    borderRadius: '8px', 
                    padding: '12px 16px',
                    fontSize: '14px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#10b981' }}>✓</span>
                      <a href={job.url} target="_blank" rel="noopener noreferrer" style={{ color: '#000', textDecoration: 'none', fontWeight: 500 }}>
                        {job.url}
                      </a>
                    </div>
                    <span style={{ color: '#a1a1aa', fontSize: '12px', backgroundColor: '#eee', padding: '2px 8px', borderRadius: '12px' }}>
                      {job.total_pages} pages
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* ── Right: Chat ──────────────────────────────────────────── */}
        <div className="split-screen__right">
          <ChatInterface activeBot={bot} />
        </div>
      </main>

      {isEditing && (
        <EditBotModal 
          bot={bot}
          onClose={() => setIsEditing(false)}
          onSuccess={handleEditSuccess}
        />
      )}
    </>
  );
}
