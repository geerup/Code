// Time-series primitives behind the dashboard: a fixed-capacity ring buffer of
// (timestamp, value) samples, with windowing, aggregate stats, and bucketed
// downsampling for drawing. Pure and deterministic so it's unit-tested; the
// chart and the (simulated or real WebSocket) stream sit on top.

export class TimeSeries {
  constructor(capacity = 600) {
    this.capacity = capacity;
    this.t = []; // timestamps (ms)
    this.v = []; // values
  }

  push(timestamp, value) {
    this.t.push(timestamp);
    this.v.push(value);
    if (this.t.length > this.capacity) {
      this.t.shift();
      this.v.shift();
    }
  }

  get length() { return this.t.length; }

  latest() {
    return this.length ? { t: this.t[this.length - 1], v: this.v[this.length - 1] } : null;
  }

  // Samples with timestamp >= (latest - windowMs).
  window(windowMs) {
    if (!this.length) return [];
    const cutoff = this.t[this.length - 1] - windowMs;
    const out = [];
    for (let i = 0; i < this.length; i++) {
      if (this.t[i] >= cutoff) out.push({ t: this.t[i], v: this.v[i] });
    }
    return out;
  }

  // min / max / avg / last over the most recent windowMs (or all if omitted).
  stats(windowMs = Infinity) {
    const pts = windowMs === Infinity
      ? this.v.map((v, i) => ({ t: this.t[i], v }))
      : this.window(windowMs);
    if (!pts.length) return { min: 0, max: 0, avg: 0, last: 0, count: 0 };
    let min = Infinity, max = -Infinity, sum = 0;
    for (const p of pts) {
      if (p.v < min) min = p.v;
      if (p.v > max) max = p.v;
      sum += p.v;
    }
    return { min, max, avg: sum / pts.length, last: pts[pts.length - 1].v, count: pts.length };
  }

  // Reduce to `buckets` averaged points for smooth rendering of long series.
  downsample(buckets) {
    const n = this.length;
    if (n <= buckets) return this.v.map((v, i) => ({ t: this.t[i], v }));
    const out = [];
    const size = n / buckets;
    for (let b = 0; b < buckets; b++) {
      const start = Math.floor(b * size);
      const end = Math.floor((b + 1) * size);
      let sum = 0;
      for (let i = start; i < end; i++) sum += this.v[i];
      out.push({ t: this.t[start], v: sum / (end - start) });
    }
    return out;
  }
}

// Manages several named series fed by a stream of {metric, t, v} events.
export class Dashboard {
  constructor(capacity = 600) {
    this.capacity = capacity;
    this.series = new Map();
  }

  ingest(event) {
    if (!this.series.has(event.metric)) {
      this.series.set(event.metric, new TimeSeries(this.capacity));
    }
    this.series.get(event.metric).push(event.t, event.v);
  }

  metrics() { return [...this.series.keys()].sort(); }
  get(metric) { return this.series.get(metric); }
}
