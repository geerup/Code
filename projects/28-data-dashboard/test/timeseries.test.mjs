import { test } from 'node:test';
import assert from 'node:assert/strict';
import { TimeSeries, Dashboard } from '../src/timeseries.js';

test('ring buffer drops oldest beyond capacity', () => {
  const ts = new TimeSeries(3);
  for (let i = 0; i < 5; i++) ts.push(i, i * 10);
  assert.equal(ts.length, 3);
  assert.deepEqual(ts.v, [20, 30, 40]);
  assert.deepEqual(ts.latest(), { t: 4, v: 40 });
});

test('window returns only recent samples', () => {
  const ts = new TimeSeries();
  for (let i = 0; i <= 10; i++) ts.push(i * 1000, i); // 0..10s
  const w = ts.window(3000); // last 3s -> t >= 7000
  assert.deepEqual(w.map((p) => p.t), [7000, 8000, 9000, 10000]);
});

test('stats computes min/max/avg/last', () => {
  const ts = new TimeSeries();
  [5, 1, 9, 3].forEach((v, i) => ts.push(i, v));
  const s = ts.stats();
  assert.equal(s.min, 1);
  assert.equal(s.max, 9);
  assert.equal(s.avg, 4.5);
  assert.equal(s.last, 3);
  assert.equal(s.count, 4);
});

test('stats on empty series is zeroed', () => {
  assert.deepEqual(new TimeSeries().stats(), { min: 0, max: 0, avg: 0, last: 0, count: 0 });
});

test('downsample reduces to N averaged buckets', () => {
  const ts = new TimeSeries(1000);
  for (let i = 0; i < 100; i++) ts.push(i, i);
  const ds = ts.downsample(10);
  assert.equal(ds.length, 10);
  // First bucket averages 0..9 = 4.5
  assert.equal(ds[0].v, 4.5);
});

test('downsample passes through when already small', () => {
  const ts = new TimeSeries();
  ts.push(0, 1); ts.push(1, 2);
  assert.equal(ts.downsample(10).length, 2);
});

test('dashboard routes events to named series', () => {
  const d = new Dashboard();
  d.ingest({ metric: 'cpu', t: 0, v: 10 });
  d.ingest({ metric: 'mem', t: 0, v: 50 });
  d.ingest({ metric: 'cpu', t: 1, v: 20 });
  assert.deepEqual(d.metrics(), ['cpu', 'mem']);
  assert.equal(d.get('cpu').length, 2);
  assert.equal(d.get('cpu').latest().v, 20);
});
