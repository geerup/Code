# 30-Project Portfolio Roadmap

A deliberate path to a software career in **AI/ML + full-stack**, anchored on
**AI agents/LLM apps** and **games/creative**. Built as a mix of small,
fully-deployed projects plus a few deep flagships — every project shipped live
with CI, tests, and a real README.

## Goals
- Prove I can **ship product** *and* understand the **systems underneath**.
- Weight the work toward **AI agents/LLM apps** and **games/creative**.
- Every project: **live deployment + CI + tests + README + demo**.
- By #30, the GitHub timeline tells one clear growth story.

## Quality bar (every project)
- [ ] README: problem, architecture, tech trade-offs, run steps
- [ ] Tests + GitHub Actions CI (lint/test/build) — green badge
- [ ] Live deployment (URL / static site / released binary) + demo GIF
- [ ] Clean commits on a branch, merged via PR
- [ ] "What I learned / what's next" note

## Legend
- **Size:** `S` ≈ a few days · `M` ≈ ~1 week · `L` ≈ 2–3 weeks · `XL` = flagship, multi-week.
- **★** = flagship (the projects interviews will center on).
- **Deploy targets:** Frontend/static → **Vercel** · Backends → **Fly.io / Render** ·
  CLIs → **GitHub Releases** (binaries) · LLM/embeddings → **Ollama** (local model host).

---

## The 30 projects (by theme, stable IDs)

### AI agents / LLM apps (12) — the most hireable lane
| ID | Project | Stack | Deploy | Demonstrates | Size |
|----|---------|-------|--------|--------------|------|
| 04 | [RAG Knowledge Assistant](./projects/04-rag-knowledge-assistant) ✅ | FastAPI + Next.js + Ollama | Fly + Vercel | RAG pipeline, citations, streaming | M |
| 05 | Agentic task runner | Python + Ollama | Fly | Planner→tool-use→execute loop, function calling | L |
| 06 | LLM code-review CLI | Go + Ollama | GH Releases | Streaming review of git diffs, plugins, packaging | M |
| 07 | AI + games bridge ("describe → playable") | Python/TS + Ollama | Vercel + Fly | Structured LLM output → game artifacts | L |
| 09 | **AI Game Master** ★ | Next.js + FastAPI + WS + Ollama | Vercel + Fly | Persistent world state, multiplayer, long-context | XL |
| 10 | **Multiplayer AI party game** ★ | Next.js + Go/FastAPI + WS + Ollama | Vercel + Fly | Real-time rooms, AI judge/host, mobile clients | XL |
| 11 | Prompt-eval / LLM-judge harness | Python | Fly + static report | Eval datasets, scoring, regression dashboards | M |
| 12 | **Multi-agent research crew** ★ | Python + Ollama | Fly | Agent orchestration, tool routing, cited reports | XL |
| 13 | Chat-bot integration (Discord/Telegram) | TS or Python + Ollama | Fly (worker) | Webhooks, conversation memory, deploy-as-a-bot | M |
| 14 | AI NPC dialogue engine | TS + Ollama | Vercel (demo) | Reusable dialogue/state machine, feeds #09/#21 | M |
| 15 | Voice AI assistant | TS/Python + STT/TTS + Ollama | Fly + Vercel | Speech→LLM→speech, latency/streaming | L |
| 16 | Semantic code search | Go/Python + embeddings | Fly | Embed a repo, rank results (applies #08) | M |

### Games / creative (9) — the differentiator
| ID | Project | Stack | Deploy | Demonstrates | Size |
|----|---------|-------|--------|--------------|------|
| 02 | Real-time multiplayer mini-game | Go + TS + WS | Fly + Vercel | Authoritative server, matchmaking, netcode | L |
| 03 | Generative-art / procedural playground | Rust + WASM | Vercel (static) | Creative coding, WASM perf, shareable toy | S |
| 17 | Procedural map/dungeon generator | Rust/TS | Vercel (static) | Algorithms (noise, BSP), seeded determinism | M |
| 18 | Physics / particle sandbox | TS + Canvas/WASM | Vercel (static) | Real-time simulation, perf budgets | M |
| 19 | Retro arcade clone (with a twist) | TS (Canvas) | Vercel (static) | Game loop, collision, juice/polish | S |
| 20 | Shader gallery | WebGL / GLSL | Vercel (static) | GPU shaders, math, visual portfolio piece | S |
| 21 | Tile / level-design editor | TS | Vercel | Tooling UX, exports JSON levels (feeds #09/#14) | M |
| 22 | Leaderboard + achievements service | Go + Postgres | Fly | Backend API, auth, anti-cheat basics | M |
| 23 | Game-jam entry (themed) | engine of choice | itch.io / web | Shipping under constraint, scope control | S |

### Systems / infra depth (5) — what makes seniors trust a junior
| ID | Project | Stack | Deploy | Demonstrates | Size |
|----|---------|-------|--------|--------------|------|
| 08 | Vector search engine from scratch | Rust/Go | GH Releases + Fly | ANN index, embeddings store (the guts of RAG) | L |
| 24 | **Persistent key-value store** ★ | Go/Rust | GH Releases | WAL, LSM/B-tree, crash recovery | XL |
| 25 | Mini message queue / job broker | Go | Fly | Pub/sub, at-least-once delivery, backpressure | L |
| 26 | Rate-limiter + tiny load balancer | Go | Fly | Token bucket, health checks, concurrency | M |
| 27 | Observability dashboard | TS + backend | Fly + Vercel | Metrics/traces across the other projects | M |

### Full-stack / glue (4)
| ID | Project | Stack | Deploy | Demonstrates | Size |
|----|---------|-------|--------|--------------|------|
| 01 | Niche real-time social app | Next.js + Postgres | Vercel + Fly | Auth, live feed, notifications, profiles | L |
| 28 | Real-time data dashboard | TS + WS backend | Vercel + Fly | Live charts, streaming data, caching | M |
| 29 | Auth + billing SaaS starter | Next.js + Stripe (test) | Vercel + Fly | Auth, subscriptions, webhooks — reusable base | L |
| 30 | **Portfolio index site (capstone)** ★ | Next.js | Vercel | Indexes all 30 with live demos + write-ups | XL |

**Theme totals:** AI 12 · Games/creative 9 · Systems 5 · Full-stack 4. **Flagships (★):** 09, 10, 12, 24, 30.

---

## Recommended build order (phased)
Each phase mixes sizes and themes so there's always something demoable, difficulty
ramps up, and the GitHub timeline shows steady growth. Ship one fully (deploy + CI +
README + demo) before starting the next.

**Phase 1 — Foundations & quick wins**
`04 RAG ✅` → `03 genart playground` → `06 code-review CLI` → `19 retro clone`

**Phase 2 — Core AI lane**
`05 agentic runner` → `11 eval harness` → `13 chat-bot` → `16 semantic code search`

**Phase 3 — Games & creative**
`02 multiplayer mini-game` → `17 procedural gen` → `20 shader gallery` → `21 level editor` → `22 leaderboard service`

**Phase 4 — Systems depth**
`08 vector search` → `26 rate-limiter` → `25 message queue` → `24 KV store ★`

**Phase 5 — Flagships & breadth**
`07 AI+games bridge` → `14 NPC dialogue` → `09 AI Game Master ★` → `10 AI party game ★` →
`12 multi-agent crew ★` → `15 voice assistant` → `18 physics sandbox` → `23 game jam` →
`27 observability` → `28 data dashboard` → `01 social app` → `29 SaaS starter`

**Capstone — `30 portfolio index site ★`** (ties everything together; pin the 6 strongest).

> Rationale: front-load fast, deployable wins to build momentum and a green CI habit;
> stack the most-expected **AI** pieces early (they carry interviews); use **games/creative**
> for variety and demo appeal; place **systems** mid-stream once fundamentals are solid;
> and finish with the **flagships** plus a capstone that showcases the whole body of work.

## Repo & profile strategy
- Built in this monorepo under `projects/NN-name/` for now (one CI workflow per project,
  path-filtered). Easy to split the strongest into standalone repos later for profile pins.
- Capstone `#30` is the public front door linking every live demo.

## Progress
- [x] Roadmap defined + detailed (all 30 scoped & ordered)
- [x] **All 30 projects built, tested, and CI-wired** 🎉
- [x] Project #04 (RAG assistant) — tested, CI green
- [x] Phase 1 complete (04, 03, 06, 19)
- [x] All five flagships built (09, 10, 12, 24, 30)
- [x] Portfolio capstone (#30) — generated from a tested catalog
- [ ] Deploy each project live (Vercel / Fly) and link from #30
- [ ] Split the strongest projects into standalone repos for profile pins

### Test coverage at a glance
Every project ships an automated test suite run in CI:
- **Go (9):** 01, 02, 06, 08, 22, 24, 25, 26, 29 — `go vet` + `go test` + `go build`.
- **Python (10):** 05, 07, 09, 10, 11, 12, 13, 15, 16, 27 — `unittest`, stdlib-only,
  LLM/IO injected so tests run offline.
- **JS (10):** 03, 14, 17(web), 18, 19, 20, 21, 23, 28, 30 — `node --test`, zero deps.
- **Rust (1):** 17 — `cargo test` (incl. flood-fill connectivity).

---
*Living document — updated as projects ship.*
