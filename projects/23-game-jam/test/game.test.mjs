import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createGame, setFlap, step } from '../src/game.js';

test('bird falls under gravity when not flapping', () => {
  const g = createGame({ seed: 1 });
  const y0 = g.bird.y;
  step(g, 0.1);
  assert.ok(g.bird.y > y0, 'bird should fall');
});

test('holding the button counteracts gravity (rises)', () => {
  const g = createGame({ seed: 1 });
  setFlap(g, true);
  const y0 = g.bird.y;
  for (let i = 0; i < 5; i++) step(g, 1 / 60);
  assert.ok(g.bird.y < y0, 'sustained flap should lift the bird');
});

test('falling off the bottom ends the game', () => {
  const g = createGame({ seed: 1 });
  for (let i = 0; i < 600 && !g.over; i++) step(g, 1 / 60);
  assert.equal(g.over, true);
});

test('walls spawn over time', () => {
  const g = createGame({ seed: 2 });
  // Autopilot: flap only when below mid-screen, so the bird hovers and survives
  // long enough for the spawn timer (1.1s) to fire.
  for (let i = 0; i < 180 && !g.over; i++) {
    setFlap(g, g.bird.y > g.height / 2);
    step(g, 1 / 60);
  }
  assert.ok(g.walls.length > 0, 'walls should have spawned');
});

test('obstacle stream is deterministic for a seed', () => {
  function firstWallGap() {
    const g = createGame({ seed: 42 });
    setFlap(g, true);
    while (g.walls.length === 0 && !g.over) step(g, 1 / 60);
    return g.walls[0]?.gapY;
  }
  assert.equal(firstWallGap(), firstWallGap());
});

test('a game over freezes further updates', () => {
  const g = createGame({ seed: 1 });
  g.over = true;
  const snapshot = { ...g.bird };
  step(g, 0.5);
  assert.deepEqual(g.bird, snapshot);
});
