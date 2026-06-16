/**
 * lib/api.ts
 *
 * All HTTP calls to the FastAPI backend live here.
 * Components never call fetch() directly — they import from this file.
 *
 * This keeps all API URLs, error handling, and response parsing
 * in one place. Changing the backend URL only requires one edit.
 */

import type {
  IngestRequest,
  IngestResponse,
  CrawlJob,
  ChatRequest,
  ChatResponse,
  Bot,
} from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// -------------------------------------------------------------------------- //
//  Generic helper — wraps fetch with error handling
// -------------------------------------------------------------------------- //

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    // Try to extract the FastAPI error detail
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

// -------------------------------------------------------------------------- //
//  Bots
// -------------------------------------------------------------------------- //

export async function createBot(name: string, description?: string): Promise<Bot> {
  return apiFetch<Bot>("/api/v1/bots", {
    method: "POST",
    body: JSON.stringify({ name, description }),
  });
}

export async function updateBot(botId: string, name?: string, description?: string): Promise<Bot> {
  return apiFetch<Bot>(`/api/v1/bots/${botId}`, {
    method: "PATCH",
    body: JSON.stringify({ name, description }),
  });
}

export async function getBots(): Promise<Bot[]> {
  return apiFetch<Bot[]>("/api/v1/bots");
}

export async function getBot(botId: string): Promise<Bot> {
  return apiFetch<Bot>(`/api/v1/bots/${botId}`);
}

export async function getBotKnowledge(botId: string): Promise<CrawlJob[]> {
  return apiFetch<CrawlJob[]>(`/api/v1/bots/${botId}/knowledge`);
}

// -------------------------------------------------------------------------- //
//  Ingest
// -------------------------------------------------------------------------- //

/**
 * Crawl a website and store its embeddings in Pinecone for a specific bot.
 */
export async function ingestWebsite(body: IngestRequest): Promise<IngestResponse> {
  return apiFetch<IngestResponse>("/api/v1/ingest/ingest", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// -------------------------------------------------------------------------- //
//  Chat
// -------------------------------------------------------------------------- //

/**
 * Send a message and get an LLM-generated answer with source attribution.
 */
export async function sendChatMessage(body: ChatRequest): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/api/v1/chat/message", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
