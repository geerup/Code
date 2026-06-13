# 🔭 Observability Dashboard (#27)

A small metrics stack built from scratch: a **counter / gauge / histogram**
library with **Prometheus-format** and JSON exposition, a demo server that
generates synthetic traffic, and a live dashboard showing request rate, errors,
in-flight gauge, and **latency percentiles (p50/p90/p99)**.

## The library (`metrics/registry.py`)
- **Counter** (monotonic), **Gauge** (up/down), **Histogram** (bucketed, with
  count/sum and **quantile estimation** from bucket boundaries).
- **Registry** renders the Prometheus text exposition format *and* JSON.
- Thread-safe; pure data structures → the percentile math and exposition are
  fully unit-tested with no server.

## Run
```bash
python -m unittest discover -s tests          # metrics + percentile + format tests
python server.py                              # http://localhost:8080
#   /metrics       Prometheus text
#   /metrics.json  dashboard feed
#   /              live dashboard
```

The same registry could instrument the other backend projects (#02, #22, #24,
#25) to make this their shared monitoring pane.

## What I learned / next
- How counters/gauges/histograms differ, how Prometheus exposition works, and
  estimating percentiles from buckets (and its accuracy limits).
- Next: labels/dimensions, exponential-decay summaries for exact quantiles, and
  scraping the other services in this monorepo.
