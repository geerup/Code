# 🐦 microfeed — Real-time Social App (#01)

A niche microblog: sign up, post (≤280 chars), follow people, like posts, and
watch a **home feed that updates in real time** over Server-Sent Events. Full
stack in Go (stdlib) + a static client.

## Features
- **Auth** with token sessions; passwords stored **salted + stretched-hashed**
  (50k SHA-256 rounds — bcrypt/argon2 noted for production).
- **Follow graph + home timeline:** your feed is posts from people you follow
  (plus your own), newest first. An **Explore** tab surfaces everyone.
- **Likes** (toggle) and **real-time updates** via `/api/events` (SSE) — post in
  one tab, see it appear in another.

## Architecture
- `internal/social` — domain core (users, follows, posts, likes, feed) behind a
  store; concurrency-safe, **unit-tested** (feed visibility, like toggling, post
  validation, auth).
- `internal/api` — HTTP handlers, token-session auth middleware, SSE broadcaster;
  tested end-to-end with `httptest` (auth required, register/login, feed
  visibility after follow).
- `cmd/server` — wiring + static file server. `Dockerfile` → Fly.

## Run
```bash
go test ./...                 # domain + API tests, no DB
go run ./cmd/server           # http://localhost:8080 (open two tabs to see SSE)
```

## What I learned / next
- Full-stack data modeling (follow graph → timeline), session auth, password
  hashing, and pushing live updates with SSE.
- Next: Postgres `Store`, cursor pagination, notifications, and a Next.js client
  reusing this API.
