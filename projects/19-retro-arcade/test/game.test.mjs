import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createGame, turn, step } from '../src/game.js';

const fixedRng = () => 0.0; // deterministic apple placement (first free cell)

test('snake starts with length 3 moving right', () => {
  const g = createGame(20, 20, fixedRng);
  assert.equal(g.snake.length, 3);
  assert.equal(g.dir, 'right');
  assert.equal(g.over, false);
});

test('step moves the head forward', () => {
  const g = createGame(20, 20, fixedRng);
  const head = { ...g.snake[0] };
  step(g);
  assert.equal(g.snake[0].x, head.x + 1);
  assert.equal(g.snake[0].y, head.y);
});

test('cannot reverse directly into itself', () => {
  const g = createGame(20, 20, fixedRng);
  turn(g, 'left'); // opposite of right — ignored
  assert.equal(g.nextDir, 'right');
});

test('hitting a wall ends the game', () => {
  const g = createGame(20, 20, fixedRng);
  for (let i = 0; i < 30; i++) step(g); // run east into the wall
  assert.equal(g.over, true);
});

test('eating an apple grows the snake, scores, and flips gravity', () => {
  const g = createGame(20, 20, fixedRng);
  // Place an apple directly ahead of the head.
  g.apple = { x: g.snake[0].x + 1, y: g.snake[0].y };
  const len = g.snake.length;
  step(g);
  assert.equal(g.score, 1);
  assert.equal(g.snake.length, len + 1);
  assert.equal(g.gravity, 'right');
});
