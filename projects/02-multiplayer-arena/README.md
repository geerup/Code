# 🪙 Coin Arena — Real-time Multiplayer (#02)

An authoritative-server multiplayer arena: players move in real time over
WebSocket and race to collect coins. The **server owns the simulation** (no
client-trusted positions), ticks at a fixed 30 Hz, and broadcasts world
snapshots to every client.

## Architecture
- `internal/game` — the **transport-free authoritative simulation**: world,
  players, coin pickups, normalized input, fixed-timestep `Step(dt)`. Pure and
  deterministic (seeded PRNG) → fully unit-tested.
- `internal/hub` — connection coordinator + game loop, written against a
  `Client` interface so it's tested with **fake clients, no network**.
- `cmd/server` — WebSocket transport (gorilla) + static file server. Each
  connection is a `wsClient` with a non-blocking outbound channel (slow clients
  drop frames instead of stalling the tick loop).

## Why authoritative + fixed timestep
Trusting clients invites cheating and desync. One server simulation, broadcast
to all, is the standard for fair real-time play; the fixed `dt` keeps physics
reproducible.

## Run
```bash
go test ./...                 # game + hub logic, no network
go run ./cmd/server           # http://localhost:8080  (open two tabs)
```

## What I learned / next
- Authoritative netcode, fixed-timestep loops, decoupling simulation from
  transport so the hard part is testable.
- Next: client-side interpolation/prediction, per-room matchmaking (reuse the
  hub), and server-reconciliation for lag.
