# 🗂️ Portfolio Capstone (#30) ★

The **front door** to the whole portfolio: a filterable index of all 30 projects,
generated from a single, **unit-tested catalog** (`src/catalog.js`). Filter by
theme (AI / Games / Creative / Systems / Full-stack) or show only the five
flagships; each card links to that project's source and README (swap to live
demo URLs as each deploys).

## Why a tested catalog
The catalog is the source of truth, so a test guards its integrity — exactly 30
entries, unique ids covering 1–30, id-prefixed slugs, valid themes/status, and
exactly five flagships. The page can't silently drift out of sync with reality.

## Run
```bash
npm test          # catalog integrity (node --test)
npm run serve     # http://localhost:8089
```

## The story it tells
- **AI agents/LLM apps** — RAG, agent runner, eval harness, multi-agent crew ★,
  code-review CLI, chat-bot, voice, semantic search.
- **Games/creative** — multiplayer arena, AI Game Master ★, AI party game ★,
  procedural gen, shaders, physics, level editor, game jam.
- **Systems** — vector search, KV store ★, message queue, rate limiter,
  observability.
- **Full-stack** — social app, data dashboard, SaaS starter, and this capstone ★.

Every project: tests + CI; flagships go deep.

## What I learned / next
- Treating presentation content as tested data; building a generated index that
  can't lie about its own contents.
- Next: pull live deploy URLs + CI badge status per project, and add screenshots.
