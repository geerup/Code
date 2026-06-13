import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mulberry32, hashSeed, rngFromSeed } from '../src/rng.js';

test('mulberry32 is deterministic for a given seed', () => {
  const a = mulberry32(42);
  const b = mulberry32(42);
  for (let i = 0; i < 100; i++) assert.equal(a(), b());
});

test('mulberry32 outputs are in [0, 1)', () => {
  const r = mulberry32(7);
  for (let i = 0; i < 1000; i++) {
    const v = r();
    assert.ok(v >= 0 && v < 1, `value ${v} out of range`);
  }
});

test('different seeds diverge', () => {
  const a = mulberry32(1)();
  const b = mulberry32(2)();
  assert.notEqual(a, b);
});

test('hashSeed is stable and 32-bit', () => {
  assert.equal(hashSeed('hello'), hashSeed('hello'));
  assert.ok(hashSeed('hello') <= 0xffffffff);
  assert.notEqual(hashSeed('hello'), hashSeed('world'));
});

test('rngFromSeed reproducible from string', () => {
  const a = rngFromSeed('seed-1');
  const b = rngFromSeed('seed-1');
  assert.equal(a(), b());
});
