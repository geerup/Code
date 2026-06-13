# 🏆 Leaderboard + Achievements Service (#22)

A small backend any game can POST to: submit scores, fetch top-N leaderboards,
unlock achievements. Pure Go stdlib (Go 1.24 `net/http` routing), with
**HMAC-signed submissions** so clients can't forge scores.

## API
```
GET  /health
POST /scores                 { player, game, points, signature }
GET  /leaderboard/{game}?limit=10
POST /achievements           { player, key }
GET  /achievements/{player}
```

Submissions are verified with `HMAC-SHA256(secret, "player:game:points")`. The
client signs with a shared secret; the server rejects anything that doesn't
match (constant-time compare). Set `LEADERBOARD_SECRET=""` to disable for local play.

## Architecture
- `internal/store` — `Store` interface + concurrency-safe in-memory impl (keeps
  each player's best per game). A Postgres impl slots in behind the same interface.
- `internal/api` — HTTP handlers + the HMAC signing/verification.
- `cmd/server` — wiring.

The `Store` seam means the API is tested end-to-end (`httptest`) with no database.

## Run
```bash
go test ./...
LEADERBOARD_SECRET=dev PORT=8080 go run ./cmd/server
```

## What I learned / next
- Designing an injectable persistence boundary; HMAC request signing as basic
  anti-cheat; Go 1.22+ method-and-path routing.
- Next: a Postgres `Store`, rate limiting per player (reuse #26), and seasonal
  (time-windowed) leaderboards.
