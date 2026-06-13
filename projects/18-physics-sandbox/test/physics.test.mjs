import { test } from 'node:test';
import assert from 'node:assert/strict';
import { World, buildGrid } from '../src/physics.js';

test('gravity accelerates a free point downward', () => {
  const w = new World({ gravity: 1000, friction: 1 });
  const p = w.addPoint(100, 100);
  const y0 = p.y;
  w.step(0.1);
  assert.ok(p.y > y0, 'point should fall');
});

test('a pinned point does not move', () => {
  const w = new World({ gravity: 1000 });
  const p = w.addPoint(50, 50, true);
  for (let i = 0; i < 10; i++) w.step(0.016);
  assert.equal(p.x, 50);
  assert.equal(p.y, 50);
});

test('a stick keeps two points near its rest length', () => {
  const w = new World({ gravity: 0, friction: 1 });
  const a = w.addPoint(0, 0, true);
  const b = w.addPoint(100, 0);
  const s = w.addStick(a, b); // rest length 100
  // Yank b far away, then relax.
  b.x = 300; b.px = 300;
  for (let i = 0; i < 60; i++) w.step(0.016, 10);
  const dist = Math.hypot(b.x - a.x, b.y - a.y);
  assert.ok(Math.abs(dist - s.length) < 5, `dist ${dist} should approach rest length ${s.length}`);
});

test('points stay within bounds', () => {
  const w = new World({ width: 200, height: 200, gravity: 5000 });
  const p = w.addPoint(100, 100);
  for (let i = 0; i < 200; i++) w.step(0.016);
  assert.ok(p.x >= 0 && p.x <= 200, `x ${p.x} in bounds`);
  assert.ok(p.y >= 0 && p.y <= 200, `y ${p.y} in bounds`);
});

test('simulation is deterministic for identical setups', () => {
  function run() {
    const w = new World({ gravity: 1200 });
    buildGrid(w, 4, 4, 20, 50, 10);
    for (let i = 0; i < 50; i++) w.step(0.016);
    return w.points.map((p) => [p.x, p.y]);
  }
  assert.deepEqual(run(), run());
});

test('buildGrid wires the expected number of sticks', () => {
  const w = new World();
  buildGrid(w, 3, 3, 10);
  // horizontal: rows*(cols-1)=3*2=6; vertical: cols*(rows-1)=3*2=6 => 12
  assert.equal(w.sticks.length, 12);
  assert.equal(w.points.length, 9);
});
