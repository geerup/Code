"""A tiny metrics library: counters, gauges, and histograms, plus a registry
that renders Prometheus text and JSON. Pure data structures (thread-safe), so
the aggregation/percentile logic is unit-tested without a server.
"""
from __future__ import annotations

import threading
from bisect import bisect_left
from dataclasses import dataclass, field

# Default histogram buckets (e.g. request latency in ms), upper bounds.
DEFAULT_BUCKETS = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]


class Counter:
    """Monotonically increasing value (requests, errors)."""

    def __init__(self) -> None:
        self._v = 0.0
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0) -> None:
        if amount < 0:
            raise ValueError("counters cannot decrease")
        with self._lock:
            self._v += amount

    @property
    def value(self) -> float:
        return self._v


class Gauge:
    """A value that goes up and down (in-flight requests, temperature)."""

    def __init__(self) -> None:
        self._v = 0.0
        self._lock = threading.Lock()

    def set(self, v: float) -> None:
        with self._lock:
            self._v = v

    def inc(self, amount: float = 1.0) -> None:
        with self._lock:
            self._v += amount

    def dec(self, amount: float = 1.0) -> None:
        with self._lock:
            self._v -= amount

    @property
    def value(self) -> float:
        return self._v


class Histogram:
    """Bucketed distribution with count/sum and quantile estimation."""

    def __init__(self, buckets: list[float] | None = None) -> None:
        self.bounds = sorted(buckets or DEFAULT_BUCKETS)
        self.counts = [0] * len(self.bounds)  # observations <= each bound
        self.inf = 0  # observations greater than the largest bound
        self.sum = 0.0
        self.count = 0
        self._lock = threading.Lock()

    def observe(self, v: float) -> None:
        with self._lock:
            self.count += 1
            self.sum += v
            idx = bisect_left(self.bounds, v)
            if idx < len(self.bounds):
                self.counts[idx] += 1
            else:
                self.inf += 1

    @property
    def avg(self) -> float:
        return self.sum / self.count if self.count else 0.0

    def quantile(self, q: float) -> float:
        """Estimate the q-quantile (0..1) from bucket boundaries."""
        if self.count == 0:
            return 0.0
        target = q * self.count
        cumulative = 0
        for bound, c in zip(self.bounds, self.counts):
            cumulative += c
            if cumulative >= target:
                return bound
        return float("inf") if self.inf else self.bounds[-1]


@dataclass
class Registry:
    counters: dict[str, Counter] = field(default_factory=dict)
    gauges: dict[str, Gauge] = field(default_factory=dict)
    histograms: dict[str, Histogram] = field(default_factory=dict)

    def counter(self, name: str) -> Counter:
        return self.counters.setdefault(name, Counter())

    def gauge(self, name: str) -> Gauge:
        return self.gauges.setdefault(name, Gauge())

    def histogram(self, name: str, buckets: list[float] | None = None) -> Histogram:
        if name not in self.histograms:
            self.histograms[name] = Histogram(buckets)
        return self.histograms[name]

    def to_json(self) -> dict:
        return {
            "counters": {n: c.value for n, c in self.counters.items()},
            "gauges": {n: g.value for n, g in self.gauges.items()},
            "histograms": {
                n: {
                    "count": h.count,
                    "avg": round(h.avg, 2),
                    "p50": h.quantile(0.50),
                    "p90": h.quantile(0.90),
                    "p99": h.quantile(0.99),
                }
                for n, h in self.histograms.items()
            },
        }

    def render_prometheus(self) -> str:
        """Render the Prometheus text exposition format."""
        lines: list[str] = []
        for name, c in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {c.value}")
        for name, g in self.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {g.value}")
        for name, h in self.histograms.items():
            lines.append(f"# TYPE {name} histogram")
            cumulative = 0
            for bound, c in zip(h.bounds, h.counts):
                cumulative += c
                lines.append(f'{name}_bucket{{le="{bound}"}} {cumulative}')
            lines.append(f'{name}_bucket{{le="+Inf"}} {cumulative + h.inf}')
            lines.append(f"{name}_sum {h.sum}")
            lines.append(f"{name}_count {h.count}")
        return "\n".join(lines) + "\n"
