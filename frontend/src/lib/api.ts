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
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
//  Ingest
// -------------------------------------------------------------------------- //

/**
 * Crawl a website and store its embeddings in Pinecone.
 * This can take a minute or more depending on the site size.
 */
export async function ingestWebsite(body: IngestRequest): Promise<IngestResponse> {
  return apiFetch<IngestResponse>("/api/v1/ingest/ingest", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/**
 * Fetch the list of previously crawled sites from Supabase.
 */
export async function getCrawlHistory(): Promise<CrawlJob[]> {
  return apiFetch<CrawlJob[]>("/api/v1/ingest/history");
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
