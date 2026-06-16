"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getBots } from "@/lib/api";
import type { Bot } from "@/lib/types";
import CreateBotModal from "./CreateBotModal";

interface Props {
  refreshTrigger: number;
  onCreateClick: () => void;
}

export default function BotList({ refreshTrigger, onCreateClick }: Props) {
  const [bots, setBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchBots() {
      setLoading(true);
      setError(null);
      try {
        const data = await getBots();
        setBots(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load bots.");
      } finally {
        setLoading(false);
      }
    }
    fetchBots();
  }, [refreshTrigger]);

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ margin: 0, fontSize: '2rem' }}>Your Bots</h1>
        <button 
          className="btn-primary" 
          style={{ padding: '10px 20px', fontSize: '16px', borderRadius: '8px' }}
          onClick={onCreateClick}
        >
          + New Bot
        </button>
      </div>

      {loading && <p>Loading bots…</p>}
      {error && <p style={{ color: 'red' }}>Could not load bots: {error}</p>}
      
      {!loading && !error && bots.length === 0 && (
        <div style={{ textAlign: 'center', padding: '4rem', backgroundColor: '#f9f9f9', borderRadius: '12px' }}>
          <p style={{ fontSize: '1.2rem', color: '#666' }}>No bots created yet.</p>
          <button className="btn-primary" onClick={onCreateClick} style={{ marginTop: '1rem' }}>Create your first bot</button>
        </div>
      )}

      {!loading && !error && bots.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {bots.map((bot) => (
            <Link href={`/bots/${bot.id}`} key={bot.id} style={{ textDecoration: 'none', color: 'inherit' }}>
              <div style={{ 
                border: '1px solid #e5e5e5', 
                borderRadius: '12px', 
                padding: '1.5rem',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                backgroundColor: '#fff',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                  <span style={{ fontSize: '24px' }}>🤖</span>
                  <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{bot.name}</h3>
                </div>
                <p style={{ margin: '0 0 1rem 0', color: '#666', flexGrow: 1 }}>{bot.description || "No description provided."}</p>
                <div style={{ fontSize: '0.85rem', color: '#999', marginTop: 'auto', borderTop: '1px solid #eee', paddingTop: '12px' }}>
                  Created {new Date(bot.created_at).toLocaleDateString()}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
