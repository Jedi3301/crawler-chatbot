# Chatbot Crawler — Full-Stack RAG App

A modular full-stack app that crawls websites, stores their content as vector embeddings, and lets you chat with them using Groq AI.

---

## Architecture

```
chatbot-crawler/
├── backend/     FastAPI — crawl, embed, vector, chat
└── frontend/    Next.js — Apple-inspired split-screen UI
```

### RAG Pipeline
```
User enters URL
  → Firecrawl crawls the site
  → Text split into 1000-char chunks (200-char overlap)
  → sentence-transformers embeds each chunk (384-dim)
  → Pinecone stores vectors + metadata
  → Supabase stores crawl job record

User asks a question
  → Question embedded → Pinecone similarity search
  → Top-5 chunks retrieved as context
  → Groq llama-3.3-70b-versatile generates answer
  → Answer + source URLs returned
```

---

## Setup

### 1. Required accounts & API keys

| Service | URL | Cost |
|---|---|---|
| Firecrawl | [firecrawl.dev](https://firecrawl.dev) | Free tier |
| Pinecone | [pinecone.io](https://pinecone.io) | Free serverless |
| Supabase | [supabase.com](https://supabase.com) | Free tier |
| Groq | [console.groq.com](https://console.groq.com) | Free tier |

### 2. Pinecone — Create an index

In the Pinecone console, create a **serverless** index with:
- **Dimensions:** `384`
- **Metric:** `cosine`

> The embedding model (`all-MiniLM-L6-v2`) produces 384-dim vectors.

### 3. Supabase — Create tables

Run this SQL in your Supabase project's SQL editor:

```sql
create table crawl_jobs (
  id          uuid primary key default gen_random_uuid(),
  url         text not null,
  status      text not null default 'completed',
  total_pages int  default 0,
  created_at  timestamptz default now()
);

create table pages (
  id           uuid primary key default gen_random_uuid(),
  crawl_job_id uuid references crawl_jobs(id) on delete cascade,
  url          text not null,
  content      text,
  created_at   timestamptz default now()
);
```

### 4. Backend

```powershell
# From project root
cd backend

# Create virtual environment (if not already done)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# → Edit .env and fill in all API keys

# Start the server
uvicorn app.main:app --reload
```

API docs: **http://localhost:8000/docs**

### 5. Frontend

```powershell
cd frontend

# Copy env file
copy .env.local.example .env.local

# Install and run
npm install
npm run dev
```

App: **http://localhost:3000**

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/ingest/ingest` | Crawl + embed + store a website |
| `GET` | `/api/v1/ingest/history` | List previously crawled sites |
| `POST` | `/api/v1/chat/message` | Ask a question (RAG) |
| `POST` | `/api/v1/crawler/crawl` | Raw crawl (no embedding) |
| `POST` | `/api/v1/crawler/scrape` | Scrape a single page |
| `GET` | `/health` | Health check |
