# 🚦 Rate Limiter + Tiny Load Balancer (#26)

Two classic infra building blocks in Go, with a demo that wires them into a
rate-limited reverse proxy.

## Rate limiter (`limiter/`)
Per-key **token bucket**: a bucket refills at a steady rate up to a burst
capacity; each request spends a token, and over-limit requests are rejected.
Ships as `net/http` middleware returning **429 + Retry-After**.

- **Deterministic tests:** the clock is injectable, so refill behavior is
  verified by advancing a fake clock — no `time.Sleep`. Tests cover burst
  exhaustion, time-based refill, capping at burst, and per-key isolation.

## Load balancer (`balancer/`)
Selects healthy backends via **round-robin** or **least-connections**, tracks
health (dead backends are skipped), and counts in-flight connections via
`Acquire()/release()`.

- Tests cover even round-robin distribution, skipping unhealthy backends, the
  no-healthy-backend error, and least-conn picking the idle backend.

## Run
```bash
go test ./...
go run ./cmd/demo        # rate-limited proxy over 3 in-process backends
```

## What I learned / next
- Token-bucket math, testing time without sleeping, and basic balancing
  strategies + health awareness.
- Next: sliding-window log limiter for smoother limits, active HTTP health
  checks, and weighted/EWMA-latency backend selection.
