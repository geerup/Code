# 📈 Real-time Data Dashboard (#28)

A live metrics dashboard with smooth streaming line charts. The dashboard
streams simulated metrics out of the box, but the **data core is transport-
agnostic** — point it at a real WebSocket and nothing else changes.

## The tested core (`src/timeseries.js`)
- **`TimeSeries`** — fixed-capacity **ring buffer** of `(t, v)` samples with:
  - `window(ms)` — recent slice,
  - `stats(ms)` — min/max/avg/last/count,
  - `downsample(buckets)` — averaged buckets so long series render fast.
- **`Dashboard`** — routes a stream of `{metric, t, v}` events into named series.

All of this is pure and deterministic, so it's covered by unit tests (ring-buffer
eviction, windowing, stats, downsampling, event routing) — the charting layer is
just Canvas on top.

## Run
```bash
npm test          # time-series core (node --test)
npm run serve     # http://localhost:8088 — live charts
```

To go truly real-time, replace the `setInterval` simulator with
`new WebSocket(url).onmessage = e => dash.ingest(JSON.parse(e.data))`.

## What I learned / next
- Ring buffers for bounded memory, downsampling for render performance, and
  separating data handling from visualization.
- Next: a small Go/Node WS backend pushing real server metrics, brushing/zoom,
  and alert thresholds.
