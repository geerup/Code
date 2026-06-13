# RAG Knowledge Assistant

> Portfolio project #4 — **AI agents / LLM apps**

Ask questions over **your own documents** and get answers grounded *only* in those
documents, with **inline citations**. The LLM and embedding layers are pluggable: it
runs on a **local model via [Ollama](https://ollama.com)** by default, and falls back to
a deterministic offline mode so a fresh clone (and CI) works with **zero external
services**.

![CI](https://github.com/geerup/Code/actions/workflows/rag-ci.yml/badge.svg)

## Why this project
Retrieval-augmented generation is the single most common pattern in production LLM apps.
This build shows the whole pipeline end to end — ingestion → chunking → embeddings →
vector search → grounded generation with citations → streaming UI — with tests, CI, and
a real deployment story, rather than a notebook demo.

## Architecture
```
┌─────────────┐     ingest text/file      ┌──────────────────────────────┐
│  Next.js UI │ ───────────────────────▶ │  FastAPI backend             │
│ (Vercel)    │                           │                              │
│             │     POST /chat (NDJSON    │  chunk → embed → SQLite      │
│  streaming  │ ◀───  stream: citations   │  vector store (cosine)       │
│  answer +   │       then tokens)        │                              │
│  citations  │                           │  retrieve top-k → prompt →   │
└─────────────┘                           │  LLM stream                  │
                                          └──────────────┬───────────────┘
                                                         │ HTTP
                                                  ┌──────▼───────┐
                                                  │  Ollama      │
                                                  │ llama3.2 +   │
                                                  │ nomic-embed  │
                                                  └──────────────┘
```

**Design choices & trade-offs**
- **Pluggable providers** (`embeddings.py`, `llm.py`): an `ollama` implementation plus a
  deterministic `fake` one. Tests/CI use `fake`; the app auto-falls-back to `fake` if
  Ollama is unreachable, so it never hard-crashes on a missing model.
- **SQLite + brute-force cosine** vector store (`store.py`): embeddings are L2-normalized
  so similarity is a single dot product. Brute force is plenty for a portfolio-scale
  corpus and keeps dependencies tiny — swapping in a real ANN index is exactly what
  portfolio project #8 (*vector search from scratch*) explores.
- **NDJSON streaming** (`main.py`): the `/chat` response streams a citations frame first,
  then token frames, so the UI can render sources immediately and the answer as it lands.

## Tech stack
| Layer | Tech |
|-------|------|
| Backend | Python 3.11, FastAPI, NumPy, SQLite |
| LLM / embeddings | Ollama (`llama3.2`, `nomic-embed-text`), pluggable |
| Frontend | Next.js 14 (App Router), TypeScript |
| CI | GitHub Actions (ruff + pytest, tsc + next build) |
| Deploy | Backend → Fly.io/Render · Frontend → Vercel |

## Run locally
### 1. Backend
```bash
cd backend
pip install . ".[dev]"

# Option A — fully offline (deterministic fake providers, no model needed):
LLM_PROVIDER=fake EMBED_PROVIDER=fake uvicorn app.main:app --reload

# Option B — real local LLM via Ollama:
ollama serve
ollama pull llama3.2 && ollama pull nomic-embed-text
uvicorn app.main:app --reload      # auto-detects Ollama on :11434
```
Backend runs at http://localhost:8000 (`/health`, `/docs` for the OpenAPI UI).

### 2. Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local      # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                            # http://localhost:3000
```

## Test & lint
```bash
cd backend  && ruff check . && python -m pytest -q          # 19 tests
cd frontend && npm run typecheck && npm run build
```

## Deploy
- **Backend (Fly.io):** `fly launch --no-deploy`, `fly volumes create rag_data --size 1`,
  set `OLLAMA_HOST` to a reachable Ollama endpoint via `fly secrets set`, then `fly deploy`.
  See `backend/fly.toml` + `backend/Dockerfile`. (Render: point a Docker service at the
  same Dockerfile.)
- **Frontend (Vercel):** import the `frontend/` directory, set `NEXT_PUBLIC_API_URL` to the
  backend URL, deploy.

> Production note: Ollama needs a host with the model loaded. Run it on a GPU box (or any
> always-on machine) and point `OLLAMA_HOST` at it, or switch the provider for a hosted API.

## API
| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/health` | — | Status + active providers |
| GET | `/documents` | — | List ingested documents |
| POST | `/ingest` | `{source, text}` | Chunk + embed + store text |
| POST | `/ingest/file` | multipart `file` | Ingest a UTF-8 text/markdown file |
| POST | `/chat` | `{question}` | NDJSON stream: citations, then tokens |

## What I learned / what's next
- Streaming NDJSON keeps the UI responsive and makes citations feel instant.
- Normalizing embeddings up front turns cosine search into one matrix–vector product.
- **Next:** PDF ingestion, per-collection namespaces, an ANN index (project #8), and an
  eval harness scoring answer groundedness against the retrieved context.
