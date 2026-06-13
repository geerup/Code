import { test } from 'node:test';
import assert from 'node:assert/strict';
import { generate } from '../dungeon.js';

test('same seed produces identical tiles', () => {
  const a = generate(60, 40, 42n);
  const b = generate(60, 40, 42n);
  assert.deepEqual([...a.tiles], [...b.tiles]);
});

test('different seeds differ', () => {
  const a = generate(60, 40, 1n);
  const b = generate(60, 40, 2n);
  assert.notDeepEqual([...a.tiles], [...b.tiles]);
});

test('produces rooms and carved floor', () => {
  const d = generate(80, 50, 99n);
  assert.ok(d.rooms.length > 0);
  const floor = d.tiles.reduce((s, t) => s + t, 0);
  assert.ok(floor > 50);
});

test('all rooms reachable from the first (flood fill)', () => {
  const d = generate(80, 50, 7n);
  const { width, height, tiles, rooms } = d;
  const seen = new Uint8Array(width * height);
  const cx = rooms[0].x + (rooms[0].w >> 1), cy = rooms[0].y + (rooms[0].h >> 1);
  const stack = [[cx, cy]];
  while (stack.length) {
    const [x, y] = stack.pop();
    if (x < 0 || y < 0 || x >= width || y >= height) continue;
    const i = y * width + x;
    if (seen[i] || tiles[i] !== 1) continue;
    seen[i] = 1;
    stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]);
  }
  for (const r of rooms) {
    const rx = r.x + (r.w >> 1), ry = r.y + (r.h >> 1);
    assert.equal(seen[ry * width + rx], 1, `room ${JSON.stringify(r)} unreachable`);
  }
});
