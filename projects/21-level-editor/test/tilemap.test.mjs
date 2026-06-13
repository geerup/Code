import { test } from 'node:test';
import assert from 'node:assert/strict';
import { TileMap } from '../src/tilemap.js';

test('new map is filled and sized correctly', () => {
  const m = new TileMap(4, 3, 0);
  assert.equal(m.data.length, 12);
  assert.equal(m.count(0), 12);
});

test('set/get within bounds, -1 out of bounds', () => {
  const m = new TileMap(3, 3);
  m.set(1, 1, 2);
  assert.equal(m.get(1, 1), 2);
  assert.equal(m.get(9, 9), -1);
});

test('flood fill spreads over contiguous like tiles only', () => {
  const m = new TileMap(3, 3, 0);
  m.set(1, 0, 1); m.set(1, 1, 1); m.set(1, 2, 1); // a wall column splits the map
  m.fill(0, 0, 2);
  assert.equal(m.get(0, 0), 2);
  assert.equal(m.get(0, 1), 2);
  assert.equal(m.get(2, 0), 0, 'fill must not cross the wall');
  assert.equal(m.get(1, 1), 1, 'wall untouched');
});

test('resize preserves overlapping cells', () => {
  const m = new TileMap(2, 2, 0);
  m.set(0, 0, 5); m.set(1, 1, 4);
  m.resize(4, 4);
  assert.equal(m.width, 4);
  assert.equal(m.get(0, 0), 5);
  assert.equal(m.get(1, 1), 4);
  assert.equal(m.get(3, 3), 0);
});

test('round-trip JSON serialization', () => {
  const m = new TileMap(3, 2, 0);
  m.set(2, 1, 3);
  const back = TileMap.fromJSON(JSON.parse(JSON.stringify(m.toJSON())));
  assert.deepEqual(back.data, m.data);
  assert.equal(back.get(2, 1), 3);
});

test('fromJSON rejects malformed input', () => {
  assert.throws(() => TileMap.fromJSON({ width: 2, height: 2, data: [0] }));
  assert.throws(() => TileMap.fromJSON(null));
});
