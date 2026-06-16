/**
 * lib/types.ts
 *
 * Shared TypeScript types that match the backend Pydantic schemas exactly.
 * Update these if you change the backend schemas.
 */

// ── Ingest ──────────────────────────────────────────────────────────────── //

export interface IngestRequest {
  url: string;
  bot_id: string;
  limit?: number;
}

export interface IngestResponse {
  crawl_job_id: string;
  url: string;
  pages_crawled: number;
  chunks_stored: number;
  message: string;
}

export interface Bot {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface CrawlJob {
  id: string;
  bot_id: string;
  url: string;
  status: string;
  total_pages: number;
  created_at: string;
}

// ── Chat ────────────────────────────────────────────────────────────────── //

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  question: string;
  bot_id: string;
  history: ChatMessage[];
}

export interface SourceChunk {
  url: string;
  text: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  sources: SourceChunk[];
}
